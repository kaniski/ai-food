import math
import random

MEAL_LABELS = [
    "Café da manhã",
    "Lanche da manhã",
    "Almoço",
    "Lanche da tarde",
    "Jantar",
    "Ceia",
    "Extra"
]

def _calc_bmr_mifflin(age: int, height_cm: float, weight_kg: float) -> float:
    # Não vou entrar em fórmula perfeita aqui, é só teste.
    # Baseado numa ideia de Mifflin (bem comum).
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5

def _goal_multiplier(goal: str) -> float:
    if goal == "cut":
        return 0.85
    if goal == "bulk":
        return 1.10
    return 1.00

def _split_macros(calories: int, goal: str) -> dict:
    # Macro bem “padrão” pra demo: proteína mais alta no bulk, mais controlado no cut.
    if goal == "cut":
        protein_g = 2.0
        fat_g = 0.8
    elif goal == "bulk":
        protein_g = 2.2
        fat_g = 1.0
    else:
        protein_g = 1.8
        fat_g = 0.9

    return {"protein_per_kg": protein_g, "fat_per_kg": fat_g}

def _format_goal(goal: str) -> str:
    return {"cut": "Emagrecimento", "maintain": "Manutenção", "bulk": "Hipertrofia"}.get(goal, "Saúde")

def _pick_pool(restriction: str):
    # Um pool simples só pra variar as refeições.
    base = [
        {
            "title": "Omelete com queijo + salada",
            "prep": "Bate 2-3 ovos, joga numa frigideira antiaderente, coloca queijo e finaliza. Salada do lado.",
            "ingredients": ["ovos", "queijo", "sal", "pimenta", "folhas", "tomate"],
            "tips": "Se quiser mais proteína, coloca frango desfiado."
        },
        {
            "title": "Frango grelhado + arroz + legumes",
            "prep": "Grelha o frango com tempero simples. Cozinha o arroz. Salteia legumes com alho e azeite.",
            "ingredients": ["frango", "arroz", "brócolis", "cenoura", "alho", "azeite"],
            "tips": "Pra ficar mais suculento: sela forte e termina no fogo baixo."
        },
        {
            "title": "Iogurte + fruta + granola",
            "prep": "Monta numa tigela: iogurte, fruta picada e granola por cima.",
            "ingredients": ["iogurte", "banana", "morango", "granola"],
            "tips": "Se estiver em cut, pega granola sem açúcar e segura a porção."
        },
        {
            "title": "Sanduíche integral de atum",
            "prep": "Mistura atum com iogurte/maionese light, monta no pão integral com folhas e tomate.",
            "ingredients": ["pão integral", "atum", "folhas", "tomate", "iogurte"],
            "tips": "Dá pra trocar atum por frango ou grão-de-bico amassado."
        },
        {
            "title": "Macarrão com molho de tomate e carne",
            "prep": "Cozinha o macarrão. Faz molho com tomate, cebola e carne moída. Junta tudo e finaliza.",
            "ingredients": ["macarrão", "tomate", "cebola", "carne moída", "sal", "orégano"],
            "tips": "Se quiser deixar mais leve, usa patinho e controla o azeite."
        },
        {
            "title": "Panqueca de banana com aveia",
            "prep": "Amassa banana, mistura com ovo e aveia. Grelha como panqueca. Canela por cima.",
            "ingredients": ["banana", "ovo", "aveia", "canela"],
            "tips": "Boa pra café da manhã rápido."
        },
    ]

    veg = [
        {
            "title": "Bowl de grão-de-bico + salada + arroz",
            "prep": "Grão-de-bico cozido com tempero, arroz e salada bem caprichada.",
            "ingredients": ["grão-de-bico", "arroz", "folhas", "tomate", "limão", "azeite"],
            "tips": "Se quiser, coloca tahine pra dar um sabor absurdo."
        },
        {
            "title": "Tofu grelhado + legumes + quinoa",
            "prep": "Grelha tofu com shoyu light, faz legumes e cozinha quinoa.",
            "ingredients": ["tofu", "quinoa", "abobrinha", "cenoura", "shoyu light"],
            "tips": "Tofu fica melhor se você prensar antes pra tirar água."
        },
        {
            "title": "Pasta de amendoim + banana + aveia",
            "prep": "Monta a tigela e mistura. Simples e eficiente.",
            "ingredients": ["pasta de amendoim", "banana", "aveia"],
            "tips": "Se for cut, segura a pasta de amendoim."
        }
    ]

    vegan = [
        {
            "title": "Overnight oats com fruta",
            "prep": "Aveia + leite vegetal + chia. Deixa na geladeira. Finaliza com frutas.",
            "ingredients": ["aveia", "leite vegetal", "chia", "morango", "banana"],
            "tips": "Se quiser mais proteína, usa iogurte vegetal proteico."
        },
        {
            "title": "Lentilha + arroz + salada",
            "prep": "Cozinha lentilha com tempero e serve com arroz e salada.",
            "ingredients": ["lentilha", "arroz", "cebola", "alho", "folhas", "limão"],
            "tips": "Lentilha bem temperada salva qualquer dieta."
        },
        {
            "title": "Macarrão com molho de tomate + cogumelos",
            "prep": "Molho de tomate caseiro e cogumelos salteados. Junta no macarrão.",
            "ingredients": ["macarrão", "tomate", "cogumelos", "alho", "cebola"],
            "tips": "Um fio de azeite no final dá outro nível."
        }
    ]

    if restriction == "vegan":
        return vegan
    if restriction == "vegetarian":
        return veg
    return base

