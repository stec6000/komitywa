"""PNG renderer for Instagram Stories (1080x1920) — uses bundled Noto Sans fonts.

Layout A (background_image present): cover-cropped photo + bottom gradient scrim +
white eyebrow/headline/subtext anchored at the bottom.
Fallback (no image): bg_color fill + eyebrow/headline/subtext with readable text color.
PNG 1080x1920 is always produced.
"""

from __future__ import annotations

import textwrap
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from content.services.colors import text_color_for_bg

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

SLIDE_TYPE_PL = {
    "hook": "NA POCZĄTEK",
    "fact": "CIEKAWOSTKA",
    "tip": "WSKAZÓWKA",
    "cta": "OD NAS",
}


class StoryRenderer:
    CANVAS_SIZE = (1080, 1920)
    FONT_PATH_REGULAR = FONTS_DIR / "NotoSans-Regular.ttf"
    FONT_PATH_BOLD = FONTS_DIR / "NotoSans-Bold.ttf"

    MARGIN_X = 80
    BOTTOM_MARGIN = 120
    EYEBROW_SIZE = 40
    HEADLINE_SIZE = 76
    SUBTEXT_SIZE = 46
    EYEBROW_GAP = 28
    HEADLINE_LINE_GAP = 12
    BLOCK_GAP = 24
    SUBTEXT_LINE_GAP = 8
    HEADLINE_WRAP = 23
    SUBTEXT_WRAP = 36
    SUBTEXT_MAX_LINES = 4
    SCRIM_HEIGHT_RATIO = 0.45
    SCRIM_MAX_ALPHA = 217

    def __init__(self) -> None:
        if not self.FONT_PATH_REGULAR.exists() or not self.FONT_PATH_BOLD.exists():
            raise RuntimeError(
                f"Required fonts missing in {FONTS_DIR}: "
                "NotoSans-Regular.ttf and NotoSans-Bold.ttf"
            )
        self._font_eyebrow = ImageFont.truetype(
            str(self.FONT_PATH_REGULAR), self.EYEBROW_SIZE
        )
        self._font_headline = ImageFont.truetype(
            str(self.FONT_PATH_BOLD), self.HEADLINE_SIZE
        )
        self._font_subtext = ImageFont.truetype(
            str(self.FONT_PATH_REGULAR), self.SUBTEXT_SIZE
        )

    @staticmethod
    def _parse_hex(color: str, default: str = "#f3ead7") -> tuple:
        value = (color or default).strip().lstrip("#")
        if len(value) != 6:
            value = default.lstrip("#")
        try:
            return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            value = default.lstrip("#")
            return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _normalize(slide) -> dict:
        """Normalize a dict OR a StorySlide instance into a plain dict.

        Returns keys: headline, subtext, bg_color, slide_type, bg_path.
        """
        if isinstance(slide, dict):
            bg_path = slide.get("background_image") or None
            return {
                "headline": slide.get("headline") or "",
                "subtext": slide.get("subtext") or "",
                "bg_color": slide.get("bg_color") or "#f3ead7",
                "slide_type": slide.get("slide_type") or "",
                "bg_path": bg_path,
            }
        # Object (e.g. StorySlide)
        bg_path = None
        bg_field = getattr(slide, "background_image", None)
        if bg_field:
            try:
                bg_path = bg_field.path
            except Exception:
                bg_path = None
        return {
            "headline": getattr(slide, "headline", "") or "",
            "subtext": getattr(slide, "subtext", "") or "",
            "bg_color": getattr(slide, "bg_color", "") or "#f3ead7",
            "slide_type": getattr(slide, "slide_type", "") or "",
            "bg_path": bg_path,
        }

    def _eyebrow_label(self, slide_type: str) -> str:
        key = (slide_type or "").strip().lower()
        return SLIDE_TYPE_PL.get(key, (slide_type or "").upper())

    @staticmethod
    def _cover_crop(img: Image.Image, size: tuple) -> Image.Image:
        target_w, target_h = size
        w, h = img.size
        if w == 0 or h == 0:
            return img.resize(size)
        scale = max(target_w / w, target_h / h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    def _build_scrim(self) -> Image.Image:
        canvas_w, canvas_h = self.CANVAS_SIZE
        scrim = Image.new("RGBA", self.CANVAS_SIZE, (0, 0, 0, 0))
        scrim_start = int(canvas_h * (1.0 - self.SCRIM_HEIGHT_RATIO))
        span = max(1, canvas_h - scrim_start)
        draw = ImageDraw.Draw(scrim)
        for y in range(scrim_start, canvas_h):
            ratio = (y - scrim_start) / span
            alpha = int(self.SCRIM_MAX_ALPHA * ratio)
            draw.line([(0, y), (canvas_w, y)], fill=(20, 16, 12, alpha))
        return scrim

    def _wrapped_lines(self, headline: str, subtext: str) -> tuple:
        headline_lines = (
            textwrap.wrap(headline, width=self.HEADLINE_WRAP) if headline else []
        )
        subtext_lines = (
            textwrap.wrap(subtext, width=self.SUBTEXT_WRAP) if subtext else []
        )
        if len(subtext_lines) > self.SUBTEXT_MAX_LINES:
            subtext_lines = subtext_lines[: self.SUBTEXT_MAX_LINES]
            last = subtext_lines[-1].rstrip()
            subtext_lines[-1] = (last[:33].rstrip() + "…") if last else "…"
        return headline_lines, subtext_lines

    def _line_height(self, draw, font) -> int:
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        return bbox[3] - bbox[1]

    def _draw_text_block(
        self,
        draw,
        eyebrow,
        headline_lines,
        subtext_lines,
        eyebrow_color,
        text_color,
    ) -> None:
        canvas_w, canvas_h = self.CANVAS_SIZE

        eyebrow_h = self._line_height(draw, self._font_eyebrow)
        headline_h = self._line_height(draw, self._font_headline)
        subtext_h = self._line_height(draw, self._font_subtext)

        total_h = 0
        if eyebrow:
            total_h += eyebrow_h + self.EYEBROW_GAP
        if headline_lines:
            total_h += (
                headline_h * len(headline_lines)
                + self.HEADLINE_LINE_GAP * (len(headline_lines) - 1)
            )
        if subtext_lines:
            total_h += self.BLOCK_GAP
            total_h += (
                subtext_h * len(subtext_lines)
                + self.SUBTEXT_LINE_GAP * (len(subtext_lines) - 1)
            )

        y = canvas_h - self.BOTTOM_MARGIN - total_h

        if eyebrow:
            spaced = " ".join(list(eyebrow))
            bbox = draw.textbbox((0, 0), spaced, font=self._font_eyebrow)
            lw = bbox[2] - bbox[0]
            draw.text(
                ((canvas_w - lw) // 2, y),
                spaced,
                font=self._font_eyebrow,
                fill=eyebrow_color,
            )
            y += eyebrow_h + self.EYEBROW_GAP

        for i, line in enumerate(headline_lines):
            bbox = draw.textbbox((0, 0), line, font=self._font_headline)
            lw = bbox[2] - bbox[0]
            draw.text(
                ((canvas_w - lw) // 2, y),
                line,
                font=self._font_headline,
                fill=text_color,
            )
            y += headline_h
            if i < len(headline_lines) - 1:
                y += self.HEADLINE_LINE_GAP

        if subtext_lines:
            y += self.BLOCK_GAP
            for i, line in enumerate(subtext_lines):
                bbox = draw.textbbox((0, 0), line, font=self._font_subtext)
                lw = bbox[2] - bbox[0]
                draw.text(
                    ((canvas_w - lw) // 2, y),
                    line,
                    font=self._font_subtext,
                    fill=text_color,
                )
                y += subtext_h
                if i < len(subtext_lines) - 1:
                    y += self.SUBTEXT_LINE_GAP

    def render(self, slide) -> bytes:
        data = self._normalize(slide)
        headline = (data["headline"] or "").strip()
        subtext = (data["subtext"] or "").strip()
        bg_color = data["bg_color"]
        eyebrow = self._eyebrow_label(data["slide_type"])
        bg_path = data["bg_path"]

        headline_lines, subtext_lines = self._wrapped_lines(headline, subtext)

        bg_image = None
        if bg_path:
            try:
                opened = Image.open(bg_path).convert("RGB")
                bg_image = self._cover_crop(opened, self.CANVAS_SIZE)
            except Exception:
                bg_image = None

        if bg_image is not None:
            # ---- Layout A: photo + gradient scrim + white text ----
            scrim = self._build_scrim()
            img = Image.alpha_composite(
                bg_image.convert("RGBA"), scrim
            ).convert("RGB")
            draw = ImageDraw.Draw(img)
            self._draw_text_block(
                draw,
                eyebrow,
                headline_lines,
                subtext_lines,
                eyebrow_color=(230, 230, 230),
                text_color=(255, 255, 255),
            )
        else:
            # ---- Fallback: solid bg_color + readable text ----
            bg_rgb = self._parse_hex(bg_color)
            text_rgb = self._parse_hex(
                text_color_for_bg(bg_color), default="#2a2420"
            )
            # dimmed eyebrow: blend text color toward bg
            eyebrow_rgb = (
                int(text_rgb[0] * 0.7 + bg_rgb[0] * 0.3),
                int(text_rgb[1] * 0.7 + bg_rgb[1] * 0.3),
                int(text_rgb[2] * 0.7 + bg_rgb[2] * 0.3),
            )
            img = Image.new("RGB", self.CANVAS_SIZE, bg_rgb)
            draw = ImageDraw.Draw(img)
            self._draw_text_block(
                draw,
                eyebrow,
                headline_lines,
                subtext_lines,
                eyebrow_color=eyebrow_rgb,
                text_color=text_rgb,
            )

        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def render_to_file(self, slide, path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.render(slide))
        return path
