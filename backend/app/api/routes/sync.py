from __future__ import annotations

import socket
from urllib.parse import quote, urlsplit

from fastapi import APIRouter, Request

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/companion")
def read_companion_snapshot(
    request: Request,
    note_limit: int = 6,
    reminder_limit: int = 8,
    workflow_limit: int = 6,
    task_limit: int = 8,
    activity_limit: int = 6,
    session_limit: int = 4,
    approval_limit: int = 10,
) -> dict:
    sync_service = request.app.state.sync_service
    return sync_service.build_companion_snapshot(
        note_limit=note_limit,
        reminder_limit=reminder_limit,
        workflow_limit=workflow_limit,
        task_limit=task_limit,
        activity_limit=activity_limit,
        session_limit=session_limit,
        approval_limit=approval_limit,
    )


@router.get("/export")
def export_companion_snapshot(
    request: Request,
    include_note_content: bool = False,
    note_limit: int = 10,
    reminder_limit: int = 20,
    workflow_limit: int = 20,
    task_limit: int = 20,
    activity_limit: int = 20,
    session_limit: int = 8,
) -> dict:
    sync_service = request.app.state.sync_service
    return sync_service.build_export_snapshot(
        include_note_content=include_note_content,
        note_limit=note_limit,
        reminder_limit=reminder_limit,
        workflow_limit=workflow_limit,
        task_limit=task_limit,
        activity_limit=activity_limit,
        session_limit=session_limit,
    )


@router.get("/access")
def companion_access_info(request: Request, session_id: str | None = None) -> dict:
    base_url = str(request.base_url)
    split = urlsplit(base_url)
    scheme = split.scheme or "http"
    hostname = split.hostname or "localhost"
    port = split.port
    host_header = request.headers.get("host", hostname)
    if ":" in host_header and host_header.count(":") == 1 and not host_header.startswith("["):
        host_name = host_header.split(":", 1)[0]
    else:
        host_name = hostname

    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_candidate(host: str, label: str) -> None:
        normalized = str(host or "").strip()
        if not normalized:
            return
        lowered = normalized.lower()
        if lowered in seen:
            return
        seen.add(lowered)
        netloc = normalized
        if port and port not in {80, 443}:
            netloc = f"{normalized}:{port}"
        origin = f"{scheme}://{netloc}"
        mobile_url = f"{origin}/mobile"
        control_room_url = f"{origin}/ui/"
        if session_id:
            encoded_session = quote(session_id, safe="")
            mobile_session_url = f"{mobile_url}?session_id={encoded_session}"
            control_room_session_url = f"{control_room_url}?session_id={encoded_session}"
        else:
            mobile_session_url = mobile_url
            control_room_session_url = control_room_url
        candidates.append(
            {
                "host": normalized,
                "label": label,
                "origin": origin,
                "mobile_url": mobile_url,
                "mobile_session_url": mobile_session_url,
                "control_room_url": control_room_url,
                "control_room_session_url": control_room_session_url,
                "is_loopback": _is_loopback_host(normalized),
                "is_lan": False,
                "preferred": False,
            }
        )

    add_candidate(hostname, "Current origin")
    if host_name and host_name != hostname:
        add_candidate(host_name, "Request host")
    add_candidate(socket.gethostname(), "Machine hostname")

    lan_candidates = _lan_ipv4_candidates()
    for ip_address in lan_candidates:
        add_candidate(ip_address, f"LAN {ip_address}")

    for candidate in candidates:
        candidate["is_lan"] = candidate["host"] in lan_candidates

    preferred_candidate = _choose_preferred_candidate(
        candidates=candidates,
        hostname=hostname,
        request_host=host_name,
    )
    for candidate in candidates:
        candidate["preferred"] = bool(preferred_candidate and candidate["host"] == preferred_candidate["host"])

    return {
        "scheme": scheme,
        "hostname": hostname,
        "port": port or (443 if scheme == "https" else 80),
        "request_host": host_header,
        "session_id": session_id or "",
        "candidates": candidates,
        "preferred_candidate": preferred_candidate or {},
        "notes": [
            "Open the mobile URL on a phone connected to the same local network as this machine.",
            "If localhost does not work on your phone, use one of the LAN entries instead.",
        ],
    }


def _lan_ipv4_candidates() -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        normalized = str(value or "").strip()
        if not normalized or normalized.startswith("127.") or normalized == "0.0.0.0":
            return
        if normalized in seen:
            return
        seen.add(normalized)
        candidates.append(normalized)

    try:
        for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            add(result[4][0])
    except OSError:
        pass

    try:
        for value in socket.gethostbyname_ex(socket.gethostname())[2]:
            add(value)
    except OSError:
        pass

    return candidates


def _is_loopback_host(host: str) -> bool:
    normalized = str(host or "").strip().lower()
    return normalized in {"localhost", "::1"} or normalized.startswith("127.")


def _choose_preferred_candidate(
    *,
    candidates: list[dict[str, str | bool]],
    hostname: str,
    request_host: str,
) -> dict[str, str | bool] | None:
    if not candidates:
        return None

    def score(candidate: dict[str, str | bool]) -> tuple[int, int, int, int]:
        host = str(candidate.get("host") or "").lower()
        is_lan = bool(candidate.get("is_lan"))
        is_loopback = bool(candidate.get("is_loopback"))
        return (
            1 if is_lan else 0,
            0 if is_loopback else 1,
            1 if host == str(request_host or "").lower() else 0,
            1 if host == str(hostname or "").lower() else 0,
        )

    return max(candidates, key=score)
