#!/usr/bin/env python3
"""Draw the Friday 20 November 2026 front page of THE WORLD TODAY.

Build-time tool for the make.fun bounty news-image-20261120. It paints a
1024x1024 newspaper front page -- masthead, black date band, one lead
story and six more in a two-by-three grid, each with a small hand-drawn
pictogram -- and writes it to news-20-nov-2026.png next to this tool.

Everything is pure Python standard library: the pixel buffer, the
5x7 bitmap letterforms, the pictograms and the PNG writer are all
implemented here, so the script runs on a vanilla interpreter with no
third-party packages. Output is deterministic: the same input always
produces the same bytes.

The seven stories are the day's verified headlines, worded as reported.
"""

import math
import struct
import zlib
from pathlib import Path

PAGE_W = 1024
PAGE_H = 1024

PAPER = (250, 244, 230)     # newsprint cream
INK = (18, 18, 18)         # near-black
CRIMSON = (176, 32, 32)    # kicker red
SLATE = (88, 84, 74)       # muted grey for the strapline
SKY = (52, 96, 158)        # blue accents (water, rain, flag)
GOLD = (198, 148, 38)      # gold accents (explosion, key)
FLAG_BLUE = (0, 80, 160)   # top stripe of the Estonian flag

# ---------------------------------------------------------------- font
# Each letterform is seven rows of five cells; '#' is ink, '.' is blank.
# Only capitals, digits and the punctuation used on the page are needed.

GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}

CELL_W = 5          # glyph columns
CELL_H = 7          # glyph rows
CELL_ADV = 6        # advance per character at scale 1 (5 + 1 gap)


def text_width(text, scale):
    """Pixel width of text at the given scale, without trailing gap."""
    if not text:
        return 0
    return len(text) * CELL_ADV * scale - scale


# ------------------------------------------------------------- stories
# Each entry drives one block on the page: kicker line, headline, deck
# and the name of the pictogram drawn beside it. The lead entry spans
# the full width; the other six fill a two-by-three grid in order.

STORIES = [
    {
        "kicker": "EUROPE - WAR",
        "headline": "RUSSIA HITS KYIV BRIDGES IN OVERNIGHT BARRAGE",
        "deck": "EIGHT KILLED AS MORE THAN 400 DRONES AND 110 MISSILES "
                "STRIKE; THREE DNIPRO BRIDGES DAMAGED.",
        "art": "bridge",
        "lead": True,
    },
    {
        "kicker": "EUROPE - NATO",
        "headline": "RUSSIAN MISSILES AND DRONE ENTER POLAND",
        "deck": "TWO MISSILES AND A DRONE CROSS IN; JETS SCRAMBLED; "
                "WARSAW SEEKS NATO AID.",
        "art": "missile",
    },
    {
        "kicker": "SOUTH ASIA - WEATHER",
        "headline": "CYCLONE AKVAN MAKES LANDFALL IN ODISHA",
        "deck": "CROSSES COAST NEAR GOPALPUR; OVER 300,000 SHELTERED; "
                "NO DEATHS REPORTED.",
        "art": "cyclone",
    },
    {
        "kicker": "EUROPE - SECURITY",
        "headline": "ESTONIA TO CLOSE BORDER WITH RUSSIA",
        "deck": "CROSSINGS SHUT FROM 1 DECEMBER FOR SIX MONTHS; "
                "MOSCOW VOWS TO RESPOND.",
        "art": "barrier",
    },
    {
        "kicker": "MIDDLE EAST - IRAQ",
        "headline": "IRAQI FORCES ENTER MILITIA STRONGHOLD",
        "deck": "TROOPS MOVE INTO JURF AL-SAKHAR IN A DEAL TO CURB "
                "KATAIB HEZBOLLAH.",
        "art": "checkpoint",
    },
    {
        "kicker": "MARKETS",
        "headline": "STOCKS SLIDE WORLDWIDE AS AI SELL-OFF DEEPENS",
        "deck": "ASIAN SHARES HEAD FOR WORST WEEK SINCE 2020; "
                "US FUTURES FALL.",
        "art": "chart",
    },
    {
        "kicker": "UNITED STATES - JUSTICE",
        "headline": "MAMDANI PLANS TO CLOSE RIKERS BY 2032",
        "deck": "MAYOR UNVEILS PLAN TO SHUT THE JAIL COMPLEX AND CUT "
                "INMATES TO ABOUT 4,100.",
        "art": "jail",
    },
]


