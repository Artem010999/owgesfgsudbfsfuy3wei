import telebot
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

tokenn = os.getenv("TELEGRAM_TOKEN", "")
openai_api_keyy = os.getenv("OPENAI_API_KEY", "")
openai_consists = OpenAI(api_key=openai_api_keyy)

botik_instanse = telebot.TeleBot(tokenn)

user_states = {}
user_historis = {}

def get_gpt_responce(messges_hist):
    try:
        completon = openai_consists.chat.completions.create(
            model="gpt-4",
            messages=messges_hist
        )
        return completon.choices[0].message.content
    except Exception as e:
        return None

def get_image_promt_from_gpt(profession_info):
    try:
        promt_for_img = f"""На основе информации о профессии: {profession_info}
        
Создай короткий промпт на английском языке для генерации изображения этой профессии. Промпт должен быть в стиле художественной иллюстрации, показывающей вайб и атмосферу работы. Не более 30 слов. Только промпт, без дополнительного текста."""
        
        img_promt_msgs = [
            {"role": "system", "content": "Ты помощник, создающий промпты для генерации изображений."},
            {"role": "user", "content": promt_for_img}
        ]
        
        img_promt = get_gpt_responce(img_promt_msgs)
        return img_promt.strip() if img_promt else None
    except Exception as e:
        return None

