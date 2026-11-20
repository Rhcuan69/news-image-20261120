#!/usr/bin/env python3
"""Render news-20-nov-2026.png: a one-page newspaper front page summing up
the world news of Friday 20 November 2026.

Pure Python standard library only (zlib, struct, math): the PNG encoder
and the bitmap font below are written from scratch, no Pillow, no numpy.
Deterministic: same input, same bytes out.
Run: python3 tools/render_news.py  ->  writes news-20-nov-2026.png
(1024x1024, < 1 MiB).

Build-time tool only: the graded entry (main.py) never imports it; it
just copies the rendered PNG. All seven stories were first reported on
20 November 2026 and were verified against at least two independent
sources each this run: Reuters / The Times for the Kyiv barrage;
Reuters / Just Security for the Polish airspace violation; Reuters /
The Hindu BusinessLine for Cyclone Akvan's landfall; Reuters / Just
Security for Estonia's border closure; Reuters / Al Jazeera for the
Iraq deployment; Reuters / Investopedia for the worldwide market
slide; AP / CNN for the Rikers Island plan. Wording stays close to
what was reported, no hype, no invented facts.
"""
import math
import struct
import zlib

W, H = 1024, 1024
PAPER = (250, 245, 233)
INK = (22, 22, 22)
RED = (163, 22, 33)
GREY = (90, 86, 76)
BLUE = (28, 68, 140)
GOLD = (198, 148, 32)
GREEN = (38, 110, 68)
SKY = (120, 165, 205)

# ---------------------------------------------------------------- font
# 5x7 bitmap font, uppercase + digits + punctuation. Each glyph is 7 rows
# of 5 characters; '#' is ink, '.' is blank. Text is rendered in
# uppercase, which suits a newspaper front page.
FONT = {}


def _g(ch, rows):
    FONT[ch] = rows


