import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from decimal import Decimal

import requests
from django.conf import settings

from .reservations import RESERVATION_TIME_LIMIT_MINUTES

logger = logging.getLogger(__name__)

P24_SANDBOX_URL = "https://sandbox.przelewy24.pl"
P24_PRODUCTION_URL = "https://secure.przelewy24.pl"


class P24RefundError(RuntimeError):
    pass


@dataclass(frozen=True)
class P24RefundRequest:
    p24_order_id: int
    p24_session_id: str
    amount: Decimal
    request_id: str
    refunds_uuid: str
    description: str

    @property
    def amount_in_grosze(self):
        return int(self.amount * 100)


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


def refund_rzut_transaction(refund):
    payload = {
        "requestId": refund.request_id,
        "refundsUuid": refund.refunds_uuid,
        "refunds": [
            {
                "orderId": refund.p24_order_id,
                "sessionId": refund.p24_session_id,
                "amount": refund.amount_in_grosze,
                "description": refund.description,
            }
        ],
    }
    response = requests.post(
        f"{get_base_url()}/api/v1/transaction/refund",
        json=payload,
        auth=(str(settings.P24_POS_ID), settings.P24_API_KEY),
        timeout=settings.P24_HTTP_TIMEOUT,
    )
    response.raise_for_status()
    try:
        result = response.json()["data"][0]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise P24RefundError(
            "Przelewy24 zwróciło nieprawidłową odpowiedź dla zwrotu."
        ) from exc
    if not result.get("status"):
        raise P24RefundError(result.get("message") or "Przelewy24 odrzuciło zwrot.")
    if (
        result.get("orderId") != refund.p24_order_id
        or result.get("sessionId") != refund.p24_session_id
        or result.get("amount") != refund.amount_in_grosze
    ):
        raise P24RefundError(
            "Odpowiedź Przelewy24 nie odpowiada żądanemu pełnemu zwrotowi."
        )
    return {**result, "completed": False}


def get_rzut_refund(refund_request):
    response = requests.get(
        f"{get_base_url()}/api/v1/refund/by/orderId/{refund_request.p24_order_id}",
        auth=(str(settings.P24_POS_ID), settings.P24_API_KEY),
        timeout=settings.P24_HTTP_TIMEOUT,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    try:
        data = response.json()["data"]
        refunds = data["refunds"]
    except (KeyError, TypeError, ValueError) as exc:
        raise P24RefundError(
            "Przelewy24 zwróciło nieprawidłowe dane istniejącego zwrotu."
        ) from exc
    if (
        data.get("orderId") != refund_request.p24_order_id
        or data.get("sessionId") != refund_request.p24_session_id
    ):
        raise P24RefundError(
            "Dane istniejącego zwrotu Przelewy24 dotyczą innej transakcji."
        )
    for refund_data in refunds:
        if refund_data.get("requestId") != refund_request.request_id:
            continue
        if refund_data.get("amount") != refund_request.amount_in_grosze:
            raise P24RefundError(
                "Istniejący zwrot Przelewy24 ma inną kwotę."
            )
        refund_status = refund_data.get("status")
        if refund_status == 4:
            raise P24RefundError(
                refund_data.get("description") or "Przelewy24 odrzuciło zwrot."
            )
        if refund_status not in {1, 2, 3}:
            raise P24RefundError(
                "Przelewy24 zwróciło nieznany status zwrotu."
            )
        return {
            "orderId": refund_request.p24_order_id,
            "sessionId": refund_request.p24_session_id,
            "amount": refund_request.amount_in_grosze,
            "status": True,
            "completed": refund_status == 1,
            "refundStatus": refund_status,
            "requestId": refund_request.request_id,
        }
    return None


def get_payment_url(token):
    base_url = get_base_url()
    return f"{base_url}/trnRequest/{token}"
