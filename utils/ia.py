
from dotenv import load_dotenv
load_dotenv()

import os
import base64
import requests

from utils.logging_utils import log_error

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_text_in_photo(image_path):
    text = ""
    try:
        base64_image = encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": "Encuentra texto en la foto del producto y regresa su nombre y contenido en gramos o mililitros en formato JSON, también incluye la cantidad estimada de productos que se ve en la foto {\"name\": \"\", \"content\": \"\", \"quantity\": \"\"}"
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": 300
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        res_j = response.json()
        text = res_j["choices"][0]["message"]["content"]
    except Exception as e:
        log_error(e)

    return text


def get_products_in_photo(image_path, names):
    text = ""
    try:
        base64_image = encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Sólo retorna el arreglo JSON. Determina los productos de tienda que se ven en la foto y regrésalos como una lista de objetos JSON {\"name\": \"\", \"description\": \"\", \"quantity\": \"\"}. Los nombres que ya están en la lista son: "+', '.join(names)+", en caso de encontrar un producto con ese mismo nombre, úsalo."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
                }
            ],
            "max_tokens": 300
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        res_j = response.json()
        text = res_j["choices"][0]["message"]["content"]
    except Exception as e:
        log_error(e)

    return text