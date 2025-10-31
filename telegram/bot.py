import telebot
from openai import OpenAI

tokenn = ""
openai_consists = OpenAI(api_key="")

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
            summar_promt = """Ты задал 3 вопроса пользователю о работе, вайб которой он хочет прочувствовать. Теперь на основе всей беседы создай краткую суммаризацию того, какой вайб работы интересует пользователя. Опиши это в понятной и интересной форме, сохраняя суть того, что пользователь хочет прочувствовать. НЕ задавай больше вопросов, только создай суммаризацию."""
            
            full_msgs = user_historis[user_id].copy()
            full_msgs.insert(0, {"role": "system", "content": summar_promt})
            
            summari = get_gpt_responce(full_msgs)
            
            if summari:
                botik_instanse.reply_to(mesage, f"Вот суммаризация:\n\n{summari}")
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
    botik_instanse.polling(none_stop=True)

