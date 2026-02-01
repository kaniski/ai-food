from typing import Any, Dict, Optional
from starlette.requests import Request

KEY = "flow_data"

def get_flow(request: Request) -> Dict[str, Any]:
    data = request.session.get(KEY)
    if isinstance(data, dict):
        return data
    return {}

def set_flow(request: Request, data: Dict[str, Any]) -> None:
    request.session[KEY] = data

def merge_flow(request: Request, patch: Dict[str, Any]) -> Dict[str, Any]:
    data = get_flow(request)
    data.update(patch)
    set_flow(request, data)
    return data

def clear_flow(request: Request) -> None:
    request.session.pop(KEY, None)
    request.session.pop("csrf_token", None)
    request.session.pop("demo_confirmed", None)

def step_done(flow: Dict[str, Any], step: int) -> bool:
    return flow.get(f"step_{step}_done") is True

def mark_step_done(flow: Dict[str, Any], step: int) -> Dict[str, Any]:
    flow[f"step_{step}_done"] = True
    return flow

def require_step(flow: Dict[str, Any], step: int) -> bool:
    # Para acessar step N, precisa ter concluído (N-1)
    if step <= 1:
        return True
    return step_done(flow, step - 1)

def get_value(flow: Dict[str, Any], key: str, default: Any = "") -> Any:
    return flow.get(key, default)

def as_bool_sim_nao(value: Optional[str]) -> str:
    if value == "sim":
        return "Sim"
    if value == "nao":
        return "Não"
    return "-"
