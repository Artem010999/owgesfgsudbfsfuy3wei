from typing import List, Dict, Any, Optional

import requests
import json
import time
import os


def get_vacancies(query: str, page: int = 0, per_page: int = 100, area: Optional[int] = None, date_from: Optional[str] = None) -> Dict[str, Any]:
    """
    Получает вакансии с HeadHunter API
    
    Args:
        query: Поисковый запрос (название профессии)
        page: Номер страницы (по умолчанию 0)
        per_page: Количество вакансий на странице (максимум 100)
        area: ID региона (например, 1 - Москва, 2 - СПб, 113 - Россия)
        date_from: Дата публикации от (формат: YYYY-MM-DD)
    
    Returns:
        Словарь с данными о вакансиях
    """
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": query,
        "page": page,
        "per_page": per_page,
    }

    if area:
        params["area"] = area
    if date_from:
        params["date_from"] = date_from
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as exception:
        print(f"Ошибка при запросе для '{query}': {exception}")

        return {}


def parse_vacancy(vacancy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Парсит данные одной вакансии в удобный формат

    Args:
        vacancy: Словарь с данными вакансии от API

    Returns:
        Отформатированный словарь с данными вакансии
    """
    salary, salary_info = vacancy.get("salary"), None
    if salary:
        salary_from, salary_to, currency = salary.get("from"), salary.get("to"), salary.get("currency", "")

        if salary_from and salary_to:
            salary_info = f"{salary_from:,} - {salary_to:,} {currency}"
        elif salary_from:
            salary_info = f"от {salary_from:,} {currency}"
        elif salary_to:
            salary_info = f"до {salary_to:,} {currency}"

    employer = vacancy.get("employer", {})

    return {
        "id": vacancy.get("id"),
        "name": vacancy.get("name"),
        "employer": {
            "name": employer.get("name"),
            "id": employer.get("id"),
        },
        "salary": salary_info,
        "salary_raw": salary,
        "area": vacancy.get("area", {}).get("name") if vacancy.get("area") else None,
        "experience": vacancy.get("experience", {}).get("name") if vacancy.get("experience") else None,
        "schedule": vacancy.get("schedule", {}).get("name") if vacancy.get("schedule") else None,
        "employment": vacancy.get("employment", {}).get("name") if vacancy.get("employment") else None,
        "published_at": vacancy.get("published_at"),
        "url": vacancy.get("alternate_url") or vacancy.get("url"),
        "snippet": {
            "requirement": vacancy.get("snippet", {}).get("requirement"),
            "responsibility": vacancy.get("snippet", {}).get("responsibility"),
        }
    }


def get_vacancies_by_area(query: str, area: int, area_name: str = "") -> List[Dict[str, Any]]:
    """
    Получает вакансии для профессии по конкретному региону

    Args:
        query: Название профессии
        area: ID региона
        area_name: Название региона (для вывода)

    Returns:
        Список отформатированных вакансий
    """
    all_vacancies = []

    first_page_data = get_vacancies(query, page=0, area=area)
    if not first_page_data:
        return all_vacancies

    total_pages = first_page_data.get("pages", 1)
    found = first_page_data.get("found", 0)

    if found == 0:
        return all_vacancies

    total_pages = min(total_pages, 20)
    area_label = f" ({area_name})" if area_name else f" (регион {area})"

    for page in range(total_pages):
        page_data = get_vacancies(query, page=page, area=area)
        items = page_data.get("items", [])

        if not items:
            break

        for vacancy in items:
            parsed_vacancy = parse_vacancy(vacancy)
            all_vacancies.append(parsed_vacancy)

        if page < total_pages - 1:
            time.sleep(0.5)

    if found > 0:
        print(f"  {area_label}: получено {len(all_vacancies)} из {found} вакансий")

    return all_vacancies


def remove_duplicates(vacancies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Удаляет дубликаты вакансий по ID

    Args:
        vacancies: Список вакансий

    Returns:
        Список уникальных вакансий
    """
    seen_ids = set()
    unique_vacancies = []

    for vacancy in vacancies:
        vacancy_id = vacancy.get("id")
        if vacancy_id and vacancy_id not in seen_ids:
            seen_ids.add(vacancy_id)
            unique_vacancies.append(vacancy)

    return unique_vacancies


def get_all_vacancies_for_profession(query: str, parse_all: bool = True, use_areas: bool = True) -> List[Dict[str, Any]]:
    """
    Получает все доступные вакансии для профессии
    Если найдено больше 2000 вакансий, автоматически разбивает запросы по регионам

    Args:
        query: Название профессии
        parse_all: Если True, парсит ВСЕ найденные страницы. Если False, парсит только первую страницу
        use_areas: Если True и найдено >2000 вакансий, разбивает запросы по регионам

    Returns:
        Список отформатированных вакансий (без дубликатов)
    """
    all_vacancies = []

    first_page_data = get_vacancies(query, page=0)
    if not first_page_data:
        return all_vacancies

    found, total_pages = first_page_data.get("found", 0), first_page_data.get("pages", 1)
    max_results = 2000  # Ограничение API >:(

    if not parse_all:
        print(f"Профессия: {query} - Найдено вакансий: {found}, Парсим 1 страницу...")
        page_data = get_vacancies(query, page=0)
        items = page_data.get("items", [])

        for vacancy in items:
            parsed_vacancy = parse_vacancy(vacancy)
            all_vacancies.append(parsed_vacancy)
        print(f"Получено {len(all_vacancies)} вакансий для '{query}'")

        return all_vacancies

    if (found > max_results) and use_areas:
        print(f"Профессия: {query} - Найдено вакансий: {found} (превышает лимит {max_results})")
        print(f"Используем разбиение по регионам для получения большего количества...")

        areas = [
            (1, "Москва"),
            (2, "Санкт-Петербург"),
            (113, "Россия"),
            (88, "Краснодар"),
            (53, "Новосибирск"),
            (66, "Екатеринбург"),
            (54, "Казань"),
            (26, "Ростов-на-Дону"),
            (4, "Нижний Новгород"),
            (76, "Челябинск"),
            (3, "Воронеж"),
            (99, "Самара"),
            (95, "Уфа"),
        ]

        print(f"  Запрашиваем данные по {len(areas)} регионам...")

        for area_id, area_name in areas:
            area_vacancies = get_vacancies_by_area(query, area_id, area_name)
            all_vacancies.extend(area_vacancies)
            time.sleep(0.3)

        before_dedup = len(all_vacancies)
        all_vacancies = remove_duplicates(all_vacancies)
        after_dedup = len(all_vacancies)

        if before_dedup > after_dedup:
            print(f"  Удалено {before_dedup - after_dedup} дубликатов")

        print(f"Получено {len(all_vacancies)} уникальных вакансий для '{query}' (из {found} найденных)")

        if len(all_vacancies) < found:
            print(f"  Получено {len(all_vacancies)} из {found} вакансий")
            print(f"  Можно получить больше, добавив больше регионов в список")

        return all_vacancies

    if found > max_results:
        print(f"Профессия: {query} - Найдено вакансий: {found}, но API ограничивает до {max_results} результатов (20 страниц × 100)")
        print(f"Парсим ВСЕ доступные {total_pages} страниц (максимум {max_results} вакансий)...")
    else:
        print(f"Профессия: {query} - Найдено вакансий: {found}, Парсим ВСЕ {total_pages} страниц...")

    for page in range(total_pages):
        page_data = get_vacancies(query, page=page)
        items = page_data.get("items", [])

        if not items:
            break

        for vacancy in items:
            parsed_vacancy = parse_vacancy(vacancy)
            all_vacancies.append(parsed_vacancy)

        if (page + 1) % 5 == 0:
            print(f"  Обработано страниц: {page + 1}/{total_pages}, получено вакансий: {len(all_vacancies)}")

        if page < total_pages - 1:
            time.sleep(0.5)

    if found > len(all_vacancies):
        print(f"Получено {len(all_vacancies)} вакансий для '{query}' (из {found} найденных) - это МАКСИМУМ через API HeadHunter")
        print(f"  Ограничение API: можно получить максимум 2000 результатов за один запрос")
    else:
        print(f"Получено {len(all_vacancies)} вакансий для '{query}' (из {found} найденных) - получены ВСЕ")

    return all_vacancies


def get_vacancies_for_professions(professions: List[str], parse_all: bool = True, save_to_folders: bool = True) -> Dict[str, Any]:
    """
    Получает вакансии для списка профессий

    Args:
        professions: Список названий профессий
        parse_all: Если True, парсит ВСЕ найденные страницы для каждой профессии
        save_to_folders: Сохранять ли данные в отдельные папки для каждой профессии

    Returns:
        Словарь с данными по всем профессиям в формате JSON
    """
    result = {
        "professions_count": len(professions),
        "total_vacancies": 0,
        "data": {}
    }

    for idx, profession in enumerate(professions, 1):
        print(f"\n[{idx}/{len(professions)}] Обработка профессии: {profession}")
        vacancies = get_all_vacancies_for_profession(profession, parse_all=parse_all)
        result["data"][profession] = {
            "count": len(vacancies),
            "vacancies": vacancies
        }
        result["total_vacancies"] += len(vacancies)

        if save_to_folders and vacancies:
            save_profession_data(profession, vacancies)

        if idx < len(professions):
            time.sleep(1)

    return result


def create_profession_folder(profession: str, base_folder: str = "parsed_jobs") -> str:
    """
    Создает папку для профессии внутри базовой папки

    Args:
        profession: Название профессии
        base_folder: Базовая папка (по умолчанию parsed_jobs)

    Returns:
        Путь к созданной папке
    """
    os.makedirs(base_folder, exist_ok=True)
    folder_name = profession.lower().strip()
    folder_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in folder_name)

    profession_path = os.path.join(base_folder, folder_name)
    os.makedirs(profession_path, exist_ok=True)

    return profession_path


