# Phase 5: Payments & Orders - Research

**Researched:** 2026-04-02
**Domain:** Przelewy24 payment integration, Django email with attachments, order lifecycle
**Confidence:** MEDIUM

## Summary

Phase 5 wires the existing checkout flow (Phase 4) to Przelewy24 for payment processing and adds email delivery for order confirmations and ebook PDFs. The existing Order model has status, cart_snapshot, email, and total fields -- Phase 5 adds `p24_session_id` to Order and `ebook_file` to Product, modifies the checkout view to register a P24 transaction and redirect to the payment page, handles the P24 webhook for payment confirmation, and sends emails.

The Przelewy24 REST API v1 uses JSON-based sign calculation with SHA-384 hashing. There are no well-maintained Python P24 libraries -- the recommendation is direct integration using the `requests` library (already in requirements.txt). The API has three key interactions: transaction registration (POST), user redirect to P24 payment page, and webhook notification + transaction verification (PUT). Django's built-in `EmailMessage` class handles PDF attachment delivery with no additional dependencies.

**Primary recommendation:** Use direct `requests`-based P24 integration (no third-party P24 library). Create a `shop/payment.py` module encapsulating all P24 API logic. Use Django's console email backend for development and SMTP for production.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-02: Design for sandbox first. P24_MERCHANT_ID, P24_POS_ID, P24_CRC_KEY, P24_API_KEY in .env with separate sandbox/production values. Switching to production = config change only.
- D-03: Order created BEFORE payment (Phase 4 approach retained). Checkout form POST creates Order with status="pending". Phase 5 adds p24_session_id field and registers transaction with P24, then redirects to P24 payment page.
- D-04: Add p24_session_id field to Order model (CharField, blank=True) via migration.
- D-05: Return URL shows pending confirmation page. Webhook processes asynchronously and updates Order status to "paid" + triggers emails.
- D-06: Failed/cancelled payments -- set Order status to "cancelled", restore cart from Order.cart_snapshot into session, redirect to /zamowienie/.
- D-07: Ebook PDF files stored in media/ebooks/. Uploaded via Django admin.
- D-08: PDF delivered as email attachment directly. No download links.
- D-09: Add ebook_file = models.FileField(upload_to="ebooks/", blank=True, null=True) to Product model.
- D-10: Delivery failure handling -- catch exception, log, continue. No automatic retry.
- D-11: Django SMTP backend via django-environ .env config. Development: console backend.
- D-12: Two separate emails -- order confirmation (all orders) + ebook delivery (orders with ebook products).
- D-13: Plain text emails. Warm personal Polish tone.
- D-14: No admin notification email. Admin monitors via Django admin panel.

### Claude's Discretion
- Exact P24 library chosen by researcher (python-przelewy24 vs. direct REST)
- P24 transaction registration endpoint structure and CRC signing implementation details
- Webhook signature verification implementation details
- Email subject line and body copy (warm Polish tone, per D-13)
- Admin fieldset layout for updated Order model
- Error page copy for payment failure

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAY-01 | User can pay via Przelewy24 (BLIK, transfers, cards) | P24 REST API v1 transaction registration + redirect pattern documented below |
| PAY-02 | System verifies payment via P24 webhook with CRC validation | SHA-384 sign verification pattern for webhook + PUT /api/v1/transaction/verify |
| PAY-03 | User sees order confirmation page after payment | Return URL view pattern -- shows pending message per D-05 |
| PAY-04 | User receives order confirmation email | Django EmailMessage plain text pattern |
| PAY-05 | User receives ebook PDF via email after payment | Django EmailMessage.attach_file() for PDF attachment |
| PAY-06 | Admin sees orders and statuses in admin panel | OrderAdmin already exists -- update readonly_fields for p24_session_id |
| LEGAL-04 | Checkout form has consent checkboxes | Already implemented in Phase 4 CheckoutForm (consent_data, consent_terms) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.25.1 (installed) | HTTP client for P24 API calls | Already in requirements.txt, standard for REST API integration |
| django.core.mail | built-in (Django 5.2) | Email sending with attachments | Built into Django, no additional dependency needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hashlib (stdlib) | built-in | SHA-384 hash for P24 sign calculation | Every P24 API request and webhook verification |
| json (stdlib) | built-in | JSON encoding for sign calculation | P24 sign = SHA384(json.dumps(params, separators)) |
| logging (stdlib) | built-in | Error logging for delivery failures | D-10: log failures, don't crash |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct requests | python-przelewy24 (GitHub) | Last commit 2016, Python 3.4 only, unmaintained -- NOT recommended |
| Direct requests | p24 (PyPI) | Last commit 2016, inactive, thin wrapper -- NOT recommended |
| Direct requests | django-payments-przelewy24 | Inactive for 12+ months, depends on django-payments framework -- overkill |