# -------------------------------------------------------------- canvas
class Sheet:
    """An RGB pixel buffer with tiny vector/text drawing helpers."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.buf = bytearray(background * (width * height))

    def dot(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.buf[i:i + 3] = bytes(colour)

    def fill(self, x0, y0, x1, y1, colour):
        """Fill the rectangle [x0, x1) x [y0, y1), clipped to the page."""
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.width, x1)
        y1 = min(self.height, y1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.width + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x0, x1, y, colour, thick=1):
        self.fill(x0, y, x1, y + thick, colour)

    def vline(self, x, y0, y1, colour, thick=1):
        self.fill(x, y0, x + thick, y1, colour)

    def frame(self, x0, y0, x1, y1, colour, thick=1):
        self.hline(x0, x1, y0, colour, thick)
        self.hline(x0, x1, y1 - thick, colour, thick)
        self.vline(x0, y0, y1, colour, thick)
        self.vline(x1 - thick, y0, y1, colour, thick)

    def segment(self, x0, y0, x1, y1, colour, thick=1):
        """Bresenham line; thickness is a square brush at each step."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.fill(x0 - half, y0 - half, x0 - half + thick,
                      y0 - half + thick, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, points, colour, thick=1):
        for a, b in zip(points, points[1:]):
            self.segment(a[0], a[1], b[0], b[1], colour, thick)

    def ring(self, cx, cy, radius, colour, thick=1):
        steps = max(24, int(2 * math.pi * radius))
        for n in range(steps):
            a = 2 * math.pi * n / steps
            self.fill(int(cx + radius * math.cos(a)) - thick // 2,
                      int(cy + radius * math.sin(a)) - thick // 2,
                      int(cx + radius * math.cos(a)) - thick // 2 + thick,
                      int(cy + radius * math.sin(a)) - thick // 2 + thick,
                      colour)

    def disc(self, cx, cy, radius, colour):
        for dy in range(-radius, radius + 1):
            dx = int(math.sqrt(radius * radius - dy * dy))
            self.hline(cx - dx, cx + dx + 1, cy + dy, colour)

    # -- text ------------------------------------------------------
    def write(self, x, y, text, scale, colour):
        """Draw one line of text; returns the x just past the last glyph."""
        cx = x
        for ch in text:
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "#":
                        self.fill(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale,
                                  y + (row + 1) * scale, colour)
            cx += CELL_ADV * scale
        return cx

    def centred(self, y, text, scale, colour):
        self.write((self.width - text_width(text, scale)) // 2,
                   y, text, scale, colour)

    def wrapped(self, x, y, text, scale, colour, max_w, leading):
        """Greedy word wrap; returns the y just below the last line."""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if text_width(trial, scale) <= max_w or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        for line in lines:
            self.write(x, y, line, scale, colour)
            y += CELL_H * scale + leading
        return y - leading


# ----------------------------------------------------------- pictograms
# Each draws inside a small box whose top-left corner is (ox, oy).
# The pictures are deliberately simple line art: a bridge under attack,
# a missile crossing a border, a cyclone swirl, a border barrier, a
# checkpoint house, a falling market chart, and a jail cell with a key.

def art_bridge(s, ox, oy):
    # blast star above the deck
    cx, cy = ox + 70, oy + 12
    for n in range(12):
        a = math.pi * n / 6
        s.segment(cx, cy,
                  cx + int(15 * math.cos(a)), cy + int(15 * math.sin(a)),
                  CRIMSON, 2)
    s.disc(cx, cy, 4, GOLD)
    # incoming streak, top right
    s.segment(ox + 118, oy + 2, ox + 146, oy + 22, INK, 2)
    s.disc(ox + 146, oy + 22, 3, CRIMSON)
    # deck, piers and the sagging span between them
    s.fill(ox, oy + 44, ox + 150, oy + 47, INK)
    s.segment(ox + 18, oy + 46, ox + 18, oy + 66, INK, 2)
    s.segment(ox + 130, oy + 46, ox + 130, oy + 66, INK, 2)
    s.segment(ox + 18, oy + 46, ox + 75, oy + 60, INK, 2)
    s.segment(ox + 130, oy + 46, ox + 75, oy + 60, INK, 2)
    # river dashes
    for yy in (oy + 70, oy + 76):
        x = ox
        while x < ox + 150:
            s.hline(x, min(x + 10, ox + 150), yy, SKY, 2)
            x += 16


def art_missile(s, ox, oy):
    # dotted border the missile has crossed
    for yy in range(oy + 4, oy + 52, 8):
        s.vline(ox + 72, yy, yy + 4, CRIMSON, 2)
    # body, nose cone and tail fins
    s.segment(ox + 8, oy + 28, ox + 92, oy + 28, INK, 3)
    s.segment(ox + 92, oy + 28, ox + 108, oy + 22, INK, 2)
    s.segment(ox + 92, oy + 28, ox + 108, oy + 34, INK, 2)
    s.segment(ox + 14, oy + 28, ox + 4, oy + 18, INK, 2)
    s.segment(ox + 14, oy + 28, ox + 4, oy + 38, INK, 2)
    s.segment(ox + 26, oy + 28, ox + 18, oy + 20, INK, 2)
    s.segment(ox + 26, oy + 28, ox + 18, oy + 36, INK, 2)
    s.disc(ox + 112, oy + 28, 3, SKY)


