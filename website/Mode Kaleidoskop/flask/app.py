
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", title="Home")

from flask import render_template, request

@app.route("/sammlung", methods=["GET", "POST"])
def sammlungClicked():
    if request.method == "POST":
        # Hier kannst du deine zusätzlichen Funktionen ausführen
        print("Button wurde geklickt!")

    return render_template("sammlung.html", title="Sammlung")



if __name__ == "__main__":
    app.run(debug=True)
