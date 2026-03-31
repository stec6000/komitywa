---
phase: 02-landing
plan: 01
subsystem: ui
tags: [django-templates, bootstrap5, landing-page, css, hero]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: base.html, static files, core app, navbar, footer, brand CSS tokens

provides:
  - Full landing page at / (hero, feature cards, about teaser, secondary CTA)
  - 5 URL patterns registered: home, about, contact, privacy-policy, regulations
  - 7 test classes covering all Phase 2 requirements (TestHeroSection, TestFeatureCards, TestAboutPage, TestContactPage, TestPrivacyPage, TestRegulationsPage, TestNavbarLinks, TestFooterLinks)
  - Phase 2 CSS components: .kk-hero, .kk-section, .kk-section-alt, .kk-btn-primary, .kk-feature-icon, .kk-link-arrow, .kk-contact-label, .kk-legal-warning
  - Stub templates for about, contact, privacy, regulations (HTTP 200, ready for Plan 02/03 content)

affects: [02-02, 02-03, Phase 2 verifier]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Plain string href for unregistered URLs (e.g., /przepisy/) per Pitfall 1
    - "{% url 'name' %} for registered Django URL patterns"
    - Section architecture: .kk-hero, .kk-section, .kk-section-alt alternating background
    - Bootstrap 5 col-lg-6 split layout for hero

key-files:
  created:
    - templates/pages/home.html
    - templates/pages/about.html
    - templates/pages/contact.html
    - templates/pages/privacy.html
    - templates/pages/regulations.html
    - static/img/hero.jpg
  modified:
    - core/views.py
    - core/urls.py
    - core/tests.py
    - templates/includes/_navbar.html
    - templates/includes/_footer.html
    - static/css/main.css

key-decisions:
  - "Plain string href=/przepisy/ used for unregistered URLs to avoid NoReverseMatch (per UI-SPEC Pitfall 1)"
  - "Navbar O nas and Kontakt links wired to /o-nas/ and /kontakt/ as part of Task 1 (needed for TestNavbarLinks)"
  - "Footer updated with privacy and regulations links as part of Task 1 (needed for TestFooterLinks)"
  - "Hero image downloaded from Unsplash (photo-1512621776951-a57141f2eefd) as vegan food photo"
  - ".kk-placeholder CSS removed as landing page replaces placeholder"

patterns-established:
  - "Section pattern: alternate .kk-section (warm-white) and .kk-section-alt (cream) for visual rhythm"
  - "Stub template pattern: extend base.html, minimal h1 with page name, ready for Plan 02/03 expansion"
  - "CTA button: .kk-btn-primary class on <a> tags, styled as olive green with hover/focus states"

requirements-completed: [LAND-01, LAND-02]

# Metrics
duration: 15min
completed: 2026-03-31
---

# Phase 02 Plan 01: Landing Page & URL Foundation Summary

**Full landing page at / with hero split-layout, 3 feature cards (Bootstrap icons), about teaser, and secondary CTA — plus all 5 Phase 2 URLs, 7 test classes, and Phase 2 CSS components**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-31T16:04:57Z
- **Completed:** 2026-03-31T16:20:00Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Replaced placeholder home page with full landing page: hero (col-lg-6 split, "Gotujemy z sercem" headline, CTA), feature cards (100% Roślinne, Lokalne Składniki, Odbiór Osobisty with Bootstrap Icons), about teaser (Nasza historia), secondary CTA
- Registered 5 URL patterns (home, about, contact, privacy-policy, regulations) and 5 view functions
- Added 7 test classes (42 total tests) covering all Phase 2 requirements — all pass
- Created 4 stub templates for Plans 02/03 expansion, returning HTTP 200
- Extended main.css with Phase 2 CSS components (.kk-hero, .kk-section, .kk-section-alt, .kk-btn-primary, .kk-feature-icon, .kk-link-arrow, .kk-contact-label, .kk-legal-warning)
- Wired navbar O nas/Kontakt links and added footer legal links

## Task Commits

Each task was committed atomically:

1. **Task 1: Register all Phase 2 views, URLs, and test scaffold** - `bd2e6ed` (feat)
2. **Task 2: Build full landing page and CSS components** - `cbc7728` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `templates/pages/home.html` - Full landing page (hero, features, about teaser, CTA)
- `templates/pages/about.html` - Stub template for Plan 02 expansion
- `templates/pages/contact.html` - Stub template for Plan 02 expansion
- `templates/pages/privacy.html` - Stub template for Plan 03 expansion
- `templates/pages/regulations.html` - Stub template for Plan 03 expansion
- `static/img/hero.jpg` - Vegan food hero image from Unsplash (220KB, 1200px)
- `core/views.py` - Added about, contact, privacy_policy, regulations views
- `core/urls.py` - Added 4 new URL patterns
- `core/tests.py` - Added 7 test classes (22 new tests)
- `templates/includes/_navbar.html` - Wired O nas and Kontakt links to real URLs
- `templates/includes/_footer.html` - Added privacy and regulations links
- `static/css/main.css` - Appended Phase 2 CSS, removed .kk-placeholder

## Decisions Made

- Used plain string `href="/przepisy/"` for unregistered URLs to avoid `NoReverseMatch` — per UI-SPEC Pitfall 1. Used `{% url 'about' %}` for registered URL.
- Navbar and footer link updates included in Task 1 commit (prerequisite for TestNavbarLinks and TestFooterLinks tests to be meaningful from the start).
- `.kk-placeholder` CSS removed since the landing page replaces the placeholder entirely.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Wired navbar and footer links in Task 1**
- **Found during:** Task 1 (test scaffold review)
- **Issue:** Plan's Task 1 action specified creating tests that assert `href="/o-nas/"` in navbar and `href="/polityka-prywatnosci/"` in footer, but Task 1 didn't explicitly list `_navbar.html` and `_footer.html` in its `<files>` tag. Without updating these includes, the TestNavbarLinks and TestFooterLinks tests would always fail until Task 2 (which also doesn't update the nav/footer).
- **Fix:** Updated navbar O nas and Kontakt links to real URLs, and added privacy/regulations links to footer — in the Task 1 commit where the test scaffold was added.
- **Files modified:** `templates/includes/_navbar.html`, `templates/includes/_footer.html`
- **Verification:** `python3 manage.py test core.tests.TestNavbarLinks core.tests.TestFooterLinks` — all pass
- **Committed in:** `bd2e6ed` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 — missing critical test support)
**Impact on plan:** Auto-fix ensures test scaffold was functional from the moment it was added. No scope creep.

## Known Stubs

The following templates are intentional stubs to be expanded by later plans:

| File | Status | Plan to expand |
|------|--------|----------------|
| `templates/pages/about.html` | Stub — minimal heading only | Plan 02-02 |
| `templates/pages/contact.html` | Stub — address/hours only | Plan 02-02 |
| `templates/pages/privacy.html` | Stub — legal warning + 1 sentence | Plan 02-03 |
| `templates/pages/regulations.html` | Stub — legal warning + 1 sentence | Plan 02-03 |

These stubs fulfill the must_have truth "All new pages return HTTP 200" and are intentional holding patterns per the plan's design. The plan's goal (full landing page + URL foundation) is achieved.

## Issues Encountered

- **Python/Django not installed in worktree environment** — worktree was created from initial commit with no virtualenv. Resolved by installing pip via `get-pip.py` and running `pip install -r requirements.txt`. Added `.env` file copied from main repo.
- **Worktree branch missing Phase 1 work** — worktree branch was at initial commit only. Resolved with `git merge main` (fast-forward, no conflicts).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Landing page complete and tested — Plan 02-02 can build O nas and Kontakt page content
- All Phase 2 URL patterns registered — Plans 02-02 and 02-03 can build content without URL changes
- Test scaffold complete — all 7 test classes ready, Plan 02-02/03 only needs to make content tests pass
- Phase 2 CSS components defined — Plans 02-02 and 02-03 can use .kk-contact-label, .kk-legal-warning without CSS work

---
*Phase: 02-landing*
*Completed: 2026-03-31*