**Recommendation (D-01 discretion):** Use direct `requests` calls. All existing Python P24 libraries are abandoned (2016 era) and predate the current REST API v1. The API surface is small (2 endpoints + 1 webhook), making a library unnecessary. The `requests` package is already installed.

**Installation:**
```bash
# No new packages needed -- requests already in requirements.txt
# Only .env additions needed for P24 credentials
```

## Architecture Patterns

### Recommended Project Structure
```
shop/
  payment.py           # P24 API client module (register, verify, sign calculation)
  emails.py            # Email sending functions (order confirmation, ebook delivery)
  models.py            # Updated Order (+ p24_session_id), Product (+ ebook_file)
  views.py             # Updated checkout, new webhook, return URL views
  urls.py              # New URL patterns for webhook + return
  tests/
    test_payment.py    # P24 integration tests (mocked)
    test_emails.py     # Email sending tests
    test_views.py      # Updated with payment flow tests
```

### Pattern 1: P24 API Client Module
**What:** Encapsulate all Przelewy24 API interaction in a single `shop/payment.py` module with pure functions.
**When to use:** Every P24 API call goes through this module.
**Example:**
```python
# shop/payment.py
import hashlib
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

P24_SANDBOX_URL = "https://sandbox.przelewy24.pl"
P24_PRODUCTION_URL = "https://secure.przelewy24.pl"


def get_base_url():
    """Return sandbox or production URL based on settings."""
    if settings.P24_SANDBOX:
        return P24_SANDBOX_URL
    return P24_PRODUCTION_URL


def calculate_sign(params):
    """
    Calculate SHA-384 sign from a dict of parameters.
    P24 expects: json.dumps with no spaces (separators=(',', ':'))
    then SHA-384 hex digest.
    """
    data = json.dumps(params, separators=(",", ":"))
    return hashlib.sha384(data.encode("utf-8")).hexdigest()


def register_transaction(order, url_return, url_status):
    """
    Register transaction with P24 REST API.
    Returns token string on success, raises on failure.
    """
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


def verify_transaction(session_id, order_id, amount):
    """
    Verify transaction after webhook notification.
    Returns True if verified successfully.
    """
    sign = calculate_sign({
        "sessionId": session_id,
        "orderId": order_id,
        "amount": amount,
        "currency": "PLN",
        "crc": settings.P24_CRC_KEY,
    })

    payload = {
        "merchantId": settings.P24_MERCHANT_ID,
        "posId": settings.P24_POS_ID,
        "sessionId": session_id,
        "orderId": order_id,
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
    """Return the URL to redirect user to P24 payment page."""
    base_url = get_base_url()
    return f"{base_url}/trnRequest/{token}"
```

### Pattern 2: Webhook View with CSRF Exemption
**What:** Django view to receive P24 payment notifications, verify signature, update order, trigger emails.
**When to use:** P24 POSTs to this endpoint after payment.
**Example:**
```python
# In shop/views.py
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Order
from .payment import calculate_sign, verify_transaction
from .emails import send_order_confirmation, send_ebook_delivery

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def p24_webhook(request):
    """Handle P24 payment notification."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    session_id = data.get("sessionId", "")
    order_id = data.get("orderId", 0)
    amount = data.get("amount", 0)

    # Verify webhook sign
    received_sign = data.get("sign", "")
    expected_sign = calculate_sign({
        "merchantId": data.get("merchantId"),
        "posId": data.get("posId"),
        "sessionId": session_id,
        "amount": amount,
        "originAmount": data.get("originAmount"),
        "currency": data.get("currency"),
        "orderId": order_id,
        "methodId": data.get("methodId"),
        "statement": data.get("statement"),
        "crc": settings.P24_CRC_KEY,
    })

    if received_sign != expected_sign:
        logger.warning("P24 webhook: invalid sign for session %s", session_id)
        return JsonResponse({"error": "Invalid sign"}, status=400)

    # Find order
    try:
        order = Order.objects.get(p24_session_id=session_id)
    except Order.DoesNotExist:
        logger.error("P24 webhook: order not found for session %s", session_id)
        return JsonResponse({"error": "Order not found"}, status=404)

    # Verify transaction with P24
    verified = verify_transaction(session_id, order_id, amount)
    if verified:
        order.status = "paid"
        order.save()
        send_order_confirmation(order)
        send_ebook_delivery(order)

    return JsonResponse({"status": "ok"})
```

