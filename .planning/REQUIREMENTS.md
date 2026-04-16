# Requirements: Kuchenna Komitywa v1.1 Wdrożenie Produkcyjne

**Defined:** 2026-04-10
**Core Value:** Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.

## v1.1 Requirements

### Infrastruktura serwera (MyDevil.net)

- [x] **INFRA-01**: Operator może uruchomić Django na MyDevil.net przez Passenger WSGI z dedykowanym virtualenv
- [x] **INFRA-02**: Operator może zarządzać całą konfiguracją produkcyjną przez plik `.env` bez zmian w kodzie
- [x] **INFRA-03**: Strona serwuje poprawnie pliki statyczne (CSS, JS, ikony) z `public/static/`
- [x] **INFRA-04**: Pliki media (ebooki PDF) są dostępne przez `public/media/` na serwerze produkcyjnym
- [x] **INFRA-05**: Operator może wdrożyć nową wersję przez skrypt `deploy.sh` (pull, install, migrate, collectstatic, restart)
- [x] **INFRA-06**: Błędy aplikacji Django są zapisywane do pliku `logs/django.log`

### Baza danych (PostgreSQL)

- [x] **DB-01**: Aplikacja używa PostgreSQL jako bazy danych na produkcji (zamiast SQLite)
- [x] **DB-02**: Wszystkie migracje Django są wykonane poprawnie na bazie PostgreSQL
- [x] **DB-03**: Operator może zalogować się do panelu administracyjnego Django po uruchomieniu produkcji

### Bezpieczeństwo i HTTPS (SSL)

- [ ] **SSL-01**: Strona jest dostępna wyłącznie przez HTTPS z certyfikatem Let's Encrypt
- [ ] **SSL-02**: Wszystkie żądania HTTP są automatycznie przekierowywane na HTTPS
- [ ] **SSL-03**: Formularze POST (logowanie, checkout, newsletter) działają poprawnie pod HTTPS — `CSRF_TRUSTED_ORIGINS` skonfigurowane
- [ ] **SSL-04**: Pliki cookie sesji i CSRF są zabezpieczone flagami Secure i HttpOnly
- [ ] **SSL-05**: Cron job pinguje stronę co 12h aby zapobiec 24h auto-shutdown na shared hostingu

### Email (Brevo SMTP)

- [x] **EMAIL-01**: Aplikacja wysyła emaile przez Brevo SMTP (nie console backend)
- [ ] **EMAIL-02**: Domena nadawcy jest zweryfikowana w Brevo przez rekordy SPF/DKIM w DNS
- [x] **EMAIL-03**: Email rejestracji + weryfikacji email działa na produkcji
- [x] **EMAIL-04**: Email resetowania hasła działa na produkcji
- [x] **EMAIL-05**: Email potwierdzenia zamówienia z załączonym eBookiem PDF działa na produkcji
- [x] **EMAIL-06**: Email double opt-in dla newslettera działa na produkcji

### Płatności (P24 Sandbox)

- [x] **P24-01**: Płatności Przelewy24 (tryb sandbox) działają na produkcji z poprawnym webhook URL wskazującym na domenę produkcyjną
- [x] **P24-02**: EBooki PDF są uploadowane przez panel admina na serwerze produkcyjnym

### Weryfikacja

- [x] **VER-01**: Pełny flow zakupu działa end-to-end: przeglądanie → koszyk → P24 sandbox → potwierdzenie → email z eBookiem
- [x] **VER-02**: `python manage.py check --deploy` nie wykazuje żadnych ostrzeżeń bezpieczeństwa

## v2 Requirements

### Płatności produkcyjne

- **P24-03**: Aplikacja przyjmuje płatności przez Przelewy24 na produkcji (nie sandbox) — zależne od dostarczenia danych sprzedawcy przez klienta

### Operacyjne

- **OPS-01**: Automatyczne backupy PostgreSQL przez cron (`pg_dump`) — defer do po launch
- **OPS-02**: Monitoring błędów przez Sentry — defer do v1.2 gdy jest realy traffic

### Newsletter campaigns

- **CAMP-01**: Admin może tworzyć i wysyłać kampanie emailowe do bazy subskrybentów — odłożone do v1.2

## Out of Scope

| Feature | Reason |
|---------|--------|
| CI/CD pipeline | Manual SSH deployment wystarczający dla tego rozmiaru projektu |
| Docker / nginx / gunicorn | Niedostępne na MyDevil shared hosting (Passenger WSGI) |
| CDN dla static files | Zbędne przy aktualnym ruchu, MyDevil Apache wystarczy |
| Migracja danych z SQLite | Brak danych produkcyjnych do przeniesienia (nowy sklep) |
| Split settings (base/dev/prod) | django-environ + .env na środowisko to właściwy wzorzec |
| Redis / Celery | Zbędne na shared hostingu, brak asynchronicznych tasków |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 7 | Complete |
| INFRA-02 | Phase 7 | Complete |
| INFRA-03 | Phase 7 | Complete |
| INFRA-04 | Phase 7 | Complete |
| INFRA-05 | Phase 7 | Complete |
| INFRA-06 | Phase 7 | Complete |
| DB-01 | Phase 8 | Complete |
| DB-02 | Phase 8 | Complete |
| DB-03 | Phase 8 | Complete |
| SSL-01 | Phase 8 | Pending |
| SSL-02 | Phase 8 | Pending |
| SSL-03 | Phase 8 | Pending |
| SSL-04 | Phase 8 | Pending |
| SSL-05 | Phase 8 | Pending |
| EMAIL-01 | Phase 9 | Complete |
| EMAIL-02 | Phase 9 | Pending |
| EMAIL-03 | Phase 9 | Complete |
| EMAIL-04 | Phase 9 | Complete |
| EMAIL-05 | Phase 9 | Complete |
| EMAIL-06 | Phase 9 | Complete |
| P24-01 | Phase 10 | Pending |
| P24-02 | Phase 10 | Pending |
| VER-01 | Phase 10 | Pending |
| VER-02 | Phase 10 | Pending |

**Coverage:**
- v1.1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-04-10*
*Last updated: 2026-04-10 after roadmap creation — all 24 requirements mapped to Phases 7-10*
