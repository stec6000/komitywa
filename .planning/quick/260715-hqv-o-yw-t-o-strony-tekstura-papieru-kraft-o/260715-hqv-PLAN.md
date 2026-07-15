---
phase: quick-260715-hqv
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - templates/base.html
  - static/css/main.css
autonomous: false
requirements:
  - QUICK-260715-hqv
must_haves:
  truths:
    - "Cała witryna ma namacalną teksturę papieru (kraft) prześwitującą tam gdzie tło to --paper"
    - "W marginesach/pustkach widoczne są blade ołówkowe szkice składników (4-6 różnych), nie łapią kliknięć ani czytników ekranu"
    - "Szkice nie zmniejszają kontrastu tekstu treści (niska opacity, poza kolumną tekstu)"
    - "Na desktopie w przeglądarce z animation-timeline szkice delikatnie dryfują/prostują się przy scrollu; Firefox/starsze Safari widzą wersję statyczną"
    - "Przy prefers-reduced-motion: reduce brak ruchu"
    - "Na mobile (390px) szkice są zredukowane/ukryte i nie kolidują z treścią"
    - "Istniejące tła sekcji (kk-section-alt, polaroidy, hero) nietknięte"
  artifacts:
    - path: "templates/base.html"
      provides: "Globalna warstwa dekoracji tła (kontener szkiców) wpięta raz dla całej witryny"
      contains: "page-sketches"
    - path: "static/css/main.css"
      provides: "Styl tekstury kraft + szkiców (data-URI SVG, pozycje, opacity, rotacje, scroll animation, mobile fallback)"
      contains: "page-sketches"
  key_links:
    - from: "templates/base.html .page-sketches elements"
      to: "static/css/main.css .sk-* rules"
      via: "class selectors"
      pattern: "page-sketches|sk-"
---

<objective>
Ożywić tło CAŁEJ witryny bez nowych plików graficznych i bez nowego JS: (1) wzmocnić namacalność tekstury papieru w stronę kraftu, (2) dodać blade ołówkowe szkice składników w marginesach/pustkach, (3) delikatny ruch szkiców przy scrollu przez CSS scroll-driven animations z bezpiecznym fallbackiem.

Purpose: Strona ma czuć się jak namacalny szkicownik kuchenny — subtelnie, bez utraty czytelności treści.
Output: Zmiany w `templates/base.html` (jedna globalna warstwa dekoracji) i `static/css/main.css` (tekstura + szkice + animacja).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@templates/base.html
@static/css/main.css

<interfaces>
<!-- Istniejący stan — NIE duplikować, budować na tym. -->

Istniejące warstwy tła w main.css (linie ~48-69):
- `body::before` — gradientowe cieniowanie papieru (mix-blend-mode: multiply, opacity: var(--texture-paper), z-index: 0).
- `body::after` — feTurbulence noise jako data-URI SVG (kafel 220x220, opacity: calc(var(--texture-grain) * 0.3), mix-blend-mode: multiply, z-index: 1).
- Zmienne: --paper #f3ead7, --paper-2 #ebe0c5, --ink #2a2420, --ink-soft, --ink-faded, --accent (olive) #6b7a3a, --accent-2 (terracotta), --texture-paper: 1, --texture-grain: 1.2.
- Kontenery treści (.wrap, .wrap-narrow, .container, section) mają position: relative; z-index: 2 — czyli są NAD warstwami tła body::before/::after.

Sekcje z własnym tłem (NIE ruszać):
- `.kk-section-alt` (linia ~110) — gradient var(--paper-2).
- Polaroidy/karty/okładki: `.polaroid-img`, `.recipe-img`, `.featured-img`, `.product-cover` mają własne background/background-image.

base.html — struktura body (linie 17-38):
- `<body>` → skip-link → _navbar → `<main id="main-content">` → newsletter → _footer → cookie_banner → skrypty (sketchbook.js = nav toggle + smooth scroll; NIE ruszać).

Breakpointy w projekcie: istnieje `@media (max-width: 600px)`. Dla ukrycia/redukcji szkiców użyj progu ~900px (tablet w dół).
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Globalna warstwa dekoracji w base.html (kontrakt selektorów)</name>
  <files>templates/base.html</files>
  <action>
Dodaj JEDNĄ globalną warstwę dekoracji szkiców jako pierwszy element wewnątrz `<body>`, tuż po `<a class="skip-link">` a przed `{% include "includes/_navbar.html" %}`.

Struktura: `<div class="page-sketches" aria-hidden="true">` zawierający 6 pustych elementów `<i>` z klasami identyfikującymi konkretny szkic składnika:
`sk sk-thyme`, `sk sk-onion`, `sk sk-carrot`, `sk sk-bowl`, `sk sk-fork`, `sk sk-sprig` (gałązka rozmarynu).
Elementy są puste (`<i class="sk sk-thyme"></i>`) — obrazek dostarcza CSS przez background-image data-URI w Task 2.

