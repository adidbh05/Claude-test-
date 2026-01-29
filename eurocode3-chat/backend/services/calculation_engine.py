"""
Eurocode 3 Calculation Engine.
Provides rigorous steel design calculations per EN 1993-1-1.

All units: Forces in kN, moments in kNm, lengths in mm, stresses in N/mm² (MPa).
"""
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field


# ============== Material Properties ==============

STEEL_GRADES = {
    "S235": {"fy_16": 235, "fy_40": 225, "fy_63": 215, "fy_80": 215, "fu": 360, "E": 210000, "G": 81000},
    "S275": {"fy_16": 275, "fy_40": 265, "fy_63": 255, "fy_80": 245, "fu": 430, "E": 210000, "G": 81000},
    "S355": {"fy_16": 355, "fy_40": 345, "fy_63": 335, "fy_80": 325, "fu": 510, "E": 210000, "G": 81000},
    "S420": {"fy_16": 420, "fy_40": 400, "fy_63": 390, "fy_80": 370, "fu": 520, "E": 210000, "G": 81000},
    "S460": {"fy_16": 460, "fy_40": 440, "fy_63": 430, "fy_80": 410, "fu": 550, "E": 210000, "G": 81000},
}

# Partial safety factors (recommended values)
GAMMA_M0 = 1.00  # Resistance of cross-sections
GAMMA_M1 = 1.00  # Resistance of members to instability
GAMMA_M2 = 1.25  # Resistance of cross-sections in tension (net area), bolts, welds

# Imperfection factors for buckling curves (Table 6.1)
BUCKLING_CURVES = {
    "a0": 0.13,
    "a": 0.21,
    "b": 0.34,
    "c": 0.49,
    "d": 0.76,
}

# Bolt properties (Table 3.1 of EN 1993-1-8)
BOLT_GRADES = {
    "4.6":  {"fub": 400, "fyb": 240},
    "4.8":  {"fub": 400, "fyb": 320},
    "5.6":  {"fub": 500, "fyb": 300},
    "5.8":  {"fub": 500, "fyb": 400},
    "6.8":  {"fub": 600, "fyb": 480},
    "8.8":  {"fub": 800, "fyb": 640},
    "10.9": {"fub": 1000, "fyb": 900},
}

# Bolt hole diameters (d0 = d + clearance)
BOLT_CLEARANCES = {
    12: 1, 14: 1, 16: 2, 18: 2, 20: 2, 22: 2, 24: 2, 27: 3, 30: 3, 36: 3,
}

# Tensile stress area (As) for metric bolts
BOLT_AREAS = {
    12: {"A": 113, "As": 84.3},
    14: {"A": 154, "As": 115},
    16: {"A": 201, "As": 157},
    18: {"A": 254, "As": 192},
    20: {"A": 314, "As": 245},
    22: {"A": 380, "As": 303},
    24: {"A": 452, "As": 353},
    27: {"A": 573, "As": 459},
    30: {"A": 707, "As": 561},
    36: {"A": 1018, "As": 817},
}

# Correlation factor for fillet welds (Table 4.1 of EN 1993-1-8)
WELD_BETA_W = {
    "S235": 0.80,
    "S275": 0.85,
    "S355": 0.90,
    "S420": 1.00,
    "S460": 1.00,
}


def get_fy(grade: str, tf: float) -> float:
    """Get yield strength based on steel grade and flange thickness (Table 3.1)."""
    steel = STEEL_GRADES.get(grade)
    if not steel:
        raise ValueError(f"Unknown steel grade: {grade}")
    if tf <= 16:
        return steel["fy_16"]
    elif tf <= 40:
        return steel["fy_40"]
    elif tf <= 63:
        return steel["fy_63"]
    else:
        return steel["fy_80"]


def get_epsilon(fy: float) -> float:
    """Calculate epsilon factor: ε = √(235/fy)."""
    return math.sqrt(235 / fy)


# ============== Cross-Section Classification (Table 5.2) ==============

