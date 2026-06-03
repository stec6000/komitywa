import logging

import requests
from django.conf import settings


log = logging.getLogger("newsletter.security")


TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(token, remote_ip=None):
    """Verify Cloudflare Turnstile token against siteverify endpoint.

    Returns:
        (success: bool, reason: str)

    Graceful skip if TURNSTILE_SECRET_KEY is not configured — returns
    (True, "skipped:no-key"). This allows code to be deployed before
    Cloudflare keys are provisioned.
    """
    if not settings.TURNSTILE_SECRET_KEY:
        log.warning("Turnstile not configured (TURNSTILE_SECRET_KEY empty) — skipping check")
        return (True, "skipped:no-key")

    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token or "",
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        response = requests.post(TURNSTILE_VERIFY_URL, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.Timeout:
        log.error("Turnstile verify timeout (ip=%s)", remote_ip)
        return (False, "timeout")
    except requests.RequestException as exc:
        log.error("Turnstile verify network error: %s (ip=%s)", exc, remote_ip)
        return (False, "network-error")
    except ValueError:
        log.error("Turnstile verify returned non-JSON (ip=%s)", remote_ip)
        return (False, "bad-response")

    success = bool(data.get("success"))
    error_codes = data.get("error-codes") or []
    reason = ",".join(error_codes) if error_codes else "ok"
    return (success, reason)


def get_client_ip(request):
    """Extract client IP from request, honoring X-Forwarded-For first hop."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.META.get("REMOTE_ADDR")
