-- MCF-20260920-PAO-NOSSO-ORDER-IDENTITY-001
-- Corrige equivalencia de telefones brasileiros usados pelo site e pela Meta WhatsApp.
-- Mantem o controle de acesso por codigo do pedido + telefone equivalente.

create or replace function public.normalize_br_phone(p_phone text)
returns text
language plpgsql
immutable
parallel safe
set search_path = pg_catalog
as $function$
declare
  v_phone text := regexp_replace(coalesce(p_phone, ''), '[^0-9]', '', 'g');
begin
  -- Meta pode entregar +55 seguido de numero nacional com 10 ou 11 digitos.
  if left(v_phone, 2) = '55' and length(v_phone) in (12, 13) then
    v_phone := substr(v_phone, 3);
  end if;

  -- Compatibilidade com celular brasileiro legado de 8 digitos:
  -- DDD + 8 digitos moveis -> DDD + 9 + 8 digitos.
  if length(v_phone) = 10
     and substring(v_phone from 3 for 1) ~ '^[6-9]$' then
    v_phone := substr(v_phone, 1, 2) || '9' || substr(v_phone, 3);
  end if;

  return v_phone;
end;
$function$;

comment on function public.normalize_br_phone(text)
is 'Canonicaliza telefone brasileiro para comparacao segura entre formulario e Meta WhatsApp.';

create or replace function public.customer_order_status(
  p_order_code text,
  p_customer_phone text
)
returns table(
  order_code text,
  status text,
  total_cents integer,
  fulfillment text,
  payment_method text,
  created_at timestamp with time zone,
  items jsonb
)
language plpgsql
security definer
set search_path = 'public'
as $function$
declare
  v_phone text := public.normalize_br_phone(p_customer_phone);
begin
  if v_phone !~ '^[0-9]{10,11}$' then
    raise exception 'Telefone inválido';
  end if;

  return query
  select
    o.order_code,
    o.status,
    o.total_cents,
    o.fulfillment,
    o.payment_method,
    o.created_at,
    coalesce(
      jsonb_agg(
        jsonb_build_object(
          'product_name', i.product_name,
          'quantity', i.quantity,
          'line_total_cents', i.line_total_cents
        )
        order by i.created_at
      ) filter (where i.id is not null),
      '[]'::jsonb
    )
  from public.orders o
  left join public.order_items i on i.order_id = o.id
  where upper(o.order_code) = upper(trim(p_order_code))
    and public.normalize_br_phone(o.customer_phone) = v_phone
  group by o.id;
end;
$function$;

create or replace function public.create_order(
  p_customer_name text,
  p_customer_phone text,
  p_fulfillment text,
  p_address text,
  p_payment_method text,
  p_notes text,
  p_items jsonb
)
returns table(order_id uuid, order_code text, total_cents integer)
language plpgsql
security definer
set search_path = 'public'
as $function$
declare
  v_order_id uuid;
  v_order_code text;
  v_total integer := 0;
  v_item jsonb;
  v_product public.products%rowtype;
  v_qty integer;
  v_phone text := public.normalize_br_phone(p_customer_phone);
begin
  if char_length(trim(coalesce(p_customer_name,''))) < 2 then
    raise exception 'Nome inválido';
  end if;
  if v_phone !~ '^[0-9]{10,11}$' then
    raise exception 'Telefone inválido';
  end if;
  if p_fulfillment not in ('pickup','delivery') then
    raise exception 'Tipo de recebimento inválido';
  end if;
  if p_fulfillment='delivery' and char_length(trim(coalesce(p_address,''))) < 5 then
    raise exception 'Endereço obrigatório';
  end if;
  if p_payment_method not in ('pix','cash','card') then
    raise exception 'Pagamento inválido';
  end if;
  if jsonb_typeof(p_items) <> 'array'
     or jsonb_array_length(p_items)=0
     or jsonb_array_length(p_items)>30 then
    raise exception 'Itens inválidos';
  end if;

  for v_item in select * from jsonb_array_elements(p_items) loop
    v_qty := coalesce((v_item->>'quantity')::integer,0);
    if v_qty < 1 or v_qty > 50 then
      raise exception 'Quantidade inválida';
    end if;
    select * into v_product
    from public.products
    where slug=v_item->>'slug' and active=true;
    if not found then
      raise exception 'Produto indisponível: %', v_item->>'slug';
    end if;
    v_total := v_total + (v_product.price_cents * v_qty);
  end loop;

  v_order_code := 'PN-' || nextval('public.paonosso_order_seq')::text;
  insert into public.orders(
    order_code,customer_name,customer_phone,fulfillment,address,
    payment_method,notes,total_cents
  )
  values(
    v_order_code,trim(p_customer_name),v_phone,p_fulfillment,
    nullif(trim(coalesce(p_address,'')),''),
    p_payment_method,nullif(trim(coalesce(p_notes,'')),''),v_total
  )
  returning id into v_order_id;

  for v_item in select * from jsonb_array_elements(p_items) loop
    v_qty := (v_item->>'quantity')::integer;
    select * into v_product
    from public.products
    where slug=v_item->>'slug' and active=true;
    insert into public.order_items(
      order_id,product_id,product_slug,product_name,
      unit_price_cents,quantity,line_total_cents
    )
    values(
      v_order_id,v_product.id,v_product.slug,v_product.name,
      v_product.price_cents,v_qty,v_product.price_cents*v_qty
    );
  end loop;

  return query select v_order_id,v_order_code,v_total;
end;
$function$;
