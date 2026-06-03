---
phase: 260603-bzf
plan: 01
subsystem: newsletter
tags:
  - anti-bot
  - turnstile
  - honeypot
  - cleanup
  - security
status: complete
key-files:
  created:
    - backend/context_processors.py
    - newsletter/captcha.py
    - newsletter/management/__init__.py
    - newsletter/management/commands/__init__.py
    - newsletter/management/commands/cleanup_junk_subscribers.py
  modified:
    - backend/settings.py
    - .env.example
    - newsletter/forms.py
    - newsletter/views.py
    - templates/includes/_newsletter_signup.html
    - static/css/main.css
commit: e23c02e
duration_minutes: 35
---

# Newsletter Anti-Bot — SUMMARY

## What was built

### 1. Cloudflare Turnstile (graceful skip)
- `TURNSTILE_SITE_KEY` i `TURNSTILE_SECRET_KEY` env-driven w `backend/settings.py`
- Context processor `backend.context_processors.turnstile` udostępnia site key w każdym templatce
- Helper `newsletter/captcha.py`:
  - `verify_turnstile(token, remote_ip)` → POST do `challenges.cloudflare.com/turnstile/v0/siteverify` z timeout 10s
  - **Graceful skip** gdy brak `TURNSTILE_SECRET_KEY` → return `(True, "skipped:no-key")` + log warning. Pozwala wdrożyć kod PRZED konfiguracją Cloudflare
  - Catch dla `Timeout`, `RequestException`, `ValueError` (bad JSON) → `(False, reason)` + log
  - `get_client_ip(request)` — XFF first hop → `REMOTE_ADDR`
- Frontend (`_newsletter_signup.html`): `{% if TURNSTILE_SITE_KEY %}` warunkowe załadowanie skryptu + `<div class="cf-turnstile">`. Pod consent checkbox, przed submit button. Light theme dla brand fit.

### 2. Honeypot
- Pole `website` (CharField, required=False) w `NewsletterSignupForm`
- `clean_website` rzuca `ValidationError("bot-detected")` jeśli niepuste → form.is_valid() False → silent redirect home
- CSS class `.kk-honeypot` w `main.css`: `position: absolute; left: -9999px; opacity: 0; pointer-events: none; height/width: 0` — 100% niewidoczne dla człowieka, znajdowane przez boty
- Template: raw HTML `<input type="text" name="website" class="kk-honeypot" tabindex="-1" autocomplete="off" aria-hidden="true">` jako pierwszy field w formularzu

### 3. View logic (`subscribe()`)
1. Form invalid (honeypot triggered or any other) → log info "honeypot" jeśli `website` w errors, redirect home (silent)
2. Pobierz `cf-turnstile-response` token z POST
3. `verify_turnstile(token, ip)` → jeśli False, log info z reason+IP, redirect home (silent)
4. Continue z istniejącym flow (Subscriber.create/update + confirmation email)

Wszystkie odrzucenia ciche — bot nie wie że został wykryty.

### 4. Logger `newsletter.security`
- `log.info` przy odrzuceniach (honeypot, turnstile fail)
- `log.warning` przy braku konfiguracji Turnstile
- `log.error` przy network/timeout errors do Cloudflare

### 5. Management command `cleanup_junk_subscribers`
- Args: `--since YYYY-MM-DD` (default 2026-05-09), `--dry-run`, `--include-confirmed`, `--yes`
- Pokazuje summary: total / unconfirmed / confirmed / unsubscribed (od daty)
- Sample 10 emaili które byłyby usunięte
- Default targets: tylko `is_confirmed=False` (safety)
- Bez `--dry-run` i bez `--yes` → interactive prompt (`Wpisz 'yes' żeby usunąć`)
- Przy `--dry-run` → exit po preview, zero delete

## Validation

### Local
- `manage.py check` → 0 issues
- Form honeypot wypełnione → `is_valid() == False`, error `{'website': ['bot-detected']}`
- Form bez honeypot → `is_valid() == True`
- `verify_turnstile("", "127.0.0.1")` bez `TURNSTILE_SECRET_KEY` → `(True, 'skipped:no-key')`
- Cleanup dry-run lokalnie (pusta DB) → 0 rekordów, exit OK

