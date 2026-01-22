from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import os
import json

app = Flask(__name__)

# ---------- FIREBASE (FROM ENV VARIABLE) ----------

firebase_json = os.environ.get("FIREBASE_KEY")
cred = credentials.Certificate(json.loads(firebase_json))
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------- WEATHER API (FROM ENV VARIABLE) ----------

WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")


@app.route("/", methods=["GET", "POST"])
def home():

    plants_ref = db.collection("plants").stream()
    plants = [doc.to_dict() for doc in plants_ref]

    if request.method == "POST":
        city = request.form["city"].strip()
        soil = request.form["soil"]
        water = request.form["water"]

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()

        if res.get("cod") != 200:
            return render_template("index.html", error=res.get("message", "City not found"))

        temp = res["main"]["temp"]
        humidity = res["main"]["humidity"]

        recommended = []
        for p in plants:
            if (p["minTemp"] <= temp <= p["maxTemp"] and
                p["soil"] == soil and
                p["water"] == water):
                recommended.append(p)

        tip = "Ensure regular maintenance and proper soil nutrition."
        if temp > 35:
            tip = "High temperature detected. Provide shade and frequent watering."
        elif temp < 15:
            tip = "Low temperature detected. Choose cold-resistant plants and reduce watering."

        return render_template(
            "index.html",
            city=city,
            soil=soil,
            water=water,
            temp=temp,
            humidity=humidity,
            recommended=recommended,
            tip=tip
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run()
