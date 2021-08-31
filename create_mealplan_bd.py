import os
import requests
import re
import json
import pathlib
import datetime

from translations import get_translation
from dotenv import load_dotenv
from shopping_list import generate_shopping_list
from exchange import convert_to_rubles


def generate_meal_plan(api_key, calories):
    url = f'https://api.spoonacular.com/mealplanner/generate'
    params = {
        'apiKey': api_key,
        'timeFrame': 'week',
        'targetCalories': calories,
        'exclude': 'alcohol'

    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    meal_plan = response.json()
    return meal_plan


def save_meal_plans(filepath, meal_plan):
    with open(filepath, 'w') as file:
        json.dump(meal_plan, file)


def load_meal_plans(filepath):
    with open(filepath) as json_file:
        meal_plans = json.load(json_file)
        return meal_plans


def parse_meal_plans(meal_plans):
    parsed_meal_plans = {}
    for number, day in enumerate(meal_plans['week'], 1):
        meals = meal_plans['week'][day]['meals']
        id = []
        for recipe in meals:
            id.append(recipe['id'])
            parsed_meal_plans[day] = id
    return parsed_meal_plans


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def create_bd(filepath, week_days):
    week_meal_plan = load_meal_plans(filepath)
    week_meal_plan = parse_meal_plans(week_meal_plan)
    daily_recipes = {}
    for number, day in enumerate(week_meal_plan):
        daily_recipes[week_days[number]] = get_daily_recipes(
            week_meal_plan[day])
        get_daily_recipes(week_meal_plan[day])
        with open(f'mealplans/{week_days[number]}.json', 'w') as file:
            json.dump(get_daily_recipes(week_meal_plan[day]), file)


def get_daily_recipes(daily_recipes_id):
    recipes = []
    for number, recipe in enumerate(daily_recipes_id):
        recipe_id = daily_recipes_id[number]
        recipe = get_recipe(api_key, recipe_id)
        recipes.append(recipe)
    return recipes


def get_recipe(api_key, resipe_id):
    url = f"https://api.spoonacular.com/recipes/{resipe_id}/information"
    params = {
        "apiKey": api_key,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    recipe = response.json()
    resipe = parser_recipe(recipe)
    return resipe


def parser_recipe(recipe):  # new
    parsered_resipe = {}
    parsered_resipe["title"] = recipe["title"]
    parsered_resipe["summary"] = clean_html(recipe["summary"])
    steps = recipe["analyzedInstructions"][0]["steps"]
    for step in steps:
        parsered_resipe["steps"] = [f"{step['number']}. {step['step']}" for
                                    step in steps]
    parsered_resipe["extendedIngredients"] = [ingredient["originalString"] for
                                              ingredient in
                                              recipe["extendedIngredients"]]
    parsered_resipe["pricePerServing"] = recipe["pricePerServing"]
    return parsered_resipe


def create_ingredients_list(week_days):  # new
    all_ingredients = []
    for day in week_days:
        with open(f"mealplans/{day}.json") as json_file:
            json_day_ingredients = json.load(json_file)
            ingredients = []
            for resipe in json_day_ingredients:
                ingredients += resipe["extendedIngredients"]
            all_ingredients += ingredients
            day_ingredients = {"items": ingredients}
            pathlib.Path('shopping_list').mkdir(parents=True, exist_ok=True)
            generate_shopping_list(api_key, day, day_ingredients)
    week_ingredients = {"items": all_ingredients}
    generate_shopping_list(api_key, "week_shopping_list", week_ingredients)


def get_instruction():
    print('Введите, что вас интересует:')
    print('Меню – ваше меню на неделю')
    print('Рецепты – ваши рецепты на весь день')
    print('Покупки – ваш план покупок на день')
    answer = input().lower()
    return answer


def check_existence_plan(filepath, week, api_key, calories):
    while True:
        generate_plan = input('Сгенерировать новый план?(Да/Нет)').lower()
        if generate_plan == 'да':
            print('Пожалуйста подождите, план уже генерируется(это может занять до 10 минут)')
            meal_plan = generate_meal_plan(api_key, calories)
            save_meal_plans(filepath, meal_plan)
            create_bd(filepath, week)
            create_ingredients_list(week)
            break
        if generate_plan == 'нет' and not os.path.exists(filepath):
            print('Пожалуйста сгенерируйте план на неделю')
            continue
        if generate_plan == 'нет' and os.path.exists(filepath):
            break
        else:
            print('Неправильный ввод')


def check_instructions(answer, folder, filepath, week):
    date = datetime.datetime.now()
    now_day = get_translation(date.strftime('%A').lower())
    while True:
        if answer == 'меню':
            return show_mealplans(week, filepath)

        if answer == 'рецепты':
            day = input('Введите день (выбрать сегодня enter):').lower()
            if day in week:
                filepath = os.path.join(folder, f'{day}.json')
                return show_recipes(filepath)
            else:
                filepath = os.path.join(folder, f'{now_day}.json')
                return show_recipes(filepath)

        if answer == 'покупки':
            products_folder = 'shopping_list'
            print('Введите:')
            print(
                'Любой день недели, что-бы увидеть покупки на определенный день')
            print('Неделя – выведет покупки на неделю')
            day = input('Если хотите выбрать сегодня нажмите enter').lower()
            if day == 'неделя':
                filepath = os.path.join(
                    products_folder,
                    'week_shopping_list.json'
                )
                return show_products(filepath)
            if day in week:
                filepath = os.path.join(products_folder, f'{day}.json')
                return show_products(filepath)
            else:
                filepath = os.path.join(products_folder, f'{now_day}.json')
                return show_products(filepath)
        else:
            print('Проверьте правильность ввода')
            answer = input().lower()


def get_plan(file):
    with open(file) as json_file:
        meals = json.load(json_file)
        return meals


def show_products(filepath):
    meals = get_plan(filepath)
    for x in meals[:-1]:
        print(
            f'{get_translation(x["name"])}  {x["amount"]} {x["unit"]}  Цена: {convert_to_rubles(x["cost"])} p.')
    print(f'Общая цена {convert_to_rubles(meals[-1]["total cost"])} p.')


def show_mealplans(week, filepath):
    meals = get_plan(filepath)
    for number, day in enumerate(meals['week']):
        print(week[number].upper())
        for x in meals['week'][day]['meals']:
            print(get_translation(x['title']))
        print()


def show_recipes(filepath):
    meals = get_plan(filepath)

    diet = ['ЗАВТРАК', 'ОБЕД', 'УЖИН']
    for number, meal in enumerate(meals):
        print()
        print()
        print(diet[number])
        print('Блюдо:', get_translation(meal['title']))
        print()
        print('Описание блюда:')
        print(get_translation(meal['summary']))
        print()
        print('Описание приготовления:')
        for step in meal["steps"]:
            print(get_translation(step))
        print()
        print('Необходимые ингредиенты:')
        for ingredient in meal['extendedIngredients']:
            print(get_translation(ingredient))
        print()
        print('Стоимость продуктов:')
        print(get_translation(meal["pricePerServing"]), 'р')


if __name__ == '__main__':
    load_dotenv()
    api_key = os.environ['SPOON_API']

    week = [
        'понедельник', 'вторник',
        'среда', 'четверг', 'пятница',
        'суббота', 'воскресенье'
    ]
    calories = '2000'
    filename = 'mealplans.json'
    folder = 'mealplans'
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(folder, f'{filename}')

    check_existence_plan(filepath, week, api_key, calories)
    answer = get_instruction()
    check_instructions(answer, folder, filepath, week)