def art_cyclone(s, ox, oy):
    cx, cy = ox + 34, oy + 28
    for radius in (22, 15, 8):
        s.ring(cx, cy, radius, SKY, 2)
    s.disc(cx, cy, 3, CRIMSON)
    # slanting rain, right side
    for i, rx in enumerate((ox + 72, ox + 84, ox + 96, ox + 108)):
        top = oy + 16 + (i % 2) * 8
        s.segment(rx, top, rx - 4, top + 8, SKY, 2)
    # rooftops sheltering below the rain
    for hx in (ox + 66, ox + 84, ox + 102):
        s.segment(hx, oy + 44, hx + 6, oy + 38, INK, 2)
        s.segment(hx + 12, oy + 44, hx + 6, oy + 38, INK, 2)
        s.fill(hx, oy + 44, hx + 12, oy + 52, INK)


def art_barrier(s, ox, oy):
    # flag pole with the Estonian tricolour
    s.vline(ox + 6, oy + 6, oy + 50, INK, 2)
    s.frame(ox + 8, oy + 6, ox + 32, oy + 25, INK, 1)
    s.fill(ox + 9, oy + 7, ox + 31, oy + 13, FLAG_BLUE)
    s.fill(ox + 9, oy + 13, ox + 31, oy + 19, INK)
    s.fill(ox + 9, oy + 19, ox + 31, oy + 24, (232, 232, 228))
    # striped barrier bar between two posts
    s.vline(ox + 46, oy + 22, oy + 50, INK, 3)
    s.vline(ox + 100, oy + 22, oy + 50, INK, 3)
    for i in range(6):
        colour = CRIMSON if i % 2 == 0 else PAPER
        s.fill(ox + 49 + i * 9, oy + 26, ox + 49 + (i + 1) * 9, oy + 34,
               colour)
    s.frame(ox + 49, oy + 26, ox + 103, oy + 34, INK, 1)
    # round stop sign at the right end
    s.disc(ox + 110, oy + 42, 8, CRIMSON)
    s.fill(ox + 104, oy + 40, ox + 116, oy + 44, PAPER)


def art_checkpoint(s, ox, oy):
    # flag pole with a red-white-black flag
    s.vline(ox + 6, oy + 6, oy + 50, INK, 2)
    s.frame(ox + 8, oy + 6, ox + 32, oy + 25, INK, 1)
    s.fill(ox + 9, oy + 7, ox + 31, oy + 13, CRIMSON)
    s.fill(ox + 9, oy + 13, ox + 31, oy + 19, (232, 232, 228))
    s.fill(ox + 9, oy + 19, ox + 31, oy + 24, INK)
    # guard house: walls, pitched roof, door
    s.fill(ox + 44, oy + 28, ox + 76, oy + 52, INK)
    s.segment(ox + 42, oy + 28, ox + 60, oy + 16, INK, 2)
    s.segment(ox + 78, oy + 28, ox + 60, oy + 16, INK, 2)
    s.fill(ox + 56, oy + 40, ox + 64, oy + 52, PAPER)
    # short striped barrier to the right of the house
    for i in range(3):
        colour = CRIMSON if i % 2 == 0 else PAPER
        s.fill(ox + 84 + i * 10, oy + 38, ox + 84 + (i + 1) * 10, oy + 44,
               colour)
    s.frame(ox + 84, oy + 38, ox + 114, oy + 44, INK, 1)
    s.vline(ox + 82, oy + 34, oy + 52, INK, 2)


def art_chart(s, ox, oy):
    # axes
    s.vline(ox + 6, oy + 6, oy + 50, INK, 2)
    s.hline(ox + 6, ox + 112, oy + 50, INK, 2)
    # jagged line falling to the lower right
    points = [(ox + 12, oy + 14), (ox + 30, oy + 20), (ox + 46, oy + 18),
              (ox + 62, oy + 30), (ox + 78, oy + 28), (ox + 94, oy + 40),
              (ox + 110, oy + 46)]
    s.polyline(points, CRIMSON, 2)
    s.segment(ox + 110, oy + 46, ox + 102, oy + 42, CRIMSON, 2)
    s.segment(ox + 110, oy + 46, ox + 104, oy + 38, CRIMSON, 2)
    s.disc(ox + 98, oy + 10, 3, GOLD)


