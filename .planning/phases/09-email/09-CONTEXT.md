# Phase 9: Email - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Konfiguracja Brevo SMTP na produkcji i weryfikacja wszystkich przepływów emailowych: rejestracja/weryfikacja konta, reset hasła, potwierdzenie zamówienia z eBookiem PDF, double opt-in newslettera. Obejmuje też SPF/DKIM i polskie szablony emaili allauth.

</domain>

<decisions>
## Implementation Decisions

### Język emaili allauth
- **D-01:** Emaile allauth (weryfikacja konta, reset hasła) — **po polsku**
- **D-02:** Stworzyć `templates/account/email/` z plikami `.txt` dla każdego przepływu allauth (email_confirmation, password_reset itd.)
- **D-03:** Brak wersji HTML — tylko plaintext, z polską stopką zawierającą nazwę firmy

### Format emaili
- **D-04:** Wszystkie transakcyjne emaile — **plaintext**, nie HTML
- **D-05:** Stopka: `-- \nKuchenna Komitywa\nhttps://kuchennakomitywa.pl`
- **D-06:** Emaile allauth trzymają się standardowej struktury allauth (temat + treść) ale z polskim tekstem

### Konto Brevo i konfiguracja SMTP
- **D-07:** Użytkownik **ma już konto Brevo** — poda SMTP credentials podczas wykonania
- **D-08:** Adres nadawcy: `noreply@kuchennakomitywa.pl` (już skonfigurowany w `DEFAULT_FROM_EMAIL`)
- **D-09:** W Brevo zweryfikować domenę `kuchennakomitywa.pl` przez rekordy SPF i DKIM w DNS MyDevil

### Env vars do ustawienia na produkcji
- **D-10:** `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- **D-11:** `EMAIL_HOST=smtp-relay.brevo.com`
- **D-12:** `EMAIL_PORT=587`
- **D-13:** `EMAIL_USE_TLS=True`
- **D-14:** `EMAIL_HOST_USER=<login Brevo SMTP>` (użytkownik poda)
- **D-15:** `EMAIL_HOST_PASSWORD=<klucz SMTP Brevo>` (użytkownik poda)
- **D-16:** `DEFAULT_FROM_EMAIL=Kuchenna Komitywa <noreply@kuchennakomitywa.pl>` (już w settings.py)

### Claude's Discretion
- Dokładna treść polskich emaili allauth (standardowe allauth tłumaczenia jako baza)
- Kolejność kroków weryfikacji DNS

</decisions>

<specifics>
## Specific Ideas

- Użytkownik ma konto Brevo — nie trzeba kroku zakładania konta
- Wszystkie emaile po polsku — spójne z resztą serwisu
- Plaintext wystarczy dla transakcyjnych emaili tej skali

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Email settings
- `backend/settings.py` §Email — linie ~205-216, wszystkie env-driven zmienne emailowe (EMAIL_BACKEND, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS, DEFAULT_FROM_EMAIL)

### Wymagania
- `.planning/REQUIREMENTS.md` §EMAIL-01 – EMAIL-06 — pełna lista wymagań emailowych do spełnienia

### Szablony allauth
- Brak istniejących `templates/account/email/` — do stworzenia od zera w tej fazie
- Allauth szuka szablonów w: `templates/account/email/{template_name}_subject.txt` i `templates/account/email/{template_name}_message.txt`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/settings.py` — wszystkie zmienne EMAIL_* gotowe jako env-driven z bezpiecznymi defaultami (console backend lokalnie)
- `deploy.sh` — do uruchomienia po dodaniu env vars na serwerze

### Established Patterns
- django-environ (`env()`) — używany do wszystkich konfiguracji; SMTP credentials dodawane tak samo jak inne env vars
- `DEFAULT_FROM_EMAIL` już ustawiony na `"Kuchenna Komitywa <noreply@kuchennakomitywa.pl>"`

### Integration Points
- allauth obsługuje wysyłkę emaili weryfikacyjnych i resetowania hasła automatycznie — zmiana EMAIL_BACKEND wystarczy
- Shop/newsletter mają własne emaile — korzystają z Django `send_mail()` przez ten sam backend

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-email*
*Context gathered: 2026-04-10*