### Pattern 3: Email with PDF Attachment
**What:** Django EmailMessage for plain text emails with PDF file attachment.
**When to use:** After webhook confirms payment.
**Example:**
```python
# shop/emails.py
import logging

from django.conf import settings
from django.core.mail import EmailMessage

from .models import Product

logger = logging.getLogger(__name__)


def send_order_confirmation(order):
    """Send order confirmation email to customer."""
    items_text = ""
    for pid, item in order.cart_snapshot.items():
        try:
            product = Product.objects.get(id=int(pid))
            items_text += f"- {product.title} x{item['quantity']} - {item['price']} PLN\n"
        except Product.DoesNotExist:
            items_text += f"- Produkt #{pid} x{item['quantity']} - {item['price']} PLN\n"

    body = (
        f"Czesc {order.name}!\n\n"
        f"Dziekujemy za zamowienie w Kuchennej Komitywie!\n\n"
        f"Numer zamowienia: #{order.id}\n"
        f"Produkty:\n{items_text}\n"
        f"Suma: {order.total} PLN\n"
        f"Data odbioru: {order.pickup_date}\n\n"
        f"Do zobaczenia!\n"
        f"Kuchenna Komitywa"
    )

    email = EmailMessage(
        subject=f"Potwierdzenie zamowienia #{order.id} - Kuchenna Komitywa",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    email.send(fail_silently=False)


def send_ebook_delivery(order):
    """Send ebook PDFs for any ebook products in the order."""
    ebook_products = []
    for pid in order.cart_snapshot.keys():
        try:
            product = Product.objects.get(id=int(pid), type="ebook")
            if product.ebook_file:
                ebook_products.append(product)
        except Product.DoesNotExist:
            continue

    if not ebook_products:
        return

    body = (
        f"Czesc {order.name}!\n\n"
        f"W zalaczniku znajdziesz zakupione ebooki.\n"
        f"Zyczymy smacznej lektury!\n\n"
        f"Kuchenna Komitywa"
    )

    email = EmailMessage(
        subject="Twoje ebooki - Kuchenna Komitywa",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    for product in ebook_products:
        try:
            email.attach_file(product.ebook_file.path, "application/pdf")
        except Exception as exc:
            logger.error(
                "Failed to attach ebook for order %d, product %d: %s",
                order.id, product.id, exc,
            )

    try:
        email.send(fail_silently=False)
    except Exception as exc:
        logger.error(
            "Failed to send ebook email for order %d: %s",
            order.id, exc,
        )
```

### Anti-Patterns to Avoid
- **Processing payment in checkout POST synchronously without redirect:** Always redirect to P24 payment page after registering the transaction. Never try to "simulate" payment in the checkout view.
- **Storing CRC key in source code:** All P24 credentials must be in .env, read via django-environ.
- **Trusting webhook data without verification:** Always verify the P24 webhook sign AND call the verify endpoint. The webhook alone is not sufficient proof of payment.
- **Blocking on email failure in webhook:** Email sending failures must not cause the webhook to return an error. Log and continue (D-10).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SHA-384 hashing | Custom crypto | `hashlib.sha384()` (stdlib) | Standard library, battle-tested, correct |
| Email with attachments | Raw SMTP | `django.core.mail.EmailMessage` | Handles MIME encoding, attachments, backend switching |
| CSRF exemption for webhook | Custom middleware | `@csrf_exempt` decorator | Django standard pattern for external callbacks |
| Environment variables | os.environ parsing | `django-environ` (already configured) | Type casting, .env file loading already set up |

## Common Pitfalls

### Pitfall 1: JSON Spaces in Sign Calculation
**What goes wrong:** P24 sign verification fails with "Incorrect CRC value" error.
**Why it happens:** Python's `json.dumps()` defaults to `separators=(', ', ': ')` which adds spaces. P24 expects compact JSON with no spaces for sign calculation.
**How to avoid:** Always use `json.dumps(params, separators=(",", ":"))` -- no spaces after comma or colon.
**Warning signs:** 400 response from P24 transaction register with "Incorrect CRC" error.

### Pitfall 2: Amount in Grosze (Cents), Not PLN
**What goes wrong:** Payment amount is 100x too small or too large.
**Why it happens:** P24 API expects amounts in grosze (1 PLN = 100 groszy). The Order model stores Decimal in PLN.
**How to avoid:** Convert with `int(order.total * 100)` when sending to P24. Convert back when comparing webhook amounts.
**Warning signs:** Amount mismatch errors during verification.

