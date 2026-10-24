from collections.abc import Mapping


def error_payload(code: str, message: str, retryable: bool, request_id: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "request_id": request_id,
        }
    }


def get_request_id_from_state(request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    return "req_unknown"


def parse_http_error_detail(detail, default_code: str, default_message: str) -> tuple[str, str]:
    if isinstance(detail, Mapping):
        code = detail.get("code") or default_code
        message = detail.get("message") or default_message
        return str(code), str(message)

    if isinstance(detail, str) and detail.strip():
        return default_code, detail.strip()

    return default_code, default_message


def is_retryable_status(status_code: int) -> bool:
    return status_code in {429, 500, 503}