class CrossSectionClassifier:
    """Classify steel cross-sections per EN 1993-1-1, Table 5.2."""

    @staticmethod
    def classify_i_section(
        h: float, b: float, tw: float, tf: float, r: float,
        fy: float, NEd: float = 0, A: float = 0
    ) -> Dict[str, Any]:
        """
        Classify an I/H section.
        Returns classification for web and flange, plus overall class.
        """
        epsilon = get_epsilon(fy)

        # Flange classification (outstand element)
        c_flange = (b - tw - 2 * r) / 2
        ct_flange = c_flange / tf

        if ct_flange <= 9 * epsilon:
            flange_class = 1
        elif ct_flange <= 10 * epsilon:
            flange_class = 2
        elif ct_flange <= 14 * epsilon:
            flange_class = 3
        else:
            flange_class = 4

        # Web classification (internal element)
        c_web = h - 2 * tf - 2 * r
        ct_web = c_web / tw

        # Determine stress ratio for web
        if A > 0 and NEd != 0:
            # Combined bending and compression
            alpha = min(1.0, max(0, 0.5 * (1 + NEd / (A * fy))))
            psi = (2 * alpha - 1)  # Stress ratio

            if alpha > 0.5:
                # Compression dominant
                if ct_web <= 396 * epsilon / (13 * alpha - 1):
                    web_class = 1
                elif ct_web <= 456 * epsilon / (13 * alpha - 1):
                    web_class = 2
                else:
                    if psi > -1:
                        limit_3 = 42 * epsilon / (0.67 + 0.33 * psi)
                    else:
                        limit_3 = 62 * epsilon * (1 - psi) * math.sqrt(-psi)
                    web_class = 3 if ct_web <= limit_3 else 4
            else:
                # Pure bending or tension dominant
                if ct_web <= 72 * epsilon:
                    web_class = 1
                elif ct_web <= 83 * epsilon:
                    web_class = 2
                elif ct_web <= 124 * epsilon:
                    web_class = 3
                else:
                    web_class = 4
        else:
            # Pure bending (default)
            if ct_web <= 72 * epsilon:
                web_class = 1
            elif ct_web <= 83 * epsilon:
                web_class = 2
            elif ct_web <= 124 * epsilon:
                web_class = 3
            else:
                web_class = 4

        overall_class = max(flange_class, web_class)

        return {
            "overall_class": overall_class,
            "flange_class": flange_class,
            "web_class": web_class,
            "c_flange": round(c_flange, 1),
            "ct_flange": round(ct_flange, 2),
            "c_web": round(c_web, 1),
            "ct_web": round(ct_web, 2),
            "epsilon": round(epsilon, 4),
            "flange_limits": {
                "class_1": round(9 * epsilon, 2),
                "class_2": round(10 * epsilon, 2),
                "class_3": round(14 * epsilon, 2),
            },
            "web_limits_bending": {
                "class_1": round(72 * epsilon, 2),
                "class_2": round(83 * epsilon, 2),
                "class_3": round(124 * epsilon, 2),
            },
            "clause": "EN 1993-1-1, Table 5.2",
        }

    @staticmethod
    def classify_hollow_section(
        h: float, b: float, t: float, fy: float,
        is_circular: bool = False
    ) -> Dict[str, Any]:
        """Classify RHS/SHS/CHS section."""
        epsilon = get_epsilon(fy)

        if is_circular:
            dt = h / t  # d/t ratio for CHS
            if dt <= 50 * epsilon**2:
                section_class = 1
            elif dt <= 70 * epsilon**2:
                section_class = 2
            elif dt <= 90 * epsilon**2:
                section_class = 3
            else:
                section_class = 4

            return {
                "overall_class": section_class,
                "d_over_t": round(dt, 2),
                "epsilon": round(epsilon, 4),
                "limits": {
                    "class_1": round(50 * epsilon**2, 2),
                    "class_2": round(70 * epsilon**2, 2),
                    "class_3": round(90 * epsilon**2, 2),
                },
                "clause": "EN 1993-1-1, Table 5.2 (sheet 3)",
            }
        else:
            # RHS/SHS - internal compression parts
            c = max(h, b) - 3 * t  # conservative
            ct = c / t

            if ct <= 33 * epsilon:
                section_class = 1
            elif ct <= 38 * epsilon:
                section_class = 2
            elif ct <= 42 * epsilon:
                section_class = 3
            else:
                section_class = 4

            return {
                "overall_class": section_class,
                "c_over_t": round(ct, 2),
                "epsilon": round(epsilon, 4),
                "limits": {
                    "class_1": round(33 * epsilon, 2),
                    "class_2": round(38 * epsilon, 2),
                    "class_3": round(42 * epsilon, 2),
                },
                "clause": "EN 1993-1-1, Table 5.2 (sheet 1)",
            }


# ============== Resistance Calculations (Clause 6.2) ==============

