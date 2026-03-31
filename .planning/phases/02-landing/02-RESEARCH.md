# Phase 2: Landing & Brand - Research

**Researched:** 2026-03-31
**Domain:** Django templates, Bootstrap 5 layout, static content pages
**Confidence:** HIGH

## Summary

Phase 2 is a content-focused, template-only phase. No new Django models, no database migrations, no new Python packages. The work involves: (1) replacing the placeholder `home.html` with a full landing page (hero, features, teasers), (2) creating 4 new pages (`/o-nas/`, `/kontakt/`, `/polityka-prywatnosci/`, `/regulamin/`), (3) wiring navbar and footer links, and (4) adding CSS for new components.

All infrastructure is already in place from Phase 1: `base.html` with Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Google Fonts (Lora + Nunito), brand CSS custom properties (`--kk-*`), navbar with placeholder links, footer, and cookie consent. The `core` app has a single view and URL pattern. New pages can be added either as new views in `core/views.py` + `core/urls.py`, or as a new `pages` app -- the simpler approach is extending `core` since it already handles the home page.

**Primary recommendation:** Add all new views to the existing `core` app using simple function-based views with `TemplateView` or `render()`. No new apps needed. All content is hardcoded in templates (no models). Stock images referenced via Unsplash/Pexels URLs in `<img>` tags or downloaded to `static/img/`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Split hero layout -- text+CTA on left, food photo on right. On mobile stacks vertically.
- **D-02:** Hero CTA button: "Zobacz przepisy" linking to `/przepisy/` (placeholder until Phase 3)
- **D-03:** Sections below hero (in order): Wyrozniki/Dlaczego my, O nas (skrot z linkiem), CTA do sklepu/przepisow
- **D-04:** 3 feature cards with Bootstrap Icons: "100% Roslinne", "Lokalne Skladniki", "Odbior Osobisty" (Claude can adjust card content to fit brand)
- **D-05:** Separate pages at `/o-nas/` and `/kontakt/` -- NOT sections on landing. Nav links go to these pages.
- **D-06:** Landing has brief teasers linking to full O nas and Kontakt pages.
- **D-07:** Contact page: text-only (address, hours, phone/email). NO map embed, NO location image.
- **D-08:** Claude writes realistic Polish draft content for all pages. User will review and replace later.
- **D-09:** Privacy policy and regulations pages -- standard Polish e-commerce legal templates with RODO basics.
- **D-10:** Legal pages linked from footer (add links to existing footer).
- **D-11:** Use free stock photos from Unsplash/Pexels -- vegan food, vegetables, kitchen scenes.
- **D-12:** Copywriting tone: warm and personal ("Gotujemy z sercem", "Zapraszamy do naszej kuchni").
- **D-13:** Carries forward Phase 1 brand: warm greens/beiges, Lora headings + Nunito body, organic feel.

### Claude's Discretion
- Specific Bootstrap Icons for feature cards (D-04)
- Legal page content structure and wording (D-09)
- Exact stock photo selection (D-11)
- Section spacing and visual rhythm

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LAND-01 | Uzytkownik widzi sekcje hero z misja firmy i value proposition | Hero section in home.html with split layout (D-01), CTA (D-02), brand copy (D-12) |
| LAND-02 | Uzytkownik moze przeczytac historie firmy w sekcji "O nas" | Separate `/o-nas/` page (D-05) with teaser on landing (D-06), draft Polish content (D-08) |
| LAND-03 | Uzytkownik widzi informacje kontaktowe z adresem odbioru, godzinami i mapa | Separate `/kontakt/` page (D-05, D-07) -- text only, no map. Note: REQUIREMENTS.md says "mapa" but D-07 explicitly overrides: NO map embed. |
| LEGAL-01 | Strona posiada strone z polityka prywatnosci | `/polityka-prywatnosci/` page with RODO template content (D-09), linked from footer (D-10) |
| LEGAL-02 | Strona posiada regulamin sklepu | `/regulamin/` page with e-commerce template content (D-09), linked from footer (D-10) |

</phase_requirements>

## Standard Stack

### Core (already installed -- no new packages)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 4.2.x (installed) | Web framework, template rendering, URL routing | Already configured |
| Bootstrap | 5.3.3 (CDN) | Responsive grid, components, utilities | Already in base.html |
| Bootstrap Icons | 1.11.3 (CDN) | Icon font for feature cards and decorative elements | Already in base.html |
| Google Fonts | Lora + Nunito | Brand typography | Already in base.html |

### Supporting
No new packages needed. This phase is purely templates + CSS + views.

