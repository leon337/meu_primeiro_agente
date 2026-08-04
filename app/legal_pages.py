"""Páginas legais incorporadas ao runtime para ambientes serverless."""

from html import escape

_CONTACT_EMAIL = "eiasophia25@gmail.com"
_UPDATED_AT = "4 de agosto de 2026"

_STYLE = """
:root{color-scheme:dark;font-family:Inter,system-ui,sans-serif;background:#07111f;color:#edf6ff}
body{margin:0;line-height:1.65;background:linear-gradient(145deg,#07111f,#0b1c2f)}
main{width:min(900px,calc(100% - 2rem));margin:0 auto;padding:3rem 0 5rem}
article{background:#0b1c2f;border:1px solid rgba(148,185,219,.18);border-radius:1.2rem;padding:clamp(1.2rem,4vw,2.4rem)}
h1,h2{line-height:1.2}h1{margin-top:0}h2{margin-top:2rem;color:#72efd2}a{color:#72efd2}.muted{color:#a4b7c8}nav{margin-bottom:1rem}ul{padding-left:1.25rem}
""".strip()


def _page(title: str, description: str, body: str) -> str:
    safe_title = escape(title)
    safe_description = escape(description)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{safe_description}">
  <title>{safe_title} — Hello Agent</title>
  <style>{_STYLE}</style>
</head>
<body>
<main>
  <nav><a href="/">← Voltar ao Hello Agent</a></nav>
  <article>
    <h1>{safe_title}</h1>
    <p class="muted">Última atualização: {_UPDATED_AT}</p>
    {body}
    <h2>Contato</h2>
    <p>Dúvidas ou solicitações podem ser enviadas para <a href="mailto:{_CONTACT_EMAIL}">{_CONTACT_EMAIL}</a>.</p>
  </article>
