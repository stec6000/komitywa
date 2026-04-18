# Phase 11: HTTPS & Bezpieczeństwo - Research

**Researched:** 2026-04-16
**Domain:** Django security settings, Let's Encrypt / MyDevil.net, HSTS, CSRF, cookie security
**Confidence:** HIGH

---

## Summary

Faza 11 to faza **weryfikacji i domknięcia** - nie budowy od zera. Infrastruktura HTTPS dla kuchennakomitywa.pl została już skonfigurowana w Fazie 8 (certyfikat Let's Encrypt, redirect HTTP→HTTPS przez Apache `sslonly`, security env vars w produkcyjnym `.env`). Faza 10 potwierdziła że `python manage.py check --deploy` przechodzi bez ostrzeżeń (1 wyciszony - W008 oczekiwany).

Zadaniem Fazy 11 jest: (1) **weryfikacja live na produkcji** że każde kryterium sukcesu jest naprawdę spełnione, (2) **aktualizacja `.env.example`** w repo - security vars powinny być odkomentowane i ustawione na wartości produkcyjne jako wzorzec (bo są teraz aktywne na serwerze), oraz (3) opcjonalne podniesienie HSTS z 3600s do docelowej wartości długoterminowej.

**Kluczowy kontekst:** Wszystkie ustawienia Django (`SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER`, `SILENCED_SYSTEM_CHECKS`) są już w `backend/settings.py`. Produkcyjny `.env` na serwerze ma je aktywne. `.env.example` w repo ma je zakomentowane - to jest główna luka.

**Primary recommendation:** Faza 11 = 1 plan. Weryfikacja produkcyjna (operator-driven checklist) + aktualizacja `.env.example` + decyzja o HSTS duration.

---

## Project Constraints (z CLAUDE.md)

- Stack: Django 5.2 + Django templates (bez SPA)
- Hosting: MyDevil.net (shared hosting z Passenger WSGI)
- Bez CI/CD - deploy manualny przez `deploy.sh`
- Jeden plik settings: `backend/settings.py` (bez split base/dev/prod)
- Env vars przez `django-environ` (`environ.Env`) z pliku `.env`
- String literals: double quotes
- `SILENCED_SYSTEM_CHECKS = ["security.W008"]` - Apache obsługuje HTTP→HTTPS, nie Django

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HTTPS-01 | Strona jest dostępna wyłącznie przez HTTPS z certyfikatem Let's Encrypt | Certyfikat zainstalowany w Fazie 8 via `devil ssl letsencrypt`. Weryfikacja: `curl -I https://kuchennakomitywa.pl` + browser padlock. |
| HTTPS-02 | Wszystkie żądania HTTP są automatycznie przekierowywane na HTTPS | Apache `sslonly` skonfigurowany w Fazie 8. `SECURE_SSL_REDIRECT=False` (celowo - unika double redirect). Weryfikacja: `curl -I http://kuchennakomitywa.pl` → oczekiwany 301/302. |
| HTTPS-03 | Formularze POST działają poprawnie pod HTTPS bez błędów CSRF | `CSRF_TRUSTED_ORIGINS` zawiera `https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl` w settings.py jako DEFAULT i w `.env`. Weryfikacja: ręczny POST formularza logowania/checkoutu. |
| HTTPS-04 | Pliki cookie sesji i CSRF mają flagi `Secure` i `HttpOnly` | `SESSION_COOKIE_SECURE=True` i `CSRF_COOKIE_SECURE=True` w produkcyjnym `.env`. Weryfikacja: DevTools → Application → Cookies. |
| HTTPS-05 | Django security headers są aktywne (HSTS, X-Content-Type-Options, X-Frame-Options) | `SECURE_CONTENT_TYPE_NOSNIFF=True`, `X_FRAME_OPTIONS="DENY"` zawsze włączone. HSTS przez `SECURE_HSTS_SECONDS` w `.env`. Weryfikacja: `curl -I https://kuchennakomitywa.pl`. |
</phase_requirements>

---

## Stan zastanego systemu (co już zrobiono)

### Co jest w settings.py (kod w repo)

[VERIFIED: codebase grep]

```python
# Zawsze włączone (nie wymagają HTTPS):
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"
SILENCED_SYSTEM_CHECKS = ["security.W008"]

# Env-driven (bezpieczne defaults = False/0):
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
CSRF_TRUSTED_ORIGINS = [
    "https://kuchennakomitywa.pl",
    "https://www.kuchennakomitywa.pl",
    # + z .env
]
```

### Co jest w .env.example (repo)

[VERIFIED: git show HEAD:.env.example]

Security vars są **zakomentowane** w `.env.example`:
```bash
# SECURE_SSL_REDIRECT=True
# SESSION_COOKIE_SECURE=True
# CSRF_COOKIE_SECURE=True
# SECURE_HSTS_SECONDS=31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS=True
# SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl
```

`CSRF_TRUSTED_ORIGINS` jest odkomentowane - prawidłowo.

### Co jest w produkcyjnym .env na serwerze (nie w repo)

[VERIFIED: Phase 08-02 SUMMARY.md + Phase 10-01 SUMMARY.md]

Produkcyjny `.env` na MyDevil zawiera aktywne (odkomentowane):
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=3600` (1 godzina - celowo konserwatywnie)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `SECURE_HSTS_PRELOAD=True` (dodane w Phase 10-01 po W021)
- `CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl`
- `SECURE_SSL_REDIRECT=False` (Apache sslonly obsługuje redirect, nie Django)

### Co check --deploy zgłasza

[VERIFIED: Phase 10-01 SUMMARY.md]

- **0 ostrzeżeń** na produkcji (stan po Fazie 10-01)
- 1 wyciszony: `security.W008` - oczekiwany (Apache obsługuje redirect)

---

## Architektura bezpieczeństwa na MyDevil

[VERIFIED: Phase 08-02 SUMMARY.md + settings.py]

```
Browser
  |
  v
Apache (MyDevil) - sslonly mode
  |  - obsługuje HTTP→HTTPS 301 redirect
  |  - terminuje TLS (Let's Encrypt cert)
  |  - ustawia X-Forwarded-Proto: https
  v
Passenger WSGI → Django
  |  - SECURE_PROXY_SSL_HEADER wykrywa HTTPS przez X-Forwarded-Proto
  |  - SECURE_SSL_REDIRECT=False (unika double-redirect)
  |  - session/CSRF cookies: Secure=True, HttpOnly=True
  |  - HSTS header przez Django SecurityMiddleware
  v
Django SecurityMiddleware (zawsze pierwszy w MIDDLEWARE)
```

**Dlaczego SECURE_SSL_REDIRECT=False:** MyDevil Apache z sslonly wykonuje redirect zanim zapytanie dotrze do Django. Gdyby Django też robiło redirect, byłby double-redirect (301→301). [VERIFIED: Phase 08-02 key-decisions]

---

## Co robi Faza 11

### Scenariusz A: Wszystko już działa poprawnie na produkcji

Faza 11 to: **weryfikacja checklistą** + **aktualizacja `.env.example`** + **podniesienie HSTS** + **sign-off**.

### Scenariusz B: Coś nie działa (np. cookies bez flagi Secure)

Wtedy Faza 11 zawiera też naprawę - ale settings.py jest już gotowy, problem byłby w produkcyjnym `.env`.

---

## Weryfikacja checklist (jak sprawdzić każde kryterium)

### HTTPS-01: Certyfikat Let's Encrypt aktywny

```bash
# Z lokalnej maszyny:
curl -vI https://kuchennakomitywa.pl 2>&1 | grep -E "SSL|certificate|issuer|expire"
# Oczekiwane: issuer: Let's Encrypt, CN=kuchennakomitywa.pl

# Lub przez browser: kłódka → "Wydano przez: Let's Encrypt"
```

[VERIFIED: standard curl TLS verification]

### HTTPS-02: HTTP → HTTPS redirect

```bash
curl -I http://kuchennakomitywa.pl
# Oczekiwane: HTTP/1.1 301 (lub 302), Location: https://kuchennakomitywa.pl/
```

### HTTPS-03: CSRF działa

Ręczny test: POST formularza logowania pod `https://kuchennakomitywa.pl/konto/logowanie/` - brak błędu 403 CSRF.

### HTTPS-04: Cookie flags

Browser DevTools → Application → Cookies → `kuchennakomitywa.pl`:
- `sessionid`: Secure=TAK, HttpOnly=TAK
- `csrftoken`: Secure=TAK (HttpOnly=NIE - to normalne dla CSRF token)

### HTTPS-05: Security headers

```bash
curl -I https://kuchennakomitywa.pl
# Oczekiwane:
# strict-transport-security: max-age=...; includeSubDomains; preload
# x-content-type-options: nosniff
# x-frame-options: DENY
```

---

## Decyzja: HSTS duration

[ASSUMED - wymaga decyzji przed zapisem do .env.example]

Obecna wartość na produkcji: `SECURE_HSTS_SECONDS=3600` (1 godzina).

Wartość w `.env.example` (zakomentowana): `31536000` (1 rok).

**Opcje:**

| Wartość | Czas | Kiedy użyć |
|---------|------|------------|
| `3600` | 1 godzina | Testowanie - łatwo odwrócić |
| `86400` | 1 dzień | Przejściowa stabilizacja |
| `2592000` | 30 dni | Długoterminowa stabilizacja |
| `31536000` | 1 rok | Pełna produkcja, wpis do preload list |

**Rekomendacja dla planisty:** Jeśli HTTPS działa stabilnie od Fazy 8 (2026-04-10, ~6 dni), można podnieść do `2592000` (30 dni) lub `31536000` (1 rok). Wartość 1 roku jest wymagana do wpisania na HSTS preload list (https://hstspreload.org). `SECURE_HSTS_PRELOAD=True` jest już aktywne na produkcji.

**UWAGA:** HSTS jest cachowany przez przeglądarkę. Raz ustawiony `max-age=31536000` - trudno cofnąć (przeglądarka będzie wymagać HTTPS przez rok nawet po usunięciu headera).

---

## Aktualizacja .env.example

Kluczowe zadanie w tej fazie: **zaktualizować `.env.example` w repo** żeby odzwierciedlał aktualny stan produkcji.

### Obecny stan (zakomentowane security vars):
```bash
# SECURE_SSL_REDIRECT=True
# SESSION_COOKIE_SECURE=True
# ...
```

### Docelowy stan po Fazie 11:
```bash
# Security - wymagane na produkcji (HTTPS musi być aktywny)
SECURE_SSL_REDIRECT=False   # Apache sslonly obsługuje redirect
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl
```

**Dlaczego to ważne:** Nowy developer (lub operator) który sklonuje repo i skopiuje `.env.example` → `.env` na produkcji, dostanie bezpieczne domyślne wartości zamiast komentarzy.

---

## Typowe pułapki

### Pułapka 1: Double redirect loop

**Co idzie źle:** Ustawienie `SECURE_SSL_REDIRECT=True` gdy Apache już robi redirect.
**Skutek:** Przeglądarka dostaje nieskończoną pętlę 301→301.
**Jak unikać:** Zachować `SECURE_SSL_REDIRECT=False` na MyDevil. [VERIFIED: Phase 08-02 key-decisions, Phase 10-01 key-decisions]

### Pułapka 2: CSRF 403 po zmianie domeny/protokołu

**Co idzie źle:** `CSRF_TRUSTED_ORIGINS` nie zawiera aktualnej domeny z protokołem `https://`.
**Skutek:** Formularze POST zwracają 403 Forbidden.
**Jak unikać:** `CSRF_TRUSTED_ORIGINS` musi zawierać `https://kuchennakomitywa.pl` i `https://www.kuchennakomitywa.pl`. [VERIFIED: settings.py DEFAULT_CSRF_TRUSTED_ORIGINS]

### Pułapka 3: Cookies bez flagi Secure

**Co idzie źle:** `SESSION_COOKIE_SECURE` lub `CSRF_COOKIE_SECURE` nie jest ustawione w `.env` na serwerze.
**Skutek:** Cookies wysyłane przez HTTP - podatność na session hijacking.
**Jak sprawdzić:** DevTools → Application → Cookies - brak checkboxa "Secure".

### Pułapka 4: HSTS uniemożliwia powrót do HTTP

**Co idzie źle:** Zbyt szybko ustawiony `SECURE_HSTS_SECONDS=31536000` gdy HTTPS nie jest stabilny.
**Skutek:** Przeglądarka odmawia dostępu do strony przez HTTP przez rok, nawet jeśli certyfikat wygaśnie.
**Jak unikać:** Podnosić stopniowo: 3600 → 86400 → 2592000 → 31536000.

### Pułapka 5: X-Frame-Options blokuje własne zasoby

**Co idzie źle:** `X_FRAME_OPTIONS = "DENY"` uniemożliwia osadzenie strony w iframe.
**Aktualny stan:** `DENY` jest ustawione i poprawne - strona nie potrzebuje być osadzana.

---

## Środowisko i dostępność narzędzi

| Narzędzie | Wymagane przez | Dostępne | Uwagi |
|-----------|---------------|----------|-------|
| SSH do MyDevil | Weryfikacja produkcji | [ASSUMED] | Dostęp SSH przez całe v1.1 |
| `curl` lokalnie | Weryfikacja headerów | ✓ | Standardowe narzędzie |
| Browser DevTools | Weryfikacja cookies | ✓ | Każda przeglądarka |
| `devil ssl letsencrypt` | Odnowienie certu (jeśli wygasł) | [ASSUMED] | MyDevil CLI, używane w Fazie 8 |
| `devil www restart` | Restart aplikacji | [ASSUMED] | Używane w deploy.sh |

**Zewnętrzne zależności bez fallbacku:**
- Dostęp SSH do MyDevil - bez tego nie można edytować produkcyjnego `.env`
- Domena kuchennakomitywa.pl musi być aktywna i wskazywać na MyDevil

---

## Validation Architecture

> Faza 11 jest fazą weryfikacji - nie ma unit testów. Wszystkie testy są smoke/manual na produkcji.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Manual verification + curl |
| Config file | brak |
| Quick run command | `curl -I https://kuchennakomitywa.pl` |
| Full suite command | Checklist 5 punktów z success criteria |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Command/Action | 
|--------|----------|-----------|----------------|
| HTTPS-01 | Certyfikat Let's Encrypt aktywny | smoke | `curl -vI https://kuchennakomitywa.pl` - sprawdź issuer |
| HTTPS-02 | HTTP → HTTPS redirect | smoke | `curl -I http://kuchennakomitywa.pl` - sprawdź 301 |
| HTTPS-03 | POST formularze bez błędu CSRF | manual | Ręczny POST formularza logowania pod HTTPS |
| HTTPS-04 | Cookie flags Secure + HttpOnly | manual | DevTools → Application → Cookies |
| HTTPS-05 | Security headers aktywne | smoke | `curl -I https://kuchennakomitywa.pl` - sprawdź HSTS, X-Content-Type-Options, X-Frame-Options |

### Wave 0 Gaps

Brak - faza weryfikacyjna, nie wymaga pisania kodu testowego.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | tak | session cookies z `Secure` + `HttpOnly` |
| V3 Session Management | tak | `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True` (Django default) |
| V4 Access Control | nie | brak zmian w autoryzacji |
| V5 Input Validation | nie | brak nowych formularzy |
| V6 Cryptography | tak | TLS 1.2+ przez Apache/Let's Encrypt, nie hand-roll |
| Transport Security | tak | HSTS, HTTPS-only, brak mixed content |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Session hijacking przez HTTP | Information Disclosure | `SESSION_COOKIE_SECURE=True` |
| CSRF przez zmianę origin | Spoofing/Tampering | `CSRF_TRUSTED_ORIGINS` + `CSRF_COOKIE_SECURE` |
| Clickjacking | Tampering | `X_FRAME_OPTIONS = "DENY"` |
| MIME sniffing | Tampering | `SECURE_CONTENT_TYPE_NOSNIFF=True` |
| Downgrade attack | Tampering | HSTS (`SECURE_HSTS_SECONDS`) |
| Mixed content | Information Disclosure | `SECURE_PROXY_SSL_HEADER` + Secure cookies |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Produkcyjny `.env` na MyDevil ma aktywne security vars (Session/CSRF Secure=True, HSTS=3600) | Stan zastanego systemu | Gdyby vars były wyłączone - cookies bez flagi Secure, brak HSTS. Łatwa naprawa przez edycję `.env` i restart. |
| A2 | Dostęp SSH do MyDevil jest dostępny dla operatora | Środowisko | Bez SSH nie można edytować `.env` na serwerze |
| A3 | Certyfikat Let's Encrypt z Fazy 8 jest nadal ważny (ważność 90 dni od 2026-04-10) | HTTPS-01 | Certyfikat wygasa ok. 2026-07-09. Faza 11 jest w granicach ważności. |
| A4 | Decyzja o docelowej wartości HSTS (3600 → 31536000) należy do planisty/użytkownika | HSTS duration | Zbyt wczesne ustawienie 31536000 blokuje powrót do HTTP przez rok |

---

## Open Questions

1. **Docelowa wartość HSTS**
   - Co wiemy: `SECURE_HSTS_SECONDS=3600` na produkcji, `SECURE_HSTS_PRELOAD=True` aktywne
   - Co niejasne: czy podnosić do 31536000 w tej fazie czy zostawić 3600 / podnieść stopniowo
   - Rekomendacja: podnieść do `31536000` jeśli HTTPS jest stabilny od Fazy 8 (~6 dni). To umożliwi wpis na [hstspreload.org](https://hstspreload.org).

2. **SECURE_SSL_REDIRECT w .env.example**
   - Co wiemy: produkcja ma `False` (Apache obsługuje redirect), ale `.env.example` ma zakomentowane `True`
   - Co niejasne: czy `.env.example` powinno mieć `False` czy w ogóle nie mieć tego klucza
   - Rekomendacja: `.env.example` powinno mieć `SECURE_SSL_REDIRECT=False` z komentarzem wyjaśniającym dlaczego

---

## Sources

### Primary (HIGH confidence)

- `backend/settings.py` - zweryfikowany kod w repo, security settings sekcja (linie 261-281)
- `.env.example` (git HEAD) - zweryfikowany plik w repo
- `.planning/phases/08-database-ssl/08-02-SUMMARY.md` (git show) - Phase 8 decisions i accomplishments
- `.planning/phases/10-payments-verification/10-01-SUMMARY.md` (git show) - Phase 10 check --deploy status

### Secondary (MEDIUM confidence)

- Django docs: deployment checklist - [CITED: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/]
- MyDevil sslonly approach - [CITED: Phase 08-02 key-decisions verified in codebase]

### Tertiary (LOW confidence)

- HSTS preload list requirements - [ASSUMED: https://hstspreload.org wymaga max-age >= 31536000]

---

## Metadata

**Confidence breakdown:**
- Aktualny stan systemu: HIGH - zweryfikowany z kodu repo i SUMMARY plików
- Weryfikacja procedury: HIGH - standardowe narzędzia (curl, DevTools)
- Decyzja o HSTS duration: LOW - wymaga decyzji operatora
- MyDevil-specific behavior: MEDIUM - potwierdzony w poprzednich fazach

**Research date:** 2026-04-16
**Valid until:** 2026-06-01 (certyfikat ważny do 2026-07-09; Django 5.2 API stabilne)
