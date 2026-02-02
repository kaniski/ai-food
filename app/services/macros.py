from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MacroResult:
    bmr: int
    tdee: int
    cal_target: int

    protein_g: int
    carbs_g: int
    fat_g: int

    protein_per_meal_g: int
    carbs_per_meal_g: int
    fat_per_meal_g: int
    kcal_per_meal: int

    protein_kcal: int
    carbs_kcal: int
    fat_kcal: int

    protein_pct: int
    carbs_pct: int
    fat_pct: int


def _round_int(x: float) -> int:
    return int(round(x))


def _activity_factor(level: str) -> float:
    # padrão mercado (simples e consistente para MVP)
    mapping = {
        "sedentario": 1.2,
        "leve": 1.375,
        "moderado": 1.55,
        "alto": 1.725,
        "muito_alto": 1.9,
    }
    return mapping.get(level, 1.2)


def _protein_factor(goal: str) -> float:
    # MVP: escolhas simples e defensáveis
    # emagrecer/ganhar_massa = um pouco mais alto
    if goal in ["emagrecer", "ganhar_massa"]:
        return 1.8
    return 1.6


def _goal_adjustment(goal: str) -> float:
    # percentual sobre TDEE
    # emagrecer: -15%
    # manter: 0%
    # ganhar_massa: +10%
    mapping = {
        "emagrecer": -0.15,
        "manter": 0.0,
        "engordar": 0.10,       # para quem quer subir peso sem foco em massa magra
        "ganhar_massa": 0.10,   # superávit leve
    }
    return mapping.get(goal, 0.0)


def compute_macros(
    *,
    peso_kg: float,
    altura_cm: int,
    idade: int,
    sexo: str,
    atividade: str,
    objetivo: str,
    refeicoes_por_dia: int,
) -> MacroResult:
    # -------------------------
    # 1) BMR (Mifflin-St Jeor)
    # -------------------------
    # homem: +5 | mulher: -161
    sex_term = 5 if sexo == "masculino" else -161
    bmr = (10 * peso_kg) + (6.25 * altura_cm) - (5 * idade) + sex_term
    bmr_i = _round_int(bmr)

    # -------------------------
    # 2) TDEE
    # -------------------------
    tdee = bmr * _activity_factor(atividade)
    tdee_i = _round_int(tdee)

    # -------------------------
    # 3) Calorias alvo (objetivo)
    # -------------------------
    cal_target = tdee * (1.0 + _goal_adjustment(objetivo))
    cal_target_i = max(1200, _round_int(cal_target))  # guardrail MVP

    # -------------------------
    # 4) Macros
    # Abordagem: proteína por kg, gordura por % e carbo como saldo
    # -------------------------
    prot_factor = _protein_factor(objetivo)
    protein_g = peso_kg * prot_factor
    protein_kcal = protein_g * 4

    fat_pct = 0.25
    fat_kcal = cal_target_i * fat_pct
    fat_g = fat_kcal / 9

    carbs_kcal = cal_target_i - (protein_kcal + fat_kcal)

    # Se sobrar negativo, reduz gordura e recalcula (prioriza proteína)
    if carbs_kcal < 0:
        fat_pct = 0.20
        fat_kcal = cal_target_i * fat_pct
        fat_g = fat_kcal / 9
        carbs_kcal = cal_target_i - (protein_kcal + fat_kcal)

    # Se ainda negativo, reduz um pouco proteína (último recurso)
    if carbs_kcal < 0:
        prot_factor = 1.6
        protein_g = peso_kg * prot_factor
        protein_kcal = protein_g * 4
        carbs_kcal = cal_target_i - (protein_kcal + fat_kcal)

    carbs_g = carbs_kcal / 4 if carbs_kcal > 0 else 0

    # arredondamentos de UX
    protein_g_i = max(0, _round_int(protein_g))
    fat_g_i = max(0, _round_int(fat_g))
    carbs_g_i = max(0, _round_int(carbs_g))

    protein_kcal_i = protein_g_i * 4
    fat_kcal_i = fat_g_i * 9
    carbs_kcal_i = carbs_g_i * 4

    total_kcal_calc = max(1, protein_kcal_i + fat_kcal_i + carbs_kcal_i)

    protein_pct = _round_int((protein_kcal_i / total_kcal_calc) * 100)
    fat_pct_i = _round_int((fat_kcal_i / total_kcal_calc) * 100)
    carbs_pct = max(0, 100 - protein_pct - fat_pct_i)

    # por refeição
    meals = max(1, refeicoes_por_dia)
    protein_pm = max(0, _round_int(protein_g_i / meals))
    fat_pm = max(0, _round_int(fat_g_i / meals))
    carbs_pm = max(0, _round_int(carbs_g_i / meals))
    kcal_pm = max(0, _round_int(cal_target_i / meals))

    return MacroResult(
        bmr=bmr_i,
        tdee=tdee_i,
        cal_target=cal_target_i,
        protein_g=protein_g_i,
        carbs_g=carbs_g_i,
        fat_g=fat_g_i,
        protein_per_meal_g=protein_pm,
        carbs_per_meal_g=carbs_pm,
        fat_per_meal_g=fat_pm,
        kcal_per_meal=kcal_pm,
        protein_kcal=protein_kcal_i,
        carbs_kcal=carbs_kcal_i,
        fat_kcal=fat_kcal_i,
        protein_pct=protein_pct,
        carbs_pct=carbs_pct,
        fat_pct=fat_pct_i,
    )
