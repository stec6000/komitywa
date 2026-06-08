import json
import time
from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from content.models import WeeklyResearch


RESEARCH_PROMPT = """
Jesteś asystentem researchowym rzemieślniczej, wegańskiej piekarni domowej 
„Kuchenna Komitywa" z Białegostoku. Piekarnia robi m.in. wegańskie brownie i babeczki, 
sprzedaje do lokalnej kawiarni oraz klientom indywidualnym. Stawia na naturalność, 
lokalność, rzemiosło i sezonowość.

Zadanie: zbierz research z ostatnich 7 dni (zakres: {date_from} – {date_to}). 
Użyj wyszukiwania w sieci. Skup się na KONKRETACH — nazwy produktów, marek, badań, 
wydarzeń, daty, źródła — a nie na ogólnikach.

Tematy (w kolejności ważności):
1. Wegańskie wypieki i cukiernictwo — nowe techniki, przepisy, składniki (zamienniki 
   jajek, roślinne masła, aquafaba, mąki, fermentacja), trendy w roślinnych deserach.
2. Roślinne alternatywy i food tech — nowości rynkowe, ciekawe składniki, innowacje 
   (zwłaszcza użyteczne w piekarni).
3. Sezonowość — co jest teraz sezonowe w Polsce i jak to wykorzystać w wypiekach 
   (owoce, zioła, dodatki).
4. Polski rynek wegański — nowości, wydarzenia, lokale, inicjatywy (ze szczególnym 
   uwzględnieniem Podlasia/Białegostoku, jeśli coś się pojawi).
5. Zdrowie i żywienie roślinne — ciekawostki naukowe, badania (rzetelne źródła).
6. Zero waste / zrównoważona kuchnia — pomysły pasujące do rzemieślniczej piekarni.
7. Ciekawostki kulturowe lub historyczne o jedzeniu — coś, co może zainspirować treść.

Preferuj świeże, użyteczne i wiarygodne informacje. Pomijaj clickbait i treści 
marketingowe bez wartości. Jeśli w danym temacie nie ma nic ciekawego z ostatniego 
tygodnia, napisz to wprost zamiast wypełniać na siłę.

Zwróć uporządkowany research po polsku, pogrupowany według powyższych tematów, 
z krótkim opisem i źródłem przy każdym punkcie.
"""


FORMAT_PROMPT = """
Jesteś redaktorem treści marki „Kuchenna Komitywa" — rzemieślniczej, wegańskiej 
piekarni domowej z Białegostoku (wegańskie brownie, babeczki i więcej).

Głos marki: ciepły, osobisty, rzemieślniczy, z pasją do roślinnej kuchni i lokalności. 
Mówimy w pierwszej osobie („u nas w kuchni", „lubimy"), do odbiorcy zwracamy się 
na „ty". Bez korpomowy, bez nachalnego marketingu, bez pustych superlatywów. 
Autentycznie, konkretnie, z sercem.

Na podstawie researchu na końcu tej wiadomości przygotuj gotowy content w trzech 
formatach. Zwróć WYŁĄCZNIE czysty JSON (bez markdown, bez backticków, bez komentarza) 
o dokładnie takiej strukturze:

{{
  "blog": {{
    "title": "chwytliwy, ale nie clickbaitowy tytuł",
    "intro": "1-2 akapity wprowadzenia",
    "sections": [{{"heading": "...", "body": "..."}}],
    "tags": ["..."],
    "meta_description": "do 155 znaków"
  }},
  "instagram_posts": [
    {{"caption": "...", "hashtags": ["..."], "visual_hint": "..."}}
  ],
  "instagram_stories": [
    {{"slide_type": "hook|fact|tip|cta", "headline": "...", "subtext": "...", "bg_color": "#hex", "visual_hint": "..."}}
  ]
}}

Wytyczne:
- BLOG: 600–900 słów, 3–4 sekcje. Merytorycznie, ale przystępnie. Wybierz 1–2 
  najciekawsze wątki z researchu i rozwiń je — nie streszczaj wszystkiego. 
  meta_description ok. 150 znaków.
- INSTAGRAM POSTY: dokładnie 5. Każdy o jednym temacie. Pierwsza linia to mocny hook. 
  80–150 słów. Na końcu lekkie CTA (pytanie / zachęta do zapisania / komentarza). 
  hashtags: 8–12 sztuk, mix: wegańskie PL (#weganie #kuchniaweganska #roslinnie), 
  piekarnicze/deserowe, lokalne (#bialystok #podlasie) oraz #kuchennakomitywa. 
  visual_hint: konkretny opis kadru — co na zdjęciu, światło, stylizacja, nastrój 
  (przyda się przy robieniu zdjęcia lub grafiki).
- INSTAGRAM STORIES: 6–7 slajdów tworzących łuk: 1 × hook → 3–4 × fact/tip → 1 × cta.
  Każdy slajd ma „headline" (mocny nagłówek, max ~55 znaków — czytelny na ekranie
  telefonu) oraz „subtext" (rozwinięcie 1–2 zdania, max ~150 znaków). „visual_hint":
  konkretny opis kadru — co na zdjęciu, światło, stylizacja, nastrój (zasila prompt
  do zdjęcia tła, tak jak przy postach). bg_color wybierz z palety marki:
  #f3ead7 (papier), #6b7a3a (oliwka), #b6562e (terakota), #c89a3a (musztarda),
  #2a2420 (atrament) — służy jako kolor tła, gdy nie ma zdjęcia.

Cały tekst po polsku.

Research:
{raw_research}
"""


