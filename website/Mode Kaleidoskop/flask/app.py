
from flask import Flask, render_template
import scripts.manageImages as im
from random import randint
import requests
import shutil
from pathlib import Path


app = Flask(__name__)

BILD_ORDNER = Path(__file__).resolve().parent / "static" / "images"

def bild_laden(bild_url, index):
    BILD_ORDNER.mkdir(parents=True, exist_ok=True)
    print()
    try:
        # Bild zuerst herunterladen
        response = requests.get(bild_url, timeout=30)
        response.raise_for_status()

        # Bild mit zweistelligem Index speichern
        bild_pfad = BILD_ORDNER / f"mode-{index:02d}.webp"
        bild_pfad.write_bytes(response.content)

        return True

    except requests.RequestException as e:
        print(f"Fehler beim Laden des Bildes: {e}")
        return False

def ordnerAufraeumen():
      # Alten Ordnerinhalt löschen
    for datei in BILD_ORDNER.iterdir():
        if datei.is_file() or datei.is_symlink():
            datei.unlink()
        elif datei.is_dir():
            shutil.rmtree(datei)

@app.route("/")
def home():
    return render_template("index.html", title="Home")

from flask import render_template, request

@app.route("/sammlung", methods=["GET", "POST"])
def sammlungClicked():
    kategorie = request.args.get("kategorie")
    if kategorie == "random":
        i = randint(0,3)
        kat = ["embedding", "farbe", "silhouette", "accessoires"]
        kategorie = kat[i]
        print(kategorie)
    if kategorie == "embedding":
        filterList = "Aehnlichkeiten"
        index = randint(0,2000)
    if kategorie == "farbe":
        filterList = "Farbe"
        index = randint(0,11200)
    if kategorie == "silhouette":
        filterList = "Silhouette"
        index = randint(0,2000)
    if kategorie == "accessoires":
        urls = im.sucheAccessoires(10)
    else:
        ids = im.getImagebyIndex(index, filterList, 10)
        urls = []
        for uuid in ids:
            url = im.loadImage(uuid)
            urls.append(url)
    for i in range(len(urls)):
        bild_laden(urls[i], i)
    
    return render_template(
        "sammlung.html",
        title="Sammlung",
        kategorie=kategorie
    )

if __name__ == "__main__":
    app.run(debug=True)
