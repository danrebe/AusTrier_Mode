"""
Findet die UUIDs aller Bilder, die eines der gesuchten Themen in thema_.1 ... thema_.36 haben.
Ergebnis: results/uuids_nach_thema.csv (uuid, themen) - eine Zeile pro Bild
"""

import csv
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent   # = AusTrier_Mode
EINGABE = PROJEKT / "data" / "dataset_modebilder.csv"
AUSGABE = PROJEKT / "results" / "uuids_nach_thema.csv"

# Genau so geschrieben, wie die Begriffe in den Metadaten stehen
THEMEN = [
    "Fächer",
    "Regenschirm",
    "Muff",
    "Schmuck, Juwelen",
    "Schal",
    "Wanderstab, Spazierstock",
]

treffer = {}  # uuid -> Liste der gefundenen Themen
with open(EINGABE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    thema_spalten = [s for s in reader.fieldnames if s.startswith("thema_")]
    for zeile in reader:
        begriffe = {(zeile[s] or "").strip() for s in thema_spalten}
        gefunden = [thema for thema in THEMEN if thema in begriffe]
        if gefunden:
            treffer[zeile["uuid"]] = gefunden

AUSGABE.parent.mkdir(parents=True, exist_ok=True)
with open(AUSGABE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["uuid", "themen"])
    for uuid, themen in treffer.items():
        writer.writerow([uuid, " | ".join(themen)])

for thema in THEMEN:
    print(f"{thema:28} {sum(thema in t for t in treffer.values())} Bilder")
print(f"\n{len(treffer)} Bilder mit mindestens einem der Themen")
print(f"\nGespeichert unter: {AUSGABE}")