def art_jail(s, ox, oy):
    # cell bars with top and bottom rails
    s.hline(ox + 6, ox + 62, oy + 8, INK, 2)
    s.hline(ox + 6, ox + 62, oy + 48, INK, 2)
    for bx in range(ox + 6, ox + 66, 10):
        s.vline(bx, oy + 8, oy + 48, INK, 3)
    # brass key beside the cell
    s.ring(ox + 88, oy + 20, 7, GOLD, 2)
    s.segment(ox + 95, oy + 20, ox + 112, oy + 20, GOLD, 2)
    s.segment(ox + 106, oy + 20, ox + 106, oy + 28, GOLD, 2)
    s.segment(ox + 112, oy + 20, ox + 112, oy + 28, GOLD, 2)


ART = {
    "bridge": art_bridge,
    "missile": art_missile,
    "cyclone": art_cyclone,
    "barrier": art_barrier,
    "checkpoint": art_checkpoint,
    "chart": art_chart,
    "jail": art_jail,
}


# -------------------------------------------------------------- layout
MARGIN = 24            # inner text margin
COL_GAP = 24           # gap between the two grid columns
ROW_TOPS = (374, 559, 744)
GRID_BOTTOM = 929


def draw_lead(sheet, story):
    """Full-width lead story: kicker, big headline, deck, bridge art."""
    sheet.write(MARGIN, 220, story["kicker"], 2, CRIMSON)
    ART[story["art"]](sheet, 848, 222)
    y = sheet.wrapped(MARGIN, 240, story["headline"], 4, INK, 806, 8)
    sheet.wrapped(MARGIN, y + 10, story["deck"], 2, INK,
                  PAGE_W - 2 * MARGIN, 5)


def draw_cell(sheet, story, x0, y0, width):
    """One grid cell: kicker, headline, deck, pictogram top right."""
    sheet.write(x0, y0, story["kicker"], 2, CRIMSON)
    ART[story["art"]](sheet, x0 + width - 118, y0 - 2)
    y = sheet.wrapped(x0, y0 + 22, story["headline"], 3, INK,
                      width - 132, 7)
    sheet.wrapped(x0, y + 8, story["deck"], 2, INK, width, 5)


def build_page():
    sheet = Sheet(PAGE_W, PAGE_H, PAPER)
    # double frame
    sheet.frame(14, 14, PAGE_W - 14, PAGE_H - 14, INK, 3)
    sheet.frame(22, 22, PAGE_W - 22, PAGE_H - 22, INK, 1)
    # masthead and rules
    sheet.centred(44, "THE WORLD TODAY", 8, INK)
    sheet.hline(MARGIN, PAGE_W - MARGIN, 114, INK, 2)
    sheet.hline(MARGIN, PAGE_W - MARGIN, 120, INK, 1)
    # black date band and strapline
    sheet.fill(MARGIN, 132, PAGE_W - MARGIN, 182, INK)
    sheet.centred(143, "FRIDAY, 20 NOVEMBER 2026", 4, PAPER)
    sheet.centred(194, "SEVEN STORIES - ONE DAY - REPORTED AROUND THE WORLD",
                  2, SLATE)
    # lead story, then a rule
    draw_lead(sheet, STORIES[0])
    sheet.hline(MARGIN, PAGE_W - MARGIN, 358, INK, 1)
    # two-by-three grid of the remaining stories
    col_w = (PAGE_W - 2 * MARGIN - COL_GAP) // 2
    for row, top in enumerate(ROW_TOPS):
        for col in range(2):
            story = STORIES[1 + row * 2 + col]
            x0 = MARGIN + col * (col_w + COL_GAP)
            draw_cell(sheet, story, x0, top, col_w)
        if row < 2:
            sheet.hline(MARGIN, PAGE_W - MARGIN, top + 176, INK, 1)
    sheet.vline(MARGIN + col_w + COL_GAP // 2, ROW_TOPS[0], GRID_BOTTOM,
                INK, 1)
    # footer
    sheet.hline(MARGIN, PAGE_W - MARGIN, 946, INK, 1)
    sheet.centred(962, "ALL STORIES FIRST REPORTED FRIDAY 20 NOVEMBER 2026.",
                  2, SLATE)
    return sheet


# ------------------------------------------------------------ PNG out
def encode_png(sheet):
    """Encode the sheet as a PNG: filter 0 rows, zlib level 9."""
    raw = bytearray()
    stride = sheet.width * 3
    for y in range(sheet.height):
        raw.append(0)
        raw += sheet.buf[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", sheet.width, sheet.height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_path = Path(__file__).resolve().parent.parent / "news-20-nov-2026.png"
    out_path.write_bytes(encode_png(build_page()))
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
