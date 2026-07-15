---
phase: quick-260715-eov
plan: 01
subsystem: recipes
tags: [seo, templates, json-ld]
requires: []
provides: ["Tag rendering without '#'", "recipeCategory JSON-LD", "category-first keywords"]
affects: [templates/recipes/detail.html, templates/recipes/list.html, recipes/views.py]
tech-stack:
  added: []
  patterns: ["Category-first, de-duplicated keyword list for Recipe JSON-LD"]
key-files:
  created: []
  modified:
    - templates/recipes/detail.html
    - templates/recipes/list.html
    - recipes/views.py
decisions:
  - "Category name is placed first in keywords, followed by tag names, de-duplicated preserving order"
metrics:
  duration: ~5m
  completed: 2026-07-15
---

# Phase quick-260715-eov Plan 01: Tagi jako słowa kluczowe Summary

Treated recipe tags as keywords: removed the displayed `#` prefix from all four tag render
locations and enriched the recipe JSON-LD with `recipeCategory` plus a category-first,
de-duplicated `keywords` list.

## What Was Built

- **Task 1** — Removed the literal `#` before `{{ t.name }}` in 4 places:
  - `templates/recipes/detail.html:47` (tag link)
  - `templates/recipes/list.html:51` (active tag link)
  - `templates/recipes/list.html:56` (inactive tag link)
  - `templates/recipes/list.html:80` (card tag span)
  - `aria-label` text, hrefs, classes, and loop structure left untouched.
- **Task 2** — In `recipes/views.py` `recipe_detail`, extended the keywords/schema block:
  - Sets `schema["recipeCategory"] = recipe.category.name` when a category is present (truthy check on nullable FK).
  - Composes `keywords` as the category name first, then tag names, de-duplicated while preserving order; only set when non-empty; joined with `", "`.
  - Kept double-quote string style per CLAUDE.md.

## Verification

- `python manage.py check` — passed (0 issues).
- `grep -rn '#{{ t.name }}' templates/recipes/` — no matches.
- Local render (Django test client) of `/przepisy/weganskie-ragu-z-tofu/` (category `Obiady`, tags `pieczone`, `tofu`):
  - Status 200.
  - JSON-LD `recipeCategory: Obiady`.
  - JSON-LD `keywords: Obiady, pieczone, tofu` (category first, no duplicates).
  - Tags render as `pieczone` / `tofu` — no leading `#`.

## Deviations from Plan

None - plan executed exactly as written.

## Commits

- `ebe0fd7` feat(quick-260715-eov-01): remove '#' prefix from displayed recipe tags
- `02813b7` feat(quick-260715-eov-01): add recipeCategory and category keyword to recipe JSON-LD

## Self-Check: PASSED

- FOUND: templates/recipes/detail.html
- FOUND: templates/recipes/list.html
- FOUND: recipes/views.py
- FOUND commit: ebe0fd7
- FOUND commit: 02813b7
