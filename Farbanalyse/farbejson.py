"""
Wandelt results/farben.csv in JSON-Filter um, ein Objekt pro Zeile der CSV.

Tag  = nächstliegender offizieller CSS-Farbname (W3C, CSS Color Module Level 4, 148 Namen).
       Die Nähe wird im Lab-Farbraum gemessen, der dem menschlichen Farbempfinden entspricht.
Wert = Hex-Wert aus der CSV.
"""

import csv
import json
import sys
import webcolors

EINGABE = sys.argv[1] if len(sys.argv) > 1 else "Farbanalyse/farben.csv"
AUSGABE = sys.argv[2] if len(sys.argv) > 2 else "filter_jsons/farben_filter.json"

#Wird nur gebraucht um die hex werte den richtigen Namen zu geben.
def rgb_zu_lab(r, g, b):
    """sRGB (0–255) -> CIE-Lab (D65)."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = lin(r), lin(g), lin(b)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.00000
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


# Alle offiziellen CSS-Farbnamen mit ihren Lab-Werten
CSS_FARBEN = {}
for name in webcolors.names("css3"):
    rgb = webcolors.name_to_rgb(name, spec="css3")
    CSS_FARBEN[name] = rgb_zu_lab(*rgb)


def farbname(hexwert):
    lab = rgb_zu_lab(*webcolors.hex_to_rgb(hexwert))
    return min(CSS_FARBEN, key=lambda n: sum((a - b) ** 2 for a, b in zip(lab, CSS_FARBEN[n])))


def main():
    namen_cache = {}
    filter_liste = []

    with open(EINGABE, newline="", encoding="utf-8") as f:
        for zeile in csv.DictReader(f):
            hexwert = zeile["hex"].lower()
            if hexwert not in namen_cache:
                namen_cache[hexwert] = farbname(hexwert)
            filter_liste.append({
                "Type": "Filter",
                "Identifikator": zeile["uuid"],
                "Farbe": {
                    "Tag": namen_cache[hexwert],
                    "Wert": hexwert,
                },
            })

    with open(AUSGABE, "w", encoding="utf-8") as f:
        json.dump(filter_liste, f, ensure_ascii=False, indent=4)

    print(f"{len(filter_liste)} Filter geschrieben nach {AUSGABE}")
    print(f"{len(namen_cache)} unterschiedliche Hex-Werte, {len(set(namen_cache.values()))} unterschiedliche Farbnamen")


if __name__ == "__main__":
    main()