def generete_image_with_dalle(promt):
    try:
        response = openai_consists.images.generate(
            model="dall-e-3",
            prompt=promt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        return None

@botik_instanse.message_handler(commands=['start'])
def start_handler(mesage):
    user_id = mesage.from_user.id
    user_states[user_id] = "waiting_first"
    user_historis[user_id] = []
    botik_instanse.reply_to(mesage, "Вайб какой работы ты хочешь прочувствовать?")

@botik_instanse.message_handler(func=lambda mesage: True)
def vibing_handl(mesage):
    user_id = mesage.from_user.id
    usr_txt = mesage.text
    
    if user_id not in user_states:
        user_states[user_id] = "waiting_first"
        user_historis[user_id] = []
    
    state = user_states[user_id]
    
    if state == "waiting_first":
        user_historis[user_id].append({"role": "user", "content": usr_txt})
        
        sistem_promt = """Ты помощник, который помогает понять вайб определенной работы. Пользователь только что рассказал о работе, вайб которой хочет прочувствовать. 
        Задай ему 2-3 вопроса, чтобы лучше понять, что именно его интересует. Задай первый вопрос."""
        
        messages_for_gpt = [
            {"role": "system", "content": sistem_promt},
            {"role": "user", "content": usr_txt}
        ]
        
        gpt_answr = get_gpt_responce(messages_for_gpt)
        
        if gpt_answr:
            user_states[user_id] = "collecting"
            user_historis[user_id].append({"role": "assistant", "content": gpt_answr})
            botik_instanse.reply_to(mesage, gpt_answr)
        else:
            botik_instanse.reply_to(mesage, "Произошла ошибка, попробуй еще раз")
    
    elif state == "collecting":
        user_historis[user_id].append({"role": "user", "content": usr_txt})
        
        iatr_assistant_mesages = [m for m in user_historis[user_id] if m["role"] == "assistant"]
        qstn_count = len(iatr_assistant_mesages)
        
        if qstn_count >= 3:
            summar_promt = """Ты задал 3 вопроса пользователю о работе, вайб которой он хочет прочувствовать. Теперь создай ответ СТРОГО в этом формате, БЕЗ любых вступлений и пояснений:

РЕЗУЛЬТАТ: [Название профессии/роли]

ТИПИЧНЫЙ ДЕНЬ:
10:00 — [Первое дело];
11:30 — [Второе дело];
14:00 — [Третье дело];
16:00 — [Четвертое дело].

ХЭШТЕГИ: #хэштег1 #хэштег2 #хэштег3 #хэштег4 #хэштег5

ПОЛЬЗА: "[Одна цитата в кавычках]"

РОСТ: [Junior → Middle → Senior → Lead]

КРИТИЧЕСКИ ВАЖНО: Твой ответ должен начинаться ТОЧНО со слова "РЕЗУЛЬТАТ:" и заканчиваться строкой с "РОСТ:". Никаких дополнительных слов до "РЕЗУЛЬТАТ:" или после "РОСТ:"."""
            
            full_msgs = user_historis[user_id].copy()
            full_msgs.insert(0, {"role": "system", "content": summar_promt})
            
            summari = get_gpt_responce(full_msgs)
            
            if summari:
                summari_upper = summari.upper()
                if "РЕЗУЛЬТАТ:" not in summari_upper:
                    fix_promt = """Твой предыдущий ответ был неправильным. Создай ответ СНОВА, но ОБЯЗАТЕЛЬНО начни его со строки "РЕЗУЛЬТАТ:" и включи все секции:

РЕЗУЛЬТАТ: [название]
ТИПИЧНЫЙ ДЕНЬ:
10:00 — [дело];
11:30 — [дело];
14:00 — [дело];
16:00 — [дело].
ХЭШТЕГИ: #х1 #х2 #х3 #х4 #х5
ПОЛЬЗА: "[цитата]"
РОСТ: [Junior → Middle → Senior → Lead]"""
                    
                    full_msgs.append({"role": "assistant", "content": summari})
                    full_msgs.append({"role": "user", "content": "Исправь формат ответа"})
                    full_msgs[0] = {"role": "system", "content": fix_promt}
                    summari = get_gpt_responce(full_msgs)
                
                rezultat = ""
                tipichniy_den = []
                hashtags = ""
                polza = ""
                rost = ""
                
                lines = summari.split('\n')
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    line_upper = line.upper()
                    if line_upper.startswith("РЕЗУЛЬТАТ:"):
                        current_section = "rezultat"
                        rezultat = line.split(":", 1)[-1].strip() if ":" in line else line
                    elif "ТИПИЧНЫЙ ДЕНЬ" in line_upper:
                        current_section = "den"
                    elif line_upper.startswith("ХЭШТЕГИ:"):
                        current_section = "hashtags"
                        hashtags = line.split(":", 1)[-1].strip() if ":" in line else line
                    elif line_upper.startswith("ПОЛЬЗА:"):
                        current_section = "polza"
                        polza = line.split(":", 1)[-1].strip() if ":" in line else line
                    elif line_upper.startswith("РОСТ:"):
                        current_section = "rost"
                        rost = line.split(":", 1)[-1].strip() if ":" in line else line
                    else:
                        if current_section == "rezultat" and not rezultat:
                            rezultat = line
                        elif current_section == "den":
                            if line and (":" in line or "—" in line or "-" in line):
                                tipichniy_den.append(line)
                        elif current_section == "hashtags" and not hashtags:
                            if "#" in line:
                                hashtags = line
                        elif current_section == "polza" and not polza:
                            polza = line.strip('"').strip() if '"' in line else line
                        elif current_section == "rost" and not rost:
                            if "→" in line or "->" in line:
                                rost = line
                            elif not rost:
                                rost = line
                
                if not rezultat or not tipichniy_den:
                    botik_instanse.reply_to(mesage, "Произошла ошибка при обработке ответа. Попробуй /start снова")
                    user_states[user_id] = "completed"
                    user_historis[user_id] = []
                    return
                
                msg1_text = f"Результат: {rezultat}\n\nТипичный день:\n" + "\n".join(tipichniy_den)
                botik_instanse.reply_to(mesage, msg1_text)
                
                if hashtags:
                    msg2 = f"Хэштеги: {hashtags}"
                    botik_instanse.send_message(mesage.chat.id, msg2)
                
                msg3_parts = []
                if polza:
                    msg3_parts.append(f"Польза: {polza}")
                if rost:
                    msg3_parts.append(f"Рост: {rost}")
                
                if msg3_parts:
                    msg3 = "\n\n".join(msg3_parts)
                    botik_instanse.send_message(mesage.chat.id, msg3)
                else:
                    if polza or rost:
                        fallback_msg = ""
                        if polza:
                            fallback_msg += f"Польза: {polza}\n\n"
                        if rost:
                            fallback_msg += f"Рост: {rost}"
                        if fallback_msg:
                            botik_instanse.send_message(mesage.chat.id, fallback_msg.strip())
                
                prof_info_full = f"{rezultat}. Типичный день: {' '.join(tipichniy_den)}. {polza if polza else ''}"
                img_promt = get_image_promt_from_gpt(prof_info_full)
                
                if img_promt:
                    botik_instanse.send_message(mesage.chat.id, "Генерирую изображение...")
                    img_url = generete_image_with_dalle(img_promt)
                    
                    if img_url:
                        img_respons = requests.get(img_url)
                        if img_respons.status_code == 200:
                            botik_instanse.send_photo(mesage.chat.id, img_respons.content)
                        else:
                            botik_instanse.send_message(mesage.chat.id, "Не удалось загрузить изображение")
                    else:
                        botik_instanse.send_message(mesage.chat.id, "Не удалось сгенерировать изображение")
                
                user_states[user_id] = "completed"
                user_historis[user_id] = []
            else:
                botik_instanse.reply_to(mesage, "Произошла ошибка при создании суммаризации")
        else:
            ostalos_voprosov = 3 - qstn_count
            sistem_promt_continue = f"Продолжай задавать вопросы для уточнения вайба работы. Задай следующий вопрос. Всего должно быть задано ровно 3 вопроса. Осталось задать {ostalos_voprosov} вопрос(ов)."
            full_msgs = user_historis[user_id].copy()
            full_msgs.insert(0, {"role": "system", "content": sistem_promt_continue})
            
            gpt_answr = get_gpt_responce(full_msgs)
            
            if gpt_answr:
                user_historis[user_id].append({"role": "assistant", "content": gpt_answr})
                botik_instanse.reply_to(mesage, gpt_answr)
            else:
                botik_instanse.reply_to(mesage, "Произошла ошибка, попробуй еще раз")
    
    else:
        botik_instanse.reply_to(mesage, "Начни новую беседу командой /start")

if __name__ == "__main__":
    import time
    import telebot.apihelper
    
    while True:
        try:
            botik_instanse.delete_webhook()
            time.sleep(2)
            botik_instanse.polling(none_stop=True, interval=0, timeout=20)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 409:
                print(f"Conflict detected: another bot instance running. Waiting 10 seconds...")
                time.sleep(10)
                continue
            else:
                print(f"API Error: {e}")
                time.sleep(5)
                continue
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
            continue

