
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", title="Home")

from flask import render_template, request

@app.route("/sammlung", methods=["GET", "POST"])
def sammlungClicked():
    kategorie = request.args.get("kategorie")

    return render_template(
        "sammlung.html",
        title="Sammlung",
        kategorie=kategorie
    )

if __name__ == "__main__":
    app.run(debug=True)