## Architecture Patterns

### Recommended Project Structure
```
core/
  views.py          # Add about, contact, privacy, regulations views
  urls.py           # Add URL patterns for new pages
templates/
  pages/
    home.html       # REPLACE placeholder with full landing page
    about.html      # O nas page
    contact.html    # Kontakt page
    privacy.html    # Polityka prywatnosci
    regulations.html # Regulamin
  includes/
    _navbar.html    # UPDATE: wire real URLs for O nas, Kontakt
    _footer.html    # UPDATE: add legal page links
static/
  css/
    main.css        # ADD: hero, feature card, page-specific styles
  img/
    hero.jpg        # Stock photo for hero section (or use Unsplash URL)
    (other images)
```

### Pattern 1: Simple Function-Based Views
**What:** Use plain `render()` views for static content pages.
**When to use:** Pages with no dynamic data, no models, just template rendering.
**Example:**
```python
# core/views.py
from django.shortcuts import render


def home(request):
    return render(request, "pages/home.html")


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")


def privacy_policy(request):
    return render(request, "pages/privacy.html")


def regulations(request):
    return render(request, "pages/regulations.html")
```

### Pattern 2: URL Naming for Template Links
**What:** Use Django's `{% url %}` tag for all internal links.
**When to use:** All navigation, CTAs, footer links.
**Example:**
```python
# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("o-nas/", views.about, name="about"),
    path("kontakt/", views.contact, name="contact"),
    path("polityka-prywatnosci/", views.privacy_policy, name="privacy-policy"),
    path("regulamin/", views.regulations, name="regulations"),
]
```

### Pattern 3: Bootstrap 5 Hero Split Layout
**What:** Two-column hero using Bootstrap grid. Text left, image right. Stacks on mobile.
**Example:**
```html
<section class="kk-hero">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-lg-6">
                <h1>Gotujemy z sercem</h1>
                <p class="lead">...</p>
                <a href="{% url 'recipes' %}" class="btn kk-btn-primary">Zobacz przepisy</a>
            </div>
            <div class="col-lg-6">
                <img src="..." class="img-fluid rounded" alt="...">
            </div>
        </div>
    </div>
</section>
```

### Pattern 4: Feature Cards with Bootstrap Icons
**What:** Three equal-width cards using Bootstrap grid + icon font.
**Example:**
```html
<section class="kk-features">
    <div class="container">
        <div class="row g-4">
            <div class="col-md-4">
                <div class="text-center">
                    <i class="bi bi-flower1 kk-feature-icon"></i>
                    <h3>100% Roslinne</h3>
                    <p>...</p>
                </div>
            </div>
            <!-- repeat for other cards -->
        </div>
    </div>
</section>
```

### Pattern 5: Brand-Consistent Button Styles
**What:** Custom button classes using `--kk-*` CSS variables.
**Example:**
```css
.kk-btn-primary {
    background-color: var(--kk-olive);
    color: white;
    border: none;
    font-family: var(--kk-font-body);
    font-weight: 700;
    padding: 12px 32px;
    border-radius: 4px;
    text-decoration: none;
    display: inline-block;
    transition: background-color 200ms ease;
}

.kk-btn-primary:hover {
    background-color: var(--kk-olive-dark);
    color: white;
}
```

### Anti-Patterns to Avoid
- **Inline styles in templates:** All styling goes in `main.css` using `--kk-*` variables. No `style=""` attributes.
- **Hard-coded URLs in templates:** Always use `{% url 'name' %}`, never `/o-nas/` as a string.
- **Generic Bootstrap without brand customization:** Every section should use `kk-*` classes, not raw Bootstrap utility classes for colors.
- **Missing `alt` text on images:** All `<img>` tags need descriptive Polish `alt` attributes for accessibility.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Responsive grid | Custom CSS grid | Bootstrap 5 `row`/`col-*` classes | Tested, responsive breakpoints built in |
| Icons | SVG files or icon sprites | Bootstrap Icons font (`bi bi-*`) | Already loaded in base.html, consistent sizing |
| Mobile menu toggle | Custom JS hamburger | Bootstrap `navbar-toggler` | Already in _navbar.html from Phase 1 |
| Section spacing | Ad-hoc margin/padding values | Consistent `kk-section` class with standard vertical padding | Maintainable, reusable across pages |

## Common Pitfalls

