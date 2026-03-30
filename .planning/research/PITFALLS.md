# Pitfalls Research

**Domain:** Vegan food business website (Django e-commerce + blog + newsletter)
**Researched:** 2026-03-30
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Hardcoded Secrets in Settings

**What goes wrong:**
SECRET_KEY, database credentials, API keys committed to git. Already present in this codebase (SECRET_KEY hardcoded, DEBUG=True).

**Why it happens:**
Django's default `startproject` generates settings with hardcoded values. Developers forget to externalize before going public.

**How to avoid:**
- Move all secrets to `.env` file (python-dotenv is already installed but unused)
- Use `os.environ.get()` or `decouple.config()` for all sensitive settings
- Add `.env` to `.gitignore` immediately
- Create `.env.example` with placeholder values

**Warning signs:**
SECRET_KEY visible in settings.py, DEBUG=True in any shared branch

**Phase to address:** Phase 1 (Foundation) — must be fixed before any public deployment

---

### Pitfall 2: Przelewy24 Webhook Security

**What goes wrong:**
Payment webhooks not properly verified. Attacker sends fake webhook marking orders as paid without actual payment.

**Why it happens:**
Developers test with P24 sandbox, webhook verification works, then skip CRC verification or IP whitelisting in production.

**How to avoid:**
- Always verify P24 webhook signature (CRC check with your CRC key)
- Verify the payment amount matches order amount
- Use P24's transaction verification endpoint as secondary check
- Whitelist P24 IP addresses for webhook endpoint
- Log all webhook attempts for audit

**Warning signs:**
Orders marked "paid" without matching P24 transaction ID, webhook endpoint accessible without signature verification

**Phase to address:** Phase 5 (Payments & Orders)

---

### Pitfall 3: Ebook PDF Accessible Without Payment

**What goes wrong:**
Ebook PDF files stored in public media directory. Anyone with the URL can download without paying.

**Why it happens:**
Django's default media serving makes all uploaded files publicly accessible via `/media/` URL.

**How to avoid:**
- Store ebook files outside MEDIA_ROOT (e.g., in a `protected/` directory)
- Serve ebooks only through a Django view that checks payment status
- Use signed, time-limited download URLs in delivery emails
- Never expose direct file paths in templates or API responses

**Warning signs:**
PDF files accessible at `/media/ebooks/filename.pdf` without authentication

**Phase to address:** Phase 4-5 (Shop setup + Payments)

---

### Pitfall 4: Missing RODO/GDPR Compliance

**What goes wrong:**
Polish law (RODO — the Polish implementation of GDPR) requires explicit consent for data processing, newsletter opt-in, cookie policy. Missing these = legal liability.

**Why it happens:**
Developers focus on features, forget legal requirements. Poland's UODO (data protection authority) actively fines businesses.

**How to avoid:**
- Cookie consent banner (required for analytics, tracking cookies)
- Newsletter double opt-in (confirmation email before adding to list)
- Privacy policy page (polityka prywatnosci) — required
- Terms of service (regulamin) — required for e-commerce
- Right to data deletion (account deletion feature)
- Data processing consent checkboxes on registration and checkout forms
- Regulamin sklepu (store terms) — required by Polish e-commerce law

**Warning signs:**
No privacy policy link in footer, newsletter without double opt-in, no cookie banner

**Phase to address:** Phase 1 (Foundation — legal pages) + Phase 5 (Checkout — consent checkboxes) + Phase 6 (Newsletter — double opt-in)

---

### Pitfall 5: Poor Image Handling for Food Photography

**What goes wrong:**
Large, unoptimized images tank page load time. Food sites are especially image-heavy (recipes, products). Core Web Vitals fail, SEO drops.

**Why it happens:**
Admin uploads high-res photos (3-5MB each). No automatic resizing or format conversion. Pages load 10+ seconds on mobile.

**How to avoid:**
- Auto-generate thumbnails at upload time (easy-thumbnails)
- Serve WebP format with JPEG fallback
- Implement lazy loading for images below the fold
- Set max upload dimensions in admin
- Use responsive `srcset` for different screen sizes
- Consider CDN for production (CloudFront, Cloudflare)

**Warning signs:**
Recipe list page > 5MB, Lighthouse performance score < 50, images served as original upload size

**Phase to address:** Phase 3 (Recipes) + Phase 7 (Polish & Production)

---

### Pitfall 6: Session Cart Data Loss

**What goes wrong:**
Cart stored only in session. Session expires or user clears cookies — cart is gone. Especially painful if user spent time selecting items.

**Why it happens:**
Session-based cart is the simplest implementation. Works fine in dev but frustrating in production.

**How to avoid:**
- For anonymous users: session cart is acceptable for v1
- For logged-in users: persist cart to database
- Merge session cart into DB cart on login
- Set session expiry to at least 7 days for cart data

**Warning signs:**
Users complain about lost carts, high checkout abandonment

**Phase to address:** Phase 4 (Shop — cart implementation)

---

### Pitfall 7: Email Deliverability for Ebook Delivery

**What goes wrong:**
Ebook PDF emails land in spam. Customer pays but never receives the ebook. Support tickets pile up.

**Why it happens:**
Sending from a new domain without proper email authentication (SPF, DKIM, DMARC). Attachments increase spam score. No dedicated email service.

