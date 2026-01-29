"""
API Routes for Engineering Tools.
Section database, calculators, load combinations, national annexes, projects, reports.
"""
from fastapi import APIRouter, HTTPException, status, Response
from typing import Optional, List

from app.models import (
    SectionQuery, SectionResponse,
    BeamCheckRequest, ColumnCheckRequest, ClassificationRequest,
    BoltCheckRequest, WeldCheckRequest, DeflectionCheckRequest,
    LoadCombinationRequest, LoadCaseInput,
    ProjectCreateRequest, ProjectUpdateRequest, SaveCalculationRequest,
    ReportRequest,
)
from services.section_database import SectionDatabase
from services.calculation_engine import (
    CrossSectionClassifier, ResistanceCalculator, StabilityCalculator,
    ConnectionCalculator, DeflectionCalculator, FireDesignCalculator,
    full_beam_check, full_column_check, get_fy, get_epsilon,
    STEEL_GRADES, BOLT_GRADES, BOLT_AREAS, BUCKLING_CURVES,
)
from services.load_combinations import LoadCombinationGenerator, LoadCase, LOAD_CATEGORIES
from services.national_annex import NationalAnnexService
from services.report_generator import ReportGenerator
from database.projects import ProjectManager

# Initialize services
section_db = SectionDatabase()
na_service = NationalAnnexService()
project_mgr = ProjectManager()

# ============== Section Database Router ==============
sections_router = APIRouter(prefix="/api/sections", tags=["Section Database"])


@sections_router.get("/types")
async def list_section_types():
    """List all available section types (IPE, HEB, HEA, CHS, etc.)."""
    return {"types": section_db.list_section_types()}


@sections_router.get("/search")
async def search_sections(
    query: str = "",
    section_type: Optional[str] = None,
    min_height: Optional[float] = None,
    max_height: Optional[float] = None,
    min_area: Optional[float] = None,
    max_mass: Optional[float] = None,
):
    """Search sections with filters."""
    results = section_db.search_sections(
        query=query, section_type=section_type,
        min_height=min_height, max_height=max_height,
        min_area=min_area, max_mass=max_mass,
    )
    return {"results": results, "count": len(results)}