class ResistanceCalculator:
    """Cross-section resistance calculations per EN 1993-1-1, Clause 6.2."""

    @staticmethod
    def tension_resistance(A: float, fy: float, Anet: Optional[float] = None,
                           fu: Optional[float] = None) -> Dict[str, Any]:
        """
        Tension resistance — Clause 6.2.3.
        Npl,Rd = A × fy / γM0  (plastic resistance of gross section)
        Nu,Rd  = 0.9 × Anet × fu / γM2 (ultimate resistance of net section)
        """
        Npl_Rd = A * fy / GAMMA_M0 / 1000  # kN

        result = {
            "Npl_Rd_kN": round(Npl_Rd, 1),
            "A_mm2": A,
            "fy_MPa": fy,
            "gamma_M0": GAMMA_M0,
            "governing": "Npl,Rd",
            "Nt_Rd_kN": round(Npl_Rd, 1),
            "clause": "EN 1993-1-1, Clause 6.2.3",
        }

        if Anet and fu:
            Nu_Rd = 0.9 * Anet * fu / GAMMA_M2 / 1000  # kN
            result["Nu_Rd_kN"] = round(Nu_Rd, 1)
            result["Anet_mm2"] = Anet
            result["fu_MPa"] = fu
            result["gamma_M2"] = GAMMA_M2
            result["Nt_Rd_kN"] = round(min(Npl_Rd, Nu_Rd), 1)
            result["governing"] = "Npl,Rd" if Npl_Rd <= Nu_Rd else "Nu,Rd"

        return result

    @staticmethod
    def compression_resistance(A: float, fy: float) -> Dict[str, Any]:
        """
        Compression resistance of cross-section — Clause 6.2.4.
        Nc,Rd = A × fy / γM0  (Class 1, 2, 3)
        """
        Nc_Rd = A * fy / GAMMA_M0 / 1000  # kN
        return {
            "Nc_Rd_kN": round(Nc_Rd, 1),
            "A_mm2": A,
            "fy_MPa": fy,
            "gamma_M0": GAMMA_M0,
            "clause": "EN 1993-1-1, Clause 6.2.4",
        }

    @staticmethod
    def bending_resistance(
        Wpl: float, Wel: float, fy: float, section_class: int
    ) -> Dict[str, Any]:
        """
        Bending resistance — Clause 6.2.5.
        Class 1 & 2: Mc,Rd = Wpl × fy / γM0
        Class 3:      Mc,Rd = Wel,min × fy / γM0
        """
        if section_class <= 2:
            Mc_Rd = Wpl * fy / GAMMA_M0 / 1e6  # kNm
            W_used = Wpl
            method = "Plastic (Wpl)"
        else:
            Mc_Rd = Wel * fy / GAMMA_M0 / 1e6  # kNm
            W_used = Wel
            method = "Elastic (Wel)"

        return {
            "Mc_Rd_kNm": round(Mc_Rd, 2),
            "W_used_mm3": W_used,
            "method": method,
            "section_class": section_class,
            "fy_MPa": fy,
            "gamma_M0": GAMMA_M0,
            "clause": "EN 1993-1-1, Clause 6.2.5",
        }

    @staticmethod
    def shear_resistance(Av: float, fy: float) -> Dict[str, Any]:
        """
        Shear resistance — Clause 6.2.6.
        Vpl,Rd = Av × (fy/√3) / γM0
        """
        Vpl_Rd = Av * (fy / math.sqrt(3)) / GAMMA_M0 / 1000  # kN
        return {
            "Vpl_Rd_kN": round(Vpl_Rd, 1),
            "Av_mm2": round(Av, 0),
            "fy_MPa": fy,
            "gamma_M0": GAMMA_M0,
            "clause": "EN 1993-1-1, Clause 6.2.6",
        }

    @staticmethod
    def shear_area_i_section(
        A: float, b: float, tw: float, tf: float, r: float, h: float
    ) -> float:
        """Calculate shear area for I/H section (major axis). Clause 6.2.6(3)."""
        Av = A - 2 * b * tf + (tw + 2 * r) * tf
        return max(Av, 1.0 * h * tw)  # η × hw × tw, η = 1.0

    @staticmethod
    def bending_shear_interaction(
        VEd: float, Vpl_Rd: float, Mc_Rd: float
    ) -> Dict[str, Any]:
        """
        Bending and shear interaction — Clause 6.2.8.
        If VEd > 0.5 × Vpl,Rd → reduced moment resistance.
        """
        ratio = VEd / Vpl_Rd

        if ratio <= 0.5:
            Mv_Rd = Mc_Rd
            reduction = 0
            interaction_needed = False
        else:
            rho = (2 * ratio - 1) ** 2
            Mv_Rd = Mc_Rd * (1 - rho)
            reduction = rho
            interaction_needed = True

        return {
            "VEd_kN": VEd,
            "Vpl_Rd_kN": Vpl_Rd,
            "shear_ratio": round(ratio, 3),
            "Mc_Rd_kNm": Mc_Rd,
            "Mv_Rd_kNm": round(Mv_Rd, 2),
            "rho": round(reduction, 4),
            "interaction_needed": interaction_needed,
            "clause": "EN 1993-1-1, Clause 6.2.8",
        }

    @staticmethod
    def combined_bending_axial(
        NEd: float, Nc_Rd: float, My_Ed: float, Mc_y_Rd: float,
        Mz_Ed: float = 0, Mc_z_Rd: float = 1,
        section_class: int = 1
    ) -> Dict[str, Any]:
        """
        Combined bending and axial force — Clause 6.2.9.
        For Class 1 & 2 I/H sections (simplified):
        MN,y,Rd = Mc,y,Rd × (1 − n) / (1 − 0.5a) but ≤ Mc,y,Rd
        """
        n = abs(NEd) / Nc_Rd if Nc_Rd > 0 else 0

        # Simplified interaction check
        utilization = n + abs(My_Ed) / Mc_y_Rd

        if Mc_z_Rd > 0:
            utilization_z = abs(Mz_Ed) / Mc_z_Rd
        else:
            utilization_z = 0

        return {
            "NEd_kN": NEd,
            "Nc_Rd_kN": Nc_Rd,
            "n_ratio": round(n, 4),
            "My_Ed_kNm": My_Ed,
            "Mc_y_Rd_kNm": Mc_y_Rd,
            "Mz_Ed_kNm": Mz_Ed,
            "Mc_z_Rd_kNm": Mc_z_Rd,
            "utilization": round(utilization + utilization_z, 4),
            "status": "OK" if (utilization + utilization_z) <= 1.0 else "FAIL",
            "clause": "EN 1993-1-1, Clause 6.2.9",
        }