**How to avoid:**
- Set up SPF, DKIM, DMARC records for your domain
- Use a transactional email service (e.g., Amazon SES, Mailgun) instead of shared SMTP
- Don't attach PDFs directly — send a secure download link instead
- Monitor delivery rates and bounce rates
- Test with mail-tester.com before launch

**Warning signs:**
Emails in spam folder during testing, bounced emails, no SPF/DKIM configured

**Phase to address:** Phase 5 (Ebook delivery) + Phase 7 (Production email setup)

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| SQLite in production | No DB setup needed | Concurrent writes fail, no backups, data loss risk | Never for e-commerce with payments |
| No Celery (sync emails) | Simpler stack | Checkout blocks while sending email, timeouts | MVP testing only, must add before launch |
| All settings in settings.py | Quick to read | Can't deploy to different environments | Development only |
| No automated tests for payments | Faster development | Payment bugs discovered by customers | Never — payments must be tested |
| Manual ebook delivery | No email infrastructure | Doesn't scale, delays, human error | First 10 orders only |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Przelewy24 | Testing only in sandbox, not handling all P24 status codes | Test full flow including error states, timeouts, double-notifications |
| Przelewy24 | Using test CRC key in production | Separate P24_MERCHANT_ID, P24_CRC_KEY, P24_API_KEY per environment |
| Email (SMTP) | Using Gmail SMTP for transactional email | Use proper transactional service (SES, Mailgun); Gmail has daily limits and poor deliverability |
| Image uploads | No file type validation | Validate file extension AND content type; reject non-image uploads |
| Newsletter | Single opt-in | Polish law requires double opt-in (confirmation email) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| N+1 queries on recipe list | Slow recipe index page, many DB queries | Use `select_related()` and `prefetch_related()` | 50+ recipes |
| Unoptimized images | Page load > 5s, high bandwidth | Auto-thumbnails, WebP, lazy loading | 10+ images per page |
| No database indexing | Slow searches, slow category filtering | Add `db_index=True` on filtered fields (category, published, slug) | 100+ recipes/products |
| No caching | Every page hit queries DB | Django cache framework, template fragment caching | 100+ concurrent users |
| Synchronous email in request | Checkout hangs for 3-5s while sending email | Celery async tasks for all email sending | Any production traffic |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Unverified P24 webhooks | Fake payment confirmations, free products | Always verify CRC signature + amount match |
| Public ebook file URLs | Anyone downloads without paying | Serve through Django view with auth check |
| No CSRF on cart/checkout | Cart manipulation, order forgery | Django CSRF is on by default — don't disable it |
| Admin panel on default URL | Brute force attacks on /admin/ | Move admin to non-standard URL, add rate limiting |
| No rate limiting on auth | Credential stuffing attacks | django-axes or django-ratelimit on login/register |
| Storing card data | PCI compliance nightmare | Never store card data — P24 handles this |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No recipe print view | Users can't print recipes for kitchen use | Add print-friendly CSS or dedicated print template |
| Checkout requires registration | Cart abandonment increases 25-35% | Allow guest checkout (email only for order + ebook delivery) |
| No order confirmation page | Users unsure if order went through | Clear confirmation page + confirmation email |
| No search on recipe blog | Users can't find specific recipes | Full-text search with title, ingredients, tags |
| Product images too small | Can't see food details, reduces trust | Large, zoomable product photos |
| No ingredient quantities scaling | Users can't adjust recipe for different servings | Allow serving count adjustment (nice-to-have for v2) |

## "Looks Done But Isn't" Checklist

- [ ] **Payments:** Payment verification webhook tested with actual P24 sandbox flow, not just mocked
- [ ] **Ebook delivery:** Email actually arrives in inbox (not spam) with working download link
- [ ] **Recipe SEO:** Schema.org JSON-LD validates in Google's Rich Results Test
- [ ] **Cart:** Works correctly with multiple products, quantities, mixed types (ebook + physical)
- [ ] **Mobile:** Full checkout flow tested on mobile (forms, payment redirect, confirmation)
- [ ] **Legal:** Privacy policy, terms of service, cookie consent, RODO compliance all present
- [ ] **Email:** SPF/DKIM/DMARC configured, tested with mail-tester.com
- [ ] **404/500:** Custom error pages exist and look professional
- [ ] **Admin:** Staff can manage recipes, products, orders without developer help
- [ ] **Sitemap:** XML sitemap includes all recipe and product pages

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Hardcoded secrets | Phase 1 (Foundation) | `.env` file exists, settings reads from env vars |
| P24 webhook security | Phase 5 (Payments) | CRC verification test passes with sandbox |
| Ebook URL exposure | Phase 4-5 (Shop + Payments) | Direct media URL returns 403/404 |
| RODO compliance | Phase 1 + 5 + 6 | All legal pages present, consent checkboxes on forms |
| Image performance | Phase 3 + 7 | Lighthouse performance > 80 |
| Session cart loss | Phase 4 (Shop) | Cart persists after page refresh and login |
| Email deliverability | Phase 5 + 7 | mail-tester.com score > 8/10 |

## Sources

- Przelewy24 developer documentation
- UODO (Polish DPA) guidelines on RODO compliance
- Django security best practices (djangoproject.com)
- Google Rich Results Test documentation
- Core Web Vitals documentation

---
*Pitfalls research for: vegan food business website*
*Researched: 2026-03-30*
