"""
EN 1990 Load Combination Generator.
Generates ULS and SLS combinations per Eurocode 0 (EN 1990:2002).
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import itertools


# ============== Load Categories & ψ Factors (Table A1.1) ==============

LOAD_CATEGORIES = {
    "A": {"name": "Domestic / Residential", "psi_0": 0.7, "psi_1": 0.5, "psi_2": 0.3},
    "B": {"name": "Office areas", "psi_0": 0.7, "psi_1": 0.5, "psi_2": 0.3},
    "C": {"name": "Congregation areas", "psi_0": 0.7, "psi_1": 0.7, "psi_2": 0.6},
    "D": {"name": "Shopping areas", "psi_0": 0.7, "psi_1": 0.7, "psi_2": 0.6},
    "E": {"name": "Storage areas", "psi_0": 1.0, "psi_1": 0.9, "psi_2": 0.8},
    "F": {"name": "Traffic (≤30 kN)", "psi_0": 0.7, "psi_1": 0.7, "psi_2": 0.6},
    "G": {"name": "Traffic (30-160 kN)", "psi_0": 0.7, "psi_1": 0.5, "psi_2": 0.3},
    "H": {"name": "Roofs (non-accessible)", "psi_0": 0.0, "psi_1": 0.0, "psi_2": 0.0},
    "Snow_below_1000m": {"name": "Snow (≤1000m altitude)", "psi_0": 0.5, "psi_1": 0.2, "psi_2": 0.0},
    "Snow_above_1000m": {"name": "Snow (>1000m altitude)", "psi_0": 0.7, "psi_1": 0.5, "psi_2": 0.2},
    "Wind": {"name": "Wind actions", "psi_0": 0.6, "psi_1": 0.2, "psi_2": 0.0},
    "Temperature": {"name": "Temperature (non-fire)", "psi_0": 0.6, "psi_1": 0.5, "psi_2": 0.0},
}

# γ factors (Table A1.2(B))
GAMMA_FACTORS = {
    "STR/GEO": {
        "gamma_G_unfav": 1.35,
        "gamma_G_fav": 1.00,
        "gamma_Q_unfav": 1.50,
        "gamma_Q_fav": 0.00,
    },
    "EQU": {
        "gamma_G_unfav": 1.10,
        "gamma_G_fav": 0.90,
        "gamma_Q_unfav": 1.50,
        "gamma_Q_fav": 0.00,
    },
}


@dataclass
class LoadCase:
    """Represents a single load case."""
    name: str
    type: str  # "permanent", "variable", "accidental"
    category: str  # Load category for ψ factors
    value: float  # Characteristic value
    favorable: bool = False  # Whether this load is favorable

    def get_psi(self, psi_type: str) -> float:
        cat = LOAD_CATEGORIES.get(self.category, {})
        return cat.get(psi_type, 0)


@dataclass
class LoadCombination:
    """Represents a calculated load combination."""
    name: str
    type: str  # "ULS_6.10", "ULS_6.10a", "ULS_6.10b", "SLS_char", etc.
    expression: str
    value: float
    breakdown: List[Dict[str, Any]]


class LoadCombinationGenerator:
    """Generate load combinations per EN 1990."""

    def __init__(self, approach: str = "6.10", limit_state: str = "STR/GEO"):
        """
        approach: "6.10" (single expression), "6.10ab" (dual expressions)
        limit_state: "STR/GEO" or "EQU"
        """
        self.approach = approach
        self.limit_state = limit_state
        self.gammas = GAMMA_FACTORS[limit_state]

    def generate_uls(self, load_cases: List[LoadCase]) -> List[LoadCombination]:
        """Generate ULS combinations."""
        permanent = [lc for lc in load_cases if lc.type == "permanent"]
        variable = [lc for lc in load_cases if lc.type == "variable"]

        combinations = []

        if not variable:
            # Permanent only
            combo = self._permanent_only(permanent)
            combinations.append(combo)
            return combinations

        if self.approach == "6.10":
            combinations.extend(self._generate_6_10(permanent, variable))
        else:
            combinations.extend(self._generate_6_10a(permanent, variable))
            combinations.extend(self._generate_6_10b(permanent, variable))

        return combinations

    def generate_sls(self, load_cases: List[LoadCase]) -> Dict[str, List[LoadCombination]]:
        """Generate all SLS combinations."""
        permanent = [lc for lc in load_cases if lc.type == "permanent"]
        variable = [lc for lc in load_cases if lc.type == "variable"]

        return {
            "characteristic": self._sls_characteristic(permanent, variable),
            "frequent": self._sls_frequent(permanent, variable),
            "quasi_permanent": self._sls_quasi_permanent(permanent, variable),
        }

    def _permanent_only(self, permanent: List[LoadCase]) -> LoadCombination:
        """Combination with permanent loads only."""
        breakdown = []
        total = 0
        expr_parts = []

        for lc in permanent:
            gamma = self.gammas["gamma_G_fav" if lc.favorable else "gamma_G_unfav"]
            factored = gamma * lc.value
            total += factored
            breakdown.append({
                "load": lc.name, "char_value": lc.value,
                "factor": gamma, "factored": round(factored, 2)
            })
            expr_parts.append(f"{gamma}×{lc.name}")

        return LoadCombination(
            name="Permanent only",
            type="ULS_perm",
            expression=" + ".join(expr_parts),
            value=round(total, 2),
            breakdown=breakdown
        )

    def _generate_6_10(
        self, permanent: List[LoadCase], variable: List[LoadCase]
    ) -> List[LoadCombination]:
        """
        Equation 6.10: ΣγG,j×Gk,j + γQ,1×Qk,1 + ΣγQ,i×ψ0,i×Qk,i
        """
        combinations = []

        for lead_idx, lead in enumerate(variable):
            breakdown = []
            total = 0
            expr_parts = []

            # Permanent loads
            for lc in permanent:
                gamma = self.gammas["gamma_G_fav" if lc.favorable else "gamma_G_unfav"]
                factored = gamma * lc.value
                total += factored
                breakdown.append({
                    "load": lc.name, "char_value": lc.value,
                    "factor": gamma, "factored": round(factored, 2),
                    "type": "permanent"
                })
                expr_parts.append(f"{gamma}×{lc.name}")

            # Leading variable action
            gamma_Q = self.gammas["gamma_Q_unfav"]
            factored_lead = gamma_Q * lead.value
            total += factored_lead
            breakdown.append({
                "load": lead.name, "char_value": lead.value,
                "factor": gamma_Q, "psi": 1.0,
                "factored": round(factored_lead, 2), "type": "leading"
            })
            expr_parts.append(f"{gamma_Q}×{lead.name}")

            # Accompanying variable actions
            for i, var in enumerate(variable):
                if i == lead_idx:
                    continue
                psi_0 = var.get_psi("psi_0")
                factored_acc = gamma_Q * psi_0 * var.value
                total += factored_acc
                breakdown.append({
                    "load": var.name, "char_value": var.value,
                    "factor": gamma_Q, "psi": psi_0,
                    "factored": round(factored_acc, 2), "type": "accompanying"
                })
                expr_parts.append(f"{gamma_Q}×{psi_0}×{var.name}")

            combinations.append(LoadCombination(
                name=f"ULS 6.10 (leading: {lead.name})",
                type="ULS_6.10",
                expression=" + ".join(expr_parts),
                value=round(total, 2),
                breakdown=breakdown
            ))

        return combinations

    def _generate_6_10a(
        self, permanent: List[LoadCase], variable: List[LoadCase]
    ) -> List[LoadCombination]:
        """
        Equation 6.10a: ΣγG,j×Gk,j + γQ,1×ψ0,1×Qk,1 + ΣγQ,i×ψ0,i×Qk,i
        """
        combinations = []

        for lead_idx, lead in enumerate(variable):
            breakdown = []
            total = 0
            expr_parts = []

            for lc in permanent:
                gamma = self.gammas["gamma_G_fav" if lc.favorable else "gamma_G_unfav"]
                factored = gamma * lc.value
                total += factored
                breakdown.append({
                    "load": lc.name, "char_value": lc.value,
                    "factor": gamma, "factored": round(factored, 2),
                    "type": "permanent"
                })
                expr_parts.append(f"{gamma}×{lc.name}")

            # All variable actions with ψ0
            for i, var in enumerate(variable):
                gamma_Q = self.gammas["gamma_Q_unfav"]
                psi_0 = var.get_psi("psi_0")
                factored = gamma_Q * psi_0 * var.value
                total += factored
                breakdown.append({
                    "load": var.name, "char_value": var.value,
                    "factor": gamma_Q, "psi": psi_0,
                    "factored": round(factored, 2),
                    "type": "leading" if i == lead_idx else "accompanying"
                })
                expr_parts.append(f"{gamma_Q}×{psi_0}×{var.name}")

            combinations.append(LoadCombination(
                name=f"ULS 6.10a (leading: {lead.name})",
                type="ULS_6.10a",
                expression=" + ".join(expr_parts),
                value=round(total, 2),
                breakdown=breakdown
            ))

        return combinations

    def _generate_6_10b(
        self, permanent: List[LoadCase], variable: List[LoadCase]
    ) -> List[LoadCombination]:
        """
        Equation 6.10b: ΣξγG,j×Gk,j + γQ,1×Qk,1 + ΣγQ,i×ψ0,i×Qk,i
        Where ξ = 0.85 (recommended)
        """
        xi = 0.85
        combinations = []

        for lead_idx, lead in enumerate(variable):
            breakdown = []
            total = 0
            expr_parts = []

            for lc in permanent:
                gamma = self.gammas["gamma_G_fav" if lc.favorable else "gamma_G_unfav"]
                factored = xi * gamma * lc.value if not lc.favorable else gamma * lc.value
                total += factored
                factor_used = xi * gamma if not lc.favorable else gamma
                breakdown.append({
                    "load": lc.name, "char_value": lc.value,
                    "factor": round(factor_used, 3),
                    "factored": round(factored, 2), "type": "permanent",
                    "xi": xi if not lc.favorable else 1.0
                })
                expr_parts.append(f"{round(factor_used, 3)}×{lc.name}")

            gamma_Q = self.gammas["gamma_Q_unfav"]
            factored_lead = gamma_Q * lead.value
            total += factored_lead
            breakdown.append({
                "load": lead.name, "char_value": lead.value,
                "factor": gamma_Q, "psi": 1.0,
                "factored": round(factored_lead, 2), "type": "leading"
            })
            expr_parts.append(f"{gamma_Q}×{lead.name}")

            for i, var in enumerate(variable):
                if i == lead_idx:
                    continue
                psi_0 = var.get_psi("psi_0")
                factored_acc = gamma_Q * psi_0 * var.value
                total += factored_acc
                breakdown.append({
                    "load": var.name, "char_value": var.value,
                    "factor": gamma_Q, "psi": psi_0,
                    "factored": round(factored_acc, 2), "type": "accompanying"
                })
                expr_parts.append(f"{gamma_Q}×{psi_0}×{var.name}")

            combinations.append(LoadCombination(
                name=f"ULS 6.10b (leading: {lead.name})",
                type="ULS_6.10b",
                expression=" + ".join(expr_parts),
                value=round(total, 2),
                breakdown=breakdown
            ))

        return combinations

    def _sls_characteristic(
        self, permanent: List[LoadCase], variable: List[LoadCase]
    ) -> List[LoadCombination]:
        """SLS characteristic: ΣGk,j + Qk,1 + Σψ0,i×Qk,i"""
        combinations = []

        for lead_idx, lead in enumerate(variable):
            breakdown = []
            total = 0

            for lc in permanent:
                total += lc.value
                breakdown.append({"load": lc.name, "value": lc.value, "factor": 1.0})

            total += lead.value
            breakdown.append({"load": lead.name, "value": lead.value, "factor": 1.0, "type": "leading"})

            for i, var in enumerate(variable):
                if i == lead_idx:
                    continue
                psi_0 = var.get_psi("psi_0")
                total += psi_0 * var.value
                breakdown.append({"load": var.name, "value": var.value, "psi": psi_0})

            combinations.append(LoadCombination(
                name=f"SLS Char (leading: {lead.name})",
                type="SLS_characteristic",
                expression="ΣGk + Qk,1 + Σψ0,i×Qk,i",
                value=round(total, 2),
                breakdown=breakdown
            ))

        return combinations

    def _sls_frequent(
        self, permanent: List[LoadCase], variable: List[LoadCase]
    ) -> List[LoadCombination]:
        """SLS frequent: ΣGk,j + ψ1,1×Qk,1 + Σψ2,i×Qk,i"""
        combinations = []

        for lead_idx, lead in enumerate(variable):
            breakdown = []
            total = 0

            for lc in permanent:
                total += lc.value
                breakdown.append({"load": lc.name, "value": lc.value, "factor": 1.0})

            psi_1 = lead.get_psi("psi_1")
            total += psi_1 * lead.value
            breakdown.append({"load": lead.name, "value": lead.value, "psi": psi_1, "type": "leading"})

            for i, var in enumerate(variable):
                if i == lead_idx:
                    continue
                psi_2 = var.get_psi("psi_2")
                total += psi_2 * var.value
                breakdown.append({"load": var.name, "value": var.value, "psi": psi_2})

            combinations.append(LoadCombination(
                name=f"SLS Freq (leading: {lead.name})",
                type="SLS_frequent",
                expression="ΣGk + ψ1,1×Qk,1 + Σψ2,i×Qk,i",
                value=round(total, 2),
                breakdown=breakdown
            ))

        return combinations

    def _sls_quasi_permanent(
        self, permanent: List[LoadCase], variable: List[LoadCase]
    ) -> List[LoadCombination]:
        """SLS quasi-permanent: ΣGk,j + Σψ2,i×Qk,i"""
        breakdown = []
        total = 0

        for lc in permanent:
            total += lc.value
            breakdown.append({"load": lc.name, "value": lc.value, "factor": 1.0})

        for var in variable:
            psi_2 = var.get_psi("psi_2")
            total += psi_2 * var.value
            breakdown.append({"load": var.name, "value": var.value, "psi": psi_2})

        return [LoadCombination(
            name="SLS Quasi-permanent",
            type="SLS_quasi_permanent",
            expression="ΣGk + Σψ2,i×Qk,i",
            value=round(total, 2),
            breakdown=breakdown
        )]

    def serialize_combinations(
        self, combinations: List[LoadCombination]
    ) -> List[Dict[str, Any]]:
        """Convert combinations to serializable format."""
        return [
            {
                "name": c.name,
                "type": c.type,
                "expression": c.expression,
                "value": c.value,
                "breakdown": c.breakdown,
            }
            for c in combinations
        ]
