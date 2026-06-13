import requests
from . import BASE_URL
from .utils import get_session, validate_slug


def get_paste_content(slug, session=None):
    if session is None:
        session = get_session()
    try:
        response = session.get(f"{BASE_URL}/api/pastes/{slug}")
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "paste" in data:
                return data["paste"].get("contentRawMarkdown", "")
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.RequestException:
        pass
    return ""


def set_paste_content(slug, content, session=None, visibility="public_read", expires_at=None):
    if session is None:
        session = get_session()
    is_valid, error_msg = validate_slug(slug)
    if not is_valid:
        raise ValueError(error_msg)

    check_response = session.get(f"{BASE_URL}/api/pastes/{slug}")
    exists = check_response.status_code == 200

    body = {
        "contentRawMarkdown": content,
        "visibility": visibility,
    }
    if expires_at:
        body["expiresAt"] = expires_at

    if exists:
        response = session.patch(f"{BASE_URL}/api/pastes/{slug}", json=body)
    else:
        body["customSlug"] = slug
        response = session.post(f"{BASE_URL}/api/pastes", json=body)
    return response
