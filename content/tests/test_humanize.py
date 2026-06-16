"""Testy deterministycznego sanitizera content/services/humanize.py.

Czyste funkcje (bez DB) — uzywamy SimpleTestCase.
"""

from django.test import SimpleTestCase

from content.services.humanize import humanize_text, humanize_json


class HumanizeTextTests(SimpleTestCase):
    def test_em_dash_with_spaces_becomes_comma(self):
        self.assertEqual(humanize_text("tekst — więcej"), "tekst, więcej")

    def test_en_dash_with_spaces_becomes_comma(self):
        self.assertEqual(humanize_text("tekst – więcej"), "tekst, więcej")

    def test_numeric_range_en_dash_preserved(self):
        self.assertEqual(humanize_text("10–15"), "10–15")

    def test_numeric_range_short_preserved(self):
        self.assertEqual(humanize_text("6–7"), "6–7")

    def test_glued_letter_em_dash_becomes_comma(self):
        self.assertEqual(humanize_text("słowo—słowo"), "słowo, słowo")

    def test_ellipsis_becomes_three_dots(self):
        self.assertEqual(humanize_text("Czekamy…"), "Czekamy...")

    def test_idempotence_on_mixed_string(self):
        x = "tekst — więcej, słowo—słowo, 10–15, Czekamy…"
        once = humanize_text(x)
        self.assertEqual(humanize_text(once), once)

    def test_polish_quotes_left_intact(self):
        # Para „ (U+201E low-open) + " (U+201D high-close) — poprawna typografia marki.
        self.assertEqual(
            humanize_text("„Kuchenna Komitywa”"),
            "„Kuchenna Komitywa”",
        )

    def test_english_opening_curly_quote_normalized(self):
        # U+201C (angielski cudzyslow otwierajacy) -> prosty ".
        self.assertEqual(
            humanize_text("“tekst”"),
            "\"tekst\"",
        )

    def test_english_closing_without_polish_open_normalized(self):
        # U+201D bez wczesniejszego „ -> prosty " (rola angielska).
        self.assertEqual(humanize_text("tekst”"), "tekst\"")

    def test_polish_pair_not_corrupted_when_201d_present(self):
        # Gdy „ jest obecny, nie ruszamy " (U+201D) — chroni cytat marki.
        s = "„cytat” i “angielski"
        out = humanize_text(s)
        self.assertIn("„cytat”", out)
        # Angielski otwierajacy U+201C i tak ma byc znormalizowany.
        self.assertNotIn("“", out)

    def test_curly_apostrophe_normalized(self):
        self.assertEqual(humanize_text("it’s"), "it's")


class HumanizeJsonTests(SimpleTestCase):
    def test_recurses_through_nested_dict_and_list(self):
        data = {"a": "x — y", "b": ["p—q", 5, {"c": "z…"}]}
        expected = {"a": "x, y", "b": ["p, q", 5, {"c": "z..."}]}
        self.assertEqual(humanize_json(data), expected)

    def test_non_string_leaf_untouched(self):
        self.assertEqual(humanize_json(5), 5)
        self.assertEqual(humanize_json(None), None)
        self.assertEqual(humanize_json(True), True)
