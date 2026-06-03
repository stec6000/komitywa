---
phase: 260603-bzf-newsletter-anti-bot-cloudflare-turnstile
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/settings.py
  - backend/context_processors.py
  - .env.example
  - newsletter/captcha.py
  - newsletter/forms.py
  - newsletter/views.py
  - newsletter/management/__init__.py
  - newsletter/management/commands/__init__.py
  - newsletter/management/commands/cleanup_junk_subscribers.py
  - templates/includes/_newsletter_signup.html
  - static/css/main.css
  - README.md
autonomous: true
requirements: [BZF-AB-01, BZF-AB-02, BZF-AB-03, BZF-AB-04]
must_haves:
  truths:
    - "Bot wypełniający hidden honeypot field 'website' jest odrzucany (silent redirect home, brak Subscriber)."
    - "Bot bez tokenu Cloudflare Turnstile nie tworzy ani nie aktywuje rekordu Subscriber (gdy klucze ustawione)."
    - "Real user widzi widget Turnstile (jeśli klucze skonfigurowane) i kończy subscription flow normalnie."
    - "Gdy TURNSTILE_SECRET_KEY=='' (env brak), helper graceful skip — site działa, formularz przepuszcza."
    - "Istniejące testy newsletter/tests/test_views.py nadal przechodzą (backward compat — bez honeypot i bez tokenu w POST → form pass, captcha skip-path)."
    - "`manage.py cleanup_junk_subscribers --dry-run` pokazuje statystyki (total, unconfirmed, confirmed, sample 10 emaili) i NIE kasuje."
    - "`manage.py cleanup_junk_subscribers --yes` kasuje wyłącznie unconfirmed od --since (default 2026-05-09); confirmed nietknięte chyba że --include-confirmed."
    - "Honeypot pole 'website' jest niewidoczne wizualnie (CSS .kk-honeypot off-screen, opacity 0, no pointer events)."
    - "Strona `/` zwraca HTTP 200 po deploy; widget Turnstile renderuje się TYLKO gdy TURNSTILE_SITE_KEY ustawiony."
  artifacts:
    - path: "backend/context_processors.py"
      provides: "Template context: TURNSTILE_SITE_KEY w każdym renderowanym szablonie"
      contains: "def turnstile(request)"
    - path: "newsletter/captcha.py"
      provides: "verify_turnstile() + get_client_ip()"
      contains: "def verify_turnstile"
    - path: "newsletter/management/commands/cleanup_junk_subscribers.py"
      provides: "Management command dry-run + delete unconfirmed subscribers od daty"
      contains: "class Command"
    - path: "newsletter/forms.py"
      provides: "NewsletterSignupForm z polem honeypot 'website' + clean_website()"
      contains: "clean_website"
    - path: "newsletter/views.py"
      provides: "subscribe() z honeypot + Turnstile verification (silent reject)"
      contains: "verify_turnstile"
    - path: "templates/includes/_newsletter_signup.html"
      provides: "Honeypot input + warunkowy Turnstile widget"
      contains: "kk-honeypot"
    - path: "static/css/main.css"
      provides: "Style .kk-honeypot (hidden) + .kk-turnstile (spacing)"
      contains: ".kk-honeypot"
  key_links:
    - from: "templates/includes/_newsletter_signup.html"
      to: "backend/context_processors.py::turnstile"
      via: "TEMPLATES[0]['OPTIONS']['context_processors'] rejestracja"
      pattern: "backend\\.context_processors\\.turnstile"
    - from: "newsletter/views.py::subscribe"
      to: "newsletter/captcha.py::verify_turnstile"
      via: "import + call z tokenem z request.POST['cf-turnstile-response']"
      pattern: "verify_turnstile\\("
    - from: "templates/includes/_newsletter_signup.html (input name=website)"
      to: "newsletter/views.py::subscribe (request.POST.get('website'))"
      via: "raw POST field — view checks before form processing"
      pattern: "request\\.POST\\.get\\(['\"]website"
    - from: "newsletter/management/commands/cleanup_junk_subscribers.py"
      to: "newsletter/models.Subscriber"
      via: "Subscriber.objects.filter(created_at__date__gte=since, is_confirmed=False)"
      pattern: "Subscriber\\.objects\\.filter"
---

<objective>
Wprowadzenie warstwy anti-bot dla zapisów do newslettera Kuchennej Komitywy:
1. Cloudflare Turnstile (server-side weryfikacja tokenu, env-driven, graceful skip gdy brak kluczy).
2. Honeypot field "website" w formularzu (silent reject botów).
3. Management command `cleanup_junk_subscribers` do bezpiecznego (dry-run domyślnie) sprzątania historycznych spamowych zapisów od 2026-05-09.

Purpose: Spam-rejestracje generują junk Subscriberów, fałszują metryki i blokują wartość listy. Trzeba odciąć bota (Turnstile + honeypot) i posprzątać przeszłość (cleanup command) bez ryzyka usunięcia legalnych subskrybentów (default: tylko unconfirmed).

