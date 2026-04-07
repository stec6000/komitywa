# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## bootstrap-css-not-loading — Incorrect SRI integrity hash on Bootstrap CDN CSS link
- **Date:** 2026-04-07
- **Error patterns:** unstyled HTML, Bootstrap CSS not loading, SRI integrity hash mismatch, no layout no colors
- **Root cause:** The Bootstrap 5.3.3 CSS link tag in base.html had an incorrect SHA-384 integrity hash. The browser downloads the CSS but the SRI check fails, so it silently refuses to apply the stylesheet.
- **Fix:** Replace the incorrect integrity hash with the correct one (sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH) in templates/base.html
- **Files changed:** templates/base.html
---
