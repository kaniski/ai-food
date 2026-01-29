from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .services.ai_agent import build_meal_plan_from_user_data

main_bp = Blueprint("main", __name__)

def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _safe_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default

@main_bp.get("/")
def index():
    return redirect(url_for("main.step1"))

@main_bp.route("/step-1", methods=["GET", "POST"])
def step1():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        age = _safe_int(request.form.get("age"))
        height_cm = _safe_float(request.form.get("height_cm"))
        weight_kg = _safe_float(request.form.get("weight_kg"))
        goal = (request.form.get("goal") or "").strip()

        if not name or age <= 0 or height_cm <= 0 or weight_kg <= 0 or goal not in ["cut", "maintain", "bulk"]:
            flash("Preenche tudo certinho aí 🙂", "error")
            return render_template("step1.html")

        # Jogo esses dados na sessão porque é a forma mais simples pro fluxo de 2 etapas.
        session["user_step1"] = {
            "name": name,
            "age": age,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "goal": goal
        }

        return redirect(url_for("main.step2"))

    return render_template("step1.html")

@main_bp.route("/step-2", methods=["GET", "POST"])
def step2():
    if "user_step1" not in session:
        flash("Volta e preenche a etapa 1 primeiro.", "error")
        return redirect(url_for("main.step1"))

    if request.method == "POST":
        likes = (request.form.get("likes") or "").strip()
        dislikes = (request.form.get("dislikes") or "").strip()
        allergies = (request.form.get("allergies") or "").strip()
        restriction = (request.form.get("restriction") or "none").strip()
        meals_per_day = _safe_int(request.form.get("meals_per_day"), default=4)
        notes = (request.form.get("notes") or "").strip()

        if meals_per_day < 3:
            meals_per_day = 3
        if meals_per_day > 7:
            meals_per_day = 7

        session["user_step2"] = {
            "likes": likes,
            "dislikes": dislikes,
            "allergies": allergies,
            "restriction": restriction,
            "meals_per_day": meals_per_day,
            "notes": notes
        }

        # Aqui seria onde você chamaria seu “agente” (ChatGPT / etc).
        # Pra versão de testes, eu só gero um plano fake bem organizado.
        user_data = {
            **session["user_step1"],
            **session["user_step2"],
        }

        plan = build_meal_plan_from_user_data(user_data)
        session["meal_plan"] = plan

        return redirect(url_for("main.loading"))

    return render_template("step2.html", step1=session.get("user_step1"))

@main_bp.get("/loading")
def loading():
    # Tela só pra dar aquela sensação de "IA trabalhando" 😄
    if "meal_plan" not in session:
        return redirect(url_for("main.step1"))
    return render_template("loading.html")

@main_bp.get("/menu")
def menu():
    plan = session.get("meal_plan")
    if not plan:
        flash("Não achei seu cardápio. Faz o fluxo de novo rapidinho.", "error")
        return redirect(url_for("main.step1"))

    return render_template("menu.html", plan=plan)

@main_bp.post("/reset")
def reset():
    # Botão "começar de novo"
    session.clear()
    return redirect(url_for("main.step1"))
