# Requirements: Kuchenna Komitywa v1.2 Infrastruktura & Bezpieczeństwo

**Defined:** 2026-04-16
**Core Value:** Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.

## v1.2 Requirements

### HTTPS & Bezpieczeństwo

- [ ] **HTTPS-01**: Strona jest dostępna wyłącznie przez HTTPS z certyfikatem Let's Encrypt
- [ ] **HTTPS-02**: Wszystkie żądania HTTP są automatycznie przekierowywane na HTTPS
- [ ] **HTTPS-03**: Formularze POST (logowanie, checkout, newsletter) działają poprawnie pod HTTPS bez błędów CSRF (`CSRF_TRUSTED_ORIGINS` skonfigurowane)
- [ ] **HTTPS-04**: Pliki cookie sesji i CSRF mają flagi `Secure` i `HttpOnly`
- [ ] **HTTPS-05**: Django security headers są aktywne (HSTS, X-Content-Type-Options, X-Frame-Options)

### Weryfikacja domeny email

- [ ] **EMAIL-01**: Domena nadawcy jest zweryfikowana w Brevo przez rekordy SPF i DKIM w DNS — emaile trafiają do skrzynki odbiorczej (nie spam)

### Stabilność serwera

- [ ] **OPS-01**: Cron job na MyDevil pinguje stronę co 12h, zapobiegając auto-shutdown serwera (MyDevil wyłącza procesy po 24h braku aktywności)

## Future Requirements

### Monitoring

- **OPS-02**: Monitoring błędów przez Sentry — po osiągnięciu realnego ruchu
- **OPS-03**: Automatyczne backupy PostgreSQL przez cron (`pg_dump`)

### Newsletter campaigns

- **CAMP-01**: Admin może tworzyć i wysyłać kampanie emailowe do bazy subskrybentów — v1.3

## Out of Scope

| Feature | Reason |
|---------|--------|
| P24 produkcyjne kredencjały | Zależne od dostarczenia danych sprzedawcy przez klienta — nie blokuje v1.2 |
| CI/CD pipeline | Manual deploy wystarczający dla tego rozmiaru projektu |
| CDN dla static files | Zbędne przy aktualnym ruchu |
| Redis / Celery | Zbędne na shared hostingu |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| HTTPS-01 | Phase 11 | Pending |
| HTTPS-02 | Phase 11 | Pending |
| HTTPS-03 | Phase 11 | Pending |
| HTTPS-04 | Phase 11 | Pending |
| HTTPS-05 | Phase 11 | Pending |
| EMAIL-01 | Phase 12 | Pending |
| OPS-01 | Phase 12 | Pending |

**Coverage:**
- v1.2 requirements: 7 total
- Mapped to phases: 7
- Unmapped: 0

---
*Requirements defined: 2026-04-16*
