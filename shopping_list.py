import requests
import json
from dotenv import load_dotenv
import os


def generate_shopping_list(api_key, day=None, ingredients=None):
    url = 'https://api.spoonacular.com/mealplanner/shopping-list/compute'
    params = {
        'apiKey': api_key,
    }
    headers = {
        'Content-Type': 'application/json'
    }
    json = ingredients
    response = requests.post(url, headers=headers, params=params,json=json)
    response.raise_for_status()
    shopping_list = response.json()
    parser_shopping_list(shopping_list, day)


def parser_shopping_list(shopping_list, day):
    parsered_shopping_list = []
    for ingredien in shopping_list["aisles"]:
        for name in ingredien['items']:
            parsered_ingredien = parser_ingredien(name)
            parsered_shopping_list.append(parsered_ingredien)
    parsered_shopping_list.append({"total cost": shopping_list["cost"]})
    with open(f'shopping_list/{day}.json', 'w') as file:
        json.dump(parsered_shopping_list, file)


def parser_ingredien(ingredien):
    parsered_ingredien = {}
    parsered_ingredien["name"] = ingredien["name"]
    parsered_ingredien["amount"] = ingredien["measures"]["metric"]["amount"]
    parsered_ingredien["unit"] = ingredien["measures"]["metric"]["unit"]
    parsered_ingredien["cost"] = ingredien["cost"]
    return parsered_ingredien


if __name__ == '__main__':
    load_dotenv()
    api_key = os.environ['SPOON_API']
    shopping_list = generate_shopping_list(api_key)
