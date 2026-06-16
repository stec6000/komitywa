"""Deterministyczny sanitizer typografii dla generowanego contentu.

Usuwa najczestsze "sygnaly AI" w polskim tekscie — przede wszystkim dlugie
mysliki (—), wielokropek Unicode (…) oraz angielskie cudzyslowy curly. Reguly
sa CELOWO konserwatywne i IDEMPOTENTNE: dwukrotne uruchomienie daje ten sam
wynik co jednokrotne. Frazy-klisze (np. "warto pamietac") NIE sa tu usuwane —
tym zajmuje sie wylacznie prompt (HUMANIZE_ADDENDUM w run_weekly_research).
"""

import re


# Mysliki otoczone bialymi znakami: " — " / " – " -> ", " (przecinek + spacja).
_DASH_SPACED_RE = re.compile(r"\s+[—–]\s+")

# Sklejony myslik MIEDZY LITERAMI: "slowo—slowo" -> "slowo, slowo".
# [^\W\d_] = znak slowny Unicode bez cyfr i podkreslnika (czyli litera).
# Dzieki temu zakresy liczbowe "10–15" / "6–7" (cyfra po obu stronach) ZOSTAJA.
_DASH_GLUED_LETTERS_RE = re.compile(r"(?<=[^\W\d_])[—–](?=[^\W\d_])")

# Wielokrotne spacje/taby -> pojedyncza spacja (newline'ow NIE ruszamy).
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")


def humanize_text(s: str) -> str:
    """Deterministyczna, IDEMPOTENTNA normalizacja jednego stringa."""
    if not isinstance(s, str):
        return s

    # 1. Mysliki.
    s = _DASH_SPACED_RE.sub(", ", s)
    s = _DASH_GLUED_LETTERS_RE.sub(", ", s)

    # 2. Wielokropek Unicode -> trzy kropki.
    s = s.replace("…", "...")  # …

    # 3. Cudzyslowy — regula KONSERWATYWNA (chroni typografie marki):
    #    - „ (U+201E) ZOSTAJE — to poprawny polski cudzyslow otwierajacy.
    #    - " (U+201C, angielski otwierajacy) -> prosty ".
    #    - ' (U+2019, curly apostrof) -> prosty '.
    #    - " (U+201D) jest DWUZNACZNE: polski zamykajacy ORAZ angielski zamykajacy.
    #      Konwertujemy je na prosty " TYLKO gdy w stringu NIE wystepuje „ (U+201E),
    #      czyli gdy na pewno nie jest czescia polskiej pary. Gdy „ jest obecny,
    #      zostawiamy " nietkniete — wolimy zostawic niz zepsuc cudzyslow marki.
    s = s.replace("“", "\"")  # "
    s = s.replace("’", "'")   # '
    if "„" not in s:          # brak „ -> bezpiecznie normalizujemy "
        s = s.replace("”", "\"")  # "

    # 4. Sprzatanie — zlanie wielokrotnych spacji (siatka bezpieczenstwa dla
    #    idempotencji; zamiana myslika daje pojedyncza spacje, ale to chroni
    #    przed wczesniejszymi podwojnymi spacjami w wejsciu).
    s = _MULTISPACE_RE.sub(" ", s)

    return s


def humanize_json(obj):
    """Rekurencyjnie czysci stringi w zagniezdzonej strukturze dict/list.

    Liscie nie-stringowe (int, float, bool, None) zwracane bez zmian.
    """
    if isinstance(obj, dict):
        return {key: humanize_json(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [humanize_json(item) for item in obj]
    if isinstance(obj, str):
        return humanize_text(obj)
    return obj
