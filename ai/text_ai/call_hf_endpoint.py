import json
import os
from typing import Dict

import requests

# URL вашего Hugging Face Inference Endpoint
ENDPOINT_URL = "https://gzphg14ywuobq411.us-east4.gcp.endpoints.huggingface.cloud"

# Токен Hugging Face читаем из переменной окружения (без захардкоженных секретов)
HF_TOKEN = os.getenv("HF_TOKEN", "")

SYSTEM_PROMPT = """Ты генерируешь данные о профессии пользователя. Предварительно надо задать ему один вопрос 
    Сгенерируй следующие данные в формате JSON:
    {
        "profession": "название профессии",
        "schedule": {
            "morning": ["активность 1 с временем", "активность 2 с временем", "активность 3 с временем"],
            "lunch": ["активность 1 с временем", "активность 2 с временем", "активность 3 с временем"],
            "evening": ["активность 1 с временем", "активность 2 с временем", "активность 3 с временем"]
        },
        "tech_stack": ["технология1", "технология2", "технология3"],
        "company_benefits": ["польза1", "польза2", "польза3"],
        "career_growth": ["путь1", "путь2", "путь3"],
        "colleague_messages": {
            "short": ["сообщение1", "сообщение2", "сообщение3"],
            "medium": ["сообщение1", "сообщение2"],
            "long": ["длинное сообщение"]
        },
        "growth_table": {
            "growth_points": ["точка1", "точка2", "точка3"],
            "vacancies": ["вакансия1", "вакансия2", "вакансия3"],
            "courses": ["курс1", "курс2", "курс3"]
        },
        "image_description": "описание картинки",
        "sound_description": "описание звука"
    }
    
    Сгенерируй реалистичные данные для случайной IT-профессии. в распорядке дня мероприятий обязательно ровно 9 (формат: время - задача), они описаны коротко. сообщения коллег чередуются формальные с неформальными (но связанные с работой, возможно в шутливой форме). профессии могут быть абсолютно из лбых сфер, не обязательно IT. Формируй JSON на основе диалога с пользователем"""


def _compose_prompt(user_prompt: str) -> str:
    user_prompt = user_prompt.strip()
    if not user_prompt:
        return SYSTEM_PROMPT
    return f"{SYSTEM_PROMPT}\n\n{user_prompt}"


def generate(
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True,
) -> Dict:
    """
    Отправляет запрос к Hugging Face Inference Endpoint.
    """
    headers = {
        "Content-Type": "application/json",
    }

    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    payload = {
        "inputs": _compose_prompt(prompt),
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": do_sample,
        },
    }

    try:
        response = requests.post(
            ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP ошибка: {e}")
        print(f"Ответ сервера: {response.text}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        raise


def chat(
    messages: list[Dict[str, str]],
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> Dict:
    """
    Отправляет диалоговый запрос к endpoint.
    """
    conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    conversation += "\nassistant:"

    return generate(
        prompt=conversation,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
    )


def demo_simple():
    """Простой пример использования"""
    print("=" * 60)
    print("Тест простого запроса")
    print("=" * 60)

    result = generate("Привет! Кратко расскажи о Python.", max_new_tokens=200)

    print("\nОтвет:")
    if isinstance(result, dict) and "generated_text" in result:
        print(result["generated_text"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def demo_chat():
    """Пример диалога"""
    print("=" * 60)
    print("Тест диалога")
    print("=" * 60)

    messages = [
        {"role": "user", "content": "Что такое машинное обучение?"},
    ]

    result = chat(messages, max_new_tokens=300)

    print("\nОтвет:")
    if isinstance(result, dict) and "generated_text" in result:
        print(result["generated_text"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def demo_multiple():
    """Несколько запросов подряд"""
    print("=" * 60)
    print("Тест нескольких запросов")
    print("=" * 60)

    prompts = [
        "Что такое нейронные сети?",
        "Объясни квантовые вычисления простыми словами.",
        "Расскажи про преимущества Python.",
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"\n--- Запрос {i} из {len(prompts)} ---")
        print(f"Вопрос: {prompt}")

        result = generate(prompt, max_new_tokens=150)

        if isinstance(result, dict) and "generated_text" in result:
            print(f"Ответ: {result['generated_text']}")
        else:
            print(f"Результат: {json.dumps(result, ensure_ascii=False)}")

        print("-" * 60)


def test_endpoint():
    """Тестирование доступности endpoint"""
    print("=" * 60)
    print("Проверка доступности endpoint")
    print("=" * 60)

    headers = {"Content-Type": "application/json"}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    try:
        # Простой тестовый запрос
        payload = {"inputs": "Тест"}
        response = requests.post(
            ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"Статус код: {response.status_code}")
        print(f"Ответ: {response.text[:500]}")  # Первые 500 символов

        if response.status_code == 200:
            print("✅ Endpoint доступен и работает!")
        else:
            print("❌ Endpoint вернул ошибку")

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            test_endpoint()
        elif command == "chat":
            demo_chat()
        elif command == "multiple":
            demo_multiple()
        else:
            # Использование как CLI инструмент
            prompt = " ".join(sys.argv[1:])
            result = generate(prompt)
            if isinstance(result, dict) and "generated_text" in result:
                print(result["generated_text"])
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Запуск всех демо
        test_endpoint()
        print("\n")
        demo_simple()
        print("\n")
        demo_chat()

