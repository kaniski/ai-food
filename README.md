# Micro Nutri Flow (FastAPI)

Fluxo de 5 etapas (forms) + página de resumo, sem banco, sem pagamentos, sem IA.
Dados ficam temporariamente em sessão (cookie assinado).

## Rodar localmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
