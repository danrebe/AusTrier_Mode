"""
Zählt, wie oft jeder Begriff in den Spalten thema_.1, thema_.2, ... der Metadaten-CSV vorkommt.

Ergebnis:
- Ausgabe im Terminal (häufigste zuerst)
- results/begriffe_haeufigkeit.csv mit den Spalten begriff, anzahl, anteil_bilder

Aufruf:  python 07_Begriffe_zaehlen.py [eingabe.csv]
"""

import csv
from collections import Counter
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent   # = AusTrier_Mode
EINGABE = PROJEKT / "data" / "dataset_modebilder.csv"
AUSGABE = PROJEKT / "results" / "begriffe_haeufigkeit.csv"
TRENNZEICHEN = ";"

def main():
    zaehler = Counter()
    anzahl_bilder = 0

    # utf-8-sig entfernt ein eventuelles BOM, das Excel an den Dateianfang schreibt
    with open(EINGABE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=TRENNZEICHEN)
        thema_spalten = [s for s in reader.fieldnames if s.startswith("thema_")]
        print(f"{len(thema_spalten)} Thema-Spalten gefunden.")

        for zeile in reader:
            anzahl_bilder += 1
            begriffe = {(zeile[s] or "").strip() for s in thema_spalten}
            begriffe.discard("")
            zaehler.update(begriffe)  # jeder Begriff zählt pro Bild höchstens einmal

    AUSGABE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUSGABE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["begriff", "anzahl", "anteil_bilder"])
        for begriff, anzahl in zaehler.most_common():
            writer.writerow([begriff, anzahl, round(anzahl / anzahl_bilder, 3)])

    print(f"{anzahl_bilder} Bilder, {len(zaehler)} unterschiedliche Begriffe.\n")
    print(f"{'Anzahl':>7}  {'Anteil':>6}  Begriff")
    for begriff, anzahl in zaehler.most_common():
        print(f"{anzahl:>7}  {anzahl / anzahl_bilder:>6.0%}  {begriff}")
    print(f"\nGespeichert unter: {AUSGABE}")


if __name__ == "__main__":
    main()