def save_to_json(data: Dict[str, Any], filename: str = "vacancies_data.json", indent: int = 2):
    """
    Сохраняет данные в JSON файл с красивым форматированием

    Args:
        data: Данные для сохранения
        filename: Имя файла
        indent: Отступ для форматирования JSON
    """
    folder = os.path.dirname(filename)
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=indent)
    print(f"Данные сохранены в файл: {filename}")


def save_profession_data(profession: str, vacancies: List[Dict[str, Any]], base_folder: str = "parsed_jobs"):
    """
    Сохраняет данные по профессии в папку профессии

    Args:
        profession: Название профессии
        vacancies: Список вакансий
        base_folder: Базовая папка (по умолчанию parsed_jobs)
    """
    profession_folder = create_profession_folder(profession, base_folder)

    data = {
        "profession": profession,
        "count": len(vacancies),
        "vacancies": vacancies
    }

    filename = os.path.join(profession_folder, "data.json")
    save_to_json(data, filename)


def main():
    """
    Основная функция для парсинга вакансий
    """
    professions = [
        "Developer",
        "Programmer",
        "Software Engineer",
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Python Developer",
        "Java Developer",
        "JavaScript Developer",
        "DevOps Engineer",
        "QA Engineer",
        "Test Engineer",
        "System Administrator",
        "Database Administrator",
        "Architect",
        "Solution Architect",
        "Data Engineer",
        "Machine Learning Engineer",
        "Data Scientist",
        "Data Analyst",
        "Business Analyst",
        "Product Manager",
        "Project Manager",
        "Scrum Master",
        "UI Designer",
        "UX Designer",
        "Web Designer",
        "Graphic Designer",
        "Marketing Manager",
        "Sales Manager",
        "HR Manager",
        "Recruiter",
        "Accountant",
        "Financial Analyst",
        "Lawyer",
        "Consultant",
        "Engineer",
        "Mechanical Engineer",
        "Electrical Engineer",
        "Civil Engineer",
        "Doctor",
        "Nurse",
        "Surgeon",
        "Therapist",
        "Pediatrician",
        "Dentist",
        "Pharmacist",
        "Veterinarian",
        "Medical Assistant",
        "Psychologist",
        "Psychiatrist",
        "Teacher",
        "Tutor",
        "Professor",
        "Educator",
        "Instructor",
        "Trainer",
        "Sales Representative",
        "Sales Assistant",
        "Cashier",
        "Store Manager",
        "Retail Assistant",
        "Merchandiser",
        "Sales Consultant",
        "Shop Assistant",
        "Builder",
        "Construction Worker",
        "Plumber",
        "Electrician",
        "Welder",
        "Carpenter",
        "Mason",
        "Painter",
        "Roofer",
        "Driver",
        "Truck Driver",
        "Delivery Driver",
        "Taxi Driver",
        "Logistics Manager",
        "Dispatcher",
        "Warehouse Worker",
        "Loader",
        "Courier",
        "Banker",
        "Loan Officer",
        "Cashier Bank",
        "Financial Advisor",
        "Auditor",
        "Bookkeeper",
        "Realtor",
        "Real Estate Agent",
        "Property Manager",
        "Waiter",
        "Cook",
        "Chef",
        "Bartender",
        "Hotel Manager",
        "Housekeeper",
        "Cleaner",
        "Security Guard",
        "Worker",
        "Machine Operator",
        "Factory Worker",
        "Assembler",
        "Quality Control",
        "Technician",
        "Photographer",
        "Musician",
        "Artist",
        "Journalist",
        "Writer",
        "Copywriter",
        "Translator",
        "Interpreter",
        "Coach",
        "Fitness Trainer",
        "Farmer",
        "Agronomist",
        "Beautician",
        "Hairdresser",
        "Cosmetologist",
        "Massage Therapist",
        "Librarian",
        "Social Worker",
        "Caregiver",
        "Babysitter",
        "Nanny",
        "Handyman",
        "Locksmith",
        "Auto Mechanic",
        "Car Mechanic",
        "Mover",
        "Packer",
    ]

    print("="*60)
    print("НАЧИНАЮ ПАРСИНГ ВАКАНСИЙ С HEADHUNTER")
    print("="*60)
    print(f"Обрабатываю {len(professions)} профессий")
    print("Парсим максимально доступные вакансии через API")
    print()
    print("УЛУЧШЕНИЕ: Автоматически разбиваем запросы по регионам")
    print("   для получения большего количества вакансий (>2000)")
    print("   Удаляем дубликаты между регионами")
    print("="*60)

    os.makedirs("parsed_jobs", exist_ok=True)
    print("\nСоздана папка: parsed_jobs\n")
    result_data = get_vacancies_for_professions(professions, parse_all=True, save_to_folders=True)

    print("\n" + "="*60)
    print("ФИНАЛЬНАЯ СТАТИСТИКА")
    print("="*60)
    print(f"Всего профессий обработано: {result_data['professions_count']}")
    print(f"Всего вакансий получено: {result_data['total_vacancies']}")
    print("\nДетализация по профессиям:")
    for profession, data in result_data["data"].items():
        folder_name = profession.lower().strip()
        folder_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in folder_name)
        print(f"  - {profession:30} {data['count']:5} вакансий -> parsed_jobs/{folder_name}/data.json")
    
    print("\n" + "-"*60)
    save_to_json(result_data, "vacancies_data.json")
    print("Общие данные также сохранены в: vacancies_data.json")
    print("="*60)
    
    return result_data


if __name__ == "__main__":
    main()