@sections_router.get("/{section_name}")
async def get_section(section_name: str):
    """Get full properties for a specific section."""
    result = section_db.get_section(section_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")
    return result


@sections_router.get("/type/{section_type}")
async def list_sections_by_type(section_type: str):
    """List all sections of a given type."""
    results = section_db.list_sections_by_type(section_type)
    if not results:
        raise HTTPException(status_code=404, detail=f"Section type '{section_type}' not found")
    return {"sections": results, "count": len(results)}


@sections_router.get("/units/all")
async def get_property_units():
    """Get units for all section properties."""
    return section_db.get_property_units()


# ============== Calculation Router ==============
calc_router = APIRouter(prefix="/api/calc", tags=["Calculations"])


@calc_router.post("/beam")
async def check_beam(req: BeamCheckRequest):
    """Full beam design check per EN 1993-1-1."""
    section = section_db.get_section(req.section_name)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{req.section_name}' not found")
    if req.steel_grade not in STEEL_GRADES:
        raise HTTPException(status_code=400, detail=f"Invalid steel grade '{req.steel_grade}'")

    props = section["properties"]
    result = full_beam_check(
        section_props=props, steel_grade=req.steel_grade,
        L=req.span_mm, MEd=req.MEd_kNm, VEd=req.VEd_kN,
        NEd=req.NEd_kN, Lcr_LTB=req.Lcr_LTB_mm,
        C1=req.C1, w_sls=req.w_sls_kN_m,
    )
    result["section_name"] = req.section_name
    return result


@calc_router.post("/column")
async def check_column(req: ColumnCheckRequest):
    """Full column design check per EN 1993-1-1."""
    section = section_db.get_section(req.section_name)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{req.section_name}' not found")
    if req.steel_grade not in STEEL_GRADES:
        raise HTTPException(status_code=400, detail=f"Invalid steel grade '{req.steel_grade}'")

    props = section["properties"]
    result = full_column_check(
        section_props=props, steel_grade=req.steel_grade,
        NEd=req.NEd_kN, My_Ed=req.My_Ed_kNm, Mz_Ed=req.Mz_Ed_kNm,
        Lcr_y=req.Lcr_y_mm, Lcr_z=req.Lcr_z_mm,
        buckling_curve_y=req.buckling_curve_y,
        buckling_curve_z=req.buckling_curve_z,
    )
    result["section_name"] = req.section_name
    return result


@calc_router.post("/classify")
async def classify_section(req: ClassificationRequest):
    """Cross-section classification per EN 1993-1-1, Table 5.2."""
    section = section_db.get_section(req.section_name)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{req.section_name}' not found")

    props = section["properties"]
    tf = props.get("tf", props.get("t", 10))
    fy = get_fy(req.steel_grade, tf)
    NEd_N = req.NEd_kN * 1000 if req.NEd_kN else 0

    if "tw" in props and "tf" in props:
        result = CrossSectionClassifier.classify_i_section(
            props["h"], props["b"], props["tw"], props["tf"],
            props.get("r", 0), fy, NEd_N, props["A"]
        )
    elif "d" in props:
        result = CrossSectionClassifier.classify_hollow_section(
            props["d"], props["d"], props["t"], fy, is_circular=True
        )
    else:
        h = props.get("h", 0)
        b = props.get("b", h)
        t = props.get("t", 0)
        result = CrossSectionClassifier.classify_hollow_section(h, b, t, fy)

    result["section_name"] = req.section_name
    result["steel_grade"] = req.steel_grade
    result["fy"] = fy
    return result


@calc_router.post("/bolt")
async def check_bolt(req: BoltCheckRequest):
    """Bolt resistance check per EN 1993-1-8."""
    if req.bolt_grade not in BOLT_GRADES:
        raise HTTPException(status_code=400, detail=f"Invalid bolt grade '{req.bolt_grade}'")
    if req.bolt_diameter not in BOLT_AREAS:
        raise HTTPException(status_code=400, detail=f"Invalid bolt diameter M{req.bolt_diameter}")

    result = {}

    # Shear check
    if req.VEd_kN > 0:
        if req.n_bolts > 1:
            result["shear"] = ConnectionCalculator.bolt_group_shear(
                req.VEd_kN, req.n_bolts, req.bolt_diameter, req.bolt_grade, req.shear_plane
            )
        else:
            shear = ConnectionCalculator.bolt_shear_resistance(
                req.bolt_diameter, req.bolt_grade, req.shear_plane
            )
            shear["utilization"] = round(req.VEd_kN / shear["Fv_Rd_kN"], 4)
            shear["status"] = "OK" if shear["utilization"] <= 1.0 else "FAIL"
            result["shear"] = shear

    # Tension check
    if req.FtEd_kN > 0:
        tension = ConnectionCalculator.bolt_tension_resistance(req.bolt_diameter, req.bolt_grade)
        tension["FtEd_kN"] = req.FtEd_kN
        tension["utilization"] = round(req.FtEd_kN / tension["Ft_Rd_kN"], 4)
        tension["status"] = "OK" if tension["utilization"] <= 1.0 else "FAIL"
        result["tension"] = tension

    # Combined check
    if req.VEd_kN > 0 and req.FtEd_kN > 0:
        Fv_Rd = ConnectionCalculator.bolt_shear_resistance(
            req.bolt_diameter, req.bolt_grade, req.shear_plane
        )["Fv_Rd_kN"]
        Ft_Rd = ConnectionCalculator.bolt_tension_resistance(
            req.bolt_diameter, req.bolt_grade
        )["Ft_Rd_kN"]
        per_bolt_V = req.VEd_kN / req.n_bolts
        per_bolt_T = req.FtEd_kN / req.n_bolts
        result["combined"] = ConnectionCalculator.bolt_combined_shear_tension(
            per_bolt_V, per_bolt_T, Fv_Rd, Ft_Rd
        )

    return result


@calc_router.post("/weld")
async def check_weld(req: WeldCheckRequest):
    """Fillet weld resistance check per EN 1993-1-8."""
    if req.steel_grade not in STEEL_GRADES:
        raise HTTPException(status_code=400, detail=f"Invalid steel grade '{req.steel_grade}'")

    fu = STEEL_GRADES[req.steel_grade]["fu"]
    result = ConnectionCalculator.fillet_weld_resistance(
        req.throat_mm, req.length_mm, fu, req.steel_grade
    )
    result["FEd_kN"] = req.FEd_kN
    result["utilization"] = round(req.FEd_kN / result["Fw_Rd_kN"], 4) if result["Fw_Rd_kN"] > 0 else float('inf')
    result["status"] = "OK" if result["utilization"] <= 1.0 else "FAIL"
    return result


@calc_router.post("/deflection")
async def check_deflection(req: DeflectionCheckRequest):
    """Deflection check at SLS."""
    section = section_db.get_section(req.section_name)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{req.section_name}' not found")

    props = section["properties"]
    E = 210000
    I = props.get("Iy", props.get("I", 0))

    result = {}
    if req.load_kN_m > 0:
        result["udl"] = DeflectionCalculator.simply_supported_udl(req.load_kN_m, req.span_mm, E, I)
    if req.point_load_kN > 0:
        result["point_load"] = DeflectionCalculator.simply_supported_point_load(
            req.point_load_kN, req.span_mm, E, I
        )

    result["section_name"] = req.section_name
    return result


@calc_router.post("/fire/critical-temperature")
async def fire_critical_temp(utilization: float):
    """Calculate critical steel temperature per EN 1993-1-2."""
    if not 0 < utilization <= 1.0:
        raise HTTPException(status_code=400, detail="Utilization must be between 0 and 1.0")
    return FireDesignCalculator.critical_temperature(utilization)


@calc_router.get("/materials")
async def list_materials():
    """List all steel grades with properties."""
    return {
        grade: {
            "fy_16mm": props["fy_16"],
            "fy_40mm": props["fy_40"],
            "fy_63mm": props["fy_63"],
            "fy_80mm": props["fy_80"],
            "fu": props["fu"],
            "E": props["E"],
            "G": props["G"],
            "epsilon": round(get_epsilon(props["fy_16"]), 4),
        }
        for grade, props in STEEL_GRADES.items()
    }


@calc_router.get("/bolts/properties")
async def list_bolt_properties():
    """List all bolt grade properties and sizes."""
    return {
        "grades": BOLT_GRADES,
        "sizes": {f"M{d}": v for d, v in BOLT_AREAS.items()},
    }


@calc_router.get("/buckling-curves")
async def list_buckling_curves():
    """List imperfection factors for buckling curves."""
    return BUCKLING_CURVES


# ============== Load Combinations Router ==============
loads_router = APIRouter(prefix="/api/loads", tags=["Load Combinations"])


@loads_router.post("/combinations")
async def generate_load_combinations(req: LoadCombinationRequest):
    """Generate EN 1990 load combinations."""
    generator = LoadCombinationGenerator(
        approach=req.approach, limit_state=req.limit_state
    )

    load_cases = [
        LoadCase(
            name=lc.name, type=lc.type, category=lc.category,
            value=lc.value, favorable=lc.favorable
        )
        for lc in req.load_cases
    ]

    result = {}

    # ULS
    uls_combos = generator.generate_uls(load_cases)
    result["uls"] = generator.serialize_combinations(uls_combos)
    result["uls_governing"] = max(result["uls"], key=lambda c: c["value"]) if result["uls"] else None

    # SLS
    if req.include_sls:
        sls = generator.generate_sls(load_cases)
        result["sls"] = {
            k: generator.serialize_combinations(v)
            for k, v in sls.items()
        }

    return result


@loads_router.get("/categories")
async def list_load_categories():
    """List EN 1990 load categories with ψ factors."""
    return LOAD_CATEGORIES


# ============== National Annex Router ==============
na_router = APIRouter(prefix="/api/national-annex", tags=["National Annex"])


@na_router.get("/countries")
async def list_countries():
    """List all available National Annexes."""
    return na_service.list_countries()


@na_router.get("/comparison")
async def na_comparison():
    """Compare key parameters across all National Annexes."""
    return na_service.get_comparison_table()


@na_router.get("/{country_code}")
async def get_national_annex(country_code: str):
    """Get National Annex parameters for a specific country."""
    result = na_service.serialize_annex(country_code)
    if not result:
        raise HTTPException(status_code=404, detail=f"National Annex for '{country_code}' not found")
    return result


@na_router.get("/{country_code}/safety-factors")
async def get_safety_factors(country_code: str):
    """Get all partial safety factors for a country."""
    return na_service.get_safety_factors(country_code)


# ============== Projects Router ==============
projects_router = APIRouter(prefix="/api/projects", tags=["Projects"])


@projects_router.post("")
async def create_project(req: ProjectCreateRequest):
    """Create a new engineering project."""
    project_id = project_mgr.create_project(
        name=req.name, description=req.description, client=req.client,
        location=req.location, steel_grade=req.steel_grade,
        national_annex=req.national_annex,
    )
    return {"project_id": project_id}


@projects_router.get("")
async def list_projects(limit: int = 50, offset: int = 0):
    """List all projects."""
    return project_mgr.list_projects(limit=limit, offset=offset)


@projects_router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project details with linked conversations and calculations."""
    result = project_mgr.get_project(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@projects_router.patch("/{project_id}")
async def update_project(project_id: str, req: ProjectUpdateRequest):
    """Update project details."""
    updates = req.model_dump(exclude_none=True)
    if not project_mgr.update_project(project_id, **updates):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project updated"}


@projects_router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    if not project_mgr.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}


@projects_router.post("/{project_id}/conversations/{conversation_id}")
async def link_conversation_to_project(project_id: str, conversation_id: str):
    """Link a conversation to a project."""
    project_mgr.link_conversation(project_id, conversation_id)
    return {"message": "Conversation linked"}


@projects_router.delete("/{project_id}/conversations/{conversation_id}")
async def unlink_conversation(project_id: str, conversation_id: str):
    """Remove a conversation from a project."""
    project_mgr.unlink_conversation(project_id, conversation_id)
    return {"message": "Conversation unlinked"}


# ============== Saved Calculations Router ==============
saved_router = APIRouter(prefix="/api/calculations", tags=["Saved Calculations"])


@saved_router.post("")
async def save_calculation(req: SaveCalculationRequest):
    """Save a calculation for later reference."""
    calc_id = project_mgr.save_calculation(
        name=req.name, calc_type=req.calc_type,
        input_data=req.input_data, result_data=req.result_data,
        project_id=req.project_id,
    )
    return {"calculation_id": calc_id}


@saved_router.get("")
async def list_calculations(project_id: Optional[str] = None, calc_type: Optional[str] = None):
    """List saved calculations."""
    return project_mgr.list_calculations(project_id=project_id, calc_type=calc_type)


@saved_router.get("/{calc_id}")
async def get_calculation(calc_id: str):
    """Get a saved calculation."""
    result = project_mgr.get_calculation(calc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return result


@saved_router.delete("/{calc_id}")
async def delete_calculation(calc_id: str):
    """Delete a saved calculation."""
    if not project_mgr.delete_calculation(calc_id):
        raise HTTPException(status_code=404, detail="Calculation not found")
    return {"message": "Calculation deleted"}


# ============== Report Router ==============
report_router = APIRouter(prefix="/api/reports", tags=["Reports"])


@report_router.post("/generate")
async def generate_report(req: ReportRequest):
    """Generate an HTML calculation report."""
    if req.calc_type == "beam":
        html_content = ReportGenerator.generate_beam_report(req.results, req.project_info)
    elif req.calc_type == "column":
        html_content = ReportGenerator.generate_column_report(req.results, req.project_info)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported report type: {req.calc_type}")

    return Response(content=html_content, media_type="text/html")
