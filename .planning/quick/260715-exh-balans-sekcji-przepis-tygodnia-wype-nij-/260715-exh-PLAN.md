---
phase: quick-260715-exh
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - templates/pages/home.html
  - static/css/main.css
autonomous: false
requirements: [QUICK-260715-exh]
must_haves:
  truths:
    - "Sekcja 'przepis tygodnia' na home (desktop ~1440px) nie ma dużej pustej przestrzeni pod tekstem w lewej kolumnie"
    - "Zdjęcie przepisu jest niższe niż dotychczasowy portret 4/5 (bliżej 4/3), kadr wciąż wypełnia ramkę (object-fit: cover)"
    - "Lewa kolumna ma mini-meta (porcje / trudność / kategoria) w stylu spójnym z ramkami .kk-meta ze strony przepisu"
    - "Zawartość lewej kolumny jest wycentrowana w pionie względem zdjęcia"
    - "Na mobile (390px) kolumny nadal stackują się pionowo, sekcja czytelna"
  artifacts:
    - path: "templates/pages/home.html"
      provides: "Markup mini-meta w lewej kolumnie sekcji featured"
      contains: "featured-meta"
    - path: "static/css/main.css"
      provides: "Style .featured-meta + niższe zdjęcie + wyśrodkowanie kolumny"
      contains: ".featured-meta"
  key_links:
    - from: "templates/pages/home.html"
      to: "static/css/main.css"
      via: "klasa .featured-meta / .featured-meta-item"
      pattern: "featured-meta"
---

<objective>
Zbalansować sekcję „przepis tygodnia" na stronie głównej: usunąć dużą pustą przestrzeń w lewej kolumnie (cel LOCKED = brak wielkiej pustki), zachowując lekki, teaserowy charakter.

Purpose: Sekcja to grid 2 kolumny. Prawa kolumna ma zdjęcie w proporcji 4/5 (portret ~620-680px), a lewa kolumna z krótkim tekstem kończy się na ~40% wysokości — powstaje ogromna pustka pod CTA. Rozwiązanie: (1) obniżyć zdjęcie do ~4/3 z max-height i object-fit cover, (2) wzbogacić lewą kolumnę o mini-meta w stylu ramek `.kk-meta` (spójność ze stroną przepisu), (3) wyśrodkować zawartość lewej kolumny w pionie.

Output: Zmiany w templates/pages/home.html + static/css/main.css. Bez zmian w widoku (core/views.py) — `featured_recipe.category` jest już `select_related`, a `servings`/`difficulty`/`prep_time` to zwykłe pola pojedynczego obiektu (brak N+1).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md

<interfaces>
<!-- Kontrakt danych: featured_recipe to obiekt Recipe (core/views.py home()). -->
<!-- Dostępne w szablonie bez zmiany widoku: -->
<!--   featured_recipe.servings (int), featured_recipe.difficulty (str), -->
<!--   featured_recipe.prep_time (int), featured_recipe.category.name (select_related), -->
<!--   featured_recipe.created_at, featured_recipe.title, featured_recipe.description, featured_recipe.slug, featured_recipe.image -->

Aktualny markup lewej kolumny (templates/pages/home.html, ~157-167):
- .featured-date (data), <h3> tytuł, <p class="featured-blurb"> opis,
  inline flex-row z <a class="btn"> „cały przepis →" + <span class="hand"> „{{ prep_time }} min".

Aktualny grid (static/css/main.css ~702):
  .featured { display:grid; grid-template-columns:1.1fr 1fr; gap:60px; padding:50px; } (brak align-items → stretch)

Aktualne zdjęcie (static/css/main.css ~740):
  .featured-img { aspect-ratio:4/5; ... }  .featured-img--photo img { width:100%;height:100%;object-fit:cover; }

Wzorzec ramek meta ze strony przepisu (static/css/main.css ~1370, templates/recipes/detail.html ~22):
  .kk-meta-item { flex-direction:column; background:var(--paper); border:1.5px solid var(--ink);
                  box-shadow:4px 5px 0 var(--paper-shadow); padding:8px 16px; transform:rotate(-1deg); }
  .kk-meta-label { font-family:var(--font-hand); font-size:16px; color:var(--ink-faded); text-transform:lowercase; }
  .kk-meta-value { font-family:var(--font-display); font-size:22px; color:var(--ink); }

Responsywność (static/css/main.css):
  @media (max-width:900px): .featured { grid-template-columns:1fr; gap:30px; padding:30px; }
  @media (max-width:600px): .featured h3 { font-size:36px; }
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Mini-meta w lewej kolumnie sekcji featured (markup)</name>
  <files>templates/pages/home.html</files>
  <action>
    W bloku `{% if featured_recipe %}` (~152-180), w lewej kolumnie (wewnętrzny `<div>` zaczynający się na ~157), po `<p class="featured-blurb">…</p>` a PRZED inline flex-row z CTA, dodaj mini-meta w nowym kontenerze `<div class="featured-meta">`. Trzy pozycje `<div class="featured-meta-item">`, każda z `<span class="featured-meta-label">` (etykieta odręczna, lowercase) + `<span class="featured-meta-value">`:
      1. label „porcje", value: `{{ featured_recipe.servings }} porcj{% if featured_recipe.servings == 1 %}a{% elif featured_recipe.servings < 5 %}e{% else %}i{% endif %}` (wzorzec liczebnika jak w recipes/detail.html ~29).
      2. label „trudność", value: `{{ featured_recipe.difficulty }}`.
      3. label „kategoria", value: `{{ featured_recipe.category.name|lower }}` — owinięte w `{% if featured_recipe.category %}…{% endif %}` (kategoria bywa null; pomiń całą pozycję gdy brak).
    NIE dodawaj hashtagów „#" (usunięte wcześniej). Nazwy klas MUSZĄ być dokładnie `featured-meta` / `featured-meta-item` / `featured-meta-label` / `featured-meta-value` (używane przez CSS w Task 2). Nie ruszaj prawej kolumny ani istniejącego CTA/`prep_time`.
  </action>
  <verify>
    <automated>python manage.py check && grep -c "featured-meta-item" templates/pages/home.html | grep -qv '^0$' && echo OK</automated>
  </verify>
  <done>Lewa kolumna zawiera `.featured-meta` z 2-3 ramkami (porcje, trudność, kategoria-warunkowo); `python manage.py check` przechodzi; brak znaku „#".</done>
