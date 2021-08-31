import requests


def convert_to_rubles(dollars):
    response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
    rate = response.json()["Valute"]["USD"]["Value"]
    rubles = round(float(dollars) * rate / 100, 2)
    return rubles


