#!/usr/bin/env python3
import os
import sys
from huggingface_hub import HfApi, InferenceClient, RepositoryNotFoundError

DEFAULT_MODEL = "meta-llama/Llama-3-8b-Instruct"

def main() -> int:
    token = os.getenv("HF_TOKEN")
    if not token:
        print("Переменная окружения HF_TOKEN не найдена. Установите её и повторите попытку.")
        return 1

    model_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    api = HfApi(token=token)

    info = api.whoami()
    print(f"Успешно аутентифицированы как: {info.get('name') or info.get('orgs', [''])[0]}")


    try:
        model_info = api.model_info(model_id)
        print(f"Модель `{model_info.modelId}` доступна. Последнее обновление: {model_info.lastModified}")
    except RepositoryNotFoundError:
        print(f"Модель `{model_id}` не найдена или недоступна для данного токена.")
        return 3

    # При необходимости можно раскомментировать блок ниже для пробного inference-запроса:
    """
    try:
        client = InferenceClient(model=model_id, token=token)
        test_output = client.text_generation("Проверка связи с моделью.", max_new_tokens=10)
        print("Inference-запрос выполнен успешно:", test_output)
    except Exception as err:
        print(f"Inference-запрос не удался: {err}")
        return 5
    """

    print("Проверка завершена успешно.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())