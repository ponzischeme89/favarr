from typing import Any, Dict, List
import logging

from favarr.services import server_request


DEFAULT_LAYOUT_IDS = (
    "home",
    "landingcategories",
    "resume",
    "suggestions",
    "latest",
)

DEFAULT_CLIENT = "Emby Web"
DEFAULT_DEVICE_ID = "faveswitch"

logger = logging.getLogger(__name__)


def _ensure_api_key(server):
    if not getattr(server, "api_key", None):
        raise ValueError("Missing API key for Emby server")


def _layout_params(user_id, client: str = None, device_id: str = None) -> Dict[str, str]:
    return {
        "Client": client or DEFAULT_CLIENT,
        "DeviceId": device_id or DEFAULT_DEVICE_ID,
        "UserId": str(user_id),
    }


def _normalize_virtual_folders(raw) -> List[dict]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        for key in ("Items", "VirtualFolders", "items", "virtualFolders"):
            if isinstance(raw.get(key), list):
                return [r for r in raw[key] if isinstance(r, dict)]
    return []


def _library_layout_ids(server) -> List[str]:
    try:
        folders = _normalize_virtual_folders(server_request(server, "/Library/VirtualFolders"))
    except Exception:
        return []
    ids = []
    for folder in folders:
        item_id = folder.get("ItemId") or folder.get("Id") or folder.get("id")
        if item_id:
            ids.append(str(item_id))
    return ids


def _candidate_layout_ids(server) -> List[str]:
    seen = set()
    combined = []
    for pref_id in list(DEFAULT_LAYOUT_IDS) + _library_layout_ids(server):
        pref_id = str(pref_id)
        if pref_id in seen:
            continue
        seen.add(pref_id)
        combined.append(pref_id)
    return combined


def _is_not_found_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "404" in msg or "not found" in msg


def get_users(server) -> List[dict]:
    """Return all Emby users."""
    _ensure_api_key(server)
    data = server_request(server, "/Users")
    return data if isinstance(data, list) else []


def get_display_pref(server, user_id, pref_id, client: str = None, device_id: str = None) -> Dict[str, Any]:
    """Fetch a display preference payload for a user."""
    _ensure_api_key(server)
    return server_request(
        server,
        f"/DisplayPreferences/{pref_id}",
        params=_layout_params(user_id, client=client, device_id=device_id),
    )


def set_display_pref(server, user_id, pref_id, body: Dict[str, Any], client: str = None, device_id: str = None):
    """Set a display preference payload for a user."""
    _ensure_api_key(server)
    if not isinstance(body, dict):
        raise ValueError("Display preference body must be an object")
    return server_request(
        server,
        f"/DisplayPreferences/{pref_id}",
        method="POST",
        params=_layout_params(user_id, client=client, device_id=device_id),
        data=body,
    )


def load_all_layouts(server, user_id, client: str = None, device_id: str = None) -> Dict[str, Any]:
    """Return a dict of all known display preference payloads for a user."""
    _ensure_api_key(server)
    layouts: Dict[str, Any] = {}
    unsupported: List[str] = []
    candidate_ids = _candidate_layout_ids(server)
    for pref_id in candidate_ids:
        try:
            layouts[pref_id] = get_display_pref(
                server,
                user_id,
                pref_id,
                client=client,
                device_id=device_id,
            )
        except Exception as exc:
            if _is_not_found_error(exc):
                logger.warning(
                    "Emby display preference not found (user_id=%s, pref_id=%s, client=%s): %s",
                    user_id,
                    pref_id,
                    client or DEFAULT_CLIENT,
                    exc,
                )
                unsupported.append(pref_id)
                continue
            raise
    return {
        "layouts": layouts,
        "unsupported": unsupported,
        "candidates": candidate_ids,
    }


def apply_layout_template(
    server,
    user_id,
    template: Dict[str, Any],
    client: str = None,
    device_id: str = None,
) -> Dict[str, Any]:
    """Overwrite user layout preferences using template JSON."""
    _ensure_api_key(server)
    if not isinstance(template, dict):
        raise ValueError("Template must be an object mapping preference ids to payloads")

    candidate_ids = _candidate_layout_ids(server)
    unsupported = [str(k) for k in template.keys() if str(k) not in candidate_ids]
    if unsupported:
        raise ValueError(f"Unsupported display preference IDs: {', '.join(unsupported)}")

    applied: List[str] = []
    errors: List[Dict[str, str]] = []
    for pref_id, payload in template.items():
        pref_key = str(pref_id)
        try:
            set_display_pref(server, user_id, pref_key, payload, client=client, device_id=device_id)
            applied.append(pref_key)
        except Exception as exc:
            errors.append({"id": pref_key, "error": str(exc)})

    return {
        "applied": applied,
        "errors": errors,
        "total": len(template),
    }