Wymagania dostępności/UX (kontrakt dla CSS):
- Kontener MUSI mieć `aria-hidden="true"` (niewidoczny dla czytników ekranu).
- Nie dodawaj żadnego JS, nie ruszaj istniejących skryptów.
- To jedyne miejsce wpięcia (globalnie, cała witryna) — NIE dodawaj szkiców per-sekcja w home.html (łatwiejsze utrzymanie: jeden kontener).

NIE stylizuj tutaj (żadnego inline style) — cały wygląd/pozycje/pointer-events w main.css.
  </action>
  <verify>
    <automated>grep -q 'class="page-sketches" aria-hidden="true"' templates/base.html && grep -c 'class="sk ' templates/base.html | grep -qx 6 && echo OK</automated>
  </verify>
  <done>base.html zawiera kontener `.page-sketches[aria-hidden=true]` z dokładnie 6 elementami `.sk sk-*`, bez inline stylów i bez nowego JS.</done>
</task>

<task type="auto">
  <name>Task 2: Tekstura kraft + styl szkiców + scroll-drift w main.css</name>
  <files>static/css/main.css</files>
  <action>
Dodaj nowy, wyraźnie oznaczony blok CSS (nagłówek komentarza np. `/* --------- Page sketches (ingredient doodles) --------- */`) — proponowane miejsce: zaraz po istniejącym bloku "Paper texture" (po linii ~69), aby dekoracje tła trzymać razem.

A. Kraft — wzmocnienie namacalności (edytuj istniejące, NIE duplikuj):
- Delikatnie podbij włóknistość: dodaj do `body::after` lub jako nowy `background-image` na body cienki, kierunkowy "fiber" — drugi mały data-URI SVG feTurbulence z `type='fractalNoise'` i niską częstotliwością kierunkową (np. baseFrequency='0.012 0.9') dla efektu włókien kraftu, w tonie --ink. Efekt ma być prawie niewidoczny (namacalność, nie szum): docelowa efektywna opacity ziarna+włókien ~0.05-0.09. Jeśli obecny grain wydaje się za mocny na screenshotach, zredukuj mnożnik w `body::after` (obecnie calc(var(--texture-grain) * 0.3)) w dół. Tekstura MUSI prześwitywać tam gdzie tło to --paper i NIE nakładać się na własne tła kart/polaroidów (warstwy są fixed z-index 0/1, kontenery treści z-index 2 — zachowaj to).

B. Kontener `.page-sketches`:
- `position: absolute; inset: 0; z-index: 0;` (POD treścią z-index:2, jak warstwy tła), `pointer-events: none;`, `overflow: hidden;`. Rozciąga się na całą wysokość dokumentu (body już relatywne? — jeśli nie, ustaw `body { position: relative; }`, tylko jeśli potrzebne, minimalnie).
- Uwaga: absolute (nie fixed) — żeby szkice były w przepływie dokumentu i miały zakres scrolla dla animacji view().

C. Szkice `.sk`:
- `position: absolute;` w marginesach/pustkach (lewy i prawy skraj viewportu, `left`/`right` bliskie krawędzi, różne `top` rozłożone po długości strony np. 8%, 24%, 45%, 62%, 80%, 92%).
- Rozmiar ~90-160px, `background-repeat: no-repeat; background-size: contain;`.
- Kolor kreski = --ink przez SVG stroke (użyj `%232a2420` w data-URI), a bladość przez `opacity: 0.06-0.10`.
- Lekkie różne rotacje (`transform: rotate(-8deg)` ... `rotate(6deg)`).
- Każdy `.sk-*` dostaje własny `background-image` = inline data-URI SVG ołówkowego szkicu składnika: gałązka tymianku, cebula, marchewka, miska z parą, widelec/łyżka, gałązka rozmarynu. Styl: rysunek jedną/kilkoma kreskami, `fill='none'`, `stroke-linecap='round'`, grubość ~1.6-2.2, ścieżki lekko "drżące"/nierówne (odręczny charakter — użyj nieregularnych punktów w path, NIE idealnych łuków). Wpisz SVG jako data-URI (koduj `#`→`%23`, `<`/`>` dozwolone w utf8, jak istniejące data-URI w pliku).

D. Ruch przy scrollu (opcjonalny sznyt, bezpieczny fallback):
- Owiń CAŁOŚĆ animacji w `@media (prefers-reduced-motion: no-preference)` ORAZ `@supports (animation-timeline: view())`.
- Dla `.sk` nadaj `animation-timeline: view();` z krótką klatkową animacją, która delikatnie prostuje/dryfuje szkic: np. z `rotate` kilka stopni + `translateY` kilka px na wejściu w viewport do neutralnej pozycji przy środku. Amplituda MAŁA (kilka px / kilka stopni). Bez tego wsparcia (Firefox/starsze Safari) = statyczne pozycje z punktu C (żaden JS, żaden ruch).
- (Opcjonalnie) minimalny scroll-drift dla polaroidów w hero tą samą techniką — tylko jeśli nie komplikuje; pomiń jeśli ryzykuje istniejący układ hero.