# ============== Stability Checks (Clause 6.3) ==============

class StabilityCalculator:
    """Member stability calculations per EN 1993-1-1, Clause 6.3."""

    @staticmethod
    def flexural_buckling(
        NEd: float, A: float, fy: float,
        Lcr: float, i: float,
        buckling_curve: str = "b"
    ) -> Dict[str, Any]:
        """
        Flexural buckling check — Clause 6.3.1.
        Nb,Rd = χ × A × fy / γM1
        """
        E = 210000  # N/mm²

        # Non-dimensional slenderness
        lambda_1 = math.pi * math.sqrt(E / fy)  # ≈ 93.9ε
        lambda_bar = (Lcr / i) / lambda_1

        # Imperfection factor
        alpha = BUCKLING_CURVES.get(buckling_curve, 0.34)

        # Reduction factor χ
        phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar ** 2)
        chi = 1.0 / (phi + math.sqrt(phi ** 2 - lambda_bar ** 2))
        chi = min(chi, 1.0)

        # Design buckling resistance
        Nb_Rd = chi * A * fy / GAMMA_M1 / 1000  # kN

        # Utilization
        utilization = NEd / Nb_Rd if Nb_Rd > 0 else float('inf')

        # Critical load (Euler)
        Ncr = math.pi ** 2 * E * (i ** 2) * A / (Lcr ** 2) / 1000  # kN (approximate using I = A*i²)

        return {
            "NEd_kN": NEd,
            "Nb_Rd_kN": round(Nb_Rd, 1),
            "chi": round(chi, 4),
            "lambda_bar": round(lambda_bar, 4),
            "phi": round(phi, 4),
            "alpha": alpha,
            "buckling_curve": buckling_curve,
            "Lcr_mm": Lcr,
            "slenderness": round(Lcr / i, 1),
            "lambda_1": round(lambda_1, 1),
            "Ncr_kN": round(Ncr, 1),
            "utilization": round(utilization, 4),
            "status": "OK" if utilization <= 1.0 else "FAIL",
            "clause": "EN 1993-1-1, Clause 6.3.1",
        }

    @staticmethod
    def lateral_torsional_buckling(
        MEd: float, Wy: float, fy: float,
        Mcr: float, section_class: int = 1,
        ltb_curve: str = "b"
    ) -> Dict[str, Any]:
        """
        Lateral-torsional buckling check — Clause 6.3.2.
        Mb,Rd = χLT × Wy × fy / γM1

        Mcr should be pre-calculated or use simplified methods.
        """
        # Design resistance without LTB
        if section_class <= 2:
            W = Wy  # Wpl
        else:
            W = Wy  # Wel

        # Non-dimensional slenderness
        lambda_LT = math.sqrt(W * fy / (Mcr * 1e6)) if Mcr > 0 else 99.0

        # Imperfection factor
        alpha_LT = BUCKLING_CURVES.get(ltb_curve, 0.34)

        # General case (Clause 6.3.2.2)
        phi_LT = 0.5 * (1 + alpha_LT * (lambda_LT - 0.2) + lambda_LT ** 2)
        chi_LT = 1.0 / (phi_LT + math.sqrt(max(phi_LT ** 2 - lambda_LT ** 2, 0)))
        chi_LT = min(chi_LT, 1.0)

        # Design buckling resistance
        Mb_Rd = chi_LT * W * fy / GAMMA_M1 / 1e6  # kNm

        utilization = MEd / Mb_Rd if Mb_Rd > 0 else float('inf')

        return {
            "MEd_kNm": MEd,
            "Mb_Rd_kNm": round(Mb_Rd, 2),
            "chi_LT": round(chi_LT, 4),
            "lambda_LT": round(lambda_LT, 4),
            "phi_LT": round(phi_LT, 4),
            "alpha_LT": alpha_LT,
            "Mcr_kNm": Mcr,
            "W_mm3": Wy,
            "ltb_curve": ltb_curve,
            "utilization": round(utilization, 4),
            "status": "OK" if utilization <= 1.0 else "FAIL",
            "clause": "EN 1993-1-1, Clause 6.3.2",
        }

    @staticmethod
    def elastic_critical_moment_simple(
        L: float, Iz: float, It: float, Iw: float,
        E: float = 210000, G: float = 81000,
        C1: float = 1.0, kz: float = 1.0, kw: float = 1.0
    ) -> float:
        """
        Simplified Mcr calculation for doubly-symmetric sections.
        Mcr = C1 × (π²EIz / (kz×L)²) × √(Iw/Iz + (kz×L)²×G×It / (π²×E×Iz))
        """
        kzL = kz * L
        term1 = math.pi ** 2 * E * Iz / (kzL ** 2)
        term2 = math.sqrt(Iw / Iz + (kzL ** 2 * G * It) / (math.pi ** 2 * E * Iz))
        Mcr = C1 * term1 * term2 / 1e6  # kNm
        return round(Mcr, 2)

    @staticmethod
    def combined_buckling_interaction(
        NEd: float, My_Ed: float, Mz_Ed: float,
        chi_y: float, chi_z: float, chi_LT: float,
        NRk: float, My_Rk: float, Mz_Rk: float,
        kyy: float, kyz: float, kzy: float, kzz: float,
    ) -> Dict[str, Any]:
        """
        Combined axial and bending — Clause 6.3.3.
        Equations 6.61 and 6.62 interaction check.
        """
        # Equation 6.61
        eq_661 = (NEd / (chi_y * NRk / GAMMA_M1) +
                  kyy * My_Ed / (chi_LT * My_Rk / GAMMA_M1) +
                  kyz * Mz_Ed / (Mz_Rk / GAMMA_M1))

        # Equation 6.62
        eq_662 = (NEd / (chi_z * NRk / GAMMA_M1) +
                  kzy * My_Ed / (chi_LT * My_Rk / GAMMA_M1) +
                  kzz * Mz_Ed / (Mz_Rk / GAMMA_M1))

        governing = max(eq_661, eq_662)

        return {
            "equation_6_61": round(eq_661, 4),
            "equation_6_62": round(eq_662, 4),
            "governing_value": round(governing, 4),
            "governing_equation": "6.61" if eq_661 >= eq_662 else "6.62",
            "status": "OK" if governing <= 1.0 else "FAIL",
            "NEd_kN": NEd,
            "My_Ed_kNm": My_Ed,
            "Mz_Ed_kNm": Mz_Ed,
            "chi_y": chi_y,
            "chi_z": chi_z,
            "chi_LT": chi_LT,
            "clause": "EN 1993-1-1, Clause 6.3.3, Eq. 6.61 & 6.62",
        }


