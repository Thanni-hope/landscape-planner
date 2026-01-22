from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore
import requests

app = Flask(__name__)

# 🔐 Firebase connection
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

WEATHER_API_KEY = "dd26e4f58a324b64702009cc22ec42bf"


@app.route("/", methods=["GET", "POST"])
def home():

    # Fetch plants from Firestore
    plants_ref = db.collection("plants").stream()
    plants = [doc.to_dict() for doc in plants_ref]

    if request.method == "POST":

        lat = request.form.get("lat")
        lon = request.form.get("lon")
        soil = request.form.get("soil")
        water = request.form.get("water")
        city = request.form.get("city")

        if not lat or not lon:
            return render_template("index.html", error="Please select location on map.")

        # 🌦 WEATHER
        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        )
        res = requests.get(weather_url).json()

        if res.get("main") is None:
            return render_template("index.html", error="Weather data not available.")

        temp = res["main"]["temp"]
        humidity = res["main"]["humidity"]

        # 🌱 SOILGRIDS
        soil_url = (
            "https://rest.isric.org/soilgrids/v2.0/properties/query"
            f"?lat={lat}&lon={lon}"
            "&property=phh2o&property=ocd&property=clay"
            "&depth=0-5cm&value=mean"
        )

        headers = {"User-Agent": "Mozilla/5.0 (LandscapePlanner/1.0)"}
        soil_res = {}

        try:
            r = requests.get(soil_url, headers=headers, timeout=10)
            if r.status_code == 200:
                soil_res = r.json()
        except:
            pass

        ph = "N/A"
        organic_carbon = "N/A"
        clay = "N/A"

        try:
            layers = soil_res.get("properties", {}).get("layers", [])
            for layer in layers:
                if layer["name"] == "phh2o":
                    ph = round(layer["depths"][0]["values"]["mean"] / 10, 2)
                if layer["name"] == "ocd":
                    organic_carbon = round(layer["depths"][0]["values"]["mean"], 2)
                if layer["name"] == "clay":
                    clay = round(layer["depths"][0]["values"]["mean"], 2)
        except:
            pass

        # 🌱 RECOMMENDATIONS
        recommended = []
        for p in plants:
            if (
                p["minTemp"] <= temp <= p["maxTemp"]
                and p["soil"] == soil
                and p["water"] == water
            ):
                recommended.append(p)

        # 🌡 DESIGN TIPS
        tips = []
        if temp > 35:
            tips.append("Use shade trees and pergolas to reduce heat.")
        if water == "low":
            tips.append("Use drought-resistant plants and drip irrigation.")
        if soil == "sandy":
            tips.append("Add compost to improve soil moisture retention.")
        if not tips:
            tips.append("Maintain regular pruning and organic mulching.")

        return render_template(
            "index.html",
            temp=temp,
            humidity=humidity,
            recommended=recommended,
            tips=tips,
            city=city,
            soil=soil,
            water=water,
            ph=ph,
            organic_carbon=organic_carbon,
            clay=clay,
            lat=lat,
            lon=lon
        )

    return render_template("index.html")
    

if __name__ == "__main__":
    app.run(debug=True)