</task>

<task type="auto">
  <name>Task 2: Niższe zdjęcie + wyśrodkowanie + style meta (CSS)</name>
  <files>static/css/main.css</files>
  <action>
    W bloku „--------- Featured recipe ---------" (~701-773):
      1. `.featured` — dodaj `align-items: center;` (wyśrodkowanie zawartości lewej kolumny w pionie względem niższego zdjęcia).
      2. `.featured-img` — zmień `aspect-ratio: 4/5` na `aspect-ratio: 4/3` i dodaj `max-height: 480px;` (obraz to penne w misce na środku — kadr centralny bezpieczny; `object-fit: cover` już jest na `.featured-img--photo img`, zostaw). Efekt: cała sekcja niższa.
    Dodaj NOWE reguły `.featured-meta` (lekka wariacja ramek `.kk-meta`, spójna wizualnie, ale skromniejsza — to teaser):
      - `.featured-meta { display:flex; flex-wrap:wrap; gap:10px 12px; margin:20px 0 4px; }`
      - `.featured-meta-item { display:flex; flex-direction:column; gap:2px; background:var(--paper); border:1.5px solid var(--ink); box-shadow:3px 4px 0 var(--paper-shadow); padding:6px 14px; transform:rotate(-1deg); }`
      - `.featured-meta-item:nth-child(even) { transform:rotate(1deg); background:var(--paper-2); }`
      - `.featured-meta-label { font-family:var(--font-hand); font-size:14px; line-height:1; text-transform:lowercase; color:var(--ink-faded); }`
      - `.featured-meta-value { font-family:var(--font-display); font-size:19px; line-height:1.1; color:var(--ink); text-transform:lowercase; }`
    Responsywność: w `@media (max-width:900px)` (~1738, gdzie `.featured` staje się 1 kolumną) dodaj `.featured { align-items:stretch; }` aby po zestackowaniu meta/tekst nie były sztucznie centrowane — kolumny renderują się naturalnie od góry. Nie zmieniaj istniejących reguł mobilnych zdjęcia (aspect-ratio 4/3 działa też na mobile).
  </action>
  <verify>
    <automated>grep -q "aspect-ratio: 4/3" static/css/main.css && grep -q "align-items: center" static/css/main.css && grep -q ".featured-meta-item" static/css/main.css && echo OK</automated>
  </verify>
  <done>`.featured` ma `align-items:center`; `.featured-img` ma `aspect-ratio:4/3` + `max-height:480px`; istnieją style `.featured-meta*`; mobile (<=900px) resetuje align do stretch.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
    Zbalansowana sekcja „przepis tygodnia": niższe zdjęcie (4/3, max 480px), lewa kolumna wzbogacona o mini-meta (porcje/trudność/kategoria) w stylu ramek jak na stronie przepisu, zawartość wyśrodkowana w pionie — bez wielkiej pustki.
  </what-built>
  <how-to-verify>
    1. `python manage.py runserver` (uruchom w tle).
    2. Headless chrome screenshot home (wzorzec jak quick 260714-li1):
       - desktop 1440px: sekcja featured — brak dużej pustej przestrzeni pod tekstem, zdjęcie niższe niż wcześniej, mini-meta widoczne, tekst wycentrowany względem zdjęcia.
       - mobile 390px: kolumny stackują się pionowo, tekst + meta + zdjęcie czytelne, nic nie wystaje.
    3. Zapisz zrzuty do przeglądu (usuń tymczasowe .jpg po weryfikacji).
  </how-to-verify>
  <resume-signal>Napisz „approved" albo opisz problemy (np. zdjęcie wciąż za wysokie / meta za ciężkie / mobile popsute).</resume-signal>
</task>

</tasks>

<verification>
- Desktop 1440px: brak wielkiej pustki w lewej kolumnie sekcji featured; zdjęcie w proporcji ~4/3.
- Mobile 390px: kolumny stackują się, sekcja czytelna.
- `python manage.py check` przechodzi.
</verification>

<success_criteria>
- Sekcja „przepis tygodnia" na home nie ma dużej pustej przestrzeni pod tekstem (cel LOCKED).
- Lewa kolumna ma mini-meta spójne wizualnie z ramkami `.kk-meta`.
- Mobile działa poprawnie (stack).
- Zmiany tylko w templates/pages/home.html + static/css/main.css (bez zmian widoku).
</success_criteria>

<output>
Create `.planning/quick/260715-exh-balans-sekcji-przepis-tygodnia-wype-nij-/260715-exh-SUMMARY.md` when done
</output>
