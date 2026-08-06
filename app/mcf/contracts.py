"""Contrato JSON aceito entre MCF e Agente Executivo Pessoal."""

MCF_TASK_SCHEMA = {
    "type": "object",
    "required": [
        "mission_id", "requester_agent", "objective", "return_to",
        "allowed_domains", "allowed_capabilities", "completion_criteria",
    ],
    "properties": {
        "mission_id": {"type": "string", "minLength": 1, "maxLength": 128},
        "requester_agent": {"type": "string", "minLength": 1, "maxLength": 80},
        "objective": {"type": "string", "minLength": 1, "maxLength": 4000},
        "return_to": {"type": "string", "minLength": 1, "maxLength": 128},
        "allowed_domains": {"type": "array", "items": {"type": "string"}},
        "allowed_capabilities": {"type": "array", "items": {"type": "string"}},
        "forbidden_actions": {"type": "array", "items": {"type": "string"}},
        "completion_criteria": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "max_autonomy": {"type": "integer", "minimum": 1, "maximum": 5},
        "owner_authorized": {"type": "boolean"},
    },
    "additionalProperties": False,
}
