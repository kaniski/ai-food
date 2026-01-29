from .menu_generator import generate_mock_plan

def build_meal_plan_from_user_data(user_data: dict) -> dict:
    """
    Aqui seria a função que chamaria o agente de IA (ChatGPT).
    Por enquanto, como é só teste, eu devolvo um plano fake mas “bem com cara de real”.

    user_data vem com:
      - name, age, height_cm, weight_kg, goal
      - likes, dislikes, allergies, restriction, meals_per_day, notes
    """

    # Se um dia você for ligar na API do ChatGPT, é aqui que entraria:
    # 1) montar prompt com user_data
    # 2) chamar o modelo
    # 3) validar e normalizar resposta
    # 4) retornar no mesmo formato desse mock

    return generate_mock_plan(user_data)