### Pitfall 3: Webhook View Missing CSRF Exemption
**What goes wrong:** P24 webhook returns 403 Forbidden.
**Why it happens:** Django CSRF middleware blocks POST requests without CSRF token. P24 server cannot provide one.
**How to avoid:** Apply `@csrf_exempt` decorator to the webhook view.
**Warning signs:** 403 responses in P24 panel notification logs.

### Pitfall 4: Session ID Uniqueness
**What goes wrong:** P24 rejects duplicate session IDs.
**Why it happens:** Using a non-unique identifier (like Order.id alone) can collide with previous attempts.
**How to avoid:** Generate p24_session_id as `f"order-{order.id}-{uuid4().hex[:8]}"` or similar unique format. Store it on the Order model.
**Warning signs:** P24 registration returns error about duplicate session.

### Pitfall 5: Race Condition Between Return URL and Webhook
**What goes wrong:** User sees return page before webhook has updated Order status.
**Why it happens:** User redirect to return URL can arrive before P24 sends webhook notification.
**How to avoid:** Per D-05 -- return URL shows a generic "thank you, email confirmation coming" page regardless of current order status. Do not rely on order status being "paid" at this point.
**Warning signs:** Users see "pending" when they expected "paid".

### Pitfall 6: Email Attachment Path for FileField
**What goes wrong:** `attach_file()` fails because FileField returns a FieldFile object, not a path string.
**Why it happens:** Django FileField.path returns the filesystem path only when using local storage.
**How to avoid:** Use `product.ebook_file.path` (not `product.ebook_file`) for `attach_file()`. This works with local filesystem storage (which is what this project uses).
**Warning signs:** TypeError or FileNotFoundError in email sending.

### Pitfall 7: Cart Restoration on Payment Failure
**What goes wrong:** User loses their cart after a cancelled payment and has to re-add items.
**Why it happens:** Cart was cleared during checkout (Phase 4). If payment fails, cart is empty.
**How to avoid:** Per D-06 -- on failure/cancel, deserialize `Order.cart_snapshot` back into `request.session["cart"]` and redirect to /zamowienie/.
**Warning signs:** Users complain about having to rebuild their cart after a payment error.

## Code Examples

### Settings Configuration for P24 and Email
```python
# backend/settings.py additions

# Przelewy24
P24_MERCHANT_ID = env.int("P24_MERCHANT_ID", default=0)
P24_POS_ID = env.int("P24_POS_ID", default=0)
P24_CRC_KEY = env("P24_CRC_KEY", default="")
P24_API_KEY = env("P24_API_KEY", default="")
P24_SANDBOX = env.bool("P24_SANDBOX", default=True)

# Email
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="Kuchenna Komitywa <noreply@kuchennakomitywa.pl>",
)
```

### .env.example Additions
```
# Przelewy24
P24_MERCHANT_ID=
P24_POS_ID=
P24_CRC_KEY=
P24_API_KEY=
P24_SANDBOX=True

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Kuchenna Komitywa <noreply@kuchennakomitywa.pl>
```

### URL Patterns for New Views
```python
# Additions to shop/urls.py
path("zamowienie/webhook/p24/", views.p24_webhook, name="p24_webhook"),
path("zamowienie/powrot/", views.p24_return, name="p24_return"),
path("zamowienie/anulowano/", views.p24_cancel, name="p24_cancel"),
```

