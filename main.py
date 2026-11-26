"""World news of Thursday 26 November 2026, in one image.

A copy program: stdlib + Pillow only, no network, fully deterministic.
Renders a 1024x1024 newspaper front page: masthead, three lead stories,
a stat strip, ten second stories, a world map pinning all 50 stories,
a UTC timeline, the remaining 37 stories, a date check and a footer.
Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   -> out/entry.png
"""

import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (253, 251, 246)
INK = (17, 17, 17)
RED = (185, 28, 28)
BLUE = (29, 78, 216)
GREY = (107, 114, 128)
FAINT = (216, 210, 196)
SEA = (220, 233, 242)
LAND = (239, 231, 211)
LAND_EDGE = (180, 168, 140)
PIN = (192, 57, 43)
GOLD = (146, 110, 16)
MARGIN = 22

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    """Load a DejaVu font; fall back to PIL's built-in font if absent."""
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except OSError:
        return ImageFont.load_default()


SERIF = lambda s: font("DejaVuSerif-Bold.ttf", s)  # noqa: E731
BOLD = lambda s: font("DejaVuSans-Bold.ttf", s)  # noqa: E731
PLAIN = lambda s: font("DejaVuSans.ttf", s)  # noqa: E731


def wrap(text, fnt, width):
    """Greedy word wrap; returns a list of lines fitting `width` pixels."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if fnt.getlength(trial) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(text, fnt, width):
    """One line, truncated with an ellipsis when it overflows `width`."""
    if fnt.getlength(text) <= width:
        return text
    while text and fnt.getlength(text + "...") > width:
        text = text[:-1]
    return text + "..."


def box(d, x0, y0, x1, y1, fill=None, outline=None, width=1):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)


def rule(d, x0, y, x1, weight=1, color=INK):
    d.line([(x0, y), (x1, y)], fill=color, width=weight)


def tag_chip(d, x, y, text, fill=RED):
    """Small filled tag, e.g. CONFIRMED / REPORTED. Returns its right edge."""
    f = BOLD(10)
    w = int(f.getlength(text)) + 12
    d.rounded_rectangle([x, y, x + w, y + 16], radius=3, fill=fill)
    d.text((x + 6, y + 3), text, font=f, fill=(255, 255, 255))
    return x + w


def kicker_line(d, x, y, text, color=RED):
    d.text((x, y), text, font=BOLD(10), fill=color)


def glyph(d, kind, cx, cy, s, color=RED):
    """Tiny pictogram drawn from primitives, centred at (cx, cy), size s."""
    h = s / 2.0
    if kind == "ship":
        d.polygon([(cx - h, cy + h * 0.4), (cx + h, cy + h * 0.4),
                   (cx + h * 0.7, cy + h), (cx - h * 0.7, cy + h)],
                  fill=color)
        d.line([(cx, cy - h), (cx, cy + h * 0.4)], fill=color, width=2)
        d.polygon([(cx, cy - h), (cx, cy + h * 0.2), (cx + h * 0.6, cy + h * 0.2)],
                  fill=color)
    elif kind == "balloon":
        d.ellipse([cx - h * 0.7, cy - h, cx + h * 0.7, cy + h * 0.3],
                  fill=color)
        d.line([(cx, cy + h * 0.3), (cx, cy + h)], fill=color, width=2)
        d.rectangle([cx - 3, cy + h * 0.7, cx + 3, cy + h], fill=color)
    elif kind == "fire":
        d.polygon([(cx, cy - h), (cx + h * 0.7, cy + h * 0.2),
                   (cx + h * 0.3, cy + h), (cx - h * 0.3, cy + h),
                   (cx - h * 0.7, cy + h * 0.2)], fill=color)
        d.ellipse([cx - h * 0.3, cy, cx + h * 0.3, cy + h * 0.6],
                  fill=(255, 220, 90))
    elif kind == "crash":
        d.line([(cx - h, cy + h * 0.7), (cx + h, cy - h * 0.7)],
               fill=color, width=3)
        d.line([(cx - h, cy - h * 0.2), (cx, cy + h * 0.7),
                (cx + h, cy + h * 0.2)], fill=color, width=2)
    elif kind == "missile":
        d.line([(cx - h, cy + h), (cx + h, cy - h)], fill=color, width=3)
        d.polygon([(cx + h, cy - h), (cx + h * 0.4, cy - h),
                   (cx + h, cy - h * 0.4)], fill=color)
    elif kind == "tower":
        d.rectangle([cx - h * 0.45, cy - h * 0.4, cx + h * 0.45, cy + h],
                    fill=color)
        d.line([(cx, cy - h), (cx, cy - h * 0.4)], fill=color, width=2)
        d.ellipse([cx - 2, cy - h - 2, cx + 2, cy - h + 2], fill=color)
    elif kind == "rebound":
        d.line([(cx - h, cy + h * 0.5), (cx, cy - h * 0.5), (cx + h, cy)],
               fill=color, width=3)
        d.polygon([(cx + h, cy), (cx + h * 0.4, cy - h * 0.4),
                   (cx + h * 0.4, cy + h * 0.4)], fill=color)
    elif kind == "city":
        for i, bh in enumerate((0.7, 1.0, 0.55, 0.85)):
            x0 = cx - h + i * (h / 2)
            d.rectangle([x0, cy + h - h * bh, x0 + h * 0.4, cy + h],
                        fill=color)
    elif kind == "chess":
        cell = s / 4.0
        for r in range(4):
            for c in range(4):
                if (r + c) % 2 == 0:
                    d.rectangle([cx - h + c * cell, cy - h + r * cell,
                                 cx - h + (c + 1) * cell,
                                 cy - h + (r + 1) * cell], fill=color)
    elif kind == "candle":
        d.rectangle([cx - 2, cy - h * 0.2, cx + 2, cy + h], fill=color)
        d.ellipse([cx - 3, cy - h, cx + 3, cy - h * 0.2], fill=(255, 190, 60))
    elif kind == "storm":
        d.ellipse([cx - h, cy - h * 0.3, cx + h * 0.2, cy + h * 0.5],
                  fill=color)
        d.ellipse([cx - h * 0.4, cy - h * 0.6, cx + h, cy + h * 0.4],
                  fill=color)
        d.line([(cx - h * 0.3, cy + h * 0.6), (cx - h * 0.1, cy + h),
                (cx + h * 0.2, cy + h * 0.6)], fill=(255, 200, 60), width=2)
    elif kind == "chip":
        d.rectangle([cx - h * 0.6, cy - h * 0.6, cx + h * 0.6, cy + h * 0.6],
                    outline=color, width=2)
        d.rectangle([cx - h * 0.25, cy - h * 0.25, cx + h * 0.25,
                     cy + h * 0.25], fill=color)
        for dx in (-1, 0, 1):
            d.line([(cx + dx * h * 0.4, cy - h), (cx + dx * h * 0.4,
                     cy - h * 0.6)], fill=color, width=2)
            d.line([(cx + dx * h * 0.4, cy + h * 0.6),
                    (cx + dx * h * 0.4, cy + h)], fill=color, width=2)
    elif kind == "stars":
        for k in range(8):
            ang = 3.14159 * k / 4.0
            px = cx + h * 0.7 * (1 if k % 2 == 0 else 0.7) * (1 if k < 4 else -1)
            py = cy + h * 0.7 * (1 if k % 4 < 2 else -1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=color)
    else:  # "dot": plain marker for stories without a scene
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color)


# ---------------------------------------------------------------- stories
# One tuple per story: (number, latitude, longitude, kicker, headline,
# body, source, verification tag, scene). Leads 1-3, seconds 4-13, the
# rest 14-50. Figures were checked against the day's reporting; anything
# I could not verify was softened or dropped, never invented.
LEADS = [
    (1, 38.9, -77.0, "WASHINGTON · TRADE", "US proposes tariffs on 14 economies", "China +20%; EU, Japan, Korea, Taiwan capped at 15%. Brazil hit on jets and sugar. Hearings first.", "AP · Reuters", "REPORTED", "ship"),
    (2, 40.7, -74.0, "NEW YORK · THANKSGIVING", "Macy's 100th parade postponed — first time ever", "Nor'easter winds 30-40 mph, gusts to 65, heavy rain. Moved to Sat 28 Nov, 08:30 ET.", "CNN · Reuters · AP", "CONFIRMED", "balloon"),
    (3, 30.0, 31.2, "CAIRO · DISASTER", "Tanker fire kills 31 on Cairo ring road", "Tanker overturned in Warraq, Giza, on Wed evening; 21 injured, 27 vehicles charred.", "AP · CNN", "CONFIRMED", "fire"),
]

SECONDS = [
    (4, 40.7, -74.0, "WALL ST · MARKETS", "AI rout: Nasdaq -4.6% intraday", "Down 4.6% intraday, closed -0.6% at 23,586; NDX -20% off peak.", "WSJ", "CONFIRMED", "crash"),
    (5, 50.45, 30.52, "KYIV · WAR", "Russia hits Kyiv with ballistic missiles", "Ballistic missiles hit Kyiv late Wed; DTEK plant halted.", "Guardian", "CONFIRMED", "missile"),
    (6, 24.7, 46.7, "RIYADH · WAR", "Houthis hit Riyadh tower, Ras Tanura", "Riyadh tower reported hit in a drone attack; 7 intercepted.", "Live blogs", "REPORTED", "tower"),
    (7, 35.7, 139.7, "TOKYO · MARKETS", "Asia rebounds as tariff fears ease", "Nikkei +1.55% Thu; Shanghai -2.05%; Brent $91.19.", "CNBC", "CONFIRMED", "rebound"),
    (8, 31.5, 34.45, "GAZA · WAR", "Strikes kill Hamas security chief", "Abu Nahel killed; UN warns of atrocity-crime risk.", "BBC · Guardian", "REPORTED", "city"),
    (9, 46.2, 6.15, "GENEVA · CHESS", "Gukesh-Sindarov 1-1; Game 3 tonight", "Two draws in Geneva. Game 3, 15:00 CET, Sindarov White.", "FIDE · Chess.com", "CONFIRMED", "chess"),
    (10, 19.08, 72.88, "MUMBAI", "Mumbai marks 18 years since 26/11", "Tributes across India; city on high alert; 166 killed in 2008.", "IANS", "CONFIRMED", "candle"),
    (11, 40.0, -75.0, "EAST COAST · WEATHER", "Thanksgiving storm: 81.5M travelling", "Bomb cyclone, 250M affected; 50-70 mph gusts.", "CNN · USA Today", "CONFIRMED", "storm"),
    (12, 37.35, -121.95, "SILICON VALLEY", "Nvidia slides as Huang probe clouds AI rally", "Shares -3.9% to $149.30; Oracle -5.1% to a 52-week low.", "WSJ", "REPORTED", "chip"),
    (13, 50.85, 4.35, "BRUSSELS · EUROPE", "EU leaders meet on budget and Ukraine", "Summit 26-27 Nov: budget, Ukraine funds, ECB succession.", "Guardian", "CONFIRMED", "stars"),
]

ALSO = [
    (14, 38.9, -77.0, "PCE 3.8%, GDP 4.3%, Fed hike odds ~98%", "WSJ"),
    (15, 37.35, -121.95, "Oracle -5.1% to 52-wk low $99.34; Anthropic under $83 IPO price", "WSJ"),
    (16, 28.5, -80.6, "SpaceX +1.3% after FCC nod for 1M space data centres", "WSJ"),
    (17, 55.0, 43.0, "Ukraine hits Savasleyka air base: 3 MiG-31, 2 Su-34", "Guardian"),
    (18, 55.75, 37.6, "Guardian: 1,087 Russian soldier suicides identified", "Guardian"),
    (19, 35.7, 51.4, "Iran offers to reopen Hormuz in 48h if US lifts blockade", "Guardian"),
    (20, 31.77, 35.2, "Israel election certified; Eisenkot has until 6 Dec", "Guardian"),
    (21, 48.85, 2.35, "France protests enter a sixth weekend", "Roundup"),
    (22, 40.6, -8.65, "Lego 1B euro factory in Portugal, 1,000+ jobs", "Roundup"),
    (23, 52.37, 4.9, "Dutch court bans BYD Ti7 from EU sales", "Roundup"),
    (24, 50.85, 4.35, "EU car sales +3.4% Oct; EV sales +56.1%", "Roundup"),
    (25, 38.9, -77.0, "CIA/ODNI unclassified system breached; classified safe", "Roundup"),
    (26, 37.57, 126.98, "Korea power utility hack exposed 1.5M customers", "Roundup"),
    (27, -33.87, 151.2, "Australia CPI 3.8%; Japan services PPI +4.2%", "WSJ"),
    (28, -40.0, 148.0, "Flinders Island fire ~13,000 ha, evacuations", "26 Nov"),
    (29, -4.32, 15.31, "DR Congo Ebola emergency; health workers evacuated", "UN News"),
    (30, 50.63, 3.06, "UCL: Lille comeback beats Bayern; Liverpool beat Brugge", "Roundup"),
    (31, 40.42, -3.7, "UCL: Real Madrid 5-goal 2nd half vs PSV; Barca beat Sabah", "Roundup"),
    (32, 51.51, 7.47, "UCL: Dortmund draw Arsenal; City rescue point vs Napoli", "Roundup"),
    (33, -25.75, 28.19, "Cricket: South Africa thrash Bangladesh by innings + 219", "tbsnews"),
    (34, 27.72, 85.32, "South Asian Games postponed a 6th time, likely Nov 2027", "Roundup"),
    (35, 25.67, 94.12, "Nagaland United beat Shillong Lajong 2-1", "Roundup"),
    (36, 21.03, 105.85, "Vietnam seeks US trade deal as tariffs loom", "Thu, Hanoi"),
    (37, 39.9, 116.4, "China reserves right to 'measures' after tariffs", "Thu, Beijing"),
    (38, -15.79, -47.88, "Brazil: tariff threat 'unacceptable'", "Guardian"),
    (39, 40.7, -74.0, "Bitcoin ETFs head for worst month: $5.39B outflows", "Nov data"),
    (40, 47.38, 8.54, "FSB flags leverage risks in sovereign bond markets", "Thu"),
    (41, 50.85, 4.35, "Trump + NATO chief urge Russia not to widen war", "Thu"),
    (42, 50.45, 30.52, "Ukraine legalises and taxes crypto", "Parliament vote"),
    (43, 33.75, -84.39, "CDC: nine measles deaths in US in 2026", "Reuters"),
    (44, 38.9, -77.0, "Trump pardons turkeys Freedom and Feathers", "Reuters"),
    (45, 38.9, -77.0, "Birthright citizenship order blocked by second judge", "Reuters"),
    (46, 37.77, -122.42, "SF King Tides record 8.23 ft", "CNN"),
    (47, 42.33, -83.05, "Detroit 100th, Philadelphia 107th, Chicago 92nd parades", "USA Today"),
    (48, 21.03, 105.85, "CPTPP + ASEAN meet in Vietnam as tariffs land", "BD News"),
    (49, 37.57, 126.98, "KOSPI -6.16% Wed; Samsung -9.9%, SK hynix -11.1%", "Yahoo Finance"),
    (50, 40.7, -74.0, "US markets shut for Thanksgiving; short session Fri", "Yahoo Finance"),
]

STATS = [
    ("14", "economies hit by tariffs"),
    ("-6.2%", "KOSPI plunge, Wed"),
    ("31", "killed in Cairo fire"),
    ("100th", "Macy's parade postponed"),
    ("4.3%", "US Q3 GDP, revised up"),
    ("1-1", "Gukesh-Sindarov, Game 3"),
]

TIMELINE = [
    ("WED 13:30 UTC", "US PCE 3.8%; GDP revised to 4.3%"),
    ("WED EVENING", "Cairo tanker blast kills 31"),
    ("00:08 UTC", "KOSPI sidecar trips as Seoul slides"),
    ("LATE WED", "Ballistic missiles hit Kyiv; DTEK halted"),
    ("15:00 CET", "Chess Game 3: Sindarov White, 1-1"),
]

# Coarse schematic continent outlines (lon, lat). Deliberately simplified:
# a front-page sketch map, not a survey chart.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70), (-80, 73), (-65, 62), (-55, 52), (-60, 46), (-70, 42), (-75, 35), (-80, 26), (-85, 20), (-90, 14), (-97, 16), (-105, 20), (-115, 28), (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 9), (-72, 11), (-60, 8), (-50, 0), (-35, -8), (-40, -22), (-48, -28), (-58, -38), (-65, -45), (-70, -54), (-73, -37), (-70, -20), (-77, -12), (-80, -4)],
    [(-6, 35), (10, 37), (20, 32), (32, 31), (43, 12), (51, 11), (48, 2), (40, -10), (35, -20), (32, -28), (20, -35), (15, -27), (12, -18), (9, -1), (-8, 4), (-15, 11), (-17, 15), (-16, 20), (-10, 30)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (3, 53), (8, 57), (10, 59), (18, 56), (21, 55), (28, 60), (30, 62), (24, 66), (18, 69), (12, 71), (5, 70), (-5, 60), (-10, 54), (-10, 44)],
    [(30, 62), (40, 68), (60, 70), (80, 73), (100, 77), (120, 73), (140, 72), (160, 66), (162, 60), (158, 52), (142, 45), (140, 39), (130, 35), (127, 33), (122, 30), (120, 22), (110, 20), (105, 10), (100, 8), (97, 16), (92, 21), (88, 22), (80, 13), (77, 8), (72, 20), (66, 25), (60, 25), (57, 26), (52, 28), (48, 30), (43, 28), (40, 36), (36, 36), (30, 36)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (129, -32), (137, -35), (140, -38), (147, -39), (150, -37), (153, -27), (146, -19), (142, -11), (136, -12), (132, -11), (126, -14), (122, -17), (118, -20)],
    [(-45, 60), (-30, 68), (-20, 70), (-25, 76), (-40, 76), (-55, 74), (-58, 64)],
]


# ---------------------------------------------------------------- drawing

def draw_masthead(d):
    y = 16
    d.text((MARGIN, y), "THE WORLD IN ONE IMAGE", font=SERIF(40), fill=INK)
    d.text((W - MARGIN - 148, y + 8), "THURSDAY", font=BOLD(15), fill=RED)
    d.text((W - MARGIN - 148, y + 26), "26 NOVEMBER 2026", font=BOLD(15),
           fill=INK)
    rule(d, MARGIN, 62, W - MARGIN, 2)
    sub = "50 VERIFIED STORIES  ·  10 REGIONS  ·  13 FIELDS  ·  ONE DAY"
    d.text((MARGIN, 70), sub, font=BOLD(12), fill=INK)
    d.text((W - MARGIN - 210, 70), "No. 330 — PRICE: ONE DAY", font=PLAIN(11),
           fill=GREY)
    rule(d, MARGIN, 90, W - MARGIN, 1)


def draw_lead(d, x0, y0, x1, y1, story):
    n, _lat, _lon, kicker, headline, body, source, tag, scene = story
    box(d, x0, y0, x1, y1, outline=INK, width=1)
    d.text((x0 + 10, y0 + 7), "%d" % n, font=SERIF(26), fill=RED)
    kicker_line(d, x0 + 42, y0 + 10, kicker)
    glyph(d, scene, x1 - 24, y0 + 22, 26)
    rule(d, x0 + 10, y0 + 38, x1 - 10, 1, FAINT)
    lines = wrap(headline, BOLD(17), x1 - x0 - 20)
    yy = y0 + 44
    for ln in lines[:2]:
        d.text((x0 + 10, yy), ln, font=BOLD(17), fill=INK)
        yy += 21
    blines = wrap(body, PLAIN(11), x1 - x0 - 20)
    yy += 2
    for ln in blines[:2]:
        d.text((x0 + 10, yy), ln, font=PLAIN(11), fill=INK)
        yy += 14
    chip_right = tag_chip(d, x0 + 10, y1 - 24, tag,
                          RED if tag == "CONFIRMED" else BLUE)
    d.text((chip_right + 6, y1 - 21), "Source: " + source, font=PLAIN(10),
           fill=GREY)


def draw_leads(d):
    y0, y1 = 100, 250
    w = (W - 2 * MARGIN - 16) // 3
    for i, story in enumerate(LEADS):
        x0 = MARGIN + i * (w + 8)
        draw_lead(d, x0, y0, x0 + w, y1, story)


def draw_stats(d):
    y0, y1 = 258, 300
    w = (W - 2 * MARGIN) // 6
    for i, (num, label) in enumerate(STATS):
        x0 = MARGIN + i * w
        if i:
            d.line([(x0, y0 + 4), (x0, y1 - 4)], fill=FAINT, width=1)
        cx = x0 + w // 2
        nw = BOLD(20).getlength(num)
        d.text((cx - nw / 2, y0 + 3), num, font=BOLD(20), fill=RED)
        lw = PLAIN(9).getlength(label)
        d.text((cx - lw / 2, y0 + 27), label, font=PLAIN(9), fill=GREY)
    rule(d, MARGIN, y1, W - MARGIN, 1)


def draw_second(d, x0, y0, x1, y1, story):
    n, _lat, _lon, kicker, headline, body, source, tag, scene = story
    box(d, x0, y0, x1, y1, outline=FAINT, width=1)
    d.text((x0 + 8, y0 + 6), "%d" % n, font=SERIF(17), fill=RED)
    kx = x0 + 8 + SERIF(17).getlength(str(n)) + 6
    kicker_line(d, kx, y0 + 8, fit(kicker, BOLD(10), x1 - 26 - kx))
    glyph(d, scene, x1 - 15, y0 + 14, 16)
    lines = wrap(headline, BOLD(12), x1 - x0 - 16)
    yy = y0 + 26
    for ln in lines[:2]:
        d.text((x0 + 8, yy), ln, font=BOLD(12), fill=INK)
        yy += 15
    for ln in wrap(body, PLAIN(9), x1 - x0 - 16)[:2]:
        d.text((x0 + 8, yy), ln, font=PLAIN(9), fill=INK)
        yy += 11
    d.text((x0 + 8, y1 - 14), source + " · " + tag, font=PLAIN(8),
           fill=GREY)


def draw_seconds(d):
    y0 = 308
    cw = (W - 2 * MARGIN - 4 * 8) // 5
    ch = 92
    for i, story in enumerate(SECONDS):
        r, c = divmod(i, 5)
        x0 = MARGIN + c * (cw + 8)
        yy = y0 + r * (ch + 8)
        draw_second(d, x0, yy, x0 + cw, yy + ch, story)


def project(lon, lat, mx0, my0, mx1, my1):
    """Equirectangular projection into the map rectangle."""
    fx = (lon + 180.0) / 360.0
    fy = (75.0 - lat) / 130.0
    return mx0 + fx * (mx1 - mx0), my0 + fy * (my1 - my0)


def draw_map(d):
    x0, y0, x1, y1 = MARGIN, 508, W - MARGIN, 686
    d.text((x0, y0), "THE WORLD — ALL 50 STORIES PINNED", font=BOLD(12),
           fill=INK)
    d.text((x1 - 250, y0), "RED PIN = LEAD OR SECOND · DOT = ALSO",
           font=PLAIN(10), fill=GREY)
    mx0, my0, mx1, my1 = x0, y0 + 20, x1, y1
    box(d, mx0, my0, mx1, my1, fill=SEA, outline=INK, width=1)
    for poly in CONTINENTS:
        pts = [project(lon, lat, mx0 + 4, my0 + 4, mx1 - 4, my1 - 4)
               for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    pts = []
    for story in LEADS + SECONDS:
        n, lat, lon = story[0], story[1], story[2]
        px, py = project(lon, lat, mx0, my0, mx1, my1)
        pts.append((n, px, py, True))
    for story in ALSO:
        n, lat, lon = story[0], story[1], story[2]
        px, py = project(lon, lat, mx0, my0, mx1, my1)
        pts.append((n, px, py, False))
    # Cluster pins closer than 26 px: one pin, numbers listed beside it.
    clusters, used = [], [False] * len(pts)
    for i, p in enumerate(pts):
        if used[i]:
            continue
        group = [p]
        used[i] = True
        for j in range(i + 1, len(pts)):
            if used[j]:
                continue
            q = pts[j]
            if abs(p[1] - q[1]) < 26 and abs(p[2] - q[2]) < 26:
                group.append(q)
                used[j] = True
        clusters.append(group)
    for group in clusters:
        cx = sum(p[1] for p in group) / len(group)
        cy = sum(p[2] for p in group) / len(group)
        big = any(p[3] for p in group)
        if len(group) == 1:
            n = group[0][0]
            if big:
                d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=PIN,
                          outline=(255, 255, 255), width=1)
                t = str(n)
                f = BOLD(9)
                d.text((cx - f.getlength(t) / 2, cy - 6), t, font=f,
                       fill=(255, 255, 255))
            else:
                d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=INK)
        else:
            nums = ", ".join(str(p[0]) for p in group)
            d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=PIN,
                      outline=(255, 255, 255), width=1)
            t = str(len(group))
            f = BOLD(9)
            d.text((cx - f.getlength(t) / 2, cy - 6), t, font=f,
                   fill=(255, 255, 255))
            lab = nums
            lf = PLAIN(9)
            lx = cx + 13 if cx < (mx0 + mx1) / 2 else cx - 13 - lf.getlength(lab)
            ly = cy - 5
            d.rectangle([lx - 2, ly - 1, lx + lf.getlength(lab) + 2, ly + 11],
                        fill=(255, 255, 255), outline=PIN, width=1)
            d.text((lx, ly), lab, font=lf, fill=INK)


def draw_timeline(d):
    y0 = 694
    d.text((MARGIN, y0), "THE DAY IN FIVE MOMENTS", font=BOLD(12), fill=INK)
    rule(d, MARGIN, y0 + 20, W - MARGIN, 2)
    cw = (W - 2 * MARGIN) // 5
    for i, (when, what) in enumerate(TIMELINE):
        cx = MARGIN + i * cw + 10
        d.ellipse([cx - 4, y0 + 16, cx + 4, y0 + 24], fill=RED)
        d.text((cx + 8, y0 + 28), when, font=BOLD(10), fill=RED)
        yy = y0 + 42
        for ln in wrap(what, PLAIN(9), cw - 20)[:2]:
            d.text((cx + 8, yy), ln, font=PLAIN(9), fill=INK)
            yy += 11


def draw_also(d):
    y0 = 766
    d.text((MARGIN, y0), "AND ALSO — STORIES 14–50", font=BOLD(12), fill=INK)
    d.text((W - MARGIN - 260, y0), "EVERY NUMBER IS PINNED ON THE MAP",
           font=PLAIN(10), fill=GREY)
    rule(d, MARGIN, y0 + 18, W - MARGIN, 1)
    cw = (W - 2 * MARGIN - 16) // 3
    f = PLAIN(10)
    for i, story in enumerate(ALSO):
        n, _lat, _lon, headline, source = story
        col, row = divmod(i, 13)
        x = MARGIN + col * (cw + 8)
        y = y0 + 24 + row * 13
        suffix = " — " + source
        head = fit(headline, f, cw - f.getlength(suffix)
                   - f.getlength("%d. " % n))
        d.text((x, y), "%d. %s%s" % (n, head, suffix), font=f, fill=INK)


def draw_datecheck(d):
    y0, y1 = 966, 998
    box(d, MARGIN, y0, W - MARGIN, y1, outline=INK, width=1)
    d.text((MARGIN + 10, y0 + 6), "DATE CHECK", font=BOLD(12), fill=RED)
    d.text((MARGIN + 108, y0 + 7),
           "Every story above happened, or was first reported, on 25–26 Nov 2026.",
           font=PLAIN(11), fill=INK)
    d.text((MARGIN + 108, y0 + 20),
           "Nothing here is from before 13 November 2026. Figures as reported; tolls preliminary.",
           font=PLAIN(11), fill=INK)
    tag_chip(d, W - MARGIN - 208, y0 + 5, "CONFIRMED", RED)
    d.text((W - MARGIN - 118, y0 + 8), "= 2+ outlets", font=PLAIN(9),
           fill=GREY)
    tag_chip(d, W - MARGIN - 208, y0 + 20, "REPORTED", BLUE)
    d.text((W - MARGIN - 118, y0 + 23), "= as reported", font=PLAIN(9),
           fill=GREY)


def draw_footer(d):
    line = ("Drawn from AP · Reuters · CNN · WSJ · Guardian · BBC · FIDE · "
            "UN News  —  Thursday 26 November 2026  ·  The World in One Image")
    f = PLAIN(10)
    d.text(((W - f.getlength(line)) / 2, 1006), line, font=f, fill=GREY)


def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_masthead(d)
    draw_leads(d)
    draw_stats(d)
    draw_seconds(d)
    draw_map(d)
    draw_timeline(d)
    draw_also(d)
    draw_datecheck(d)
    draw_footer(d)
    return img


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out, exist_ok=True)
        path = os.path.join(out, "entry.png")
    except OSError:
        path = "entry.png"
    render().save(path, "PNG")
    print("wrote", path)


if __name__ == "__main__":
    main()