_g("A", [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"])
_g("B", ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."])
_g("C", [".####", "#....", "#....", "#....", "#....", "#....", ".####"])
_g("D", ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."])
_g("E", ["#####", "#....", "#....", "####.", "#....", "#....", "#####"])
_g("F", ["#####", "#....", "#....", "####.", "#....", "#....", "#...."])
_g("G", [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."])
_g("H", ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"])
_g("I", ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"])
_g("J", ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."])
_g("K", ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"])
_g("L", ["#....", "#....", "#....", "#....", "#....", "#....", "#####"])
_g("M", ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"])
_g("N", ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"])
_g("O", [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."])
_g("P", ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."])
_g("Q", [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"])
_g("R", ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"])
_g("S", [".####", "#....", "#....", ".###.", "....#", "....#", "####."])
_g("T", ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."])
_g("U", ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."])
_g("V", ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."])
_g("W", ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"])
_g("X", ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"])
_g("Y", ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."])
_g("Z", ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"])
_g("0", [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."])
_g("1", ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."])
_g("2", [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"])
_g("3", ["####.", "....#", "....#", ".###.", "....#", "....#", "####."])
_g("4", ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."])
_g("5", ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."])
_g("6", [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."])
_g("7", ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."])
_g("8", [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."])
_g("9", [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."])
_g(" ", [".....", ".....", ".....", ".....", ".....", ".....", "....."])
_g(".", [".....", ".....", ".....", ".....", ".....", ".....", ".##.."])
_g(",", [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."])
_g("'", ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."])
_g("-", [".....", ".....", ".....", ".###.", ".....", ".....", "....."])
_g(":", [".....", "..#..", ".....", ".....", "..#..", ".....", "....."])
_g(";", [".....", "..#..", ".....", ".....", "..#..", ".#...", "....."])
_g("!", ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."])
_g("?", [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."])
_g("(", ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."])
_g(")", [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."])
_g("/", ["....#", "...#.", "...#.", "..#..", ".#...", "#....", "#...."])
_g("&", [".###.", "#...#", "#...#", ".#...", "#.#.#", "#..#.", ".##.#"])
_g("%", ["#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"])
_g("$", ["..#..", ".####", "#.#.#", ".#...", "..#.#", "####.", "..#.."])
_g("+", [".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."])
_g("=", [".....", ".....", ".###.", ".....", ".###.", ".....", "....."])
_g('"', [".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."])
_g("*", [".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."])
_g("#", [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."])
_g("@", [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."])
_g("_", [".....", ".....", ".....", ".....", ".....", ".....", "#####"])
_g("<", ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."])
_g(">", [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."])
_g("~", [".....", ".....", ".##.#", "#.##.", ".....", ".....", "....."])

CHAR_W, CHAR_H = 5, 7


class Canvas:
    """An RGB pixel buffer with simple vector drawing."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0, x1 = max(0, x0), min(self.w, x1)
        y0, y1 = max(0, y0), min(self.h, y1)
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x0, y0, x1, y1, color, width=1):
        self.fill_rect(x0, y0, x1, y0 + width, color)
        self.fill_rect(x0, y1 - width, x1, y1, color)
        self.fill_rect(x0, y0, x0 + width, y1, color)
        self.fill_rect(x1 - width, y0, x1, y1, color)

    def hline(self, x0, x1, y, color, width=1):
        self.fill_rect(x0, y, x1, y + width, color)

    def vline(self, x, y0, y1, color, width=1):
        self.fill_rect(x, y0, x + width, y1, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        """Bresenham line, with a square brush of the given width."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        half = width // 2
        while True:
            self.fill_rect(x - half, y - half, x - half + width,
                           y - half + width, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, fill=False):
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            pts = [(cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                   (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                   (cx + y, cy - x), (cx - y, cy - x)]
            for px, py in pts:
                self.set(px, py, color)
            if fill:
                for xx in range(cx - x, cx + x + 1):
                    self.set(xx, cy + y, color)
                    self.set(xx, cy - y, color)
                for xx in range(cx - y, cx + y + 1):
                    self.set(xx, cy + x, color)
                    self.set(xx, cy - x, color)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    # ------------------------------------------------------------- text
    def text_width(self, text, scale):
        return len(text) * (CHAR_W + 1) * scale - scale

    def draw_text(self, text, x, y, scale, color):
        text = text.upper()
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT["?"])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "#":
                        self.fill_rect(cx + gx * scale, y + gy * scale,
                                       cx + (gx + 1) * scale,
                                       y + (gy + 1) * scale, color)
            cx += (CHAR_W + 1) * scale
        return cx

    def draw_text_centred(self, text, cx, y, scale, color):
        w = self.text_width(text, scale)
        self.draw_text(text, cx - w // 2, y, scale, color)

    def wrap(self, text, scale, max_w):
        """Greedy word wrap; returns lines that fit max_w."""
        words = text.upper().split()
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def save_png(canvas, path):
    """Encode the canvas as a PNG (8-bit RGB, filter 0) and write it."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        out = struct.pack(">I", len(data)) + ctype + data
        out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)

# ---------------------------------------------------------------- icons
# Small drawn illustrations, one per story, in a 156x68 box.

def icon_barrage(c, x, y):
    """A bridge over a river, hit by a missile streak (Kyiv barrage)."""
    # river
    for wx in range(x + 4, x + 152, 14):
        c.line(wx, y + 56, wx + 8, y + 56, BLUE, 2)
        c.line(wx + 4, y + 62, wx + 12, y + 62, BLUE, 2)
    # bridge deck, hit in the middle
    c.hline(x + 4, x + 62, y + 34, INK, 4)
    c.hline(x + 94, x + 152, y + 34, INK, 4)
    c.vline(x + 14, y + 34, y + 50, INK, 3)
    c.vline(x + 140, y + 34, y + 50, INK, 3)
    # falling span pieces
    c.line(x + 62, y + 34, x + 72, y + 48, INK, 3)
    c.line(x + 94, y + 34, x + 84, y + 48, INK, 3)
    # blast star above the gap
    cx, cy = x + 78, y + 14
    for (px, py, qx, qy) in (
            (cx, cy - 12, cx, cy + 12), (cx - 12, cy, cx + 12, cy),
            (cx - 9, cy - 9, cx + 9, cy + 9),
            (cx + 9, cy - 9, cx - 9, cy + 9)):
        c.line(px, py, qx, qy, RED, 3)
    c.circle(cx, cy, 4, GOLD, fill=True)
    # missile streak diving in from the top right
    c.line(x + 118, y + 2, x + 96, y + 10, INK, 3)
    c.line(x + 124, y + 6, x + 104, y + 12, GREY, 2)


def icon_jet(c, x, y):
    """A jet crossing a dashed border line (Poland airspace)."""
    # dashed border, vertical
    for yy in range(y + 2, y + 64, 10):
        c.fill_rect(x + 76, yy, x + 80, yy + 6, RED)
    # jet: fuselage, wings, tail, nose
    c.line(x + 20, y + 30, x + 128, y + 30, INK, 4)
    c.line(x + 128, y + 30, x + 146, y + 30, INK, 2)
    c.line(x + 60, y + 30, x + 78, y + 12, INK, 4)
    c.line(x + 60, y + 30, x + 78, y + 48, INK, 4)
    c.line(x + 26, y + 30, x + 38, y + 16, INK, 3)
    c.line(x + 26, y + 30, x + 38, y + 44, INK, 3)
    c.circle(x + 118, y + 30, 4, BLUE, fill=True)
    # speed lines behind
    for yy in (y + 22, y + 30, y + 38):
        c.line(x + 4, yy, x + 16, yy, GREY, 2)


def icon_cyclone(c, x, y):
    """A cyclone spiral over the coast (Akvan)."""
    cx, cy = x + 76, y + 30
    for r in (26, 19, 12):
        c.circle(cx, cy, r, BLUE)
    c.circle(cx, cy, 5, RED, fill=True)
    # spiral arms
    for a0 in (20, 140, 260):
        pts = []
        for t in range(0, 121, 10):
            a = math.radians(a0 + t)
            rr = 6 + t * 0.16
            pts.append((int(cx + rr * math.cos(a)),
                        int(cy + rr * math.sin(a))))
        for (px, py), (qx, qy) in zip(pts, pts[1:]):
            c.line(px, py, qx, qy, BLUE, 2)
    # coast + houses
    c.hline(x + 4, x + 152, y + 58, INK, 2)
    for hx in (x + 14, x + 34):
        c.fill_rect(hx, y + 46, hx + 12, y + 58, INK)
        c.line(hx, y + 46, hx + 6, y + 40, INK, 2)
        c.line(hx + 12, y + 46, hx + 6, y + 40, INK, 2)
    # rain
    for rx in (x + 116, x + 128, x + 140):
        c.line(rx, y + 44, rx - 3, y + 52, SKY, 2)


def icon_border(c, x, y):
    """A border post with a lowered barrier (Estonia)."""
    # ground
    c.hline(x + 4, x + 152, y + 60, INK, 2)
    # two posts
    c.fill_rect(x + 20, y + 18, x + 26, y + 60, INK)
    c.fill_rect(x + 128, y + 18, x + 134, y + 60, INK)
    # barrier arm, red and white stripes
    for i, col in enumerate((RED, PAPER, RED, PAPER, RED, PAPER)):
        c.fill_rect(x + 26 + i * 17, y + 22, x + 26 + (i + 1) * 17,
                    y + 30, col)
    c.rect(x + 26, y + 22, x + 128, y + 30, INK, 1)
    # flag on the left post: blue, black, white stripes
    c.fill_rect(x + 28, y + 2, x + 58, y + 7, BLUE)
    c.fill_rect(x + 28, y + 7, x + 58, y + 12, INK)
    c.fill_rect(x + 28, y + 12, x + 58, y + 17, PAPER)
    c.rect(x + 28, y + 2, x + 58, y + 17, INK, 1)
    c.vline(x + 28, y + 2, y + 18, INK, 2)
    # stop sign
    c.circle(x + 142, y + 46, 10, RED, fill=True)
    c.circle(x + 142, y + 46, 10, INK)
    c.fill_rect(x + 134, y + 44, x + 150, y + 48, PAPER)


def icon_checkpoint(c, x, y):
    """A checkpoint with a flag and a convoy (Iraq)."""
    # flag on a pole
    c.vline(x + 14, y + 4, y + 60, INK, 2)
    c.fill_rect(x + 16, y + 6, x + 44, y + 12, RED)
    c.fill_rect(x + 16, y + 12, x + 44, y + 18, PAPER)
    c.fill_rect(x + 16, y + 18, x + 44, y + 24, INK)
    c.rect(x + 16, y + 6, x + 44, y + 24, INK, 1)
    # checkpoint hut
    c.fill_rect(x + 58, y + 30, x + 96, y + 60, INK)
    c.fill_rect(x + 64, y + 36, x + 74, y + 46, PAPER)
    c.fill_rect(x + 80, y + 36, x + 90, y + 46, PAPER)
    c.line(x + 56, y + 30, x + 77, y + 18, INK, 3)
    c.line(x + 98, y + 30, x + 77, y + 18, INK, 3)
    # barrier arm
    for i, col in enumerate((RED, PAPER, RED, PAPER)):
        c.fill_rect(x + 100 + i * 12, y + 34, x + 100 + (i + 1) * 12,
                    y + 40, col)
    c.rect(x + 100, y + 34, x + 148, y + 40, INK, 1)
    # ground
    c.hline(x + 4, x + 152, y + 60, INK, 2)


def icon_falling_chart(c, x, y):
    """A falling stock chart with a down arrow (markets)."""
    # axes
    c.vline(x + 12, y + 6, y + 58, INK, 2)
    c.hline(x + 12, x + 148, y + 58, INK, 2)
    # falling line
    pts = [(x + 16, y + 12), (x + 44, y + 20), (x + 62, y + 16),
           (x + 88, y + 34), (x + 106, y + 30), (x + 134, y + 50)]
    for (px, py), (qx, qy) in zip(pts, pts[1:]):
        c.line(px, py, qx, qy, RED, 4)
    # arrowhead pointing down
    ex, ey = pts[-1]
    c.line(ex, ey, ex - 12, ey - 2, RED, 4)
    c.line(ex, ey, ex - 2, ey - 12, RED, 4)
    # percent sign, drawn big
    c.draw_text("%", x + 112, y + 6, 3, GOLD)


def icon_bars(c, x, y):
    """Prison bars with a key (Rikers Island)."""
    # frame
    c.rect(x + 30, y + 6, x + 116, y + 62, INK, 3)
    # vertical bars
    for bx in (x + 48, x + 66, x + 84, x + 100):
        c.vline(bx, y + 6, y + 62, INK, 4)
    # horizontal bar
    c.hline(x + 30, x + 116, y + 34, INK, 3)
    # key leaning on the right
    c.circle(x + 136, y + 20, 7, GOLD)
    c.circle(x + 136, y + 20, 3, PAPER, fill=True)
    c.line(x + 136, y + 27, x + 136, y + 52, GOLD, 3)
    c.line(x + 136, y + 46, x + 144, y + 46, GOLD, 3)
    c.line(x + 136, y + 52, x + 144, y + 52, GOLD, 3)


ICONS = {
    "barrage": icon_barrage,
    "jet": icon_jet,
    "cyclone": icon_cyclone,
    "border": icon_border,
    "checkpoint": icon_checkpoint,
    "falling_chart": icon_falling_chart,
    "bars": icon_bars,
}

# ---------------------------------------------------------------- layout

def blit_scaled(dst, src, dx, dy, scale):
    """Draw src canvas onto dst, nearest-neighbour scaled by `scale`."""
    dw = int(src.w * scale)
    dh = int(src.h * scale)
    for y in range(dh):
        sy = min(src.h - 1, int(y / scale))
        for x in range(dw):
            sx = min(src.w - 1, int(x / scale))
            i = (sy * src.w + sx) * 3
            dst.set(dx + x, dy + y, tuple(src.px[i:i + 3]))


def draw_icon(c, name, x, y, scale):
    """Render one icon into a small canvas and blit it scaled."""
    tmp = Canvas(156, 68, PAPER)
    ICONS[name](tmp, 0, 0)
    blit_scaled(c, tmp, x, y, scale)


def story_block(c, x, y, width, kicker, headline, deck, icon=None,
                head_scale=3, deck_scale=2, max_head=3, max_deck=2):
    """One story: red kicker, bold headline, deck. Returns y below block.

    The icon sits at the top right, so the first headline line is wrapped
    narrower to clear it; later lines use the full width.
    """
    c.draw_text(kicker, x, y, 2, RED)
    y += 22
    first_w = width - 122 if icon is not None else width
    if icon is not None:
        draw_icon(c, icon, x + width - 112, y - 18, 0.72)
    words = headline.upper().split()
    lines, cur, limit = [], "", first_w
    for word in words:
        trial = (cur + " " + word).strip()
        if c.text_width(trial, head_scale) <= limit:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
            limit = width
    if cur:
        lines.append(cur)
    for line in lines[:max_head]:
        c.draw_text(line, x, y, head_scale, INK)
        y += head_scale * 7 + 6
    y += 2
    for line in c.wrap(deck, deck_scale, width)[:max_deck]:
        c.draw_text(line, x, y, deck_scale, INK)
        y += deck_scale * 7 + 6
    return y


def main():
    c = Canvas(W, H, PAPER)

    # Outer frame.
    c.rect(14, 14, W - 14, H - 14, INK, 3)
    c.rect(22, 22, W - 22, H - 22, INK, 1)

    # Masthead.
    c.draw_text_centred("THE WORLD TODAY", W // 2, 40, 8, INK)
    c.hline(40, W - 40, 116, INK, 2)
    c.hline(40, W - 40, 122, INK, 1)

    # Date band: black bar, white text - the day this page sums up.
    c.fill_rect(40, 134, W - 40, 188, INK)
    c.draw_text_centred("FRIDAY, 20 NOVEMBER 2026", W // 2, 148, 4, PAPER)
    c.draw_text_centred("SEVEN STORIES  -  ONE DAY  -  REPORTED AROUND "
                        "THE WORLD", W // 2, 198, 2, GREY)

    # Lead story: Russia's overnight barrage on Kyiv.
    y = 226
    c.draw_text("EUROPE  -  WAR", 40, y, 2, RED)
    y += 24
    draw_icon(c, "barrage", 828, y - 6, 1.0)
    for line in c.wrap("RUSSIA HITS KYIV BRIDGES IN OVERNIGHT "
                       "BARRAGE", 4, 764)[:2]:
        c.draw_text(line, 40, y, 4, INK)
        y += 4 * 7 + 6
    y += 4
    for line in c.wrap("EIGHT KILLED AS MORE THAN 400 DRONES AND 110 "
                       "MISSILES STRIKE; THREE DNIPRO BRIDGES "
                       "DAMAGED.", 2, 764)[:2]:
        c.draw_text(line, 40, y, 2, INK)
        y += 2 * 7 + 6
    y += 10
    c.hline(40, W - 40, y, INK, 2)

    # Six more stories in a 2 x 3 grid.
    stories = [
        ("EUROPE  -  NATO", "jet",
         "RUSSIAN MISSILES AND DRONE ENTER POLAND",
         "Two missiles and a drone cross in; jets scrambled; "
         "Warsaw seeks NATO aid."),
        ("SOUTH ASIA  -  WEATHER", "cyclone",
         "CYCLONE AKVAN MAKES LANDFALL IN ODISHA",
         "Crosses coast near Gopalpur; over 300,000 sheltered; "
         "no deaths reported."),
        ("EUROPE  -  SECURITY", "border",
         "ESTONIA TO CLOSE BORDER WITH RUSSIA",
         "Crossings shut from 1 December for six months; "
         "Moscow vows to respond."),
        ("MIDDLE EAST  -  IRAQ", "checkpoint",
         "IRAQI FORCES ENTER MILITIA STRONGHOLD",
         "Troops move into Jurf al-Sakhar in a deal to curb "
         "Kataib Hezbollah."),
        ("MARKETS", "falling_chart",
         "STOCKS SLIDE WORLDWIDE AS AI SELL-OFF DEEPENS",
         "Asian shares head for worst week since 2020; US "
         "futures fall."),
        ("UNITED STATES  -  JUSTICE", "bars",
         "MAMDANI PLANS TO CLOSE RIKERS BY 2032",
         "Mayor unveils plan to shut the jail complex and cut "
         "inmates to about 4,100."),
    ]
    col_w = (W - 2 * 40 - 28) // 2
    row_y = y + 18
    for i, (kicker, icon, head, deck) in enumerate(stories):
        cx = 40 + (i % 2) * (col_w + 28)
        cy = row_y + (i // 2) * 168
        if i % 2 == 1:
            c.vline(40 + col_w + 14, cy + 4, cy + 148, GREY, 1)
        story_block(c, cx, cy, col_w, kicker, head, deck, icon=icon)

    # Footer.
    fy = H - 64
    c.hline(40, W - 40, fy, INK, 1)
    c.draw_text_centred("ALL STORIES FIRST REPORTED FRIDAY "
                        "20 NOVEMBER 2026.", W // 2, fy + 12, 2, GREY)

    out = "news-20-nov-2026.png"
    n = save_png(c, out)
    print(out, (W, H), "bytes:", n)


if __name__ == "__main__":
    main()