### Pitfall 1: Hero CTA Links to Non-Existent Route
**What goes wrong:** The CTA "Zobacz przepisy" links to `/przepisy/` which does not exist yet (Phase 3).
**Why it happens:** Phase 2 must reference a future page.
**How to avoid:** Use `href="/przepisy/"` as a plain string (not `{% url %}`) since the named route does not exist. Add a comment marking it as a placeholder. Or define the URL pattern now pointing to a "coming soon" view.
**Warning signs:** Django template error if `{% url 'recipes' %}` is used without a matching URL pattern.

### Pitfall 2: Forgetting to Wire Navbar Links
**What goes wrong:** Nav links for "O nas" and "Kontakt" remain as `href="#"` after creating the pages.
**Why it happens:** The navbar partial was created in Phase 1 with placeholder links.
**How to avoid:** Update `_navbar.html` as part of this phase. Replace `href="#"` with `{% url 'about' %}` and `{% url 'contact' %}`.

### Pitfall 3: Stock Image Performance
**What goes wrong:** Large unoptimized stock photos slow page load.
**Why it happens:** Unsplash/Pexels originals can be 5+ MB.
**How to avoid:** Download specific sizes (max 1200px width for hero), use `loading="lazy"` on below-fold images, set explicit `width`/`height` attributes.

### Pitfall 4: Legal Content Not Marked as Placeholder
**What goes wrong:** Someone deploys with placeholder legal text and it looks official.
**Why it happens:** Claude writes realistic-sounding legal content (D-08).
**How to avoid:** Add a visible banner or HTML comment at the top of legal pages: "UWAGA: Tekst wzorcowy -- wymaga dostosowania przez prawnika."

### Pitfall 5: CSS Specificity Conflicts with Bootstrap
**What goes wrong:** Custom brand styles don't apply or Bootstrap styles override them.
**Why it happens:** Bootstrap uses specific class selectors that can win in cascade.
**How to avoid:** Use `kk-*` prefixed classes on custom components. Apply brand colors through CSS custom properties, not by overriding Bootstrap classes directly.

### Pitfall 6: Missing `{% load static %}` in New Templates
**What goes wrong:** Static file references break in new page templates.
**Why it happens:** New templates extending `base.html` still need `{% load static %}` if they reference static files directly.
**How to avoid:** Add `{% load static %}` at the top of any template that uses `{% static %}` tags.

## Code Examples

### View Registration Pattern (core/urls.py)
```python
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("o-nas/", views.about, name="about"),
    path("kontakt/", views.contact, name="contact"),
    path("polityka-prywatnosci/", views.privacy_policy, name="privacy-policy"),
    path("regulamin/", views.regulations, name="regulations"),
]
```

### Template Inheritance Pattern (new page)
```html
{% extends "base.html" %}

{% block title %}O nas - Kuchenna Komitywa{% endblock %}

{% block content %}
<section class="kk-section">
    <div class="container">
        <h1>O nas</h1>
        <p>...</p>
    </div>
</section>
{% endblock %}
```

### Footer with Legal Links Pattern
```html
<footer class="kk-footer">
    <div class="container">
        <div class="row">
            <div class="col-md-6">
                <p class="mb-0">&copy; 2026 Kuchenna Komitywa. Wszelkie prawa zastrzezone.</p>
            </div>
            <div class="col-md-6 text-md-end">
                <a href="{% url 'privacy-policy' %}">Polityka prywatnosci</a>
                <a href="{% url 'regulations' %}" class="ms-3">Regulamin</a>
            </div>
        </div>
    </div>
</footer>
```

### Navbar Active Link Pattern
```html
<a class="nav-link {% if request.resolver_match.url_name == 'about' %}active{% endif %}"
   href="{% url 'about' %}">O nas</a>
```

### Recommended Bootstrap Icons for Feature Cards
| Card | Icon | Class |
|------|------|-------|
| 100% Roslinne | Leaf/flower | `bi-flower1` or `bi-tree` |
| Lokalne Skladniki | Map pin / basket | `bi-geo-alt` or `bi-basket` |
| Odbior Osobisty | Shop / bag | `bi-shop` or `bi-bag-check` |

Full icon reference: https://icons.getbootstrap.com/

