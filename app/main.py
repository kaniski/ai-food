from __future__ import annotations

import secrets
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, SESSION_COOKIE, SESSION_MAX_AGE_SECONDS
from app.schemas import Step1In, Step2In, Step3In, Step4In, Step5In, UserCreate
from app.services.mongo import get_db

# --------------------------------------------------
# Carrega variáveis de ambiente (.env)
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# App FastAPI
# --------------------------------------------------
app = FastAPI()

# --------------------------------------------------
# Middlewares
# --------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie=SESSION_COOKIE,
    max_age=SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=False,  # em produção vira True
)

# --------------------------------------------------
# Static e Templates
# --------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# --------------------------------------------------
# Startup: testa conexão com MongoDB
# --------------------------------------------------
@app.on_event("startup")
async def startup_event():
    db = get_db()
    await db.command("ping")
    print("✅ MongoDB conectado com sucesso")


# --------------------------------------------------
# Sessão / CSRF / Guardas de etapa
# --------------------------------------------------
def ensure_csrf(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(24)
        request.session["csrf"] = token
    return token


def csrf_check(request: Request, csrf: str | None) -> bool:
    expected = request.session.get("csrf")
    return bool(expected and csrf and secrets.compare_digest(expected, csrf))


def require_step(request: Request, step_needed: int) -> bool:
    # step_needed: 1..5
    if step_needed <= 1:
        return True
    if step_needed >= 2 and "step1" not in request.session:
        return False
    if step_needed >= 3 and "step2" not in request.session:
        return False
    if step_needed >= 4 and "step3" not in request.session:
        return False
    if step_needed >= 5 and "step4" not in request.session:
        return False
    return True


def base_context(request: Request, step: int) -> Dict[str, Any]:
    return {
        "request": request,
        "step": step,
        "page_title": "MicroNutri — Plano alimentar simples e personalizado",
        "meta_description": "Crie um plano alimentar prático, adaptado às suas preferências e objetivos.",
        "errors": {},
        "values": {},
        "csrf_token": ensure_csrf(request),
        "saved": request.session.get("saved_demo", False),
        "saved_id": request.session.get("saved_id"),
    }


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def as_bool(v: str) -> bool:
    return v.strip().lower() in ["1", "true", "sim", "yes", "y", "on"]


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
    ctx["values"] = {
        "email": email,
        "nome": nome,
        "numero": numero,
        "idade": idade,
        "peso": peso,
    }

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
    # Limpando qualquer “salvo” anterior, caso a pessoa edite e confirme de novo
    request.session.pop("saved_demo", None)
    request.session.pop("saved_id", None)
    return redirect("/step/2")


# --------------------------------------------------
# STEP 2
# --------------------------------------------------
@app.get("/step/2", response_class=HTMLResponse)
async def step2(request: Request):
    if not require_step(request, 2):
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
    if not require_step(request, 2):
        return redirect("/")
    ctx = base_context(request, step=2)
    ctx["values"] = {
        "feliz_corpo": feliz_corpo,
        "mudar_rapido": mudar_rapido,
        "cansado_espelho": cansado_espelho,
    }

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue a página e tente de novo."
        return templates.TemplateResponse("step2.html", ctx)

    try:
        payload = Step2In(
            feliz_corpo=as_bool(feliz_corpo),
            mudar_rapido=as_bool(mudar_rapido),
            cansado_espelho=as_bool(cansado_espelho),
        )
    except ValidationError as e:
        ctx["errors"]["__all__"] = "Responda todas as perguntas para continuar."
        return templates.TemplateResponse("step2.html", ctx)

    request.session["step2"] = payload.model_dump()
    return redirect("/step/3")


# --------------------------------------------------
# STEP 3
# --------------------------------------------------
@app.get("/step/3", response_class=HTMLResponse)
async def step3(request: Request):
    if not require_step(request, 3):
        return redirect("/" if "step1" not in request.session else "/step/2")
    ctx = base_context(request, step=3)
    ctx["values"] = request.session.get("step3", {})
    return templates.TemplateResponse("step3.html", ctx)


@app.post("/step/3", response_class=HTMLResponse)
async def step3_post(
    request: Request,
    csrf: str = Form(...),
    objetivo: str = Form(...),
    refeicoes_por_dia: int = Form(...),
):
    if not require_step(request, 3):
        return redirect("/" if "step1" not in request.session else "/step/2")
    ctx = base_context(request, step=3)
    ctx["values"] = {"objetivo": objetivo, "refeicoes_por_dia": refeicoes_por_dia}

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue a página e tente de novo."
        return templates.TemplateResponse("step3.html", ctx)

    try:
        payload = Step3In(objetivo=objetivo, refeicoes_por_dia=refeicoes_por_dia)
    except ValidationError as e:
        errors = {}
        for err in e.errors():
            field = err.get("loc", ["__all__"])[0]
            errors[str(field)] = err.get("msg", "Campo inválido")
        ctx["errors"] = errors
        return templates.TemplateResponse("step3.html", ctx)

    request.session["step3"] = payload.model_dump()
    return redirect("/step/4")


# --------------------------------------------------
# STEP 4
# --------------------------------------------------
@app.get("/step/4", response_class=HTMLResponse)
async def step4(request: Request):
    if not require_step(request, 4):
        return redirect("/step/3")
    ctx = base_context(request, step=4)
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
    if not require_step(request, 4):
        return redirect("/step/3")
    ctx = base_context(request, step=4)
    ctx["values"] = {
        "alergias_texto": alergias_texto,
        "nao_come": nao_come,
        "alergias_tags": alergias_tags,
        "restricoes_tags": restricoes_tags,
    }

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue a página e tente de novo."
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
    return redirect("/step/5")


# --------------------------------------------------
# STEP 5
# --------------------------------------------------
@app.get("/step/5", response_class=HTMLResponse)
async def step5(request: Request):
    if not require_step(request, 5):
        return redirect("/step/4")
    ctx = base_context(request, step=5)
    ctx["values"] = request.session.get("step5", {})
    return templates.TemplateResponse("step5.html", ctx)


@app.post("/step/5", response_class=HTMLResponse)
async def step5_post(
    request: Request,
    csrf: str = Form(...),
    observacoes: str = Form(""),
):
    if not require_step(request, 5):
        return redirect("/step/4")
    ctx = base_context(request, step=5)
    ctx["values"] = {"observacoes": observacoes}

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue a página e tente de novo."
        return templates.TemplateResponse("step5.html", ctx)

    try:
        payload = Step5In(observacoes=(observacoes or "").strip() or None)
    except ValidationError:
        ctx["errors"]["__all__"] = "Revise suas respostas e tente novamente."
        return templates.TemplateResponse("step5.html", ctx)

    request.session["step5"] = payload.model_dump()
    return redirect("/review")


# --------------------------------------------------
# REVIEW + CONFIRM (Mongo insert)
# --------------------------------------------------
@app.get("/review", response_class=HTMLResponse)
async def review(request: Request):
    if "step5" not in request.session:
        # evita review sem completar o fluxo
        if "step4" in request.session:
            return redirect("/step/5")
        if "step3" in request.session:
            return redirect("/step/4")
        if "step2" in request.session:
            return redirect("/step/3")
        if "step1" in request.session:
            return redirect("/step/2")
        return redirect("/")

    ctx = base_context(request, step=6)

    ctx["data"] = {
        "step1": request.session.get("step1", {}),
        "step2": request.session.get("step2", {}),
        "step3": request.session.get("step3", {}),
        "step4": request.session.get("step4", {}),
        "step5": request.session.get("step5", {}),
    }
    return templates.TemplateResponse("review.html", ctx)


@app.post("/review/confirm", response_class=HTMLResponse)
async def confirm(request: Request, csrf: str = Form(...)):
    if "step5" not in request.session:
        return redirect("/")

    ctx = base_context(request, step=6)

    if not csrf_check(request, csrf):
        ctx["errors"]["__all__"] = "Sessão expirada. Recarregue a página e tente de novo."
        ctx["data"] = {
            "step1": request.session.get("step1", {}),
            "step2": request.session.get("step2", {}),
            "step3": request.session.get("step3", {}),
            "step4": request.session.get("step4", {}),
            "step5": request.session.get("step5", {}),
        }
        return templates.TemplateResponse("review.html", ctx)

    # Monta documento final (UserCreate) e persiste em users
    try:
        doc = UserCreate(
            **request.session.get("step1", {}),
            **request.session.get("step2", {}),
            **request.session.get("step3", {}),
            **request.session.get("step4", {}),
            **request.session.get("step5", {}),
        )
    except ValidationError:
        ctx["errors"]["__all__"] = "Algum dado ficou inconsistente. Volte e revise as etapas."
        ctx["data"] = {
            "step1": request.session.get("step1", {}),
            "step2": request.session.get("step2", {}),
            "step3": request.session.get("step3", {}),
            "step4": request.session.get("step4", {}),
            "step5": request.session.get("step5", {}),
        }
        return templates.TemplateResponse("review.html", ctx)

    db = get_db()
    res = await db.get_collection("users").insert_one(doc.model_dump())

    request.session["saved_demo"] = True
    request.session["saved_id"] = str(res.inserted_id)

    return redirect("/review")


# --------------------------------------------------
# Reset
# --------------------------------------------------
@app.post("/reset")
async def reset(request: Request, csrf: str = Form(...)):
    # mesmo o reset, validamos csrf para evitar post “solto”
    if not csrf_check(request, csrf):
        return redirect("/")
    request.session.clear()
    return redirect("/")
