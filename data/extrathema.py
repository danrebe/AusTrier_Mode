"""
Extrahiert aus dataset_modebilder.csv alle Bilder mit den Themen Kind, Sport oder Verkleidung.
Ergebnis: results/themen_kind_sport_verkleidung.csv mit den Spalten thema, uuid
(eine Zeile pro Thema; alle UUIDs des Themas werden mit " | " verbunden).
"""

import os
import csv
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent   # = AusTrier_Mode
EINGABE = PROJEKT / "data" / "dataset_modebilder.csv"
AUSGABE = PROJEKT / "results" / "themen_kind_sport_verkleidung.csv"

# Begriff in den Metadaten -> Thema in der Ergebnisdatei
ZUORDNUNG = {
    "Kind": "Kind",
    "Mädchenkleid": "Kind",
    "Kleidung für Mädchen": "Kind",
    "Kleidung für Jungen": "Kind",
    "Sport": "Sport",
    "Verkleidung, Maskierung": "Verkleidung, Maskierung",
}
REIHENFOLGE = ["Kind", "Sport", "Verkleidung, Maskierung"]

treffer = {thema: [] for thema in REIHENFOLGE}  # thema -> Liste der UUIDs
with open(EINGABE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    thema_spalten = [s for s in reader.fieldnames if s.startswith("thema_")]
    for zeile in reader:
        begriffe = {(zeile[s] or "").strip() for s in thema_spalten}
        themen = {ZUORDNUNG[b] for b in begriffe if b in ZUORDNUNG}
        for thema in themen:  # Menge: jedes Bild höchstens einmal pro Thema
            treffer[thema].append(zeile["uuid"])

AUSGABE.parent.mkdir(parents=True, exist_ok=True)
with open(AUSGABE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["thema", "uuid"])
    for thema in REIHENFOLGE:
        writer.writerow([thema, " , ".join(treffer[thema])])

for thema in REIHENFOLGE:
    print(f"{thema:25} {len(treffer[thema])} Bilder")
print(f"\nGespeichert unter: {AUSGABE}")