# Phase 2: Landing & Brand - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the public-facing landing page with brand identity, separate "O nas" and "Kontakt" pages, and required legal pages (privacy policy, regulations). All pages extend the base.html template from Phase 1 with Bootstrap 5 and the established sage/olive/cream brand palette. Nav links (Przepisy, Sklep) remain as placeholders until their respective phases.

</domain>

<decisions>
## Implementation Decisions

### Hero & Landing Layout
- **D-01:** Split hero layout — text+CTA on left, food photo on right. On mobile stacks vertically.
- **D-02:** Hero CTA button: "Zobacz przepisy" linking to recipes page (placeholder `/przepisy/` until Phase 3)
- **D-03:** Sections below hero (in order): Wyróżniki/Dlaczego my, O nas (skrót z linkiem), CTA do sklepu/przepisów
- **D-04:** 3 feature cards with Bootstrap Icons: "100% Roślinne", "Lokalne Składniki", "Odbiór Osobisty" (or similar — Claude can adjust card content to fit brand)

### O nas & Kontakt Pages
- **D-05:** Separate pages at `/o-nas/` and `/kontakt/` — NOT sections on landing. Nav links go to these pages.
- **D-06:** Landing has brief teasers linking to full O nas and Kontakt pages.
- **D-07:** Contact page: text-only (address, hours, phone/email). NO map embed, NO location image.
- **D-08:** Claude writes realistic Polish draft content for all pages — company story, contact info, etc. User will review and replace with real content later.

### Legal Pages
- **D-09:** Claude's Discretion: Privacy policy and regulations pages — standard Polish e-commerce legal templates. Placeholder content that covers RODO basics.
- **D-10:** Legal pages linked from footer (already has footer from Phase 1 — add links).

### Brand Imagery & Tone
- **D-11:** Use free stock photos from Unsplash/Pexels — vegan food, vegetables, kitchen scenes. Include actual image URLs/files in implementation.
- **D-12:** Copywriting tone: warm and personal — "Gotujemy z sercem", "Zapraszamy do naszej kuchni" style. As if the owner is speaking directly to visitors.
- **D-13:** Carries forward from Phase 1: warm greens/beiges palette (D-08, D-09), Lora headings + Nunito body (D-10), organic/handcrafted feel (D-11)

### Claude's Discretion
- Specific Bootstrap Icons for feature cards (D-04)
- Legal page content structure and wording (D-09)
- Exact stock photo selection (D-11)
- Section spacing and visual rhythm

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Project vision, core value, constraints
- `.planning/REQUIREMENTS.md` — v1 requirements (LAND-01, LAND-02, LAND-03, LEGAL-01, LEGAL-02 for this phase)
- `.planning/ROADMAP.md` — Phase structure and success criteria

### Phase 1 Outputs
- `.planning/phases/01-foundation/01-CONTEXT.md` — Brand decisions (colors, fonts, feel)
- `.planning/phases/01-foundation/01-01-SUMMARY.md` — Django config, static handling
- `.planning/phases/01-foundation/01-02-SUMMARY.md` — Template hierarchy, brand CSS
- `.planning/phases/01-foundation/01-03-SUMMARY.md` — Cookie consent implementation

### Existing Templates & CSS
- `templates/base.html` — Master template to extend
- `templates/includes/_navbar.html` — Nav with placeholder links
- `templates/includes/_footer.html` — Footer to add legal links to
- `static/css/main.css` — Brand CSS custom properties (--kk-*)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `base.html`: Master template with Bootstrap 5.3.3, Google Fonts (Lora+Nunito), brand CSS
- `_navbar.html`: Nav with Przepisy, Sklep, O nas, Kontakt links (currently `href="#"` — wire to real URLs)
- `_footer.html`: Footer with copyright — add legal page links
- `static/css/main.css`: Brand color variables (--kk-sage, --kk-olive, --kk-cream, etc.), typography, navbar/footer styles
- `core/` app: Home view at `/` — extend with new views or create new `pages/` app

### Established Patterns
- Template inheritance: `{% extends "base.html" %}` with `{% block content %}`
- Partial includes: `templates/includes/_*.html`
- CSS custom properties: `--kk-*` prefix for all brand values
- Polish locale (`pl`), Warsaw timezone

### Integration Points
- `core/urls.py` or new app URLs: Add `/o-nas/`, `/kontakt/`, `/polityka-prywatnosci/`, `/regulamin/`
- `_navbar.html`: Replace `href="#"` with real URLs for O nas, Kontakt
- `_footer.html`: Add links to privacy policy and regulations
- `static/css/main.css`: Add styles for hero, feature cards, page-specific layouts

</code_context>

<specifics>
## Specific Ideas

- Hero split layout: left text + CTA, right food photo. Warm, inviting first impression.
- Feature cards: 3 cards with icons — "100% Roślinne", "Lokalne Składniki", "Odbiór Osobisty"
- Contact page: just text — no map or location images. Keep it simple.
- Copywriting: warm and personal tone, as if the owner is speaking directly ("z sercem", "zapraszamy")
- Stock photos from Unsplash/Pexels for hero and sections

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-landing*
*Context gathered: 2026-03-31*