# Obserwowane fail-e Sonnet 4.6 — model zwraca nieescape'owane cudzysłowy
# w polskich tekstach (np. „brownie"), co rozwala json.loads(). Dodajemy w runtime,
# zeby nie modyfikowac VERBATIM FORMAT_PROMPT (verbatim z briefu, patrz PROMPTS-VERBATIM.md).
JSON_STRICTNESS_ADDENDUM = (
    "\n\nKRYTYCZNE: zwroc WYLACZNIE prawidlowy, parsowalny JSON. "
    "Kazdy cudzyslow wewnatrz stringa MUSI byc escapowany jako \\\". "
    "Zadnych komentarzy, zadnego tekstu poza JSON-em."
)


# Twardy limit prob retry na 429 — zapobiega nieskonczonej petli (DoS guard).
MAX_429_RETRIES = 3


def _parse_retry_after(headers, default=60):
    """Czyta naglowek retry-after (sekundy) z mapy naglowkow. Fallback = default."""
    raw = headers.get("retry-after") if headers else None
    if raw is None:
        return default
    try:
        return max(1, int(round(float(raw))))
    except (ValueError, TypeError):
        return default


def _strip_markdown_fences(raw_format: str) -> str:
    """Sciagamy ewentualne fence'y markdown z odpowiedzi modelu."""
    if raw_format.startswith("```"):
        raw_format = raw_format.split("\n", 1)[1] if "\n" in raw_format else raw_format
        if raw_format.endswith("```"):
            raw_format = raw_format.rsplit("```", 1)[0]
        raw_format = raw_format.strip()
        # Usun ewentualny prefix "json" po pierwszym fence:
        if raw_format.startswith("json\n"):
            raw_format = raw_format[5:].strip()
    return raw_format


