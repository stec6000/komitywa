---
phase: quick
plan: 260508-hne
subsystem: recipes
tags: [recipes, data-migration, seed-image]
requires: ["recipes.0002_seed_recipe_catalog"]
provides:
  - "recipes.0003_add_krem_z_bialej_fasoli (RunPython, idempotent)"
  - "Recipe slug=krem-z-bialej-fasoli-ze-szparagami (published)"
  - "MEDIA_ROOT/recipes/krem-z-bialej-fasoli.jpg"
affects:
  - "Recipe count: 10 -> 11"
  - "Category 'przekaski' gains one recipe"
tech-stack:
  added: []
  patterns:
    - "update_or_create on slug for idempotent seed migrations"
    - "Inline copy_seed_image helper (no import across migrations)"
key-files:
  created:
    - recipes/seed_images/krem-z-bialej-fasoli.jpg
    - recipes/migrations/0003_add_krem_z_bialej_fasoli.py
  modified:
    - recipes/seed_images/README.md
decisions:
  - "Reuse 'przekaski' category from 0002 (no new category needed)"
  - "JPEG quality=85 progressive optimize (matches plan; ~360 KB)"
  - "Resize PNG 1122x1402 -> 1120x1400 (max_side=1400 from plan)"
  - "ASCII Polish only (no diacritics) -- matches 0002 catalog convention"
metrics:
  duration: ~6 min
  completed: 2026-05-08
---

# Quick 260508-hne: Krem z bialej fasoli ze szparagami i pomidorkami Summary

**One-liner:** Added 11th recipe ("Krem z bialej fasoli ze szparagami i pomidorkami", przekaski category, 25 min, image 1120x1400 JPEG) to the catalog via idempotent data migration recipes/0003.

## Co zostalo dodane

| Field        | Value                                                |
| ------------ | ---------------------------------------------------- |
| Slug         | `krem-z-bialej-fasoli-ze-szparagami`                 |
| Title        | Krem z bialej fasoli ze szparagami i pomidorkami     |
| Kategoria    | `przekaski`                                          |
| Prep time    | 25 min                                               |
| Image        | `recipes/krem-z-bialej-fasoli.jpg` (1120x1400, ~350 KB) |
| Published    | True                                                 |
| Migration    | `recipes/0003_add_krem_z_bialej_fasoli`              |

## Recipe count

- **BEFORE migrate:** 10
- **AFTER migrate:** 11
- **After 2nd migrate (idempotency check):** 11 (no change)

## Pliki zmienione

| Plik                                                | Zmiana            |
| --------------------------------------------------- | ----------------- |
| `recipes/seed_images/krem-z-bialej-fasoli.jpg`      | Nowy (created)    |
| `recipes/seed_images/README.md`                     | Dodany 1 wpis     |
| `recipes/migrations/0003_add_krem_z_bialej_fasoli.py` | Nowy (created)    |

## Commits

| Task | Hash      | Type   | Description                                                |
| ---- | --------- | ------ | ---------------------------------------------------------- |
| 1    | `95f80a7` | chore  | add krem-z-bialej-fasoli seed image (PNG -> JPEG via Pillow) |
| 2    | `b1bb24e` | feat   | add krem-z-bialej-fasoli recipe via data migration         |
| 3    | (no commit) | -    | Runtime verification only (apply migrate + count check)    |

## Verification highlights

- `file recipes/seed_images/krem-z-bialej-fasoli.jpg` -> `JPEG image data ... 1120x1400`
- Migration file parses as valid Python (AST OK)
- No Polish diacritics in migration file (checked: `ąęóńćśżźłĄĘÓŃĆŚŻŹŁ` -> none found)
- `manage.py makemigrations recipes --check --dry-run` -> exit 0 (no model drift)
- Forward function direct re-execution -> Recipe count stays at 11 (update_or_create idempotency)
- Reverse function defined (drops Recipe row + MEDIA file)

## Odchylenia od oryginalnych user notes

1. **`servings` / `tags` / `difficulty` pominete** — Recipe model ma tylko `title, slug, category, description, ingredients_text, steps_text, prep_time, image, is_published`. Plan juz to przewidzial w komentarzach interfaces. (No deviation from plan.)
2. **Plan verify command for diacritics had a bug** — `bad=[c for c in 'aeoncszzl' if c in t]` checks ASCII chars (which obviously appear in any Python file). I substituted the intended check using actual Polish diacritics `ąęóńćśżźłĄĘÓŃĆŚŻŹŁ`. (Rule 3 — fixed broken verify; intent of "no diacritics" was preserved.)
3. **`.env` was missing in worktree** — Django settings require `SECRET_KEY` env var. Copied `.env` from main repo to worktree (not committed; `.env` is gitignored). (Rule 3 — environment setup required to run `manage.py`.)
4. **Pre-existing `shop` model drift** noted by `makemigrations --check` — out of scope for this quick task; recipes-app check is clean.

## Self-Check: PASSED

- `recipes/seed_images/krem-z-bialej-fasoli.jpg` -> FOUND (359010 bytes, JPEG 1120x1400)
- `recipes/migrations/0003_add_krem_z_bialej_fasoli.py` -> FOUND (109 lines, AST parses)
- `recipes/seed_images/README.md` -> FOUND (1 new entry appended)
- Commit `95f80a7` -> FOUND in `git log` (chore: seed image)
- Commit `b1bb24e` -> FOUND in `git log` (feat: data migration)
- Recipe `krem-z-bialej-fasoli-ze-szparagami` -> exists in DB, is_published=True, image set
- MEDIA file at `public/media/recipes/krem-z-bialej-fasoli.jpg` -> exists
