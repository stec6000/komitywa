---
status: fix-applied-awaiting-user-verification
trigger: "Po wdrożeniu tła (quick 260715-hqv) obrazki dziwnie wyglądają przy scrollowaniu na produkcji"
created: 2026-07-15
updated: 2026-07-15
---

## Symptoms

DATA_START
- **Expected:** Tło strony (tekstura kraft + blade szkice + delikatny scroll-drift szkiców) nie wpływa na wygląd zdjęć ani czytelność treści podczas przewijania.
- **Actual:** Użytkownik zgłasza (Chrome, produkcja kuchennakomitywa.pl): "tylko obrazki dziwnie wygladaja przy scollowaniu" — obrazki/zdjęcia wyglądają dziwnie podczas przewijania. Niejednoznaczne, czy chodzi o (a) szkice tła .sk (skaczą/kręcą się dziwnie), czy (b) zdjęcia/polaroidy, po których "pływa" ziarno tekstury.
- **Errors:** Brak komunikatów błędów; problem czysto wizualny.
- **Timeline:** Zaczęło się bezpośrednio po deployu commita ea45a16 (feat: tekstura kraft + ołówkowe szkice + scroll-drift) dziś 2026-07-15 (~13:46). Wcześniej działało dobrze.
- **Reproduction:** Otworzyć kuchennakomitywa.pl w Chrome (desktop) i scrollować stronę główną; obserwować obrazki. Lokalnie: runserver + Chrome headless/dev.
DATA_END

## Kontekst techniczny (od orkiestratora)

- Zmiana podejrzana: commit `ea45a16` w `static/css/main.css` (+98 linii) i `8ece8bb` w `templates/base.html` (warstwa `.page-sketches` z 6 elementami `.sk-*`).
- Scroll-drift: `@media (prefers-reduced-motion: no-preference) { @supports (animation-timeline: view()) { .sk { animation-name: sk-drift; animation-timeline: view(); animation-range: entry 0% cover 60%; } } }`, keyframes `from { transform: rotate(var(--sk-rot)) translateY(14px) } to { transform: rotate(0) translateY(0) }`.
- Hipotezy startowe:
  1. `animation-timeline: view()` na elementach `.sk` pozycjonowanych absolutnie w kontenerze `inset: 0` obejmującym całą stronę — timeline `view()` śledzi widoczność elementu; przy elementach umieszczonych procentowo (top: X%) względem całej wysokości dokumentu animacja może się przeliczać dziwnie/skokowo przy scrollu, a rotacja od --sk-rot do 0deg może wyglądać jak "kręcące się obrazki".
  2. Tekstura `body::before/::after` (sprawdzić czy position: fixed i z-index względem treści) — jeśli nakładka ziarna leży NAD zdjęciami, przy scrollu zdjęcia przesuwają się pod nieruchomym ziarnem → wrażenie "brudnych/pływających" fotografii.
  3. Kompozycja: animowane transformy na dużych elementach z data-URI SVG mogą powodować jank/mignięcia przy repaint.
- Fix ma dotyczyć wyłącznie warstwy tła; w ostateczności usunąć scroll-drift (statyczne szkice zostają — użytkownik akceptował "domieszkę" ruchu, nie kosztem jakości).
- Weryfikacja wizualna: lokalny runserver (baza lokalna ma przepis wegańskie ragù; skopiować media z public/media/recipes/ jeśli praca w worktree) + screenshoty/scroll w headless Chrome.

## Current Focus

reasoning_checkpoint:
  hypothesis: "Scroll-drift na elementach .sk (animation-timeline: view(), keyframes sk-drift rotate+translateY) sprawia, że blade szkice-obrazki (SVG doodle w --ink) obracają się i przesuwają w trakcie przewijania w Chrome — to jedyne NOWE, scroll-wyzwalane zachowanie wizualne dodane w ea45a16. Użytkownik ('tylko obrazki dziwnie wyglądają przy scrollowaniu') widzi poruszające się blade rysunki."
  confirming_evidence:
    - "CDP: CSS.supports('animation-timeline','view()') === true w Chrome 149 → reguły scroll-drift są AKTYWNE (prod Chrome też je odpali)."
    - "Scroll-drift to jedyny nowy element wyzwalany scrollem w commicie ea45a16; body::before/after to warstwy statyczne (fixed)."
    - "6 elementów .sk to obrazki (inline SVG data-URI) → pasuje do 'obrazki' w zgłoszeniu."
  falsification_test: "Gdyby po usunięciu bloku scroll-drift (statyczne szkice zostają) obrazki nadal 'dziwnie wyglądały przy scrollu', hipoteza byłaby błędna — wróć do badania tekstury fixed+mix-blend-mode (jank repaintu)."
  fix_rationale: "Usunięcie bloku @media(prefers-reduced-motion)/@supports(animation-timeline) likwiduje ruch szkiców przy scrollu u samego źródła, zachowując statyczne rotacje (dekoracja zostaje). Adresuje przyczynę (ruch wyzwalany scrollem), nie objaw."
  blind_spots: "Headless Chrome nie renderuje aktywnej animacji view() w ustabilizowanych pozycjach (computed transform = statyczna baza), więc ruchu nie dało się złapać na statycznym screenshocie; opieram się na tym, że reguła jest wspierana+aktywna. Weryfikacja końcowa u użytkownika na realnym Chrome konieczna."
