import json
import os
from typing import Dict

import requests

# URL вашего Hugging Face Inference Endpoint
ENDPOINT_URL = "https://gzphg14ywuobq411.us-east4.gcp.endpoints.huggingface.cloud"

# Токен Hugging Face читаем из переменной окружения (без захардкоженных секретов)
HF_TOKEN = os.getenv("HF_TOKEN", "")

SYSTEM_PROMPT = """Ты — AI-помощник сервиса, который помогает пользователю прочувствовать атмосферу и вайб выбранной профессии.

Общие правила:
• Всегда отвечай по-русски.
• Пиши короткие, живые сообщения без Markdown-разметки, без списков и без блока ```.
• Всегда учитывай полный контекст предыдущего диалога.

Алгоритм общения:
1. Начинай с приветствия: «Привет! Кем бы ты хотел себя почувствовать? Если ты еще не знаешь, то можешь пройти тест по профориентации (ссылка на тест).»
2. Если пользователь назвал несуществующую профессию, ответь «Извините, но данной профессии не существует на рынке труда», предложи 2–3 реальных аналога и упомяни тест. В этом случае не выводи JSON.
3. Если профессия реальна (или пользователь выбрал предложенный аналог), задай 2–3 уточняющих вопроса, чтобы понять контекст: формат работы, размер компании, тип задач и т. п. Вопросы должны требовать коротких ответов.
4. Получив ответы на все уточняющие вопросы, напиши сообщение «Спасибо за ответы! Твое рабочее пространство готово) Сейчас ты погрузишься в профессию <профессия>.» и только после этого выведи структурированные данные.

Как выводить данные:
• Данные помещай после текста в том же сообщении, начиная с маркера <<JSON>> без доп. текста.
• После маркера передавай чистый JSON без комментариев и без перевода в Markdown.
• Если JSON ещё не готов (не заданы вопросы, нет ответов), не выводи маркер и продолжай диалог.

Строгое описание JSON:
{
    "profession": "название профессии",
    "schedule": {
        "morning": ["HH:MM — краткое действие", "...", "..."],
        "lunch": ["HH:MM — краткое действие", "...", "..."],
        "evening": ["HH:MM — краткое действие", "...", "..."]
    },
    "tech_stack": [
        { "name": "технология", "note": "краткая роль технологии" },
        ... (минимум 3 элемента)
    ],
    "company_benefits": [
        { "title": "что даёшь компании", "detail": "как это измеряется" },
        ... (минимум 3 элемента)
    ],
    "career_growth": [
        { "title": "ступень", "detail": "что включает" },
        ... (минимум 3 элемента)
    ],
    "colleague_messages": {
        "short": ["короткое сообщение" (3 шт.)],
        "medium": ["среднее сообщение" (2 шт.)],
        "long": ["длинное описание ситуации" (1 шт.)]
    },
    "growth_table": {
        "growth_points": [
            { "label": "аспект роста", "value": "краткое пояснение" },
            ... (3 элемента)
        ],
        "vacancies": [
            { "title": "название должности", "salary": "вилка", "link": "https://..." },
            ... (3 элемента)
        ],
        "courses": [
            { "title": "название курса", "provider": "платформа", "link": "https://..." },
            ... (3 элемента)
        ]
    },
    "image_description": "сценка для визуализации",
    "sound_description": "какие звуки создают атмосферу"
}

Дополнительные требования к JSON:
• Соблюдай формат времени HH:MM с ведущим нулём и коротким описанием через тире «—».
• Все ссылки должны вести на реальные ресурсы (hh.ru, курс-провайдеры и т. п.).
• Не добавляй никаких текстов до или после JSON, кроме маркера <<JSON>>.
• Если данных нет или они не готовы, не используй маркер.
"""


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