### Production
- `manage.py check` → 0 issues
- `git log -1 HEAD` → `e23c02e` (matches push)
- `https://kuchennakomitywa.pl/` → HTTP 200
- HTML zawiera `kk-honeypot` (honeypot field obecny w DOM)
- HTML NIE zawiera `turnstile` (graceful skip — klucze nie skonfigurowane jeszcze)

### Production cleanup dry-run (output)
```
Subskrybenci od 2026-05-09:
  Total           : 1728
  Unconfirmed     : 1351  <- usuniemy
  Confirmed       : 377
  Unsubscribed    : 362

Do usunięcia: 1351 rekordów (tylko unconfirmed)

Próbka pierwszych 10 emaili do usunięcia:
  - 56chrysler@wshu.net
  - AJCUSHMAN80@GMAIL.COM
  - DGAGLIANO@KOLBESTRIPING.COM
  - DMUCHOWSKI@TWP.MOUNTHOLLY.NJ.US
  - EMILYKDAY@EPBFI.COM
  - FISCHERWYO@MSN.COM
  - Fabiolaescobedo@aol.com
  - INFO@ACELECTRICALINC.COM
  - JULIE@CASONROOFING.COM
  - LEWIST@LAWTONWELDING.COM
```

Wzorzec: BIG CAPS, korpo adresy (info@, twp.gov), masówka — wygląda jak typowy spam-bot fill.

## Deploy

- Commit: `e23c02e` — `feat(newsletter): anti-bot — Cloudflare Turnstile + honeypot + cleanup command`
- Push: `892874d..e23c02e` → `origin/main`
- Deploy: paramiko + `bash ./deploy.sh` → exit 0, app restarted
- Server HEAD: `e23c02e` (matches)
- 11 files changed, 241 insertions(+)
- 0 external AI API calls

## Next steps for the user

### 1. Usunąć boty z bazy
```bash
ssh jem3pizze@panel84.mydevil.net
cd ~/domains/kuchennakomitywa.pl/public_python

# Najpierw jeszcze raz dry-run:
~/.virtualenvs/komitywa/bin/python manage.py cleanup_junk_subscribers --dry-run

# Jeśli liczby OK, faktyczny delete (1351 unconfirmed):
~/.virtualenvs/komitywa/bin/python manage.py cleanup_junk_subscribers --yes
```

### 2. Włączyć Cloudflare Turnstile (opcjonalne ale rekomendowane)

a) <https://dash.cloudflare.com/?to=/:account/turnstile> → zaloguj się (załóż konto jeśli nie masz — free)
b) "Add site":
   - Name: `Kuchenna Komitywa`
   - Domain: `kuchennakomitywa.pl` (i ewentualnie `www.kuchennakomitywa.pl` jako drugi)
   - Widget Mode: **Managed** (CF sam decyduje kiedy challenge)
c) Save → dostaniesz Site Key + Secret Key
d) Na serwerze:
   ```bash
   ssh jem3pizze@panel84.mydevil.net
   cat >> ~/domains/kuchennakomitywa.pl/public_python/.env <<EOF
   TURNSTILE_SITE_KEY=0x4AAAAAAA<...>
   TURNSTILE_SECRET_KEY=0x4AAAAAAA<...>
   EOF
   devil www restart kuchennakomitywa.pl
   ```
e) Otwórz <https://kuchennakomitywa.pl/> — widget powinien się załadować (zwykle niewidoczny dla legitymowanych userów). Sprawdź w HTML: `view-source:https://kuchennakomitywa.pl/` → grep `turnstile` powinno teraz pokazać linki.

### Co jest live a co czeka

| Warstwa | Status | Skuteczność |
|---|---|---|
| Honeypot `website` | ✅ ACTIVE (od deploy) | ~70-90% prymitywnych botów |
| Cloudflare Turnstile | ⏸ WAITING for keys | ~99% sophisticated botów |
| Cleanup junk subscribers | ✅ READY (dry-run done, user runs --yes) | 1351 rekordów do wycięcia |

Bez Turnstile honeypot łapie większość problemu. Z Turnstile zostanie naprawdę mało (głównie ludzie którzy pomylili adres).

## Files

- **Created:** 5 (`context_processors.py`, `captcha.py`, 2 `__init__.py`, `cleanup_junk_subscribers.py`)
- **Modified:** 6 (`settings.py`, `.env.example`, `forms.py`, `views.py`, `_newsletter_signup.html`, `main.css`)
- **Commit:** `e23c02e`
- **LOC:** +241 / -2
