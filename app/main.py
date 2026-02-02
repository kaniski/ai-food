from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, SESSION_COOKIE, SESSION_MAX_AGE_SECONDS
from app.schemas import Step1In, Step2In, Step3In, Step4In, Step5In, UserCreate, MacrosIn
from app.services.mongo import get_db
from app.services.macros import compute_macros

load_dotenv()

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie=SESSION_COOKIE,
    max_age=SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_event():
    db = get_db()
    await db.command("ping")
    print("✅ MongoDB conectado com sucesso")


# -------------------------
# Helpers sessão/CSRF
# -------------------------
def ensure_csrf(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(24)
        request.session["csrf"] = token
    return token


def csrf_check(request: Request, csrf: str | None) -> bool:
    expected = request.session.get("csrf")
    return bool(expected and csrf and secrets.compare_digest(expected, csrf))


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def base_context(request: Request, step: int) -> Dict[str, Any]:
    return {
        "request": request,
        "step": step,
        "page_title": "MicroNutri — Plano alimentar simples e personalizado",
        "meta_description": "Crie um plano alimentar prático, adaptado às suas preferências e objetivos.",
        "errors": {},
        "values": {},
        "csrf_token": ensure_csrf(request),
    }


def as_bool(v: str) -> bool:
    return v.strip().lower() in ["1", "true", "sim", "yes", "y", "on"]


# -------------------------
# Guards de etapa
# -------------------------
def can_access(request: Request, page: str) -> bool:
    s = request.session
    if page == "step1":
        return True
    if page == "step2":
        return "step1" in s
    if page == "step3":
        return "step1" in s and "step2" in s
    if page == "macros":
        return "step1" in s and "step2" in s and "step3" in s
    if page == "step4":
        return "step1" in s and "step2" in s and "step3" in s and "macros" in s
    if page == "step5":
        return "step1" in s and "step2" in s and "step3" in s and "macros" in s and "step4" in s
    if page == "review":
        return "step1" in s and "step2" in s and "step3" in s and "macros" in s and "step4" in s and "step5" in s
    return False


# -------------------------
# Persistência incremental (LEADS)
# -------------------------
def _lead_key_from_session(request: Request) -> Optional[Dict[str, Any]]:
    step1 = request.session.get("step1") or {}
    email = step1.get("email")
    if not email:
        return None
    return {"email": email}


async def upsert_lead_progress(request: Request, step_name: str, payload: Dict[str, Any]) -> None:
    """
    Salva o progresso a cada etapa.
    Isso alimenta seu funil/CRM (email marketing etc).
    """
    key = _lead_key_from_session(request)
    if not key:
        return

    db = get_db()
    leads = db.get_collection("leads")
    now = datetime.utcnow()

    update_doc: Dict[str, Any] = {
        "$set": {
            f"steps.{step_name}": payload,
            "last_step": step_name,
            "updated_at": now,
        },
        "$setOnInsert": {
            "email": key["email"],
            "created_at": now,
            "first_seen_at": now,
            "source": "micronutri-web",
        },
        "$addToSet": {"completed_steps": step_name},
    }

    await leads.update_one(key, update_doc, upsert=True)


# --------------------------------------------------
# STEP 1
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def step1(request: Request):
    ctx = base_context(request, step=1)
    ctx["values"] = request.session.get("step1", {})
    return templates.TemplateResponse("step1.html", ctx)


@app.post("/", response_class=HTMLResponse)
async def step1_post(
    request: Request,
    csrf: str = Form(...),
    email: str = Form(...),
    nome: str = Form(...),
    numero: str = Form(...),
    idade: int = Form(...),
    peso: float = Form(...),
):
    ctx = base_context(request, step=1)
    ctx["values"] = {"email": email, "nome": nome, "numero": numero, "idade": idade, "peso": peso}

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue a página e tente de novo."
        return templates.TemplateResponse("step1.html", ctx)

    try:
        payload = Step1In(email=email, nome=nome, numero=numero, idade=idade, peso=peso)
    except ValidationError as e:
        errors = {}
        for err in e.errors():
            field = err.get("loc", ["__all__"])[0]
            errors[str(field)] = err.get("msg", "Campo inválido")
        ctx["errors"] = errors
        return templates.TemplateResponse("step1.html", ctx)

    request.session["step1"] = payload.model_dump()

    # se editar step1, invalida downstream
    for k in ["step2", "step3", "macros", "step4", "step5"]:
        request.session.pop(k, None)

    # salva no lead imediatamente
    await upsert_lead_progress(request, "step1", request.session["step1"])

    return redirect("/step/2")


# --------------------------------------------------
# STEP 2
# --------------------------------------------------
@app.get("/step/2", response_class=HTMLResponse)
async def step2(request: Request):
    if not can_access(request, "step2"):
        return redirect("/")
    ctx = base_context(request, step=2)
    ctx["values"] = request.session.get("step2", {})
    return templates.TemplateResponse("step2.html", ctx)


@app.post("/step/2", response_class=HTMLResponse)
async def step2_post(
    request: Request,
    csrf: str = Form(...),
    feliz_corpo: str = Form(...),
    mudar_rapido: str = Form(...),
    cansado_espelho: str = Form(...),
):
    if not can_access(request, "step2"):
        return redirect("/")
    ctx = base_context(request, step=2)
    ctx["values"] = {"feliz_corpo": feliz_corpo, "mudar_rapido": mudar_rapido, "cansado_espelho": cansado_espelho}

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue e tente de novo."
        return templates.TemplateResponse("step2.html", ctx)

    try:
        payload = Step2In(
            feliz_corpo=as_bool(feliz_corpo),
            mudar_rapido=as_bool(mudar_rapido),
            cansado_espelho=as_bool(cansado_espelho),
        )
    except ValidationError:
        ctx["errors"]["__all__"] = "Responda todas as perguntas para continuar."
        return templates.TemplateResponse("step2.html", ctx)

    request.session["step2"] = payload.model_dump()
    for k in ["step3", "macros", "step4", "step5"]:
        request.session.pop(k, None)

    await upsert_lead_progress(request, "step2", request.session["step2"])
    return redirect("/step/3")


# --------------------------------------------------
# STEP 3
# --------------------------------------------------
@app.get("/step/3", response_class=HTMLResponse)
async def step3(request: Request):
    if not can_access(request, "step3"):
        return redirect("/step/2" if "step1" in request.session else "/")
    ctx = base_context(request, step=3)
    ctx["values"] = request.session.get("step3", {})
    return templates.TemplateResponse("step3.html", ctx)


@app.post("/step/3", response_class=HTMLResponse)
async def step3_post(
    request: Request,
    csrf: str = Form(...),
    objetivo: str = Form(...),
    refeicoes_por_dia: int = Form(...),
    sexo: str = Form(...),
    altura_cm: int = Form(...),
    atividade: str = Form(...),
):
    if not can_access(request, "step3"):
        return redirect("/step/2")
    ctx = base_context(request, step=3)
    ctx["values"] = {
        "objetivo": objetivo,
        "refeicoes_por_dia": refeicoes_por_dia,
        "sexo": sexo,
        "altura_cm": altura_cm,
        "atividade": atividade,
    }

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue e tente de novo."
        return templates.TemplateResponse("step3.html", ctx)

    try:
        payload = Step3In(
            objetivo=objetivo,
            refeicoes_por_dia=refeicoes_por_dia,
            sexo=sexo,
            altura_cm=altura_cm,
            atividade=atividade,
        )
    except ValidationError as e:
        errors = {}
        for err in e.errors():
            field = err.get("loc", ["__all__"])[0]
            errors[str(field)] = err.get("msg", "Campo inválido")
        ctx["errors"] = errors
        return templates.TemplateResponse("step3.html", ctx)

    request.session["step3"] = payload.model_dump()
    for k in ["macros", "step4", "step5"]:
        request.session.pop(k, None)

    await upsert_lead_progress(request, "step3", request.session["step3"])
    return redirect("/macros")


# --------------------------------------------------
# MACROS
# --------------------------------------------------
@app.get("/macros", response_class=HTMLResponse)
async def macros(request: Request):
    if not can_access(request, "macros"):
        return redirect("/step/3" if "step2" in request.session else "/")

    ctx = base_context(request, step=4)

    step1 = request.session.get("step1", {})
    step3 = request.session.get("step3", {})

    result = compute_macros(
        peso_kg=float(step1["peso"]),
        altura_cm=int(step3["altura_cm"]),
        idade=int(step1["idade"]),
        sexo=str(step3["sexo"]),
        atividade=str(step3["atividade"]),
        objetivo=str(step3["objetivo"]),
        refeicoes_por_dia=int(step3["refeicoes_por_dia"]),
    )

    macros_payload = MacrosIn(
        bmr=result.bmr,
        tdee=result.tdee,
        cal_target=result.cal_target,
        protein_g=result.protein_g,
        carbs_g=result.carbs_g,
        fat_g=result.fat_g,
        protein_kcal=result.protein_kcal,
        carbs_kcal=result.carbs_kcal,
        fat_kcal=result.fat_kcal,
        protein_pct=result.protein_pct,
        carbs_pct=result.carbs_pct,
        fat_pct=result.fat_pct,
        kcal_per_meal=result.kcal_per_meal,
        protein_per_meal_g=result.protein_per_meal_g,
        carbs_per_meal_g=result.carbs_per_meal_g,
        fat_per_meal_g=result.fat_per_meal_g,
    ).model_dump()

    ctx["macros"] = macros_payload
    ctx["refeicoes"] = step3.get("refeicoes_por_dia")
    return templates.TemplateResponse("macros.html", ctx)


@app.post("/macros/confirm")
async def macros_confirm(request: Request, csrf: str = Form(...)):
    if not can_access(request, "macros"):
        return redirect("/step/3")
    if not csrf_check(request, csrf):
        return redirect("/macros")

    step1 = request.session.get("step1", {})
    step3 = request.session.get("step3", {})

    result = compute_macros(
        peso_kg=float(step1["peso"]),
        altura_cm=int(step3["altura_cm"]),
        idade=int(step1["idade"]),
        sexo=str(step3["sexo"]),
        atividade=str(step3["atividade"]),
        objetivo=str(step3["objetivo"]),
        refeicoes_por_dia=int(step3["refeicoes_por_dia"]),
    )

    request.session["macros"] = MacrosIn(
        bmr=result.bmr,
        tdee=result.tdee,
        cal_target=result.cal_target,
        protein_g=result.protein_g,
        carbs_g=result.carbs_g,
        fat_g=result.fat_g,
        protein_kcal=result.protein_kcal,
        carbs_kcal=result.carbs_kcal,
        fat_kcal=result.fat_kcal,
        protein_pct=result.protein_pct,
        carbs_pct=result.carbs_pct,
        fat_pct=result.fat_pct,
        kcal_per_meal=result.kcal_per_meal,
        protein_per_meal_g=result.protein_per_meal_g,
        carbs_per_meal_g=result.carbs_per_meal_g,
        fat_per_meal_g=result.fat_per_meal_g,
    ).model_dump()

    await upsert_lead_progress(request, "macros", request.session["macros"])
    return redirect("/step/4")


# --------------------------------------------------
# STEP 4
# --------------------------------------------------
@app.get("/step/4", response_class=HTMLResponse)
async def step4(request: Request):
    if not can_access(request, "step4"):
        return redirect("/macros" if "step3" in request.session else "/")
    ctx = base_context(request, step=5)
    ctx["values"] = request.session.get("step4", {})
    return templates.TemplateResponse("step4.html", ctx)


@app.post("/step/4", response_class=HTMLResponse)
async def step4_post(
    request: Request,
    csrf: str = Form(...),
    alergias_texto: str = Form(""),
    nao_come: str = Form(""),
    alergias_tags: list[str] = Form([]),
    restricoes_tags: list[str] = Form([]),
):
    if not can_access(request, "step4"):
        return redirect("/macros")

    ctx = base_context(request, step=5)
    ctx["values"] = {
        "alergias_texto": alergias_texto,
        "nao_come": nao_come,
        "alergias_tags": alergias_tags,
        "restricoes_tags": restricoes_tags,
    }

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue e tente de novo."
        return templates.TemplateResponse("step4.html", ctx)

    try:
        payload = Step4In(
            alergias_texto=(alergias_texto or "").strip() or None,
            alergias_tags=alergias_tags or [],
            nao_come=(nao_come or "").strip() or None,
            restricoes_tags=restricoes_tags or [],
        )
    except ValidationError:
        ctx["errors"]["__all__"] = "Revise suas respostas e tente novamente."
        return templates.TemplateResponse("step4.html", ctx)

    request.session["step4"] = payload.model_dump()
    request.session.pop("step5", None)

    await upsert_lead_progress(request, "step4", request.session["step4"])
    return redirect("/step/5")


# --------------------------------------------------
# STEP 5
# --------------------------------------------------
@app.get("/step/5", response_class=HTMLResponse)
async def step5(request: Request):
    if not can_access(request, "step5"):
        return redirect("/step/4")
    ctx = base_context(request, step=6)
    ctx["values"] = request.session.get("step5", {})
    return templates.TemplateResponse("step5.html", ctx)


@app.post("/step/5", response_class=HTMLResponse)
async def step5_post(
    request: Request,
    csrf: str = Form(...),
    observacoes: str = Form(""),
):
    if not can_access(request, "step5"):
        return redirect("/step/4")

    ctx = base_context(request, step=6)
    ctx["values"] = {"observacoes": observacoes}

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue e tente de novo."
        return templates.TemplateResponse("step5.html", ctx)

    try:
        payload = Step5In(observacoes=(observacoes or "").strip() or None)
    except ValidationError:
        ctx["errors"]["__all__"] = "Revise suas respostas e tente novamente."
        return templates.TemplateResponse("step5.html", ctx)

    request.session["step5"] = payload.model_dump()
    await upsert_lead_progress(request, "step5", request.session["step5"])
    return redirect("/review")


# --------------------------------------------------
# REVIEW + CONFIRM
# --------------------------------------------------
@app.get("/review", response_class=HTMLResponse)
async def review(request: Request):
    if not can_access(request, "review"):
        if "step4" in request.session:
            return redirect("/step/5")
        if "macros" in request.session:
            return redirect("/step/4")
        if "step3" in request.session:
            return redirect("/macros")
        if "step2" in request.session:
            return redirect("/step/3")
        if "step1" in request.session:
            return redirect("/step/2")
        return redirect("/")

    ctx = base_context(request, step=7)
    ctx["data"] = {
        "step1": request.session.get("step1", {}),
        "step2": request.session.get("step2", {}),
        "step3": request.session.get("step3", {}),
        "macros": request.session.get("macros", {}),
        "step4": request.session.get("step4", {}),
        "step5": request.session.get("step5", {}),
    }
    return templates.TemplateResponse("review.html", ctx)


@app.post("/review/confirm", response_class=HTMLResponse)
async def confirm(request: Request, csrf: str = Form(...)):
    if not can_access(request, "review"):
        return redirect("/")
    if not csrf_check(request, csrf):
        return redirect("/review")

    doc = UserCreate(
        **request.session.get("step1", {}),
        **request.session.get("step2", {}),
        **request.session.get("step3", {}),
        **request.session.get("macros", {}),
        **request.session.get("step4", {}),
        **request.session.get("step5", {}),
    )

    db = get_db()
    await db.get_collection("users").insert_one(doc.model_dump())

    try:
        await upsert_lead_progress(request, "completed", {"at": datetime.utcnow().isoformat()})
    except Exception:
        pass

    request.session.clear()
    return redirect("/")


# --------------------------------------------------
# Reset
# --------------------------------------------------
@app.post("/reset")
async def reset(request: Request, csrf: str = Form(...)):
    if not csrf_check(request, csrf):
        return redirect("/")
    request.session.clear()
    return redirect("/")
