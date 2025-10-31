from gigachat import GigaChat
import ssl
import json

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

giga = GigaChat(
    credentials="OWRlNjRhNDMtZGQ3OC00NmQyLWI2NTAtOWEyYTU0Mzk0MGQ1OjkwYmIwMDMzLWUyNTUtNGIwMS1iMjY5LThjZjcyZWQwNTZiNA==",
    ssl_context=ssl_context,
    verify_ssl_certs=False
)

def generate_profession_data():  
    system_prompt = """Ты генерируешь данные о случайной профессии. 
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
    
    Сгенерируй реалистичные данные для случайной IT-профессии. в распорядке дня мероприятий обязательно ровно 9 (формат: время - задача), они описаны коротко. сообщения коллег чередуются формальные с неформальными (но связанные с работой, возможно в шутливой форме). профессии могут быть абсолютно из лбых сфер, не обязательно IT"""
    
    try:
        response = giga.chat(system_prompt)
        response_text = response.choices[0].message.content

        if '```json' in response_text:
            json_str = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            json_str = response_text.split('```')[1].strip()
        else:
            json_str = response_text.strip()
        
        data = json.loads(json_str)
        return data
    except Exception as e:
        print(f"Ошибка при генерации данных: {e}")
        
def main():
    print("Генерация данных о случайной профессии...")
    data = generate_profession_data()
    profession = data["profession"]
    schedule = data["schedule"]
    tech_stack = data["tech_stack"]
    company_benefits = data["company_benefits"]
    career_growth = data["career_growth"]
    colleague_messages = data["colleague_messages"]
    growth_table = data["growth_table"]
    image_description = data["image_description"]
    sound_description = data["sound_description"]
    print(f"\n=== ПРОФЕССИЯ: {profession} ===")
    print(f"\n📅 РАСПОРЯДОК ДНЯ:")
    print("Утро:")
    for item in schedule["morning"]:
        print(f"  • {item}")
    print("Обеденное время:")
    for item in schedule["lunch"]:
        print(f"  • {item}")
    print("Вечер:")
    for item in schedule["evening"]:
        print(f"  • {item}")
    
    print(f"\n🛠 ТЕХНОЛОГИЧЕСКИЙ СТЕК:")
    for tech in tech_stack:
        print(f"  • {tech}")
    
    print(f"\n💼 ПОЛЬЗА ДЛЯ КОМПАНИИ:")
    for benefit in company_benefits:
        print(f"  • {benefit}")
    
    print(f"\n📈 ПУТИ РОСТА:")
    for growth in career_growth:
        print(f"  • {growth}")
    
    print(f"\n💬 СООБЩЕНИЯ ОТ КОЛЛЕГ:")
    print("Короткие:")
    for msg in colleague_messages["short"]:
        print(f"  • {msg}")
    print("Средние:")
    for msg in colleague_messages["medium"]:
        print(f"  • {msg}")
    print("Длинное:")
    print(f"  • {colleague_messages['long'][0]}")
    
    print(f"\n📊 ТАБЛИЦА РОСТА:")
    print(f"{'Точки роста':<100} {'Вакансии':<100} {'Курсы':<100}")
    print("-" * 75)
    for i in range(len(growth_table["growth_points"])):
        print(f"{growth_table['growth_points'][i]:<100} {growth_table['vacancies'][i]:<100} {growth_table['courses'][i]:<100}")
    
    print(f"\n🖼 ОПИСАНИЕ КАРТИНКИ:")
    print(image_description)
    print(f"\n🔊 ОПИСАНИЕ ЗВУКА:")
    print(sound_description)
    return {
        "profession": profession,
        "schedule": schedule,
        "tech_stack": tech_stack,
        "company_benefits": company_benefits,
        "career_growth": career_growth,
        "colleague_messages": colleague_messages,
        "growth_table": growth_table,
        "image_description": image_description,
        "sound_description": sound_description
    }

if __name__ == "__main__":
    generated_data = main()