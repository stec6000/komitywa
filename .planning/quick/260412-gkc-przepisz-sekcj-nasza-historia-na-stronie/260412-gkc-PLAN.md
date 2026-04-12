---
phase: quick
plan: 260412-gkc
type: execute
wave: 1
depends_on: []
files_modified:
  - templates/pages/about.html
autonomous: true
requirements: []
must_haves:
  truths:
    - "Sekcja Nasza historia napisana w pierwszej osobie liczby pojedynczej"
    - "Brak jakichkolwiek odniesień do Warszawy lub Mokotowa"
    - "Ton swobodny i autentyczny, nie korporacyjny"
  artifacts:
    - path: "templates/pages/about.html"
      provides: "Zaktualizowana sekcja Nasza historia"
      contains: "Nasza historia"
  key_links: []
---

<objective>
Zastąp istniejące dwa akapity sekcji "Nasza historia" w szablonie about.html nową wersją — luźną, pierwszoosobową, bez Warszawy, z duchem prostego chłopaka z Białegostoku za kuchnią.

Purpose: Strona O nas powinna brzmieć autentycznie i spójnie z wizerunkiem marki.
Output: Zaktualizowany plik templates/pages/about.html z nowym tekstem sekcji.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Zastąp sekcję Nasza historia nowym tekstem</name>
  <files>templates/pages/about.html</files>
  <action>
    W pliku templates/pages/about.html znajdź blok sekcji "Nasza historia" (dwa akapity między h2 a kolejnym elementem) i zastąp go dokładnie poniższym HTML-em. Nie zmieniaj nic poza tymi dwoma akapitami — zachowaj otaczającą strukturę szablonu bez zmian.

    STARY TEKST (do zastąpienia):
    ```html
    <h2>Nasza historia</h2>
    <p>Wszystko zaczęło się w małej domowej kuchni na warszawskim Mokotowie. Eksperymentowaliśmy z przepisami, szukając idealnych proporcji smaków i tekstur. Każde danie testowaliśmy na rodzinie i przyjaciołach, aż w końcu usłyszeliśmy: „Musicie to robić na poważnie!"</p>
    <p>Dziś Kuchenna Komitywa to nie tylko przepisy — to gotowe dania w słoikach, domowe ciasta na zamówienie i ebooki pełne naszych najlepszych receptur. Wszystko przygotowujemy ręcznie, z lokalnych, sezonowych składników.</p>
    ```

    NOWY TEKST (wstaw dokładnie tak):
    ```html
    <h2>Nasza historia</h2>
    <p>Zaczęło się tak, jak chyba u większości — od gotowania dla siebie i dla bliskich. Żadnego planu, żadnego biznesplanu, po prostu kuchnia, garnek i ciekawość, czy da się zrobić coś dobrego bez mięsa. Wyszło, że tak. I że najwyraźniej nie tylko mnie to smakuje.</p>
    <p>Dziś Kuchenna Komitywa to moja kuchnia przeniesiona trochę dalej — w słoiki, w ciasta na zamówienie i w ebooki, które możesz ściągnąć i gotować u siebie. Wszystko robię ręcznie, z lokalnych produktów, bez kombinowania. Prosto i smacznie — tyle i aż tyle.</p>
    ```
  </action>
  <verify>
    grep -n "Mokotowie\|Warszawy\|warszawskim\|Eksperymentowaliśmy\|testowaliśmy" templates/pages/about.html
    — powinien zwrócić ZERO wyników (brak starych fraz)

    grep -n "Zaczęło się tak\|garnek i ciekawość\|moja kuchnia" templates/pages/about.html
    — powinien zwrócić wyniki (nowy tekst obecny)
  </verify>
  <done>Plik about.html zawiera nową wersję sekcji Nasza historia — pierwsza osoba l. poj., bez Warszawy, luźny ton. Żadna inna część szablonu nie została zmieniona.</done>
</task>

</tasks>

<verification>
grep -c "Mokotowie" templates/pages/about.html  # musi zwrócić 0
grep -c "moja kuchnia" templates/pages/about.html  # musi zwrócić 1
</verification>

<success_criteria>
Sekcja "Nasza historia" na stronie O nas brzmi autentycznie, w pierwszej osobie l. poj., bez odniesień do Warszawy. Reszta szablonu niezmieniona.
</success_criteria>

<output>
Po zakończeniu utwórz `.planning/quick/260412-gkc-przepisz-sekcj-nasza-historia-na-stronie/260412-gkc-SUMMARY.md` z opisem co zmieniono.
</output>