Output:
- backend/settings.py (TURNSTILE_* przez django-environ env() + context_processor)
- backend/context_processors.py (nowy)
- newsletter/captcha.py (helper siteverify + IP)
- newsletter/forms.py (honeypot field w NewsletterSignupForm)
- newsletter/views.py (honeypot check + Turnstile verify + silent reject)
- newsletter/management/commands/cleanup_junk_subscribers.py (nowy command)
- templates/includes/_newsletter_signup.html (honeypot raw input + widget)
- static/css/main.css (.kk-honeypot, .kk-turnstile)
- README.md (sekcja Newsletter anti-bot)
- Deploy na prod + dry-run output w SUMMARY
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md
@backend/settings.py
@newsletter/forms.py
@newsletter/views.py
@newsletter/models.py
@newsletter/urls.py
@newsletter/emails.py
@newsletter/tests/test_views.py
@templates/includes/_newsletter_signup.html
@templates/base.html
@.env.example

<interfaces>
<!-- Key contracts the executor will produce/consume. -->

# Cloudflare Turnstile siteverify (external API)
POST https://challenges.cloudflare.com/turnstile/v0/siteverify
  data = {
    "secret": TURNSTILE_SECRET_KEY,
    "response": <token from "cf-turnstile-response" POST field>,
    "remoteip": <optional client IP>,
  }
Response JSON: { "success": bool, "error-codes": [str, ...], "hostname": str, "challenge_ts": str }

# newsletter/captcha.py public API
def verify_turnstile(token: str, remote_ip: str | None = None) -> tuple[bool, str]
def get_client_ip(request) -> str | None   # public

# Form HTML output (template renders RAW HTML inputs, not via {{ form }})
<input type="text" name="website" class="kk-honeypot" autocomplete="off" tabindex="-1" aria-hidden="true">
<div class="cf-turnstile kk-turnstile" data-sitekey="{{ TURNSTILE_SITE_KEY }}" data-theme="light"></div>
# Turnstile JS sends back POST field "cf-turnstile-response" automatically.

# Existing form class & fields (from current codebase):
# newsletter/forms.py: NewsletterSignupForm with fields: email, consent_newsletter
# newsletter/views.py: subscribe view at /newsletter/zapisz/, url name "newsletter:subscribe"
# Existing tests POST {"email": ..., "consent_newsletter": "on"} — MUST stay green

# Settings convention: django-environ env() with defaults, NOT os.environ.get
# Example: ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# Subscriber model (read-only here)
Subscriber.objects.filter(created_at__date__gte=<date>, is_confirmed=<bool>, is_unsubscribed=<bool>)
# Fields: email, is_confirmed (bool), confirmation_token, confirmation_sent_at,
#         unsubscribe_token, is_unsubscribed (bool), created_at (auto_now_add)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Settings + context processor + .env.example</name>
  <files>backend/settings.py, backend/context_processors.py, .env.example</files>
  <action>
1. W `backend/settings.py` dodaj POD linią z `ANTHROPIC_API_KEY`:
   ```python
   # Cloudflare Turnstile (anti-bot — newsletter signup). Brak kluczy = graceful skip.
   TURNSTILE_SITE_KEY = env("TURNSTILE_SITE_KEY", default="")
   TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY", default="")
   ```
   Użyj wrappera `env(...)` (django-environ) tak jak istniejące env-driven settings — NIE `os.environ.get`.

2. Stwórz nowy plik `backend/context_processors.py`:
   ```python
   from django.conf import settings


   def turnstile(request):
       return {"TURNSTILE_SITE_KEY": settings.TURNSTILE_SITE_KEY}
   ```

3. W `backend/settings.py` w `TEMPLATES[0]["OPTIONS"]["context_processors"]` dodaj na końcu listy (po `"shop.context_processors.cart_count"`):
   ```python
   "backend.context_processors.turnstile",
   ```

4. Zaktualizuj `.env.example` — dodaj sekcję po sekcji "Security":
   ```
   # Cloudflare Turnstile (anti-bot dla newsletter signup) — opcjonalne, brak = graceful skip
   # TURNSTILE_SITE_KEY=
   # TURNSTILE_SECRET_KEY=
   ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python manage.py check 2>&amp;1 | tee /tmp/check.txt &amp;&amp; grep -qE "0 issues|System check identified no issues|System check identified some issues" /tmp/check.txt &amp;&amp; .venv/bin/python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings'); django.setup(); from django.conf import settings; assert hasattr(settings,'TURNSTILE_SITE_KEY') and hasattr(settings,'TURNSTILE_SECRET_KEY'); assert 'backend.context_processors.turnstile' in settings.TEMPLATES[0]['OPTIONS']['context_processors']; print('settings OK')"</automated>
  </verify>
  <done>
- `manage.py check` zwraca 0 issues (lub tylko silenced).
- `settings.TURNSTILE_SITE_KEY` i `settings.TURNSTILE_SECRET_KEY` istnieją (default "").
- `backend.context_processors.turnstile` zarejestrowany w TEMPLATES.
- `.env.example` zaktualizowany.
  </done>
</task>

<task type="auto">
  <name>Task 2: newsletter/captcha.py — Turnstile helper + IP extractor</name>
  <files>newsletter/captcha.py</files>
  <action>
Stwórz `newsletter/captcha.py`:
```python
import logging

import requests
from django.conf import settings

