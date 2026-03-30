# Phase 1: Foundation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase transforms the existing API-only Django backend into a server-rendered HTML application with proper template infrastructure, environment configuration, static/media file handling, responsive design (Bootstrap 5), and RODO-compliant cookie consent. No content pages are built here — only the skeleton that all future pages will use.

</domain>

<decisions>
## Implementation Decisions

### Navigation
- **D-01:** Main nav links: Przepisy, Sklep, O nas, Kontakt
- **D-02:** Logo in nav links to landing page (strona glowna)
- **D-03:** Cart icon with item count badge in navigation
- **D-04:** Claude's Discretion: Mobile menu style (hamburger or bottom bar — pick what fits the warm/natural brand best)

### Cookie Consent
- **D-05:** Minimal bottom bar style cookie banner (not modal, not full-screen)
- **D-06:** Two buttons: "Akceptuj" and "Odrzuc" (simple accept/reject, no granular settings)
- **D-07:** Must comply with RODO — remember user choice, don't re-show after decision

### Visual Identity / Brand
- **D-08:** Climate/vibe: Warm and natural — like a home kitchen, organic shapes, cozy feeling
- **D-09:** Color palette: Greens + beiges — sage, olive, cream, natural earth tones
- **D-10:** Claude's Discretion: Typography — choose fonts that match the warm/natural kitchen vibe (serif headings for elegance + sans-serif body recommended)
- **D-11:** Overall design should feel handcrafted, inviting, organic — not corporate or cold

### Claude's Discretion
- Mobile menu implementation style (D-04)
- Font pairing selection (D-10)
- Specific Bootstrap 5 customization approach (SCSS variables vs CSS custom properties)
- Cookie consent implementation method (custom vs library like django-cookie-consent)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Project vision, core value, constraints
- `.planning/REQUIREMENTS.md` — v1 requirements with REQ-IDs (FOUND-01..05, LEGAL-03 for this phase)
- `.planning/ROADMAP.md` — Phase structure and success criteria

### Codebase State
- `.planning/codebase/STACK.md` — Current Django 5.2 stack, dependencies
- `.planning/codebase/ARCHITECTURE.md` — Current API-only architecture, migration path
- `.planning/codebase/STRUCTURE.md` — Current directory layout
- `.planning/codebase/CONCERNS.md` — Hardcoded SECRET_KEY, DEBUG=True, missing .env usage

### Research
- `.planning/research/STACK.md` — Recommended additions (Bootstrap 5, htmx, crispy-forms)
- `.planning/research/ARCHITECTURE.md` — Template infrastructure, build order, migration strategy
- `.planning/research/PITFALLS.md` — Hardcoded secrets pitfall, security concerns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `accounts/` app: Custom User model, allauth templates (email confirmation, password reset) — keep and extend
- `backend/settings.py`: Base configuration — needs env var migration, template config, static/media config
- `backend/urls.py`: URL routing — add template-based views alongside API routes
- `python-dotenv`: Already in requirements.txt but unused — activate in settings.py

### Established Patterns
- Email templates already in Polish (accounts/templates/account/email/)
- Django admin configured with custom UserAdmin
- Token + Session authentication both enabled

### Integration Points
- `backend/settings.py`: Add TEMPLATES config, STATICFILES_DIRS, MEDIA_ROOT/URL, Bootstrap
- `backend/urls.py`: Add template view routes alongside existing API routes
- New `templates/` dir at project root for base.html and includes
- New `static/` dir at project root for CSS, JS, images

</code_context>

<specifics>
## Specific Ideas

- Warm, home kitchen feel — not a tech/corporate site
- Greens and beiges evoke plants, nature, vegan values
- Navigation should feel simple and welcoming
- Cookie banner should be unobtrusive (bottom bar, minimal)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-30*
