import json
from pathlib import Path

def getImagebyIndex(index, filter, offset):
    datei = Path(__file__).parent.parent/ "data"/ "index.json"
    with open(datei, "r", encoding="utf-8") as f:
                    daten = json.load(f)

    filterlist = daten["Filter"][filter]
    return filterlist[index-offset:index+offset+1]

def loadImage(id, type):
    ordner = Path(__file__).parent.parent/ "data"/ "images"
    dateiliste = []
    for datei in ordner.glob("*.json"):
        try:
            with open(datei, "r", encoding="utf-8") as f:
                daten = json.load(f)
            
            if daten.get("Identifikator") == id:
                if daten.get("Type") == type:
                    dateiliste.append(daten)

        except (json.JSONDecodeError, OSError) as e:
            print(f"Fehler bei {datei.name}: {e}")
    return dateiliste

print(getImagebyIndex(4,"Farbe",3))
print(loadImage("FILTER_005", "Filter"))