log = logging.getLogger("newsletter.security")

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def get_client_ip(request) -> str | None:
    """Best-effort: X-Forwarded-For first hop, fallback REMOTE_ADDR."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.META.get("REMOTE_ADDR") or None


def verify_turnstile(token: str, remote_ip: str | None = None) -> tuple[bool, str]:
    """
    Weryfikuje token Cloudflare Turnstile.
    Returns (success, reason). reason in {"ok", "skipped:no-key", "timeout",
    "network-error", "bad-response", joined-error-codes}.
    """
    if not settings.TURNSTILE_SECRET_KEY:
        log.warning(
            "Turnstile not configured (TURNSTILE_SECRET_KEY empty) — skipping verification"
        )
        return (True, "skipped:no-key")

    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token or "",
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        resp = requests.post(TURNSTILE_VERIFY_URL, data=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        log.error("Turnstile verify timeout (ip=%s)", remote_ip)
        return (False, "timeout")
    except requests.RequestException as exc:
        log.error("Turnstile verify network error: %s (ip=%s)", exc, remote_ip)
        return (False, "network-error")
    except ValueError as exc:
        log.error("Turnstile verify JSON parse error: %s", exc)
        return (False, "bad-response")

    success = bool(data.get("success"))
    error_codes = data.get("error-codes") or []
    if error_codes:
        reason = ",".join(error_codes)
    else:
        reason = "ok" if success else "no-success"
    return (success, reason)
```

Dwukrotnie sprawdź: dla TURNSTILE_SECRET_KEY=="" return MUSI być `(True, "skipped:no-key")` — to klucz wstecznej kompatybilności z istniejącymi testami i dev.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.conf import settings
settings.TURNSTILE_SECRET_KEY = ''
from newsletter.captcha import verify_turnstile, get_client_ip
ok, reason = verify_turnstile('')
assert ok is True and reason == 'skipped:no-key', f'expected (True,skipped:no-key), got ({ok},{reason})'
class R:
    META = {'HTTP_X_FORWARDED_FOR':'1.2.3.4, 10.0.0.1', 'REMOTE_ADDR':'127.0.0.1'}
assert get_client_ip(R()) == '1.2.3.4'
class R2:
    META = {'REMOTE_ADDR':'127.0.0.1'}
assert get_client_ip(R2()) == '127.0.0.1'
print('captcha skip-path + IP OK')
"</automated>
  </verify>
  <done>
- Plik `newsletter/captcha.py` istnieje z `verify_turnstile`, `get_client_ip`.
- Bez TURNSTILE_SECRET_KEY → `(True, "skipped:no-key")` (graceful skip).
- `get_client_ip` parsuje XFF first hop, fallback REMOTE_ADDR.
- Logger `newsletter.security` skonfigurowany na module level.
  </done>
</task>

<task type="auto">
  <name>Task 3: newsletter/forms.py — honeypot field "website"</name>
  <files>newsletter/forms.py</files>
  <action>
W `newsletter/forms.py` dodaj do `NewsletterSignupForm`:

1. Pole `website` na końcu definicji pól (PO `consent_newsletter`):
   ```python
   website = forms.CharField(
       required=False,
       widget=forms.TextInput(
           attrs={
               "class": "kk-honeypot",
               "autocomplete": "off",
               "tabindex": "-1",
               "aria-hidden": "true",
           }
       ),
       label="",
   )
   ```

2. Dodaj metodę `clean_website` (POD definicją pól, jako instance method klasy):
   ```python
   def clean_website(self):
       value = self.cleaned_data.get("website", "")
       if value:
           raise forms.ValidationError("bot-detected")
       return value
   ```

Nie zmieniaj pól `email` ani `consent_newsletter`. Nie zmieniaj importów.

WAŻNE: istniejące testy w `newsletter/tests/test_views.py` POST-ują BEZ pola `website` w request.POST. Ponieważ `website` jest `required=False` i nieobecność = pusta wartość → `clean_website` zwraca `""` → form valid. Backward compat OK.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from newsletter.forms import NewsletterSignupForm
f = NewsletterSignupForm(data={'email':'a@b.pl','consent_newsletter':'on'})
assert f.is_valid(), f'clean form should be valid, errors={f.errors}'
f2 = NewsletterSignupForm(data={'email':'a@b.pl','consent_newsletter':'on','website':'http://spam'})
assert not f2.is_valid() and 'website' in f2.errors, f'bot form should fail on website, errors={f2.errors}'
print('honeypot form OK')
"</automated>
  </verify>
  <done>
- `NewsletterSignupForm` akceptuje brak/empty honeypot.
- `NewsletterSignupForm` odrzuca wypełniony honeypot z błędem na `website`.
- Widget renderuje się z `class="kk-honeypot"`.
- Istniejące testy z `consent_newsletter`+`email` bez `website` nadal przechodzą.
  </done>
</task>

<task type="auto">
  <name>Task 4: Template — honeypot raw input + Turnstile widget</name>
  <files>templates/includes/_newsletter_signup.html</files>
  <action>
Obecny szablon używa RAW HTML inputs (nie `{{ form.email }}` itd.). Trzymaj się tej konwencji.

W `templates/includes/_newsletter_signup.html`:

1. ZARAZ po `{% csrf_token %}` a PRZED `<input type="email" ...>` dodaj honeypot:
   ```django
   {# anti-bot honeypot — must remain hidden via .kk-honeypot in main.css #}
   <div class="kk-honeypot" aria-hidden="true">
     <label for="kk-website">Website</label>
     <input type="text" name="website" id="kk-website" class="kk-honeypot" autocomplete="off" tabindex="-1" aria-hidden="true">
   </div>
   ```

2. PO bloku `.form-check` (consent checkbox) a PRZED `<button type="submit" ...>` dodaj widget Turnstile (warunkowo):
   ```django
   {% if TURNSTILE_SITE_KEY %}
     <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
     <div class="cf-turnstile kk-turnstile" data-sitekey="{{ TURNSTILE_SITE_KEY }}" data-theme="light"></div>
   {% endif %}
   ```

UWAGA na kolejność HTML — obecnie button jest PRZED `.form-check`. Albo (a) zachowaj istniejącą kolejność i dodaj Turnstile widget PO `.form-check` (na końcu formy, przed `</form>`), albo (b) przenieś button na koniec formy (DOLEJ formy) i wsadź widget przed nim. Wybierz (a) — minimalna zmiana — i umieść widget jako ostatni element przed `</form>`:

Finalna struktura formy:
```django
<form method="POST" action="{% url 'newsletter:subscribe' %}">
    {% csrf_token %}
    {# honeypot #}
    <div class="kk-honeypot" aria-hidden="true">
      <label for="kk-website">Website</label>
      <input type="text" name="website" id="kk-website" class="kk-honeypot" autocomplete="off" tabindex="-1" aria-hidden="true">
    </div>
    <input type="email" name="email" placeholder="twój e-mail" required aria-label="Adres email">
    <button type="submit" class="btn btn-accent">zapisz mnie</button>
    <div class="form-check">
        <input type="checkbox" name="consent_newsletter" id="id_consent_newsletter" required>
        <label for="id_consent_newsletter">
            Wyrażam zgodę na otrzymywanie newslettera.
            <a href="{% url 'privacy-policy' %}" target="_blank" rel="noopener">Polityka prywatności</a>
        </label>
    </div>
    {% if TURNSTILE_SITE_KEY %}
      <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
      <div class="cf-turnstile kk-turnstile" data-sitekey="{{ TURNSTILE_SITE_KEY }}" data-theme="light"></div>
    {% endif %}
</form>
```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.template.loader import get_template
from django.test import RequestFactory
from django.conf import settings
settings.TURNSTILE_SITE_KEY = '0xTEST_KEY'
t = get_template('includes/_newsletter_signup.html')
req = RequestFactory().get('/')
html = t.render({'TURNSTILE_SITE_KEY':'0xTEST_KEY'}, req)
assert 'kk-honeypot' in html, 'honeypot wrapper missing'
assert 'name=\"website\"' in html, 'website field not rendered'
assert 'cf-turnstile' in html and '0xTEST_KEY' in html, 'turnstile widget missing'
# Test graceful skip — empty site key, no widget
settings.TURNSTILE_SITE_KEY = ''
html2 = t.render({'TURNSTILE_SITE_KEY':''}, req)
assert 'cf-turnstile' not in html2, 'widget should NOT render without site key'
assert 'kk-honeypot' in html2, 'honeypot should always render'
print('template render OK (both with and without site key)')
"</automated>
  </verify>
  <done>
- Template renderuje honeypot div z polem `website` (zawsze).
- Template renderuje widget Turnstile TYLKO gdy `TURNSTILE_SITE_KEY` ustawiony.
- Brak `TURNSTILE_SITE_KEY` → widget się NIE renderuje (graceful skip).
- Istniejące email input + consent checkbox + submit nietknięte.
  </done>
</task>

<task type="auto">
  <name>Task 5: CSS — .kk-honeypot (hidden) + .kk-turnstile (spacing)</name>
  <files>static/css/main.css</files>
  <action>
Na końcu `static/css/main.css` (append, nie modyfikuj istniejących reguł) dodaj:
```css
/* newsletter anti-bot */
.kk-honeypot {
    position: absolute !important;
    left: -9999px !important;
    opacity: 0 !important;
    pointer-events: none !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
}
.kk-turnstile {
    margin: 12px 0;
}
```
Brand: nie wprowadzaj nowych kolorów; widget Turnstile używa `data-theme="light"` (paper bg pasuje).
  </action>
  <verify>
    <automated>grep -q "kk-honeypot" /home/tomo/workspace/komitywa/static/css/main.css &amp;&amp; grep -q "kk-turnstile" /home/tomo/workspace/komitywa/static/css/main.css &amp;&amp; grep -q "left: -9999px" /home/tomo/workspace/komitywa/static/css/main.css &amp;&amp; echo CSS_OK</automated>
  </verify>
  <done>
- `.kk-honeypot` w main.css z off-screen + opacity 0 + pointer-events none.
- `.kk-turnstile` z margin.
- Brak modyfikacji istniejących reguł.
  </done>
</task>

<task type="auto">
  <name>Task 6: newsletter/views.py — honeypot + Turnstile verify (silent reject)</name>
  <files>newsletter/views.py</files>
  <action>
W `newsletter/views.py`:

1. Na górze (po istniejących importach) dodaj:
   ```python
   import logging

   from .captcha import get_client_ip, verify_turnstile

   log = logging.getLogger("newsletter.security")
   ```

2. W view `subscribe(request)`, BEZPOŚREDNIO po `if request.method != "POST": return redirect("home")` a PRZED `form = NewsletterSignupForm(request.POST)`:
   ```python
   # Honeypot fast path — bot fills hidden "website" field.
   if request.POST.get("website", "").strip():
       log.info(
           "newsletter honeypot triggered ip=%s ua=%s",
           get_client_ip(request),
           request.META.get("HTTP_USER_AGENT", "")[:200],
       )
       return redirect("home")
   ```

3. PO `form.is_valid()` check passes, ale PRZED `email = form.cleaned_data["email"]`:
   ```python
   # Cloudflare Turnstile server-side verify (graceful skip when key not configured).
   token = request.POST.get("cf-turnstile-response", "")
   ok, reason = verify_turnstile(token, get_client_ip(request))
   if not ok:
       log.info(
           "newsletter turnstile reject reason=%s ip=%s",
           reason,
           get_client_ip(request),
       )
       return redirect("home")
   ```

4. NIE dodawaj user-visible komunikatów error — silent redirect home.
5. Zachowaj ISTNIEJĄCY flow (existing/new subscriber, confirmation email, IntegrityError handling) BEZ ZMIAN po passing verification.
6. Sprawdź że `redirect("home")` używa url name (już używane w existing code — OK).

WAŻNE: kolejność check'ów:
1) Method check
2) Honeypot raw POST check (najtańsze, łapie 90% botów)
3) Form validation (existing)
4) Turnstile token verify (graceful skip when key=="")
5) Existing subscriber flow
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python manage.py test newsletter.tests.test_views -v 0 2>&amp;1 | tee /tmp/views.txt | tail -5 &amp;&amp; grep -qE "OK$|Ran [0-9]+ tests" /tmp/views.txt &amp;&amp; .venv/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.conf import settings
settings.TURNSTILE_SECRET_KEY = ''
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test import Client
from django.db import connection
from django.core.management import call_command
# in-memory test DB
connection.creation.create_test_db(verbosity=0, autoclobber=True)
from newsletter.models import Subscriber
c = Client()
before = Subscriber.objects.count()
r = c.post('/newsletter/zapisz/', {'email':'bot@spam.test','consent_newsletter':'on','website':'http://x'})
after = Subscriber.objects.count()
assert r.status_code in (301,302), f'expected redirect, got {r.status_code}'
assert after == before, f'bot should NOT create subscriber, before={before} after={after}'
print('view honeypot reject OK')
connection.creation.destroy_test_db(verbosity=0)
"</automated>
  </verify>
  <done>
- Wszystkie istniejące testy `newsletter/tests/test_views.py` przechodzą (backward compat).
- POST z wypełnionym honeypot → 302 redirect home, NO Subscriber created.
- POST clean (honeypot empty, no Turnstile key) → istniejący flow działa (graceful skip).
- Brak user-visible błędu (silent reject).
- Logger `newsletter.security` używany do audytu reject events.
  </done>
</task>

<task type="auto">
  <name>Task 7: Management command cleanup_junk_subscribers (dry-run safety)</name>
  <files>newsletter/management/__init__.py, newsletter/management/commands/__init__.py, newsletter/management/commands/cleanup_junk_subscribers.py</files>
  <action>
1. Stwórz puste pliki:
   - `newsletter/management/__init__.py` (pusty)
   - `newsletter/management/commands/__init__.py` (pusty)

2. Stwórz `newsletter/management/commands/cleanup_junk_subscribers.py`:
```python
import datetime as _dt

from django.core.management.base import BaseCommand, CommandError

from newsletter.models import Subscriber


class Command(BaseCommand):
    help = (
        "Sprząta junk subscribers od --since (default 2026-05-09). "
        "Default targets: tylko unconfirmed. Default tryb: --dry-run-style preview, "
        "real delete wymaga --yes lub interactive 'yes'."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--since", type=str, default="2026-05-09",
            help="ISO date YYYY-MM-DD (default 2026-05-09)",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Tylko podgląd, bez kasowania",
        )
        parser.add_argument(
            "--include-confirmed", action="store_true",
            help="DANGER: kasuje też is_confirmed=True",
        )
        parser.add_argument(
            "--yes", action="store_true",
            help="Skip interactive confirmation (CI/script).",
        )

    def handle(self, *args, **opts):
        try:
            since = _dt.date.fromisoformat(opts["since"])
        except ValueError as exc:
            raise CommandError(f"Bad --since date: {exc}")

        dry_run = opts["dry_run"]
        include_confirmed = opts["include_confirmed"]
        skip_prompt = opts["yes"]

        qs = Subscriber.objects.filter(created_at__date__gte=since)
        total = qs.count()
        unconfirmed = qs.filter(is_confirmed=False).count()
        confirmed = qs.filter(is_confirmed=True).count()
        unsubscribed = qs.filter(is_unsubscribed=True).count()

        self.stdout.write(self.style.NOTICE("=== cleanup_junk_subscribers ==="))
        self.stdout.write(f"Since:            {since.isoformat()}")
        self.stdout.write(f"Total w zakresie: {total}")
        self.stdout.write(f"  unconfirmed:    {unconfirmed}")
        self.stdout.write(f"  confirmed:      {confirmed}")
        self.stdout.write(f"  unsubscribed:   {unsubscribed}")

        if include_confirmed:
            targets = qs
            self.stdout.write(self.style.WARNING(
                "Target: ALL (włącznie z confirmed) — DANGEROUS"
            ))
        else:
            targets = qs.filter(is_confirmed=False)
            self.stdout.write("Target: tylko unconfirmed (safe default)")

        target_count = targets.count()
        self.stdout.write(self.style.NOTICE(f"Do skasowania: {target_count}"))

        sample = list(
            targets.values_list("email", flat=True).order_by("email")[:10]
        )
        if sample:
            self.stdout.write("Sample (max 10):")
            for em in sample:
                self.stdout.write(f"  - {em}")
        else:
            self.stdout.write("Sample: (brak)")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("DRY-RUN — nic nie usunięto."))
            return

        if target_count == 0:
            self.stdout.write(self.style.SUCCESS("Nic do usunięcia."))
            return

        if not skip_prompt:
            answer = input("Type 'yes' to confirm delete: ")
            if answer.strip() != "yes":
                self.stdout.write(self.style.WARNING("Anulowano."))
                return

        deleted, _details = targets.delete()
        self.stdout.write(self.style.SUCCESS(f"Usunięto {deleted} rekordów."))
```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python manage.py cleanup_junk_subscribers --dry-run --since 2026-05-09 2>&amp;1 | tee /tmp/cleanup.txt &amp;&amp; grep -q "DRY-RUN" /tmp/cleanup.txt &amp;&amp; grep -q "Total w zakresie" /tmp/cleanup.txt &amp;&amp; grep -q "Target: tylko unconfirmed" /tmp/cleanup.txt</automated>
  </verify>
  <done>
- `python manage.py cleanup_junk_subscribers --dry-run` działa, pokazuje statystyki + sample, nic nie kasuje.
- Bez `--yes` i bez `--dry-run` → interaktywny prompt "yes" exact match.
- Default targets tylko unconfirmed; `--include-confirmed` zmienia.
- Default `--since=2026-05-09`.
- Polish output z `self.style.SUCCESS/WARNING/NOTICE`.
  </done>
</task>

<task type="auto">
  <name>Task 8: README.md — sekcja Newsletter anti-bot</name>
  <files>README.md</files>
  <action>
README.md istnieje. Dodaj na końcu (append) nową sekcję:

```markdown

## Newsletter anti-bot

Dwuwarstwowa ochrona zapisów do newslettera:

1. **Honeypot field** — ukryte pole `website` w formularzu (`.kk-honeypot`, off-screen via CSS). Boty wypełniają wszystkie pola; wypełnione `website` → silent reject (redirect home, brak komunikatu).
2. **Cloudflare Turnstile** — server-side weryfikacja tokenu. Env-driven, graceful skip gdy brak kluczy.

### Konfiguracja Turnstile

1. Załóż project na https://dash.cloudflare.com/?to=/:account/turnstile
2. Utwórz site → wybierz "Managed" challenge → skopiuj Site Key i Secret Key.
3. Ustaw w env (np. `.env` lub config serwera):
   ```
   TURNSTILE_SITE_KEY=0x...
   TURNSTILE_SECRET_KEY=0x...
   ```
4. Restart Django (gunicorn / passenger).
5. Brak kluczy = graceful skip (widget się nie renderuje, server-side verify zwraca `(True, "skipped:no-key")`). Honeypot zawsze aktywny.

### Cleanup historycznych spamowych zapisów

```bash
# Podgląd (default — bezpieczne):
python manage.py cleanup_junk_subscribers --dry-run

# Inna data graniczna:
python manage.py cleanup_junk_subscribers --dry-run --since 2026-04-01

# Realny delete (tylko unconfirmed, prompt 'yes' wymagany):
python manage.py cleanup_junk_subscribers

# Realny delete bez prompta (CI/skrypt):
python manage.py cleanup_junk_subscribers --yes

# DANGEROUS — kasuje też confirmed:
python manage.py cleanup_junk_subscribers --include-confirmed --yes
```

Default target: TYLKO `is_confirmed=False` od `--since=2026-05-09` (data wprowadzenia anti-bot).
```
  </action>
  <verify>
    <automated>grep -q "Newsletter anti-bot" /home/tomo/workspace/komitywa/README.md &amp;&amp; grep -q "cleanup_junk_subscribers" /home/tomo/workspace/komitywa/README.md &amp;&amp; grep -q "TURNSTILE_SITE_KEY" /home/tomo/workspace/komitywa/README.md &amp;&amp; echo README_OK</automated>
  </verify>
  <done>
- README.md zawiera sekcję "Newsletter anti-bot" z konfiguracją Turnstile + użyciem cleanup command.
- Brak modyfikacji istniejących sekcji README.
  </done>
</task>

<task type="auto">
  <name>Task 9: Local validation suite — check + tests + cleanup dry-run</name>
  <files>(no files modified — validation only)</files>
  <action>
Uruchom kolejno w /home/tomo/workspace/komitywa (każdy command MUSI przejść):
1. `.venv/bin/python manage.py check` → "0 issues" (lub silenced-only).
2. `.venv/bin/python manage.py test newsletter -v 1` → wszystkie testy OK (istniejące test_views, test_models, test_emails nadal pass).
3. `.venv/bin/python manage.py cleanup_junk_subscribers --dry-run` → output zawiera "DRY-RUN" i statystyki.
4. `.venv/bin/python manage.py collectstatic --noinput --dry-run 2>&1 | tail -3` — sanity że nowa zawartość main.css zbuduje się.
5. Smoke render strony `/` lokalnie (jeśli serwer dev się włącza) lub przez `t.render` z Task 4 — sprawdź że honeypot input jest w HTML.

Jeśli którykolwiek krok fail → STOP, fix przed deploy.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python manage.py check 2>&amp;1 | grep -qE "0 issues|System check identified no issues|System check identified some issues" &amp;&amp; .venv/bin/python manage.py test newsletter -v 0 2>&amp;1 | tee /tmp/all_tests.txt | tail -5 &amp;&amp; grep -qE "OK$" /tmp/all_tests.txt &amp;&amp; .venv/bin/python manage.py cleanup_junk_subscribers --dry-run 2>&amp;1 | grep -q "DRY-RUN" &amp;&amp; echo LOCAL_OK</automated>
  </verify>
  <done>
- `manage.py check` przechodzi (0 issues).
- Cała `newsletter` test suite przechodzi.
- Cleanup dry-run output zapisany do późniejszego porównania z prod output.
- Brak nowych ostrzeżeń w `check`.
  </done>
</task>

<task type="auto">
  <name>Task 10: Commit + deploy + prod dry-run cleanup (capture output do SUMMARY)</name>
  <files>(git commit + SSH deploy; no local files modified by this task)</files>
  <action>
1. `git add` zmienione pliki (lista z `files_modified` w frontmatter).
2. Commit jeden lub dwa atomic:
   - Opcja A (single, jeśli diff < 250 linii): `feat(newsletter): anti-bot — Turnstile + honeypot + cleanup_junk_subscribers command`
   - Opcja B (split, jeśli diff większy):
     - `feat(newsletter): anti-bot — Cloudflare Turnstile + honeypot field (silent reject)`
     - `feat(newsletter): add cleanup_junk_subscribers management command (dry-run default)`
3. `git push origin main`.

4. SSH deploy przez paramiko (host `panel84.mydevil.net`, user `jem3pizze`, password `Tak12toto.`):
   ```python
   import paramiko
   c = paramiko.SSHClient()
   c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   c.connect("panel84.mydevil.net", username="jem3pizze", password="Tak12toto.")
   stdin, stdout, stderr = c.exec_command("cd ~/domains/kuchennakomitywa.pl/public_python && bash ./deploy.sh")
   print(stdout.read().decode())
   print(stderr.read().decode())
   c.close()
   ```

5. Po deploy — PROD smoke + DRY-RUN cleanup (uruchom przez SSH):
   ```python
   import paramiko
   c = paramiko.SSHClient()
   c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   c.connect("panel84.mydevil.net", username="jem3pizze", password="Tak12toto.")
   commands = [
     "cd ~/domains/kuchennakomitywa.pl/public_python && ~/.virtualenvs/komitywa/bin/python manage.py check",
     "cd ~/domains/kuchennakomitywa.pl/public_python && ~/.virtualenvs/komitywa/bin/python manage.py cleanup_junk_subscribers --dry-run",
     "curl -sk -o /dev/null -w 'HTTP %{http_code}\\n' https://kuchennakomitywa.pl/",
   ]
   for cmd in commands:
       print("$", cmd)
       i, o, e = c.exec_command(cmd)
       print(o.read().decode())
       print(e.read().decode())
   c.close()
   ```

6. **KRYTYCZNE:** Zapisz CAŁY output z `cleanup_junk_subscribers --dry-run` (statystyki + sample emaile) w SUMMARY.md tego planu. User MUSI zobaczyć liczby przed odpaleniem realnego delete.

7. **NIE odpalaj** `cleanup_junk_subscribers` bez `--dry-run` ani z `--yes` — user to zrobi ręcznie po review.

8. Sanity: prod `manage.py check` 0 issues, https://kuchennakomitywa.pl/ → HTTP 200, response zawiera `kk-honeypot`.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; git log -1 --pretty=%s | grep -qiE "newsletter|anti-bot|turnstile" &amp;&amp; curl -sk -o /tmp/home.html -w "%{http_code}" https://kuchennakomitywa.pl/ | grep -q "200" &amp;&amp; grep -q "kk-honeypot" /tmp/home.html</automated>
  </verify>
  <done>
- Commit(y) na main, push wykonany.
- Deploy script przeszedł bez błędów na panel84.mydevil.net.
- Prod `manage.py check` → 0 issues.
- Prod `cleanup_junk_subscribers --dry-run` output capture'owany do SUMMARY (statystyki + sample 10 emaili).
- https://kuchennakomitywa.pl/ → HTTP 200.
- Response zawiera `kk-honeypot` (anti-bot live na prod).
- Realny delete NIE wykonany (user decyzja).
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| anonymous browser/bot → POST /newsletter/zapisz/ | untrusted POST input, możliwa automatyzacja masowa |
| Django → Cloudflare siteverify (HTTPS, outbound) | zaufany zewnętrzny serwis, wymaga timeout/error handling |
| operator CLI (SSH) → manage.py cleanup_junk_subscribers | privileged destructive operation na produkcyjnej bazie |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-bzf-01 | Spoofing | subscribe view (bot pretends real user) | mitigate | Cloudflare Turnstile token verification server-side (Task 2/6) — token podpisywany przez CF, brak/błędny → silent reject. |
| T-bzf-02 | Tampering | honeypot bypass (bot ignores hidden field) | mitigate | Honeypot to defense-in-depth; primary gate = Turnstile (Task 3+6). Boty form-fillers wpadają na honeypot. |
| T-bzf-03 | Repudiation | brak audytu czemu request odrzucony | mitigate | Logger `newsletter.security` loguje (ip, reason, ua-prefix-200chars) na każde reject — info-level (Task 2+6). |
| T-bzf-04 | Information Disclosure | error messages ujawniają reason rejection (helps bot tuning) | mitigate | Silent redirect home, BRAK user-visible błędu; szczegóły tylko w server log (Task 6). |
| T-bzf-05 | Denial of Service | bot flooding siteverify → koszt CPU/network | accept | Turnstile free tier wystarczy; timeout=10s zapobiega hangowi (Task 2). Rate-limit per IP jest out-of-scope (zaplanowany follow-up). |
| T-bzf-06 | Elevation of Privilege | management command kasuje confirmed subscribers przez pomyłkę | mitigate | Default target = tylko `is_confirmed=False`; `--include-confirmed` wymaga JAWNEGO flagi; bez `--yes` interaktywny prompt "yes" exact match; default workflow = dry-run first (Task 7+10). |
| T-bzf-07 | Tampering | TURNSTILE_SECRET_KEY w env leak / commit | mitigate | `.env.example` zawiera tylko zakomentowane klucze (Task 1); `.env` w `.gitignore`. Klucze read przez django-environ. |
| T-bzf-08 | Denial of Service | Cloudflare API down → all signups blocked | mitigate | `requests.Timeout` / `RequestException` → log error + `(False, "timeout|network-error")` → silent reject (Task 2). Operator może tymczasowo ustawić TURNSTILE_SECRET_KEY="" by graceful-skip do recovery. |
| T-bzf-09 | Repudiation | brak konfirmacji że delete poszedł na prawidłowy zakres | mitigate | Command printuje sample 10 emaili PRZED delete; dry-run wymuszany jako pierwszy krok deploy workflow (Task 7+10). Liczby w SUMMARY do review. |
| T-bzf-10 | Information Disclosure | log IP adresów subskrybentów-botów | accept | IP/UA logowane tylko przy reject (nie przy success). Retencja logów po stronie serwera kontrolowana przez existing `LOGGING` setting (WARNING+); security info-level zachowa się jak inne info-logi. PII = sam IP, ryzyko niskie. |
</threat_model>

<verification>
- `manage.py check` → 0 issues (local + prod).
- Form sanity: pusty/absent honeypot → valid; wypełniony → invalid na `website`.
- Captcha sanity: brak klucza → `(True, "skipped:no-key")`.
- Template sanity: render zawiera `kk-honeypot`, `name="website"` ZAWSZE; `cf-turnstile` z site key TYLKO gdy ustawiony.
- View sanity: POST z honeypot → 302, brak nowego Subscriber. Istniejące testy newsletter/tests/test_views.py PASS.
- Cleanup dry-run: drukuje statystyki, sample, NIE kasuje.
- Prod: https://kuchennakomitywa.pl/ → HTTP 200, HTML zawiera `kk-honeypot`.
- Prod dry-run output z liczbami w SUMMARY (do review przez user).
</verification>

<success_criteria>
- Wszystkie 10 zadań mają `<verify>` automated PASS.
- Subscriber.objects.count() po bot-POST = przed POST (zero new junk).
- Honeypot field 100% niewidoczny wizualnie (CSS .kk-honeypot).
- TURNSTILE_SECRET_KEY="" → site działa, formularz przepuszcza (graceful skip).
- TURNSTILE_SITE_KEY="" → widget Turnstile się NIE renderuje (graceful skip).
- `cleanup_junk_subscribers --dry-run` na prod zwraca statystyki + sample emaile, output zapisany do SUMMARY.
- Real delete NIE wykonany przez executora — czeka na user.
- README.md zaktualizowany z sekcją "Newsletter anti-bot".
- Commit(y) podpisują się jako `feat(newsletter):`.
- HTTP 200 na https://kuchennakomitywa.pl/ po deploy.
- Form renderuje się na każdej stronie z `_newsletter_signup.html` (włączane przez `base.html`).
- Istniejące newsletter testy (test_views.py, test_models.py, test_emails.py) nadal przechodzą.
</success_criteria>

<output>
After completion, create `.planning/quick/260603-bzf-newsletter-anti-bot-cloudflare-turnstile/260603-bzf-SUMMARY.md` zawierający:
- Skrót zmian (files touched, lines added).
- Confirmation że honeypot + Turnstile + cleanup command działają lokalnie i na prod.
- **PEŁNY OUTPUT** z prod `cleanup_junk_subscribers --dry-run` (statystyki + sample 10 emaili) — KRYTYCZNE dla user review.
- Lista commitów (SHA + message).
- Instrukcja dla user: jak wykonać realny delete po review liczb (SSH command + `manage.py cleanup_junk_subscribers --yes`).
- Sprawdzone HTTP statusy z prod.
- Lista znanych "won't fix in this plan" (rate limiting per IP, email blacklist, captcha dla shop checkout) — info-only.
- Notatka czy klucze TURNSTILE_* zostały już skonfigurowane na prod (jeśli tak — widget aktywny; jeśli nie — honeypot jako jedyna warstwa).
</output>