</main>
</body>
</html>"""


PRIVACY_HTML = _page(
    "Política de Privacidade",
    "Política de Privacidade do Hello Agent.",
    """
    <p>Esta política explica como o <strong>Hello Agent</strong> trata informações quando uma pessoa usa a interface web ou conversa com o agente pelo WhatsApp.</p>

    <h2>1. Dados tratados</h2>
    <ul>
      <li>mensagens e comandos enviados voluntariamente;</li>
      <li>identificador da sessão web ou número do WhatsApp necessário para manter a conversa;</li>
      <li>metadados técnicos mínimos, como data, horário, estado da requisição e registros de erro;</li>
      <li>resultados de ferramentas locais somente quando a pessoa solicita uma função autorizada.</li>
    </ul>
    <p>O Hello Agent não solicita senhas, códigos de autenticação, chaves de API ou dados financeiros por mensagem.</p>

    <h2>2. Finalidades</h2>
    <p>Os dados são usados para responder às mensagens, manter o contexto da sessão, executar funções autorizadas, proteger o serviço contra abuso, diagnosticar falhas e melhorar a confiabilidade.</p>

    <h2>3. Serviços utilizados</h2>
    <p>As mensagens podem ser processadas pela Meta/WhatsApp Cloud API, pelo Google Gemini e pela infraestrutura de hospedagem da Vercel. Cada fornecedor trata dados segundo seus próprios termos e políticas.</p>

    <h2>4. Retenção e segurança</h2>
    <p>O contexto de conversa é mantido apenas pelo período operacional necessário e pode ser reiniciado. Registros técnicos podem ser preservados temporariamente para segurança e diagnóstico. São aplicadas autenticação, validação de webhook, limitação de ferramentas e armazenamento de segredos fora do código-fonte.</p>

    <h2>5. Compartilhamento</h2>
    <p>Não vendemos dados pessoais. O compartilhamento ocorre somente com os provedores necessários ao funcionamento, por obrigação legal ou para proteger o serviço e seus usuários.</p>

    <h2>6. Direitos da pessoa</h2>
    <p>A pessoa pode solicitar confirmação de tratamento, acesso, correção, exclusão, informação sobre compartilhamento e outras medidas previstas pela legislação aplicável. Consulte também as <a href="/data-deletion">instruções de exclusão de dados</a>.</p>

    <h2>7. Crianças e adolescentes</h2>
    <p>O serviço não foi criado para coletar intencionalmente dados de crianças. Responsáveis devem supervisionar o uso por menores de idade.</p>
    """,
)


DATA_DELETION_HTML = _page(
    "Exclusão de Dados",
    "Instruções para solicitar a exclusão de dados no Hello Agent.",
    """
    <p>É possível solicitar a exclusão das informações associadas ao uso do Hello Agent.</p>

    <h2>Como solicitar</h2>
    <ol>
      <li>Envie um e-mail para <a href="mailto:eiasophia25@gmail.com">eiasophia25@gmail.com</a> com o assunto <strong>Exclusão de dados — Hello Agent</strong>.</li>
      <li>Informe o canal usado: Web ou WhatsApp.</li>
      <li>Para WhatsApp, informe somente o número no formato internacional. Não envie senha, token ou código de autenticação.</li>
      <li>Descreva quais dados deseja excluir.</li>
    </ol>

    <h2>Prazo e confirmação</h2>
    <p>A solicitação será analisada e respondida em até 15 dias, salvo prazo diferente exigido pela legislação. Poderá ser necessária uma verificação limitada de identidade para impedir exclusões fraudulentas.</p>

    <h2>O que será removido</h2>
    <p>Serão removidos os dados sob controle direto do Hello Agent que possam ser relacionados à pessoa. Informações que precisem ser mantidas por obrigação legal, segurança, prevenção de fraude ou defesa de direitos serão preservadas apenas pelo período necessário.</p>

    <h2>Dados em outros provedores</h2>
    <p>Pedidos relativos a dados mantidos diretamente por Meta/WhatsApp, Google ou outros provedores também podem depender dos canais de privacidade desses serviços.</p>
    """,
)


TERMS_HTML = _page(
    "Termos de Serviço",
    "Termos de Serviço do Hello Agent.",
    """
    <p>Ao usar o Hello Agent, a pessoa concorda com estes termos.</p>

    <h2>1. Finalidade</h2>
    <p>O Hello Agent é um assistente experimental para responder perguntas e executar um conjunto limitado de funções autorizadas. As respostas podem conter erros e devem ser verificadas antes de decisões relevantes.</p>

    <h2>2. Uso permitido</h2>
    <p>O usuário deve utilizar o serviço de forma lícita e não deve tentar obter acesso indevido, interferir na infraestrutura, enviar conteúdo malicioso, explorar vulnerabilidades ou usar o agente para prejudicar terceiros.</p>

    <h2>3. Credenciais e informações sensíveis</h2>
    <p>Não envie senhas, códigos de autenticação, chaves secretas, documentos confidenciais ou dados financeiros. O usuário é responsável por revisar as informações fornecidas ao serviço.</p>

    <h2>4. Disponibilidade</h2>
    <p>O serviço pode sofrer interrupções, limites de provedores, manutenção ou alterações sem garantia de disponibilidade contínua. Quando possível, falhas temporárias serão apresentadas de forma clara.</p>

    <h2>5. Limitação</h2>
    <p>O Hello Agent não substitui profissionais qualificados e não oferece garantia de exatidão para orientação médica, jurídica, financeira, de segurança ou outras decisões de alto impacto.</p>

    <h2>6. Privacidade</h2>
    <p>O tratamento de informações está descrito na <a href="/privacy">Política de Privacidade</a>. Solicitações de remoção seguem as <a href="/data-deletion">instruções de exclusão</a>.</p>

    <h2>7. Alterações</h2>
    <p>Estes termos podem ser atualizados para refletir mudanças técnicas, legais ou operacionais. A data da versão vigente aparece no início da página.</p>
    """,
)