E. Mobile/redukcja:
- W `@media (max-width: 900px)` zredukuj: ukryj większość szkiców (`display: none`) zostawiając ewentualnie 1-2 przy samej krawędzi z jeszcze niższą opacity, lub całkowicie `display: none` dla `.page-sketches` — priorytet: zero kolizji z treścią na wąskich ekranach.

Nie używaj `!important`. Nie zmieniaj istniejących reguł kart/polaroidów/sekcji poza pkt A tekstury.
  </action>
  <verify>
    <automated>grep -q 'page-sketches' static/css/main.css && grep -q 'sk-thyme' static/css/main.css && grep -q 'pointer-events: *none' static/css/main.css && grep -q '@supports (animation-timeline: view())' static/css/main.css && grep -q 'prefers-reduced-motion: no-preference' static/css/main.css && grep -q 'max-width: *900px' static/css/main.css && echo OK</automated>
  </verify>
  <done>main.css ma blok szkiców: kontener pointer-events:none z-index pod treścią, 6 klas .sk-* z data-URI SVG w kolorze --ink niską opacity, rotacje, scroll-drift owinięty w @supports + prefers-reduced-motion:no-preference, redukcja/ukrycie na @media max-width:900px; tekstura kraft wzmocniona ale subtelna. Brak zmian w tłach kart/sekcji.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Globalna tekstura kraft + ołówkowe szkice składników w tle całej witryny + delikatny scroll-drift (CSS-only, zero JS, zero nowych plików graficznych). Zebrano screenshoty headless Chrome do oceny subtelności i braku kolizji z treścią.</what-built>
  <how-to-verify>
Automatyzacja PRZED checkpointem (wykonuje wykonawca):
1. Uruchom serwer: `python manage.py runserver 127.0.0.1:8010` (w tle).
2. Zrób pełnostronicowe screenshoty headless (google-chrome jest w /usr/bin/google-chrome), wzorzec jak w poprzednich quick-taskach:
   - Home desktop 1440 full-page → `.tmp-sketch-home-1440.png`
   - Home mobile 390 → `.tmp-sketch-home-390.png`
   - Strona szczegółu przepisu desktop 1440 → `.tmp-sketch-recipe-1440.png`
   Przykład: `google-chrome --headless --disable-gpu --hide-scrollbars --window-size=1440,3000 --screenshot=.tmp-sketch-home-1440.png http://127.0.0.1:8010/` (dostosuj URL przepisu do istniejącego slug; dla full-page użyj wysokiego window-size lub flagi full-page zgodnie z poprzednim wzorcem).
3. Zatrzymaj serwer po zrzutach.

Ocena wizualna (człowiek):
1. Tekstura papieru jest namacalna ale prawie niewidoczna — nie wygląda jak szum/brud, nie obniża kontrastu tekstu.
2. Szkice składników są blade, tylko w marginesach/pustkach, NIE zachodzą na kolumnę tekstu tak by utrudniać czytanie.
3. Mobile 390: szkice zredukowane/ukryte, treść czysta, brak kolizji.
4. Strona przepisu: tło spójne, treść czytelna, żadne istniejące tła sekcji/kart nie popsute.
5. (Jeśli przeglądarka wspiera) scroll-drift jest ledwo zauważalny, nie rozprasza.
  </how-to-verify>
  <resume-signal>Napisz "approved" albo opisz co poprawić (za mocna tekstura / szkice za widoczne / kolizja z treścią / złe pozycje).</resume-signal>
</task>

</tasks>

<verification>
- `grep` gates z Task 1 i Task 2 przechodzą.
- Screenshoty desktop 1440 (home + przepis) i mobile 390 zebrane i ocenione.
- Brak nowych plików `.js`/graficznych; zmiany tylko w base.html i main.css.
- Istniejące tła sekcji/kart/polaroidów niezmienione (poza subtelnym wzmocnieniem tekstury body).
</verification>

<success_criteria>
- Cała witryna ma namacalną, subtelną teksturę kraft prześwitującą na tłach --paper.
- 4-6 bladych ołówkowych szkiców składników w marginesach, pointer-events:none, aria-hidden, nie obniżają kontrastu treści.
- Scroll-drift działa gdzie wspierany, statyczny fallback gdzie nie; brak ruchu przy prefers-reduced-motion:reduce.
- Mobile: szkice zredukowane/ukryte, zero kolizji z treścią.
- Zero JS, zero nowych plików graficznych.
</success_criteria>

<output>
Create `.planning/quick/260715-hqv-o-yw-t-o-strony-tekstura-papieru-kraft-o/260715-hqv-SUMMARY.md` when done.
</output>