# ============== Connection Design (EN 1993-1-8) ==============

class ConnectionCalculator:
    """Steel connection design calculations per EN 1993-1-8."""

    @staticmethod
    def bolt_shear_resistance(
        bolt_diameter: int, bolt_grade: str,
        shear_plane: str = "threaded", n_shear_planes: int = 1
    ) -> Dict[str, Any]:
        """
        Bolt shear resistance — Clause 3.6.1.
        Fv,Rd = αv × fub × A / γM2
        """
        grade = BOLT_GRADES.get(bolt_grade)
        bolt = BOLT_AREAS.get(bolt_diameter)
        if not grade or not bolt:
            raise ValueError(f"Invalid bolt: M{bolt_diameter} {bolt_grade}")

        fub = grade["fub"]

        if shear_plane == "threaded":
            A = bolt["As"]
            # αv depends on grade
            if bolt_grade in ["4.6", "5.6", "8.8"]:
                alpha_v = 0.6
            else:  # 4.8, 5.8, 6.8, 10.9
                alpha_v = 0.5
        else:
            A = bolt["A"]
            alpha_v = 0.6

        Fv_Rd = alpha_v * fub * A / GAMMA_M2 / 1000  # kN (per plane)
        Fv_Rd_total = Fv_Rd * n_shear_planes

        return {
            "Fv_Rd_kN": round(Fv_Rd, 1),
            "Fv_Rd_total_kN": round(Fv_Rd_total, 1),
            "bolt": f"M{bolt_diameter}",
            "grade": bolt_grade,
            "alpha_v": alpha_v,
            "fub_MPa": fub,
            "A_mm2": A,
            "shear_plane": shear_plane,
            "n_shear_planes": n_shear_planes,
            "gamma_M2": GAMMA_M2,
            "clause": "EN 1993-1-8, Table 3.4",
        }

    @staticmethod
    def bolt_tension_resistance(bolt_diameter: int, bolt_grade: str) -> Dict[str, Any]:
        """
        Bolt tension resistance — Clause 3.6.1.
        Ft,Rd = 0.9 × fub × As / γM2
        """
        grade = BOLT_GRADES.get(bolt_grade)
        bolt = BOLT_AREAS.get(bolt_diameter)
        if not grade or not bolt:
            raise ValueError(f"Invalid bolt: M{bolt_diameter} {bolt_grade}")

        Ft_Rd = 0.9 * grade["fub"] * bolt["As"] / GAMMA_M2 / 1000  # kN

        return {
            "Ft_Rd_kN": round(Ft_Rd, 1),
            "bolt": f"M{bolt_diameter}",
            "grade": bolt_grade,
            "k2": 0.9,
            "fub_MPa": grade["fub"],
            "As_mm2": bolt["As"],
            "gamma_M2": GAMMA_M2,
            "clause": "EN 1993-1-8, Table 3.4",
        }

    @staticmethod
    def bolt_bearing_resistance(
        bolt_diameter: int, fu: float, t: float,
        e1: float, e2: float, p1: float, p2: float,
        is_inner: bool = False, direction: str = "load"
    ) -> Dict[str, Any]:
        """
        Bolt bearing resistance — Clause 3.6.1.
        Fb,Rd = k1 × αb × fu × d × t / γM2
        """
        d0 = bolt_diameter + BOLT_CLEARANCES.get(bolt_diameter, 2)

        # αb calculation (in direction of load transfer)
        if not is_inner:  # edge bolt
            alpha_d = e1 / (3 * d0)
        else:
            alpha_d = p1 / (3 * d0) - 0.25

        fub = BOLT_GRADES.get("8.8", {}).get("fub", 800)  # default
        alpha_b = min(alpha_d, fub / fu, 1.0)

        # k1 (perpendicular to load)
        if not is_inner:
            k1 = min(2.8 * e2 / d0 - 1.7, 2.5)
        else:
            k1 = min(1.4 * p2 / d0 - 1.7, 2.5)

        Fb_Rd = k1 * alpha_b * fu * bolt_diameter * t / GAMMA_M2 / 1000  # kN

        return {
            "Fb_Rd_kN": round(Fb_Rd, 1),
            "k1": round(k1, 3),
            "alpha_b": round(alpha_b, 3),
            "bolt": f"M{bolt_diameter}",
            "d0_mm": d0,
            "fu_MPa": fu,
            "t_mm": t,
            "gamma_M2": GAMMA_M2,
            "clause": "EN 1993-1-8, Table 3.4",
        }

    @staticmethod
    def bolt_combined_shear_tension(
        Fv_Ed: float, Ft_Ed: float,
        Fv_Rd: float, Ft_Rd: float
    ) -> Dict[str, Any]:
        """
        Combined shear and tension — Clause 3.6.1.
        Fv,Ed / Fv,Rd + Ft,Ed / (1.4 × Ft,Rd) ≤ 1.0
        """
        interaction = Fv_Ed / Fv_Rd + Ft_Ed / (1.4 * Ft_Rd)

        return {
            "interaction_value": round(interaction, 4),
            "Fv_Ed_kN": Fv_Ed,
            "Ft_Ed_kN": Ft_Ed,
            "Fv_Rd_kN": Fv_Rd,
            "Ft_Rd_kN": Ft_Rd,
            "shear_ratio": round(Fv_Ed / Fv_Rd, 4),
            "tension_ratio": round(Ft_Ed / (1.4 * Ft_Rd), 4),
            "status": "OK" if interaction <= 1.0 else "FAIL",
            "clause": "EN 1993-1-8, Table 3.4",
        }

    @staticmethod
    def fillet_weld_resistance(
        a: float, L: float, fu: float,
        steel_grade: str = "S355"
    ) -> Dict[str, Any]:
        """
        Fillet weld resistance — Clause 4.5.3.3 (simplified method).
        Fw,Rd = a × Leff × fvw,d
        fvw,d = fu / (√3 × βw × γM2)
        """
        beta_w = WELD_BETA_W.get(steel_grade, 0.90)
        fvw_d = fu / (math.sqrt(3) * beta_w * GAMMA_M2)

        L_eff = max(L - 2 * a, 0)  # effective length (end craters)
        Fw_Rd = a * L_eff * fvw_d / 1000  # kN

        # Per unit length
        fw_Rd_per_mm = a * fvw_d / 1000  # kN/mm

        return {
            "Fw_Rd_kN": round(Fw_Rd, 1),
            "fw_Rd_per_mm_kN": round(fw_Rd_per_mm, 3),
            "fvw_d_MPa": round(fvw_d, 1),
            "a_mm": a,
            "L_mm": L,
            "L_eff_mm": round(L_eff, 1),
            "beta_w": beta_w,
            "fu_MPa": fu,
            "steel_grade": steel_grade,
            "gamma_M2": GAMMA_M2,
            "clause": "EN 1993-1-8, Clause 4.5.3.3",
        }

    @staticmethod
    def bolt_group_shear(
        VEd: float, n_bolts: int, bolt_diameter: int, bolt_grade: str,
        shear_plane: str = "threaded"
    ) -> Dict[str, Any]:
        """Check a bolt group in shear."""
        single = ConnectionCalculator.bolt_shear_resistance(
            bolt_diameter, bolt_grade, shear_plane
        )
        Fv_Rd_per_bolt = single["Fv_Rd_kN"]
        total_resistance = Fv_Rd_per_bolt * n_bolts
        force_per_bolt = VEd / n_bolts
        utilization = VEd / total_resistance

        return {
            "VEd_kN": VEd,
            "n_bolts": n_bolts,
            "Fv_Rd_per_bolt_kN": Fv_Rd_per_bolt,
            "total_resistance_kN": round(total_resistance, 1),
            "force_per_bolt_kN": round(force_per_bolt, 1),
            "utilization": round(utilization, 4),
            "status": "OK" if utilization <= 1.0 else "FAIL",
            "clause": "EN 1993-1-8, Clause 3.7",
        }


