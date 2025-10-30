import json
import os
from typing import Dict, List, Any
from pathlib import Path


def load_json_file(filepath: str) -> Dict[str, Any]:
    """
    Загружает JSON файл
    
    Args:
        filepath: Путь к JSON файлу
    
    Returns:
        Словарь с данными из JSON файла или None в случае ошибки
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке {filepath}: {e}")
        return None


def find_all_data_files(base_folder: str = "parsed_jobs") -> List[tuple]:
    """
    Находит все файлы data.json в папках профессий
    
    Args:
        base_folder: Базовая папка с данными
    
    Returns:
        Список кортежей (путь_к_файлу, название_профессии)
    """
    data_files = []
    
    if not os.path.exists(base_folder):
        print(f"Папка {base_folder} не найдена!")
        return data_files
    
    # Проходим по всем папкам в parsed_jobs
    for folder_name in os.listdir(base_folder):
        folder_path = os.path.join(base_folder, folder_name)
        
        # Проверяем, что это папка
        if os.path.isdir(folder_path):
            data_file = os.path.join(folder_path, "data.json")
            
            # Проверяем, существует ли data.json
            if os.path.exists(data_file):
                data_files.append((data_file, folder_name))
    
    return data_files


def merge_all_vacancies(base_folder: str = "parsed_jobs", output_file: str = "all_vacancies.json") -> Dict[str, Any]:
    """
    Объединяет все вакансии из всех папок в один большой JSON файл
    
    Args:
        base_folder: Базовая папка с данными
        output_file: Имя выходного файла
    
    Returns:
        Словарь с объединенными данными
    """
    print("="*60)
    print("ОБЪЕДИНЕНИЕ ВСЕХ JSON ФАЙЛОВ")
    print("="*60)
    
    # Находим все файлы data.json
    data_files = find_all_data_files(base_folder)
    
    if not data_files:
        print(f"\n❌ Не найдено ни одного файла data.json в папке {base_folder}")
        return {}
    
    print(f"\nНайдено {len(data_files)} файлов для объединения:")
    for filepath, profession in data_files:
        print(f"  - {profession}")
    
    # Объединяем данные
    merged_data = {
        "total_professions": len(data_files),
        "total_vacancies": 0,
        "professions": {},
        "all_vacancies": []
    }
    
    all_vacancies_dict = {}  # Словарь для удаления дубликатов по ID
    
    print("\nЗагружаю и объединяю данные...")
    
    for filepath, profession in data_files:
        data = load_json_file(filepath)
        
        if not data:
            continue
        
        profession_name = data.get("profession", profession)
        vacancies = data.get("vacancies", [])
        count = data.get("count", len(vacancies))
        
        # Добавляем данные по профессии
        merged_data["professions"][profession_name] = {
            "count": count,
            "source_folder": profession
        }
        
        # Добавляем вакансии (удаляем дубликаты по ID)
        for vacancy in vacancies:
            vacancy_id = vacancy.get("id")
            if vacancy_id:
                # Если вакансия с таким ID еще не добавлена, добавляем её
                if vacancy_id not in all_vacancies_dict:
                    all_vacancies_dict[vacancy_id] = vacancy
                    merged_data["all_vacancies"].append(vacancy)
        
        print(f"  {profession_name}: {count} вакансий")
    
    merged_data["total_vacancies"] = len(merged_data["all_vacancies"])
    
    # Сохраняем объединенный файл
    print(f"\nСохраняю объединенные данные в {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("СТАТИСТИКА ОБЪЕДИНЕНИЯ")
    print("="*60)
    print(f"Всего профессий: {merged_data['total_professions']}")
    print(f"Всего уникальных вакансий: {merged_data['total_vacancies']}")
    print(f"\nПо профессиям:")
    for prof_name, prof_data in merged_data["professions"].items():
        print(f"  - {prof_name:30} {prof_data['count']:5} вакансий")
    print(f"\n✅ Объединенный файл сохранен: {output_file}")
    print("="*60)
    
    return merged_data


def main():
    """
    Основная функция для объединения JSON файлов
    """
    # Объединяем все вакансии
    result = merge_all_vacancies(
        base_folder="parsed_jobs",
        output_file="all_vacancies.json"
    )
    
    return result


if __name__ == "__main__":
    main()





