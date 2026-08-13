# Rozdzielenie Rezerwacji od Zamówień Rzutu

**Rezerwacja** atomowo blokuje ilości Pozycji Rzutu i użycie Kodu Rabatowego na 15 minut podczas płatności internetowej. **Zamówienie Rzutu** powstaje dopiero po potwierdzeniu płatności, pełnym rabacie albo świadomym zaakceptowaniu Zamówienia Ręcznego przez administratora. Przelewy24 otrzymuje ten sam 15-minutowy limit transakcji. Rezerwacje wygasza cron uruchamiany co minutę, wspierany awaryjnym czyszczeniem podczas żądań, a przydział Puli korzysta z atomowych aktualizacji warunkowych zgodnych z SQLite. Dzięki temu porzucone płatności nie zaśmiecają listy Zamówień Rzutu, a równocześni Klienci nie mogą kupić tych samych ostatnich sztuk.

## Konsekwencje

- Koszyk Rzutu nigdy nie blokuje Dostępności.
- Rezerwacje mają własny cykl życia, a wygasłe i nieudane rekordy są przechowywane przez 30 dni.
- Wstrzymany lub zamknięty Rzut może blokować nowe Rezerwacje bez unieważniania istniejącej i niewygasłej Rezerwacji.
- Podsumowanie Rzutu uwzględnia potwierdzone, nieanulowane Zamówienia Rzutu, w tym zaakceptowane Zamówienia Ręczne, ale nigdy aktywne Rezerwacje.
