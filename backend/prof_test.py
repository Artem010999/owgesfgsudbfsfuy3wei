from gigachat import GigaChat
import ssl

class CareerAdvisor:
    def __init__(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self.giga = GigaChat(
            credentials="OWRlNjRhNDMtZGQ3OC00NmQyLWI2NTAtOWEyYTU0Mzk0MGQ1OjkwYmIwMDMzLWUyNTUtNGIwMS1iMjY5LThjZjcyZWQwNTZiNA==",
            ssl_context=ssl_context,
            verify_ssl_certs=False
        )
    
    def get_recommendation(self, user_answers):
        prompt = f"""
        Проанализируй ответы пользователя на профориентационный тест и порекомендуй ОДНУ наиболее подходящую профессию.
        
        ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:
        {self._format_answers(user_answers)}
        
        ТРЕБОВАНИЯ К ОТВЕТУ:
        - Рекомендуй ТОЛЬКО ОДНУ профессию (самую подходящую)
        - Название профессии должно быть конкретным, современным и востребованным на рынке
        - Укажи краткое обоснование выбора (2-3 предложения)
        - Формат ответа должен быть четким: 
          "🎯 РЕКОМЕНДУЕМАЯ ПРОФЕССИЯ: [название]"
          "📋 ОБОСНОВАНИЕ: [текст]"
        
        Учти все аспекты: интересы, условия работы, сильные стороны, ограничения, сроки обучения и приоритеты.
        """
        
        try:
            response = self.giga.chat(prompt)
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при получении рекомендации: {str(e)}"
    
    def _format_answers(self, answers):
        formatted = []

        if 'q1' in answers:
            formatted.append(f"• Интересы и предпочтения: {answers['q1']}")
               
        if 'q2' in answers:
            workplaces = ", ".join(answers['q2'])
            formatted.append(f"• Комфортные условия работы: {workplaces}")

        if 'q3' in answers:
            strengths = ", ".join(answers['q3'])
            formatted.append(f"• Сильные стороны: {strengths}")
        
        if 'q4' in answers:
            limitations = ", ".join(answers['q4'])
            formatted.append(f"• Условия и ограничения: {limitations}")
        
        if 'q5' in answers:
            formatted.append(f"• Готовность к обучению: {answers['q5']}")
        
        if 'q6' in answers:
            priorities = ", ".join(answers['q6'])
            formatted.append(f"• Важные аспекты работы: {priorities}")
        
        if 'q7' in answers and answers['q7'].strip():
            formatted.append(f"• Описание работы мечты: {answers['q7']}")
        
        return "\n".join(formatted)

def main():
    advisor = CareerAdvisor()
    sample_answers = {
        'q1': 'Творчество, дизайн, тексты/медиа',
        'q2': ['Офис/деловой центр', 'Удалённая работа'],
        'q3': ['Креативность и визуальное мышление', 'Общение и эмпатия', 'Письмо, языки, подача информации'],
        'q4': ['Важна удалёнка', 'Нужен стабильный график 5/2'],
        'q5': '6–12 месяцев',
        'q6': ['Свобода и творчество', 'Высокий доход и рост'],
        'q7': 'Хочу создавать цифровые продукты и работать в гибкой команде'
    }
    recommendation = advisor.get_recommendation(sample_answers)
    print("🎯 РЕЗУЛЬТАТ ПРОФОРИЕНТАЦИОННОГО ТЕСТА")
    print("="*60)
    print(recommendation)
    print("="*60)

if __name__ == "__main__":
    main()