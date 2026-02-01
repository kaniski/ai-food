from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# --------------------------------------------------
# STEP 1 — Dados básicos
# --------------------------------------------------
class Step1In(BaseModel):
    email: EmailStr
    nome: str
    numero: str
    idade: int
    peso: float

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        partes = v.strip().split()
        if len(partes) < 2 or any(len(p) < 2 for p in partes):
            raise ValueError("Informe nome e sobrenome")
        return v.strip()

    @field_validator("numero")
    @classmethod
    def validar_numero(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10 or len(digits) > 13:
            raise ValueError("Número inválido")
        return digits

    @field_validator("idade")
    @classmethod
    def validar_idade(cls, v: int) -> int:
        if v < 10 or v > 100:
            raise ValueError("Idade inválida")
        return v

    @field_validator("peso")
    @classmethod
    def validar_peso(cls, v: float) -> float:
        if v < 20 or v > 300:
            raise ValueError("Peso inválido")
        return v


# --------------------------------------------------
# STEP 2 — Perguntas de dor/desejo
# --------------------------------------------------
class Step2In(BaseModel):
    feliz_corpo: bool
    mudar_rapido: bool
    cansado_espelho: bool


# --------------------------------------------------
# STEP 3 — Objetivo e rotina
# --------------------------------------------------
class Step3In(BaseModel):
    objetivo: str  # emagrecer | engordar | ganhar_massa
    refeicoes_por_dia: int

    @field_validator("refeicoes_por_dia")
    @classmethod
    def validar_refeicoes(cls, v: int) -> int:
        if v not in [2, 3, 4, 5, 6]:
            raise ValueError("Quantidade inválida")
        return v


# --------------------------------------------------
# STEP 4 — Restrições e alergias
# --------------------------------------------------
class Step4In(BaseModel):
    alergias_texto: Optional[str] = None
    alergias_tags: List[str] = []
    nao_come: Optional[str] = None
    restricoes_tags: List[str] = []


# --------------------------------------------------
# STEP 5 — Observações finais
# --------------------------------------------------
class Step5In(BaseModel):
    observacoes: Optional[str] = None


# --------------------------------------------------
# USER — Documento final para MongoDB
# --------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    nome: str
    numero: str
    idade: int
    peso: float

    feliz_corpo: bool
    mudar_rapido: bool
    cansado_espelho: bool

    objetivo: str
    refeicoes_por_dia: int

    alergias_texto: Optional[str] = None
    alergias_tags: List[str] = []
    nao_come: Optional[str] = None
    restricoes_tags: List[str] = []

    observacoes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