class Command(BaseCommand):
    help = "Uruchamia tygodniowy research + format na contentu (call 1 + call 2 do Anthropic)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Wymus ponowne wygenerowanie nawet jesli status to 'formatted'.",
        )
        parser.add_argument(
            "--retry-format",
            action="store_true",
            help="Pomija call 1, uzywa istniejacego raw_research i robi tylko call 2 (format).",
        )

    def _create_with_429_retry(self, client, call_label, **create_kwargs):
        """client.messages.create(**create_kwargs) z retry na RateLimitError (429).

        Czyta retry-after z exc.response.headers, spi tyle ile kaze serwer
        (fallback 60s), ponawia do MAX_429_RETRIES razy. Po wyczerpaniu prob
        rzuca CommandError z czytelnym komunikatem. Dotyczy WYLACZNIE 429 i
        samego wywolania create — nie lapie json.JSONDecodeError ani innych
        wyjatkow.
        """
        from anthropic import RateLimitError  # lazy, wzorzec jak Anthropic w handle()
        for attempt in range(MAX_429_RETRIES):
            try:
                return client.messages.create(**create_kwargs)
            except RateLimitError as exc:
                if attempt == MAX_429_RETRIES - 1:
                    raise CommandError(
                        f"{call_label}: rate limit 429 po {MAX_429_RETRIES} probach: {exc}"
                    ) from exc
                response = getattr(exc, "response", None)
                headers = getattr(response, "headers", None)
                wait = _parse_retry_after(headers, default=60)
                self.stderr.write(self.style.WARNING(
                    f"[429] {call_label}: rate limit, retry {attempt + 1}/{MAX_429_RETRIES} za {wait}s..."
                ))
                time.sleep(wait)

    def _call_format(self, client, prompt: str) -> dict:
        """Wykonuje call 2 (format) z auto-retry na json.JSONDecodeError.

        Logika:
        1. call → ekstrakcja text → strip fence → json.loads. Sukces → return.
        2. json.JSONDecodeError → warning z pos/lineno/colno + 100 znakow kontekstu
           → sleep 60s → drugi call z TYM SAMYM promptem → strip fence → json.loads.
        3. Drugi tez pada → CommandError z fragmentami obu blędow.
        """

        def _do_call() -> str:
            response = self._create_with_429_retry(
                client,
                "call 2 (format)",
                model="claude-sonnet-4-6",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(
                block.text
                for block in response.content
                if getattr(block, "type", None) == "text"
            ).strip()
            return _strip_markdown_fences(text)

        text = _do_call()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            context = text[max(0, exc.pos - 50):exc.pos + 50]
            self.stderr.write(self.style.WARNING(
                f"[2/2] JSONDecodeError na 1. probie: {exc} "
                f"(pos={exc.pos}, lineno={exc.lineno}, colno={exc.colno}). "
                f"Kontekst (~100 znakow wokol pos): {context!r}"
            ))
            self.stderr.write(self.style.WARNING("[2/2] Retry za 60s..."))
            time.sleep(60)
            text2 = _do_call()
            try:
                return json.loads(text2)
            except json.JSONDecodeError as exc2:
                raise CommandError(
                    f"call 2 (format) JSON parse FAIL po 2 probach. "
                    f"1: {exc} | pos={exc.pos}. "
                    f"2: {exc2} | pos={exc2.pos}. "
                    f"Raw2 (truncated 2000): {text2[:2000]}"
                ) from exc2

    def handle(self, *args, **options):
        # Walidacja konfliktu flag:
        if options["force"] and options["retry_format"]:
            raise CommandError(
                "--force i --retry-format jednoczesnie nie ma sensu — wybierz jedno."
            )

        today = date.today()
        # Poniedzialek tego tygodnia:
        current_monday = today - timedelta(days=today.weekday())
        # Niedziela poprzedniego tygodnia = current_monday - 1 dzien:
        date_to = current_monday - timedelta(days=1)
        # Poniedzialek poprzedniego tygodnia:
        date_from = date_to - timedelta(days=6)
        # ISO week label dla daty z poprzedniego tygodnia (date_to nalezy do poprzedniego):
        iso_year, iso_week, _ = date_to.isocalendar()
        week_label = f"{iso_year}-W{iso_week:02d}"

        existing = WeeklyResearch.objects.filter(week_label=week_label).first()
        if (
            existing
            and existing.status == "formatted"
            and not options["force"]
            and not options["retry_format"]
        ):
            self.stdout.write(
                self.style.WARNING(
                    f"WeeklyResearch dla {week_label} juz istnieje ze statusem 'formatted'. "
                    f"Pomijam (uzyj --force aby nadpisac)."
                )
            )
            return

        api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        if not api_key:
            raise CommandError(
                "ANTHROPIC_API_KEY nie jest ustawiony (settings/.env)."
            )

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise CommandError(
                "Brak pakietu `anthropic`. Zainstaluj: pip install anthropic"
            ) from exc

        client = Anthropic(api_key=api_key)

        if options["retry_format"]:
            # Galaz A: pomijamy call 1, ladujemy istniejacy raw_research.
            row = WeeklyResearch.objects.filter(week_label=week_label).first()
            if row is None:
                raise CommandError(
                    f"Brak rekordu WeeklyResearch dla tygodnia {week_label}, "
                    f"nie ma czego retry-owac."
                )
            if not row.raw_research:
                raise CommandError(
                    f"raw_research dla {week_label} jest pusty, nie ma czego formatowac."
                )
            raw_research = row.raw_research
            self.stdout.write(self.style.NOTICE(
                f"[--retry-format] Pomijam call 1, uzywam istniejacego raw_research "
                f"({len(raw_research)} znakow)."
            ))
        else:
            # Galaz B: normalny flow — get_or_create + reset + call 1.
            row, _ = WeeklyResearch.objects.get_or_create(
                week_label=week_label,
                defaults={
                    "date_from": date_from,
                    "date_to": date_to,
                    "status": "pending",
                },
            )
            # Reset stanu przy --force lub po failed:
            row.date_from = date_from
            row.date_to = date_to
            row.status = "pending"
            row.error_message = ""
            row.save(update_fields=["date_from", "date_to", "status", "error_message", "updated_at"])

            self.stdout.write(self.style.NOTICE(
                f"[1/2] Research dla {week_label} ({date_from} – {date_to})..."
            ))
            try:
                research_response = self._create_with_429_retry(
                    client,
                    "call 1 (research)",
                    model="claude-sonnet-4-6",
                    max_tokens=8000,
                    # max_uses ogranicza liczbe rund web_search, by nie drenowac
                    # minutowego bucketa ITPM (Tier 1 = 30K input tokens/min).
                    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
                    messages=[
                        {
                            "role": "user",
                            "content": RESEARCH_PROMPT.format(
                                date_from=date_from.isoformat(),
                                date_to=date_to.isoformat(),
                            ),
                        }
                    ],
                )
                raw_research = "".join(
                    block.text
                    for block in research_response.content
                    if getattr(block, "type", None) == "text"
                ).strip()
                if not raw_research:
                    raise RuntimeError("Pusty research po wyfiltrowaniu blokow text.")
                row.raw_research = raw_research
                row.status = "research_done"
                row.save(update_fields=["raw_research", "status", "updated_at"])
                self.stdout.write(self.style.SUCCESS(
                    f"[1/2] OK — {len(raw_research)} znakow researchu."
                ))
            except Exception as exc:
                row.status = "failed"
                row.error_message = f"call 1 (research): {exc}"
                row.save(update_fields=["status", "error_message", "updated_at"])
                self.stderr.write(self.style.ERROR(f"[1/2] FAIL: {exc}"))
                raise

            # Pauza 60s miedzy call 1 a call 2 — Tier 1 rate limit safety.
            self.stdout.write(self.style.NOTICE(
                "Pauza 60s przed call 2 (Tier 1 rate limit safety)..."
            ))
            time.sleep(60)

        # Wspolny blok call 2 (oba galezie laduja tu z raw_research zdefiniowanym).
        self.stdout.write(self.style.NOTICE(f"[2/2] Formatowanie JSON dla {week_label}..."))
        prompt = FORMAT_PROMPT.replace("{raw_research}", raw_research) + JSON_STRICTNESS_ADDENDUM
        try:
            parsed = self._call_format(client, prompt)
        except CommandError as exc:
            row.status = "failed"
            row.error_message = str(exc)
            row.save(update_fields=["status", "error_message", "updated_at"])
            self.stderr.write(self.style.ERROR(f"[2/2] FAIL: {exc}"))
            raise
        except Exception as exc:
            row.status = "failed"
            row.error_message = f"call 2 (format): {exc}"
            row.save(update_fields=["status", "error_message", "updated_at"])
            self.stderr.write(self.style.ERROR(f"[2/2] FAIL: {exc}"))
            raise

        row.formatted_json = parsed
        row.status = "formatted"
        row.error_message = ""
        row.save(update_fields=["formatted_json", "status", "error_message", "updated_at"])
        self.stdout.write(self.style.SUCCESS(f"[2/2] OK — JSON zapisany."))

        self.stdout.write(self.style.SUCCESS(f"Pipeline ukonczony dla {week_label}."))
