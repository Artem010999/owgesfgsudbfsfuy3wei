import json
import os
from typing import Dict, Optional

import requests

# URL вашего Hugging Face Inference Endpoint
ENDPOINT_URL = "https://gzphg14ywuobq411.us-east4.gcp.endpoints.huggingface.cloud"

# Токен Hugging Face теперь читаем из переменной окружения
HF_TOKEN = os.getenv("HF_TOKEN", "")

def generate(
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True,
) -> Dict:
    """
    Отправляет запрос к Hugging Face Inference Endpoint.
    
    Args:
        prompt: Текст для генерации
        max_new_tokens: Максимальное количество новых токенов
        temperature: Температура для генерации
        top_p: Top-p параметр для nucleus sampling
        do_sample: Использовать ли sampling
    
    Returns:
        Словарь с результатом генерации
    """
    headers = {
        "Content-Type": "application/json",
    }
    
    # Добавляем токен, если указан
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    
    # Формируем payload согласно формату handler.py
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": do_sample,
        }
    }
    
    try:
        response = requests.post(
            ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=300  # 5 минут таймаут для больших моделей
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
    
    Args:
        messages: Список сообщений в формате [{"role": "user", "content": "текст"}]
        max_new_tokens: Максимальное количество новых токенов
        temperature: Температура для генерации
        top_p: Top-p параметр
    
    Returns:
        Словарь с результатом генерации
    """
    # Формируем промпт из сообщений
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    prompt += "\nassistant:"
    
    return generate(
        prompt=prompt,
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

