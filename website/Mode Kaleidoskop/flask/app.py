
from flask import Flask, render_template
import scripts.manageImages as im
from random import randint

app = Flask(__name__)


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
        
        ids = im.getImagebyIndex(index, filterList, 5)
        print(ids)
        urls = []
        for uuid in ids:
            url = im.loadImage(uuid)
            urls.append(url)
    print(urls)
    return render_template(
        "sammlung.html",
        title="Sammlung",
        kategorie=kategorie
    )

if __name__ == "__main__":
    app.run(debug=True)
