import hashlib
import json
import logging

import requests
from django.conf import settings

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


def register_transaction(order, url_return, url_status):
    sign = calculate_sign({
        "sessionId": order.p24_session_id,
        "merchantId": settings.P24_MERCHANT_ID,
        "amount": int(order.total * 100),
        "currency": "PLN",
        "crc": settings.P24_CRC_KEY,
    })
    payload = {
        "merchantId": settings.P24_MERCHANT_ID,
        "posId": settings.P24_POS_ID,
        "sessionId": order.p24_session_id,
        "amount": int(order.total * 100),
        "currency": "PLN",
        "description": f"Zamowienie #{order.id}",
        "email": order.email,
        "country": "PL",
        "language": "pl",
        "urlReturn": url_return,
        "urlStatus": url_status,
        "sign": sign,
    }
    base_url = get_base_url()
    response = requests.post(
        f"{base_url}/api/v1/transaction/register",
        json=payload,
        auth=(str(settings.P24_POS_ID), settings.P24_API_KEY),
    )
    response.raise_for_status()
    data = response.json()
    return data["data"]["token"]


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
    )
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("status") == "success"


def get_payment_url(token):
    base_url = get_base_url()
    return f"{base_url}/trnRequest/{token}"