### CSS Section Spacing Convention
```css
/* Standard section vertical spacing */
.kk-section {
    padding: 80px 0;
}

.kk-section-alt {
    padding: 80px 0;
    background-color: var(--kk-cream);
}

/* Reduce on mobile */
@media (max-width: 767.98px) {
    .kk-section,
    .kk-section-alt {
        padding: 48px 0;
    }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate CSS files per page | Single `main.css` with section classes | Phase 1 established | Keep everything in `main.css` |
| TemplateView class-based | Function views with `render()` | Phase 1 established | Simple, consistent with `core/views.py` pattern |

## Open Questions

1. **Stock photos: download vs. external URL**
   - What we know: D-11 says use Unsplash/Pexels photos.
   - What's unclear: Whether to download and serve from `static/img/` or reference external URLs directly.
   - Recommendation: Download and serve locally from `static/img/`. External URLs can break, have CORS issues, and add latency. Use Unsplash source URLs to download specific sizes (e.g., `https://images.unsplash.com/photo-xxx?w=1200`).

2. **LAND-03 vs D-07: Map requirement**
   - What we know: REQUIREMENTS.md says "adresem odbioru, godzinami i mapa" but D-07 explicitly says NO map embed, NO location image.
   - What's unclear: Nothing -- the user decision (D-07) overrides the original requirement wording.
   - Recommendation: Text-only contact info as per D-07. The requirement is satisfied with address + hours + contact details.

3. **Przepisy/Sklep placeholder links**
   - What we know: Hero CTA links to `/przepisy/`, navbar has Przepisy and Sklep links.
   - What's unclear: Should these be dead links (`#`) or point to actual placeholder pages?
   - Recommendation: Keep navbar links as `#` for Przepisy and Sklep (unchanged from Phase 1). Hero CTA uses `href="/przepisy/"` which will 404 until Phase 3 -- acceptable for development. Alternatively, create a simple "Wkrotce" placeholder page.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (built-in) |
| Config file | None needed (Django default test runner) |
| Quick run command | `python manage.py test core -v2` |
| Full suite command | `python manage.py test -v2` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAND-01 | Hero section with mission and value proposition visible | unit | `python manage.py test core.tests.TestHeroSection -v2` | No -- Wave 0 |
| LAND-02 | O nas page accessible and contains company story | unit | `python manage.py test core.tests.TestAboutPage -v2` | No -- Wave 0 |
| LAND-03 | Contact page with address, hours, contact info | unit | `python manage.py test core.tests.TestContactPage -v2` | No -- Wave 0 |
| LEGAL-01 | Privacy policy page accessible | unit | `python manage.py test core.tests.TestPrivacyPage -v2` | No -- Wave 0 |
| LEGAL-02 | Regulations page accessible | unit | `python manage.py test core.tests.TestRegulationsPage -v2` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python manage.py test core -v2`
- **Per wave merge:** `python manage.py test -v2`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `core/tests.py` -- Add TestHeroSection: assert hero section content, CTA button, split layout
- [ ] `core/tests.py` -- Add TestAboutPage: assert `/o-nas/` returns 200, has company story content
- [ ] `core/tests.py` -- Add TestContactPage: assert `/kontakt/` returns 200, has address, hours
- [ ] `core/tests.py` -- Add TestPrivacyPage: assert `/polityka-prywatnosci/` returns 200, has RODO content
- [ ] `core/tests.py` -- Add TestRegulationsPage: assert `/regulamin/` returns 200, has regulations content
- [ ] `core/tests.py` -- Add TestNavbarLinks: assert O nas and Kontakt links use `{% url %}` not `#`
- [ ] `core/tests.py` -- Add TestFooterLinks: assert footer contains privacy and regulations links

## Project Constraints (from CLAUDE.md)

- **Stack:** Django 5.2 + Django templates (no SPA)
- **Language:** Polish only
- **String quoting:** Double quotes for all new string literals
- **Imports:** Use `from X import Y` style; relative imports within same app
- **Naming:** snake_case for modules/functions, PascalCase for classes
- **CSS prefix:** All brand values use `--kk-*` custom properties
- **GSD workflow:** All changes through GSD commands

## Sources

### Primary (HIGH confidence)
- Project codebase: `templates/base.html`, `static/css/main.css`, `core/views.py`, `core/urls.py` -- verified existing infrastructure
- Phase 1 outputs: `_navbar.html`, `_footer.html` -- verified current state of partials
- Bootstrap 5.3.3 CDN already loaded in base.html -- verified from template source

### Secondary (MEDIUM confidence)
- Bootstrap Icons reference: https://icons.getbootstrap.com/ -- icon class names for feature cards
- Unsplash license: free for commercial use without attribution (verified from Unsplash license page)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new packages, everything already installed
- Architecture: HIGH -- simple views + templates pattern, well-established Django convention
- Pitfalls: HIGH -- common Django template issues, well-documented
- Content: MEDIUM -- Polish legal templates and copywriting are draft content by nature

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable -- no fast-moving dependencies)
