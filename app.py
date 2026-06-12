from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)


def generate_summary(rain, sunny, cold):

    if rain >= 60:
        return "High chance of rainfall. Carry an umbrella."

    elif sunny >= 60:
        return "Weather is likely to be sunny and suitable for outdoor activities."

    elif cold >= 60:
        return "Historically this date has been relatively cold. Consider warm clothing."

    else:
        return "Weather conditions appear mixed based on historical records."


def get_coordinates(city):

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"

    response = requests.get(url).json()

    if "results" not in response:
        return None

    return (
        response["results"][0]["latitude"],
        response["results"][0]["longitude"]
    )


def get_weather_probabilities(city, target_date):

    coordinates = get_coordinates(city)

    if coordinates is None:
        return None

    latitude, longitude = coordinates

    target = datetime.strptime(target_date, "%Y-%m-%d")
    month_day = target.strftime("%m-%d")

    rainy_years = 0
    sunny_years = 0
    cold_years = 0

    years_checked = 0

    current_year = datetime.now().year

    for year in range(current_year - 5, current_year):

        date_str = f"{year}-{month_day}"

        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={latitude}"
            f"&longitude={longitude}"
            f"&start_date={date_str}"
            f"&end_date={date_str}"
            f"&daily=temperature_2m_mean,precipitation_sum"
            f"&timezone=auto"
        )

        try:

            response = requests.get(url, timeout=10)
            data = response.json()

            if "daily" not in data:
                continue

            temp = data["daily"]["temperature_2m_mean"][0]
            rain = data["daily"]["precipitation_sum"][0]

            years_checked += 1

            if rain > 0:
                rainy_years += 1
            else:
                sunny_years += 1

            if temp < 18:
                cold_years += 1

        except Exception as e:
            print("API Error:", e)

    if years_checked == 0:
        return None

    rain_prob = round((rainy_years / years_checked) * 100, 2)
    sunny_prob = round((sunny_years / years_checked) * 100, 2)
    cold_prob = round((cold_years / years_checked) * 100, 2)

    summary = generate_summary(
        rain_prob,
        sunny_prob,
        cold_prob
    )

    result = {
        "rain": rain_prob,
        "sunny": sunny_prob,
        "cold": cold_prob,
        "summary": summary
    }

    print(result)

    return result


@app.route("/", methods=["GET", "POST"])
def home():

    result = None
    error = None

    if request.method == "POST":

        city = request.form["city"]
        date = request.form["date"]

        result = get_weather_probabilities(city, date)

        if result is None:
            error = "Unable to fetch weather history for this city."

    return render_template(
        "index.html",
        result=result,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)