# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-04-04
**Phases:** 6 | **Plans:** 16 | **Tasks:** 30

### What Was Built

- Full Django template layer (Bootstrap 5, brand CSS) on top of existing API-only backend
- Landing page, O nas, Kontakt, privacy policy, regulations — complete public presence
- Recipe blog with category filters, search, pagination, Schema.org JSON-LD for SEO
- Product catalog with session cart, checkout form, LEGAL-04 consent fields
- End-to-end Przelewy24 payment flow (SHA-384 webhook, ebook PDF email delivery)
- RODO-compliant newsletter with double opt-in and token-based unsubscribe

### What Worked

- **Yolo mode** allowed parallel agent waves without confirmation gates — dramatically faster execution
- **UI-SPEC.md per phase** gave templates clear design contracts, preventing rework
- **Session-based cart** kept Phase 4 scope tight — no auth dependency, no DB complexity
- **Distributing LEGAL requirements** across phases (cookie consent in 1, legal pages in 2, consent checkboxes in 5) kept each phase cohesive
- **Phase summaries as one-liners** give precise, searchable history

### What Was Inefficient

- REQUIREMENTS.md checkbox tracking fell behind — 4 requirements were shipped but not marked, creating unnecessary "incomplete" noise at milestone close
- ROADMAP.md progress table not updated as phases completed (all showed correct on disk, not in file)
- Phase 1 had a STATE.md git conflict from parallel worktree execution — small friction

### Patterns Established

- `django-environ` over `python-dotenv` for typed settings in Django projects
- Shop URLs all in single `shop/urls.py` mounted at root to match UI-SPEC paths
- Tests use `get_or_create` for seeded categories to avoid migration data conflicts
- Detail CSS in `extra_css` block to avoid cross-plan main.css ownership conflicts
- Ebook quantity lock in cart (digital goods pattern)
- P24 return page shows "pending" state — does NOT check `order.status` (webhook lag)

### Key Lessons

1. **Phase SUMMARY.md is the source of truth** — requirements tracking in REQUIREMENTS.md lags; don't block on it
2. **UI-SPEC.md is worth the upfront cost** — phases with UI-SPEC had zero template structure rework
3. **Yolo mode + parallel waves** = highest throughput; gates add friction without proportional safety for internal code
4. **LEGAL requirements belong in context phases**, not a separate phase — merged into Foundation, Landing, Payments naturally
5. **P24 sandbox validation before Phase 5** would have reduced assumptions in plan design

### Cost Observations

- Model mix: ~100% sonnet (quality profile)
- Sessions: ~10-12 across all phases
- Notable: 4-day wall time for 6 phases, 16 plans — averaging ~15min/plan execution

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 MVP | ~12 | 6 | First milestone — established all patterns |

### Cumulative Quality

| Milestone | Tests | Zero-Dep Additions |
|-----------|-------|-------------------|
| v1.0 | 40+ passing | django-environ, Przelewy24 client (custom) |

### Top Lessons (Verified Across Milestones)

1. Track requirements via SUMMARY.md, not checkbox files — SUMMARY is written at execution time
2. UI-SPEC before any template phase saves significant rework
