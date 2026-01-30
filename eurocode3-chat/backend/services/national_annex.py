"""
National Annex Parameters for Eurocode 3.
Provides country-specific values that override recommended Eurocode values.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class NationalAnnexParams:
    """National Annex parameters for a specific country."""
    country_code: str
    country_name: str

    # Partial safety factors (EN 1993-1-1)
    gamma_M0: float = 1.00
    gamma_M1: float = 1.00
    gamma_M2: float = 1.25

    # Load factors (EN 1990)
    gamma_G_unfav: float = 1.35
    gamma_G_fav: float = 1.00
    gamma_Q_unfav: float = 1.50
    xi: float = 0.85  # Reduction factor for 6.10b
    use_6_10ab: bool = True  # Use 6.10a/b instead of single 6.10

    # Buckling (EN 1993-1-1)
    ltb_method: str = "general"  # "general" or "rolled_welded"
    lambda_LT_0: float = 0.4  # Plateau length for LTB (rolled/welded method)
    beta_LT: float = 0.75  # Correction factor for LTB

    # Deflection limits
    deflection_permanent: str = "L/250"
    deflection_variable: str = "L/300"
    deflection_total: str = "L/250"

    # Connection design (EN 1993-1-8)
    gamma_M3: float = 1.25  # Slip resistance at ULS
    gamma_M3_ser: float = 1.10  # Slip resistance at SLS
    gamma_M6: float = 1.00  # Joints (pins at ULS)
    gamma_M7: float = 1.10  # Preload of high-strength bolts

    # Fire design (EN 1993-1-2)
    gamma_M_fi: float = 1.00  # In fire situation

    # Additional notes
    notes: str = ""


# ============== National Annex Database ==============

NATIONAL_ANNEXES: Dict[str, NationalAnnexParams] = {
    "EC": NationalAnnexParams(
        country_code="EC",
        country_name="Eurocode Recommended",
        notes="Default recommended values from EN 1993-1-1",
    ),
    "UK": NationalAnnexParams(
        country_code="UK",
        country_name="United Kingdom (BS NA)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.10,
        xi=0.925,
        use_6_10ab=True,
        ltb_method="rolled_welded",
        lambda_LT_0=0.4,
        beta_LT=0.75,
        deflection_variable="L/360",
        gamma_M3=1.25,
        gamma_M3_ser=1.10,
        notes="Based on BS NA to BS EN 1993-1-1:2005+A1:2014",
    ),
    "DE": NationalAnnexParams(
        country_code="DE",
        country_name="Germany (DIN EN)",
        gamma_M0=1.00,
        gamma_M1=1.10,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=True,
        ltb_method="general",
        deflection_variable="L/300",
        notes="Based on DIN EN 1993-1-1/NA:2015",
    ),
    "FR": NationalAnnexParams(
        country_code="FR",
        country_name="France (NF EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=True,
        ltb_method="general",
        deflection_variable="L/250",
        notes="Based on NF EN 1993-1-1/NA:2013",
    ),
    "NL": NationalAnnexParams(
        country_code="NL",
        country_name="Netherlands (NEN EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.25,
        xi=0.89,
        use_6_10ab=False,  # NL uses single equation 6.10
        ltb_method="general",
        notes="Based on NEN EN 1993-1-1+C2+A1/NB:2016",
    ),
    "BE": NationalAnnexParams(
        country_code="BE",
        country_name="Belgium (NBN EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=True,
        ltb_method="general",
        notes="Based on NBN EN 1993-1-1 ANB:2010",
    ),
    "IT": NationalAnnexParams(
        country_code="IT",
        country_name="Italy (UNI EN)",
        gamma_M0=1.05,
        gamma_M1=1.05,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=False,
        ltb_method="general",
        notes="Based on NTC 2018 / UNI EN 1993-1-1 NA",
    ),
    "ES": NationalAnnexParams(
        country_code="ES",
        country_name="Spain (UNE EN)",
        gamma_M0=1.05,
        gamma_M1=1.05,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=False,
        ltb_method="general",
        notes="Based on CTE DB SE-A / UNE EN 1993-1-1 NA",
    ),
    "SE": NationalAnnexParams(
        country_code="SE",
        country_name="Sweden (SS EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.25,
        xi=0.89,
        use_6_10ab=True,
        ltb_method="general",
        notes="Based on SS EN 1993-1-1/NA:2011",
    ),
    "NO": NationalAnnexParams(
        country_code="NO",
        country_name="Norway (NS EN)",
        gamma_M0=1.05,
        gamma_M1=1.05,
        gamma_M2=1.25,
        xi=0.89,
        use_6_10ab=True,
        ltb_method="general",
        notes="Based on NS EN 1993-1-1/NA:2008",
    ),
    "FI": NationalAnnexParams(
        country_code="FI",
        country_name="Finland (SFS EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=True,
        ltb_method="general",
        notes="Based on SFS EN 1993-1-1/NA:2017",
    ),
    "DK": NationalAnnexParams(
        country_code="DK",
        country_name="Denmark (DS EN)",
        gamma_M0=1.10,
        gamma_M1=1.20,
        gamma_M2=1.35,
        xi=0.85,
        use_6_10ab=True,
        ltb_method="general",
        notes="Based on DS EN 1993-1-1 DK NA:2015",
    ),
    "PL": NationalAnnexParams(
        country_code="PL",
        country_name="Poland (PN EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=True,
        ltb_method="general",
        notes="Based on PN EN 1993-1-1/NA:2006",
    ),
    "IE": NationalAnnexParams(
        country_code="IE",
        country_name="Ireland (IS EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.10,
        xi=0.925,
        use_6_10ab=True,
        ltb_method="rolled_welded",
        lambda_LT_0=0.4,
        beta_LT=0.75,
        notes="Irish NA closely follows UK NA",
    ),
    "PT": NationalAnnexParams(
        country_code="PT",
        country_name="Portugal (NP EN)",
        gamma_M0=1.00,
        gamma_M1=1.00,
        gamma_M2=1.25,
        xi=0.85,
        use_6_10ab=True,
        ltb_method="general",
        notes="Based on NP EN 1993-1-1 NA:2010",
    ),
}


class NationalAnnexService:
    """Service for managing National Annex parameters."""

    def __init__(self, default_country: str = "EC"):
        self.default_country = default_country

    def get_annex(self, country_code: str) -> Optional[NationalAnnexParams]:
        """Get National Annex parameters for a country."""
        return NATIONAL_ANNEXES.get(country_code.upper())

    def list_countries(self) -> list[Dict[str, str]]:
        """List all available National Annexes."""
        return [
            {
                "code": code,
                "name": na.country_name,
                "notes": na.notes,
            }
            for code, na in NATIONAL_ANNEXES.items()
        ]

    def get_safety_factors(self, country_code: str) -> Dict[str, float]:
        """Get all partial safety factors for a country."""
        na = self.get_annex(country_code)
        if not na:
            na = NATIONAL_ANNEXES["EC"]

        return {
            "gamma_M0": na.gamma_M0,
            "gamma_M1": na.gamma_M1,
            "gamma_M2": na.gamma_M2,
            "gamma_M3": na.gamma_M3,
            "gamma_M3_ser": na.gamma_M3_ser,
            "gamma_M_fi": na.gamma_M_fi,
            "gamma_G_unfav": na.gamma_G_unfav,
            "gamma_G_fav": na.gamma_G_fav,
            "gamma_Q_unfav": na.gamma_Q_unfav,
            "xi": na.xi,
        }

    def get_comparison_table(self) -> list[Dict[str, Any]]:
        """Generate a comparison table of key parameters across all NAs."""
        return [
            {
                "country": na.country_name,
                "code": code,
                "γM0": na.gamma_M0,
                "γM1": na.gamma_M1,
                "γM2": na.gamma_M2,
                "ξ": na.xi,
                "approach": "6.10a/b" if na.use_6_10ab else "6.10",
                "LTB": na.ltb_method,
            }
            for code, na in NATIONAL_ANNEXES.items()
        ]

    def serialize_annex(self, country_code: str) -> Dict[str, Any]:
        """Serialize NA parameters for API response."""
        na = self.get_annex(country_code)
        if not na:
            return {}

        return {
            "country_code": na.country_code,
            "country_name": na.country_name,
            "safety_factors": {
                "gamma_M0": na.gamma_M0,
                "gamma_M1": na.gamma_M1,
                "gamma_M2": na.gamma_M2,
                "gamma_M3": na.gamma_M3,
            },
            "load_combination": {
                "gamma_G_unfav": na.gamma_G_unfav,
                "gamma_G_fav": na.gamma_G_fav,
                "gamma_Q_unfav": na.gamma_Q_unfav,
                "xi": na.xi,
                "approach": "6.10a/b" if na.use_6_10ab else "6.10",
            },
            "buckling": {
                "ltb_method": na.ltb_method,
                "lambda_LT_0": na.lambda_LT_0,
                "beta_LT": na.beta_LT,
            },
            "deflection_limits": {
                "permanent": na.deflection_permanent,
                "variable": na.deflection_variable,
                "total": na.deflection_total,
            },
            "notes": na.notes,
        }