next_action: usunąć blok scroll-drift z static/css/main.css, zrobić screenshoty PO fixie, commit atomowy (bez push)

## Evidence

- timestamp: 2026-07-15T15:16
  checked: git show ea45a16 (static/css/main.css) + 8ece8bb (base.html) + pełny odczyt main.css:48-165
  found: body::before(z-index:0) i body::after(z-index:1) to position:fixed; mix-blend-mode:multiply. Treść (.wrap/section) ma z-index:2 (nad teksturą). .page-sketches: absolute inset:0 z-index:0 (pod treścią). 6 x .sk ze statycznymi rotacjami + blok scroll-drift (animation-timeline: view(), animation-range: entry 0% cover 60%, keyframes rotate(var(--sk-rot))→rotate(0) + translateY 14px→0).
  implication: Jedyne scroll-wyzwalane zachowanie to drift .sk. Tekstura jest pod treścią.

- timestamp: 2026-07-15T15:20
  checked: CDP hit-test document.elementFromPoint(cx,cy) w środku widocznej fotografii (krem-z-bialej-fasoli.jpg)
  found: topEl === sam <img> (sameAsImg:true) — żadna warstwa (tekstura/szkice) nie leży NAD fotografiami.
  implication: Nakładka ziarna NIE brudzi zdjęć (są nieprzezroczyste i nad teksturą). Hipoteza 2 (ziarno pływa po zdjęciach) obalona.

- timestamp: 2026-07-15T15:20
  checked: CDP getComputedStyle('.sk-onion').transform przy scrollY 0/400/900/1400 + CSS.supports('animation-timeline','view()')
  found: supports=true (reguły drift aktywne). W ustabilizowanych pozycjach transform = statyczna baza rotate(7deg) (fill-mode: none → poza aktywnym zakresem wraca do bazy). Ruch zachodzi w TRAKCIE przewijania przez zakres entry→cover, nie w spoczynku.
  implication: Scroll-drift jest realnie włączony w Chrome; szkice poruszają się podczas aktywnego scrollu. To najlepszy kandydat na 'obrazki dziwnie przy scrollu'.

## Eliminated

- hypothesis: "Nakładka tekstury (body::after, ziarno kraft) leży NAD zdjęciami i 'pływa' po nich przy scrollu"
  evidence: "CDP hit-test w centrum fotografii zwraca sam <img> jako element wierzchni (sameAsImg:true); treść ma z-index:2, tekstura z-index:1 (pod spodem). Multiply blenduje się z tłem, nie z fotografiami."
  timestamp: 2026-07-15T15:20

## Resolution

root_cause: Blok scroll-drift dodany w ea45a16 (@media (prefers-reduced-motion: no-preference) { @supports (animation-timeline: view()) { .sk { animation: sk-drift ... } } }) animuje 6 szkiców-obrazków (.sk) transformem zależnym od pozycji scrolla w Chrome — blade rysunki obracają się i przesuwają podczas przewijania, co użytkownik zgłasza jako "obrazki dziwnie wyglądają przy scrollowaniu". Nakładka tekstury została obalona jako przyczyna (leży pod treścią).
fix: Usunięto z static/css/main.css blok scroll-drift (@media/@supports z animation-timeline: view(), keyframes sk-drift, zmienne --sk-rot). Statyczne szkice (rotacje z reguł .sk-*) pozostają — dekoracja zachowana, zero ruchu przy scrollu. Wybrano opcję najbezpieczniejszą wizualnie zgodnie z instrukcją orkiestratora (przy niejednoznaczności: usuń scroll-drift, statyczne szkice zostają). Zaktualizowano też stały komentarz przy .sk.
verification: CDP/Chrome 149 headless — PRZED fixem 6 aktywnych animacji na .sk; PO fixie getAnimations() na wszystkich .sk = 0 (ruch scroll-driven zlikwidowany). Hit-test w centrum fotografii nadal zwraca sam <img> (żadna warstwa nad zdjęciami). Screenshoty przy scrollY 0/600/1200/2000/3000/3675 PRZED i PO — wygląd identyczny w spoczynku, szkice-dekoracja zachowane, fotografie czyste. Screenshoty referencyjne w .planning/debug/screenshots/ (nie commitowane).
files_changed: [static/css/main.css]
