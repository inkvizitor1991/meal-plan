import os
import deepl_api

from dotenv import load_dotenv


load_dotenv()
deepl_api_key = os.environ['TRANSLATOR_API']

def get_translation(text):
    deepl = deepl_api.DeepL(deepl_api_key)
    translations = deepl.translate(source_language="EN", target_language="RU", texts=[text])
    return translations[0]['text']




