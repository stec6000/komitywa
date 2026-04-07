---
status: resolved
trigger: "Site renders as unstyled HTML — Bootstrap CSS and custom brand CSS not loading in dev server"
created: 2026-04-07T07:38:00Z
updated: 2026-04-07T07:39:00Z
---

## Current Focus

hypothesis: Bootstrap CSS SRI integrity hash is incorrect — browser silently rejects the stylesheet
test: Compare hash in base.html with actual SHA-384 of the CDN file
expecting: Hashes will differ, confirming browser rejects the file
next_action: Fix the integrity hash in base.html

## Symptoms

expected: Bootstrap 5 navbar, hero split-layout, sage-olive-cream brand colors, Lora/Nunito fonts
actual: Plain unstyled HTML with bullet-point nav links, no layout, no colors — looks like CSS is not loading at all
errors: No visible errors in terminal, but browser console would show SRI mismatch
reproduction: Visit http://127.0.0.1:8000/ in dev server
started: v1.0 MVP shipped; post-milestone staged change to urls.py suggests someone noticed static issues

## Eliminated

- hypothesis: staticfiles_urlpatterns() missing from urls.py prevents static file serving
  evidence: Django runserver auto-serves static files when django.contrib.staticfiles is in INSTALLED_APPS and DEBUG=True. The staged change adding staticfiles_urlpatterns() is redundant but not harmful.
  timestamp: 2026-04-07T07:38:30Z

- hypothesis: STATICFILES_DIRS or static file paths misconfigured
  evidence: settings.py has STATICFILES_DIRS = [BASE_DIR / "static"], and static/css/main.css exists on disk at that path
  timestamp: 2026-04-07T07:38:30Z

- hypothesis: base.html missing {% load static %} or {% static %} tags
  evidence: Template has {% load static %} on line 1, uses {% static 'css/main.css' %} correctly
  timestamp: 2026-04-07T07:38:30Z

## Evidence

- timestamp: 2026-04-07T07:38:30Z
  checked: SRI integrity hash on Bootstrap 5.3.3 CSS link in base.html
  found: Template has sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YcnS/1RVbMnKGYbJW2vP2MFa7i/re2el1ZMu but actual file hash is sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH
  implication: Browser downloads CSS but SRI check fails, so it silently discards the stylesheet. This explains the completely unstyled page.

- timestamp: 2026-04-07T07:38:40Z
  checked: Bootstrap JS bundle integrity hash
  found: JS hash sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz matches actual file — JS is fine
  implication: Only the CSS link has the wrong hash

- timestamp: 2026-04-07T07:38:45Z
  checked: Bootstrap Icons CSS link
  found: No integrity attribute on the icons link — loads without SRI check, so it's fine
  implication: Icons CSS not affected

## Resolution

root_cause: The Bootstrap 5.3.3 CSS <link> tag in templates/base.html has an incorrect SRI integrity hash (sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YcnS/1RVbMnKGYbJW2vP2MFa7i/re2el1ZMu). The correct hash is sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH. The browser downloads the CSS but the integrity check fails, so it silently refuses to apply it. This makes the entire page render as unstyled HTML.
fix: Replace the incorrect integrity hash with the correct one in templates/base.html line 17
verification: Dev server started, page serves correct integrity hash, static/css/main.css returns HTTP 200
files_changed: [templates/base.html]