def _filter_by_text(meals, dislikes: str, allergies: str):
    # Bem simples: se o texto do item bater em um "não como", tenta evitar.
    blacklist = (dislikes + " " + allergies).lower()
    if not blacklist.strip():
        return meals

    cleaned = []
    for m in meals:
        hay = (m["title"] + " " + " ".join(m.get("ingredients", []))).lower()
        if any(word.strip() and word.strip() in hay for word in blacklist.split(",")):
            continue
        cleaned.append(m)

    return cleaned or meals  # se filtrar tudo, volta pro original pra não quebrar

def generate_mock_plan(user_data: dict) -> dict:
    age = int(user_data["age"])
    height_cm = float(user_data["height_cm"])
    weight_kg = float(user_data["weight_kg"])
    goal = user_data["goal"]

    bmr = _calc_bmr_mifflin(age, height_cm, weight_kg)

    # "atividade" fixa pra demo
    tdee = bmr * 1.45
    target_cal = int(round(tdee * _goal_multiplier(goal)))

    macro_cfg = _split_macros(target_cal, goal)
    protein_g = int(round(weight_kg * macro_cfg["protein_per_kg"]))
    fat_g = int(round(weight_kg * macro_cfg["fat_per_kg"]))
    # carbs = restante
    carbs_g = int(round(max(0, (target_cal - (protein_g * 4) - (fat_g * 9)) / 4)))

    meals_per_day = int(user_data.get("meals_per_day", 4))
    restriction = user_data.get("restriction", "none")
    likes = user_data.get("likes", "")
    dislikes = user_data.get("dislikes", "")
    allergies = user_data.get("allergies", "")
    notes = user_data.get("notes", "")

    pool = _pick_pool(restriction)
    pool = _filter_by_text(pool, dislikes=dislikes, allergies=allergies)

    # Monta refeições do dia
    meal_items = []
    for i in range(meals_per_day):
        picked = random.choice(pool)
        meal_items.append({
            "label": MEAL_LABELS[i] if i < len(MEAL_LABELS) else f"Refeição {i+1}",
            "title": picked["title"],
            "prep": picked["prep"],
            "ingredients": picked["ingredients"],
            "tips": picked.get("tips", "")
        })

    # Info extra "legal" na tela feito.
    water_ml = int(round(weight_kg * 35))
    steps_hint = 8000 if goal != "bulk" else 7000

    return {
        "user": {
            "name": user_data["name"],
            "goal_label": _format_goal(goal),
            "age": age,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "restriction": restriction,
            "likes": likes,
            "dislikes": dislikes,
            "allergies": allergies,
            "notes": notes
        },
        "macros": {
            "calories": target_cal,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g
        },
        "extras": {
            "water_ml": water_ml,
            "steps_hint": steps_hint,
            "consistency_tip": "Faz o básico bem feito por 14 dias antes de inventar moda."
        },
        "meals": meal_items
    }
