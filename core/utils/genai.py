from core.settings import settings

import google.generativeai as genai
import random

genai.configure(api_key=settings.genai.api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

temperature_choices = [0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2]


def gpt_thinks(prompt: str):
    temperature = random.choice(temperature_choices)
    generation_config = genai.GenerationConfig(
            max_output_tokens=512,
            temperature=temperature,
    )
    
    response = model.generate_content(prompt, generation_config=generation_config)
    if response and response.text:
        return response.text
    else:
        return 'Ошибка запроса'