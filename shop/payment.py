import hashlib
import hmac
import json
import logging

import requests
from django.conf import settings

from .reservations import RESERVATION_TIME_LIMIT_MINUTES

logger = logging.getLogger(__name__)

P24_SANDBOX_URL = "https://sandbox.przelewy24.pl"
P24_PRODUCTION_URL = "https://secure.przelewy24.pl"


def get_base_url():
    if settings.P24_SANDBOX:
        return P24_SANDBOX_URL
    return P24_PRODUCTION_URL


def calculate_sign(params):
    data = json.dumps(params, separators=(",", ":"))
    return hashlib.sha384(data.encode("utf-8")).hexdigest()


def is_valid_p24_notification(data):
    expected_sign = calculate_sign({
        "merchantId": data.get("merchantId"),
        "posId": data.get("posId"),
        "sessionId": data.get("sessionId", ""),
        "amount": data.get("amount", 0),
        "originAmount": data.get("originAmount"),
        "currency": data.get("currency"),
        "orderId": data.get("orderId", 0),
        "methodId": data.get("methodId"),
        "statement": data.get("statement"),
        "crc": settings.P24_CRC_KEY,
    })
    return hmac.compare_digest(str(data.get("sign", "")), expected_sign)


def register_transaction(order, url_return, url_status):
    return _register_transaction(
        session_id=order.p24_session_id,
        total=order.total,
        email=order.email,
        description=f"Zamówienie #{order.id}",
        url_return=url_return,
        url_status=url_status,
    )


def register_rzut_transaction(reservation, url_return, url_status):
    return _register_transaction(
        session_id=reservation.p24_session_id,
        total=reservation.total,
        email=reservation.customer_email,
        description=f"Rezerwacja Rzutu {reservation.rzut.title}",
        url_return=url_return,
        url_status=url_status,
        time_limit=RESERVATION_TIME_LIMIT_MINUTES,
    )


def _register_transaction(
    *,
    session_id,
    total,
    email,
    description,
    url_return,
    url_status,
    time_limit=None,
):
    sign = calculate_sign({
        "sessionId": session_id,
        "merchantId": settings.P24_MERCHANT_ID,
        "amount": int(total * 100),
        "currency": "PLN",
        "crc": settings.P24_CRC_KEY,
    })
    payload = {
        "merchantId": settings.P24_MERCHANT_ID,
        "posId": settings.P24_POS_ID,
        "sessionId": session_id,
        "amount": int(total * 100),
        "currency": "PLN",
        "description": description,
        "email": email,
        "country": "PL",
        "language": "pl",
        "urlReturn": url_return,
        "urlStatus": url_status,
        "sign": sign,
    }
    if time_limit is not None:
        payload["timeLimit"] = time_limit
    response = requests.post(
        f"{get_base_url()}/api/v1/transaction/register",
        json=payload,
        auth=(str(settings.P24_POS_ID), settings.P24_API_KEY),
        timeout=settings.P24_HTTP_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["data"]["token"]


def verify_transaction(session_id, order_id_p24, amount):
    sign = calculate_sign({
        "sessionId": session_id,
        "orderId": order_id_p24,
        "amount": amount,
        "currency": "PLN",
        "crc": settings.P24_CRC_KEY,
    })
    payload = {
        "merchantId": settings.P24_MERCHANT_ID,
        "posId": settings.P24_POS_ID,
        "sessionId": session_id,
        "orderId": order_id_p24,
        "amount": amount,
        "currency": "PLN",
        "sign": sign,
    }
    base_url = get_base_url()
    response = requests.put(
        f"{base_url}/api/v1/transaction/verify",
        json=payload,
        auth=(str(settings.P24_POS_ID), settings.P24_API_KEY),
        timeout=settings.P24_HTTP_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("status") == "success"


def get_payment_url(token):
    base_url = get_base_url()
    return f"{base_url}/trnRequest/{token}"