### Modified Checkout Flow
```python
# Conceptual change to shop/views.py checkout()
# After Order.objects.create():
# 1. Generate p24_session_id
# 2. Call payment.register_transaction(order, url_return, url_status)
# 3. Get token, build payment URL
# 4. Redirect to P24 payment URL
# Instead of redirect("shop:checkout_confirm")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| P24 SOAP API | P24 REST API v1 | ~2020 | Use REST endpoints at /api/v1/ |
| MD5 sign (pipe-separated) | SHA-384 sign (JSON) | REST API v1 | Use json.dumps + hashlib.sha384 |
| Form POST to trnDirect | API register + redirect to trnRequest | REST API v1 | Two-step: register via API, redirect with token |

**Deprecated/outdated:**
- python-przelewy24 (GitHub tkajtoch): Last commit 2016, uses old SOAP API with MD5 signing. Do not use.
- p24 (PyPI piotrekio): Last commit 2016, inactive. Do not use.
- django-payments-przelewy24: Inactive for 12+ months, depends on django-payments framework.

## Open Questions

1. **Exact webhook notification sign fields**
   - What we know: Webhook POST includes fields like merchantId, posId, sessionId, amount, originAmount, currency, orderId, methodId, statement, sign
   - What's unclear: The exact set of fields included in the webhook sign calculation. The notification sign may include different fields than registration sign.
   - Recommendation: Start with the documented pattern (all webhook fields except sign itself + CRC key). Test against P24 sandbox to confirm. The P24 sandbox panel shows notification logs which help debug sign mismatches.

2. **P24 sandbox test accounts**
   - What we know: P24 provides a sandbox environment at sandbox.przelewy24.pl
   - What's unclear: Whether a real P24 merchant account is needed for sandbox testing, or if there are public test credentials
   - Recommendation: Register for a P24 sandbox account at przelewy24.pl. Sandbox registration is free. Include this as a prerequisite in the plan.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (built-in, Django 5.2) |
| Config file | backend/settings.py (default test runner) |
| Quick run command | `python3 manage.py test shop --verbosity=2` |
| Full suite command | `python3 manage.py test --verbosity=2` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAY-01 | Checkout creates order + registers P24 transaction + redirects | unit (mocked P24) | `python3 manage.py test shop.tests.test_views -k p24` | Wave 0 |
| PAY-02 | Webhook verifies sign + calls verify endpoint + updates order | unit (mocked P24) | `python3 manage.py test shop.tests.test_payment` | Wave 0 |
| PAY-03 | Return URL renders confirmation page | unit | `python3 manage.py test shop.tests.test_views -k return` | Wave 0 |
| PAY-04 | Order confirmation email sent after payment | unit | `python3 manage.py test shop.tests.test_emails -k confirmation` | Wave 0 |
| PAY-05 | Ebook PDF attached to delivery email | unit | `python3 manage.py test shop.tests.test_emails -k ebook` | Wave 0 |
| PAY-06 | Admin shows orders with p24_session_id | unit | `python3 manage.py test shop.tests.test_views -k admin` | Existing (update) |
| LEGAL-04 | Consent checkboxes in checkout form | unit | `python3 manage.py test shop.tests.test_views -k consent` | Existing |

### Sampling Rate
- **Per task commit:** `python3 manage.py test shop --verbosity=2`
- **Per wave merge:** `python3 manage.py test --verbosity=2`
- **Phase gate:** Full suite green before /gsd:verify-work

### Wave 0 Gaps
- [ ] `shop/tests/test_payment.py` -- covers PAY-02 (P24 sign calculation, register, verify with mocked requests)
- [ ] `shop/tests/test_emails.py` -- covers PAY-04, PAY-05 (email sending with Django test outbox)
- [ ] Update `shop/tests/test_views.py` -- covers PAY-01, PAY-03 (checkout redirect, return URL, webhook)

## Sources

### Primary (HIGH confidence)
- Django 5.2 documentation -- EmailMessage, email backends, CSRF exemption (built-in knowledge, verified against installed Django 5.2.12)
- Existing codebase -- shop/models.py, shop/views.py, shop/cart.py, shop/urls.py, backend/settings.py (direct file reads)

### Secondary (MEDIUM confidence)
- [Przelewy24 REST API docs](https://developers.przelewy24.pl/) -- official documentation (403 blocked for scraping, details from multiple cross-referenced sources)
- [Medium P24 Next.js integration](https://medium.com/@pether.maciejewski/przelewy24-p24-integration-with-next-js-app-router-no-library-in-use-89557c3aa4fc) -- confirmed API structure: POST /api/v1/transaction/register, PUT /api/v1/transaction/verify, SHA-384 JSON sign
- [GitHub nexonyt/Przelewy24-REST-API](https://github.com/nexonyt/Przelewy24-REST-API) -- reference implementation snippets
- [GitHub piatkowski/przelewy24-php](https://github.com/piatkowski/przelewy24-php) -- PHP library confirming API patterns
- [node-przelewy24 Issue #9](https://github.com/ingameltd/node-przelewy24/issues/9) -- critical finding: JSON whitespace causes CRC failures

### Tertiary (LOW confidence)
- Webhook notification sign field set -- inferred from multiple sources but not verified against official docs (blocked). Must validate against P24 sandbox.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- uses only stdlib + requests (already installed) + Django builtins
- Architecture: MEDIUM -- P24 API patterns cross-verified from 4+ sources but official docs were 403-blocked
- Pitfalls: HIGH -- common issues well-documented across community sources (JSON spaces, amount conversion, CSRF)
- Sign calculation: MEDIUM -- JSON.dumps + SHA384 confirmed by multiple sources, but exact webhook sign fields need sandbox validation

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (P24 API is stable, unlikely to change)