# ============== Deflection Checks ==============

class DeflectionCalculator:
    """Serviceability limit state deflection checks."""

    @staticmethod
    def simply_supported_udl(
        w: float, L: float, E: float, I: float
    ) -> Dict[str, Any]:
        """
        Deflection of simply supported beam under UDL.
        δ = 5wL⁴ / (384EI)
        w in kN/m, L in mm, E in N/mm², I in mm⁴
        """
        w_N_mm = w / 1000  # kN/m → N/mm
        delta = 5 * w_N_mm * L ** 4 / (384 * E * I)

        # Common limits
        limits = {
            "L/250": L / 250,
            "L/300": L / 300,
            "L/360": L / 360,
        }

        checks = {}
        for name, limit in limits.items():
            checks[name] = {
                "limit_mm": round(limit, 2),
                "ratio": round(delta / limit, 4),
                "status": "OK" if delta <= limit else "FAIL",
            }

        return {
            "delta_mm": round(delta, 2),
            "w_kN_m": w,
            "L_mm": L,
            "span_ratio": f"L/{round(L / delta, 0)}" if delta > 0 else "N/A",
            "checks": checks,
            "clause": "EN 1993-1-1, Clause 7.2.1",
        }

    @staticmethod
    def simply_supported_point_load(
        P: float, L: float, E: float, I: float,
        a: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Deflection under point load.
        Mid-span: δ = PL³ / (48EI)
        At distance a: δ = Pa(L²-a²)^(3/2) / (9√3 × EIL) (max for a < L/2)
        """
        P_N = P * 1000  # kN → N

        if a is None:
            # Mid-span point load
            delta = P_N * L ** 3 / (48 * E * I)
        else:
            # General position
            b = L - a
            delta = P_N * b * a * (L ** 2 - a ** 2 - b ** 2) / (6 * E * I * L) if a <= L else 0

        limits = {
            "L/250": L / 250,
            "L/300": L / 300,
            "L/360": L / 360,
        }

        checks = {}
        for name, limit in limits.items():
            checks[name] = {
                "limit_mm": round(limit, 2),
                "ratio": round(delta / limit, 4) if limit > 0 else 0,
                "status": "OK" if delta <= limit else "FAIL",
            }

        return {
            "delta_mm": round(delta, 2),
            "P_kN": P,
            "L_mm": L,
            "span_ratio": f"L/{round(L / delta, 0)}" if delta > 0 else "N/A",
            "checks": checks,
            "clause": "EN 1993-1-1, Clause 7.2.1",
        }


# ============== Fire Design (EN 1993-1-2 Simplified) ==============

class FireDesignCalculator:
    """Simplified fire resistance calculations per EN 1993-1-2."""

    @staticmethod
    def critical_temperature(utilization: float) -> Dict[str, Any]:
        """
        Calculate critical steel temperature — Clause 4.2.4.
        θa,cr = 39.19 × ln(1/(0.9674 × μ0^3.833) - 1) + 482
        """
        mu_0 = max(utilization, 0.013)  # avoid math errors

        try:
            theta_cr = 39.19 * math.log(1 / (0.9674 * mu_0 ** 3.833) - 1) + 482
            theta_cr = min(max(theta_cr, 20), 1000)
        except (ValueError, ZeroDivisionError):
            theta_cr = 350  # Conservative default

        return {
            "theta_cr_degC": round(theta_cr, 1),
            "utilization_mu0": round(mu_0, 4),
            "clause": "EN 1993-1-2, Clause 4.2.4",
        }

    @staticmethod
    def section_factor(
        perimeter_exposed: float, A: float,
        box: bool = False
    ) -> Dict[str, Any]:
        """
        Section factor Am/V (or [Am/V]b for box protection).
        Am = exposed perimeter per unit length
        V = cross-section area per unit length
        """
        Am_V = perimeter_exposed / A * 1000  # m⁻¹

        return {
            "Am_V_m_inv": round(Am_V, 1),
            "perimeter_mm": perimeter_exposed,
            "A_mm2": A,
            "protection_type": "box" if box else "profile",
            "clause": "EN 1993-1-2, Clause 4.2.5",
        }

    @staticmethod
    def reduction_factor_ky(theta: float) -> float:
        """Yield strength reduction factor at temperature θ (Table 3.1)."""
        # Simplified linear interpolation from EC3-1-2 Table 3.1
        temp_ky = [
            (20, 1.000), (100, 1.000), (200, 1.000), (300, 1.000),
            (400, 1.000), (500, 0.780), (600, 0.470), (700, 0.230),
            (800, 0.110), (900, 0.060), (1000, 0.040), (1100, 0.020),
            (1200, 0.000),
        ]
        for i in range(len(temp_ky) - 1):
            t1, k1 = temp_ky[i]
            t2, k2 = temp_ky[i + 1]
            if t1 <= theta <= t2:
                return k1 + (k2 - k1) * (theta - t1) / (t2 - t1)
        return 0.0


# ============== Unified Design Check ==============

def full_beam_check(
    section_props: Dict, steel_grade: str,
    L: float, MEd: float, VEd: float,
    NEd: float = 0,
    Lcr_LTB: Optional[float] = None,
    C1: float = 1.0,
    w_sls: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Complete beam design check per EN 1993-1-1.

    Returns all individual checks and overall utilization.
    """
    sp = section_props
    tf = sp.get("tf", sp.get("t", 10))
    fy = get_fy(steel_grade, tf)
    fu = STEEL_GRADES[steel_grade]["fu"]
    E = STEEL_GRADES[steel_grade]["E"]

    results = {"section": sp, "steel_grade": steel_grade, "fy": fy, "fu": fu}

    # 1. Classification
    if "tw" in sp and "tf" in sp:
        classification = CrossSectionClassifier.classify_i_section(
            sp["h"], sp["b"], sp["tw"], sp["tf"], sp.get("r", 0), fy, NEd, sp["A"]
        )
    else:
        classification = {"overall_class": 1}  # Default for hollow sections

    results["classification"] = classification
    sec_class = classification["overall_class"]

    # 2. Bending resistance
    Wpl = sp.get("Wpl_y", sp.get("W_pl", 0))
    Wel = sp.get("Wel_y", sp.get("W_el", 0))
    bending = ResistanceCalculator.bending_resistance(Wpl, Wel, fy, sec_class)
    results["bending"] = bending

    # 3. Shear resistance
    if "tw" in sp:
        Av = ResistanceCalculator.shear_area_i_section(
            sp["A"], sp["b"], sp["tw"], sp["tf"], sp.get("r", 0), sp["h"]
        )
    else:
        Av = sp["A"] * 0.6  # Approximate for hollow sections
    shear = ResistanceCalculator.shear_resistance(Av, fy)
    results["shear"] = shear

    # 4. Bending-shear interaction
    interaction = ResistanceCalculator.bending_shear_interaction(
        VEd, shear["Vpl_Rd_kN"], bending["Mc_Rd_kNm"]
    )
    results["bending_shear_interaction"] = interaction

    # 5. Lateral-torsional buckling (if applicable)
    if Lcr_LTB and "Iz" in sp and "It" in sp:
        Mcr = StabilityCalculator.elastic_critical_moment_simple(
            Lcr_LTB, sp["Iz"], sp["It"], sp.get("Iw", 0),
            E=E, G=STEEL_GRADES[steel_grade]["G"], C1=C1
        )
        ltb = StabilityCalculator.lateral_torsional_buckling(
            MEd, Wpl, fy, Mcr, sec_class
        )
        results["ltb"] = ltb

    # 6. Deflection (SLS)
    if w_sls and "Iy" in sp:
        deflection = DeflectionCalculator.simply_supported_udl(
            w_sls, L, E, sp["Iy"]
        )
        results["deflection"] = deflection

    # 7. Utilization summary
    utilizations = {
        "bending": round(MEd / bending["Mc_Rd_kNm"], 4) if bending["Mc_Rd_kNm"] > 0 else 0,
        "shear": round(VEd / shear["Vpl_Rd_kN"], 4) if shear["Vpl_Rd_kN"] > 0 else 0,
    }
    if "ltb" in results:
        utilizations["ltb"] = results["ltb"]["utilization"]

    results["utilizations"] = utilizations
    results["max_utilization"] = max(utilizations.values())
    results["overall_status"] = "OK" if results["max_utilization"] <= 1.0 else "FAIL"

    return results


def full_column_check(
    section_props: Dict, steel_grade: str,
    NEd: float, My_Ed: float = 0, Mz_Ed: float = 0,
    Lcr_y: float = 0, Lcr_z: float = 0,
    buckling_curve_y: str = "b", buckling_curve_z: str = "c",
) -> Dict[str, Any]:
    """
    Complete column design check per EN 1993-1-1.
    """
    sp = section_props
    tf = sp.get("tf", sp.get("t", 10))
    fy = get_fy(steel_grade, tf)
    E = STEEL_GRADES[steel_grade]["E"]

    results = {"section": sp, "steel_grade": steel_grade, "fy": fy}

    # Classification
    if "tw" in sp:
        classification = CrossSectionClassifier.classify_i_section(
            sp["h"], sp["b"], sp["tw"], sp["tf"], sp.get("r", 0), fy, NEd, sp["A"]
        )
    else:
        classification = {"overall_class": 1}
    results["classification"] = classification

    # Compression resistance
    compression = ResistanceCalculator.compression_resistance(sp["A"], fy)
    results["compression"] = compression

    # Flexural buckling y-y
    if Lcr_y > 0:
        iy = sp.get("iy", sp.get("i", 1))
        buck_y = StabilityCalculator.flexural_buckling(
            NEd, sp["A"], fy, Lcr_y, iy, buckling_curve_y
        )
        results["buckling_y"] = buck_y

    # Flexural buckling z-z
    if Lcr_z > 0:
        iz = sp.get("iz", sp.get("i", 1))
        buck_z = StabilityCalculator.flexural_buckling(
            NEd, sp["A"], fy, Lcr_z, iz, buckling_curve_z
        )
        results["buckling_z"] = buck_z

    # Utilization summary
    utilizations = {
        "compression": round(NEd / compression["Nc_Rd_kN"], 4) if compression["Nc_Rd_kN"] > 0 else 0,
    }
    if "buckling_y" in results:
        utilizations["buckling_y"] = results["buckling_y"]["utilization"]
    if "buckling_z" in results:
        utilizations["buckling_z"] = results["buckling_z"]["utilization"]

    results["utilizations"] = utilizations
    results["max_utilization"] = max(utilizations.values()) if utilizations else 0
    results["overall_status"] = "OK" if results["max_utilization"] <= 1.0 else "FAIL"

    return results
