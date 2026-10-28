import json
from pathlib import Path
import random

from pathlib import Path
import json

def getSpecial(id):
    special = ["Kind", "Sport", "Verkleidung", "Maskierung"]
    ordner = Path(__file__).parent.parent / "data" / "metadata_jsons" / "json_output"
    datei = ordner / f"{id}.json"
    
    with open(datei, "r", encoding="utf-8") as f:
        daten = json.load(f)

    treffer = [element for element in daten["Thema"] if element in special]

    if len(treffer):
        return treffer[0]

    return "NA"
    

def getImagebyIndex(index, filter, offset):
    datei = Path(__file__).parent.parent / "data" / "index.json"

    with open(datei, "r", encoding="utf-8") as f:
        daten = json.load(f)


    filterlist = daten["Filter"][filter]

    special = getSpecial(filterlist[index])
    if special != "NA":
        if special == "Verkleidung":
            special = "Maskierung"
        dateiSpecial = Path(__file__).parent.parent / "data" / f"{special}Filter.json"
        
        with open(dateiSpecial, "r", encoding="utf-8") as f:
            datenSpecial = json.load(f)
        
        filterlistSpecial = datenSpecial["Filter"][filter]
        start = max(0, index - 4)
        ende = min(len(filterlistSpecial), index + 4 + 1)
        ergebnis = filterlistSpecial[start:ende]

        startNeu = max(0, index - offset + 4)
        endeNeu = min(len(filterlist), index + offset + 1 - 4)

        ergebnis = filterlist[startNeu : index] + ergebnis + filterlist[index + 1: endeNeu]

    else:
        start = max(0, index - offset)
        ende = min(len(filterlist), index + offset + 1)

        ergebnis = filterlist[start:ende]

    ziel_laenge = 2 * offset + 1

    if filter == "Farbe" or special != "NA":
        ergebnis = list(dict.fromkeys(ergebnis))

        while (
            len(ergebnis) < ziel_laenge
            and (start > 0 or ende < len(filterlist))
        ):
            if start > 0:
                start -= 1

            if ende < len(filterlist):
                ende += 1

            ergebnis = list(dict.fromkeys(filterlist[start:ende]))

    return ergebnis[:ziel_laenge]

def loadImage(id):
    ordner = Path(__file__).parent.parent / "data" / "metadata_jsons" / "json_output"
    datei = ordner / f"{id}.json"

    with open(datei, "r", encoding="utf-8") as f:
        daten = json.load(f)

    return daten["URL"]


    
def sucheWeitereAccessoires(wert, anz, eigene_id=None):
    treffer = []

    ordner = (
        Path(__file__).parent.parent
        / "data" / "metadata_jsons" / "json_output"
    )

    dateien = list(ordner.glob("*.json"))

    # Startposition der ausgewählten Datei finden
    start_index = 0

    if eigene_id is not None:
        for i, datei in enumerate(dateien):
            if datei.stem == str(eigene_id):
                start_index = i + 1
                break

    # Nur die nachfolgenden Dateien durchsuchen
    for datei in dateien[start_index:]:
        with open(datei, "r", encoding="utf-8") as f:
            daten = json.load(f)

        accessoires = daten.get("accessoires", [])

        if isinstance(accessoires, list) and wert in accessoires:
            if "URL" in daten:
                treffer.append(daten["URL"])

        if len(treffer) >= anz:
            break

    return treffer


def sucheAccessoires(anz, id=None):
    ordner = (
        Path(__file__).parent.parent
        / "data" / "metadata_jsons" / "json_output"
    )

    if id is None:
        # Zufällige JSON-Datei auswählen
        dateien = list(ordner.glob("*.json"))

        if not dateien:
            return []

        random.shuffle(dateien)

        daten = None
        datei = None

        # Zufällige Reihenfolge durchprobieren,
        # bis eine Datei mit Accessoires gefunden wird
        for pfad in dateien:
            with open(pfad, "r", encoding="utf-8") as f:
                temp = json.load(f)

            accessoires = temp.get("accessoires")

            if isinstance(accessoires, list) and accessoires:
                daten = temp
                datei = pfad
                break

        if daten is None:
            return []

    else:
        datei = ordner / f"{id}.json"

        if not datei.exists():
            return []

        with open(datei, "r", encoding="utf-8") as f:
            daten = json.load(f)

        accessoires = daten.get("accessoires")

        if not isinstance(accessoires, list) or not accessoires:
            return []

    wert = daten["accessoires"][0]

    treffer = sucheWeitereAccessoires(
        wert,
        anz,
        eigene_id=datei.stem
    )

    if "URL" in daten:
        treffer.insert(0, daten["URL"])

    return treffer


if __name__ == "__main__":
    print(getImagebyIndex(4,"Farbe",3))
    print(loadImage("FILTER_005", "Filter"))