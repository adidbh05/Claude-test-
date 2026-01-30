"""
Pydantic models for the Eurocode 3 Structural Design Chat API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============== Chat Models ==============

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime
    tokens_used: Optional[int] = None


class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


# ============== System Models ==============

class RateLimitInfo(BaseModel):
    requests_remaining: int
    reset_time: datetime
    limit: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: str


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_status: str
    database_status: str


# ============== Section Database Models ==============

class SectionQuery(BaseModel):
    query: str = ""
    section_type: Optional[str] = None
    min_height: Optional[float] = None
    max_height: Optional[float] = None
    min_area: Optional[float] = None
    max_mass: Optional[float] = None


class SectionResponse(BaseModel):
    name: str
    type: str
    properties: Dict[str, Any]


# ============== Calculation Models ==============

class BeamCheckRequest(BaseModel):
    section_name: str = Field(..., description="e.g. 'IPE 300'")
    steel_grade: str = Field(default="S355")
    span_mm: float = Field(..., gt=0)
    MEd_kNm: float = Field(..., ge=0, description="Design bending moment")
    VEd_kN: float = Field(..., ge=0, description="Design shear force")
    NEd_kN: float = Field(default=0, description="Design axial force")
    Lcr_LTB_mm: Optional[float] = Field(None, description="Buckling length for LTB")
    C1: float = Field(default=1.0, description="Moment distribution factor")
    w_sls_kN_m: Optional[float] = Field(None, description="SLS UDL for deflection check")


class ColumnCheckRequest(BaseModel):
    section_name: str = Field(..., description="e.g. 'HEB 200'")
    steel_grade: str = Field(default="S355")
    NEd_kN: float = Field(..., gt=0, description="Design axial force")
    My_Ed_kNm: float = Field(default=0)
    Mz_Ed_kNm: float = Field(default=0)
    Lcr_y_mm: float = Field(..., gt=0, description="Buckling length y-y")
    Lcr_z_mm: float = Field(..., gt=0, description="Buckling length z-z")
    buckling_curve_y: str = Field(default="b")
    buckling_curve_z: str = Field(default="c")


class ClassificationRequest(BaseModel):
    section_name: str
    steel_grade: str = "S355"
    NEd_kN: float = 0


class BoltCheckRequest(BaseModel):
    bolt_diameter: int = Field(..., description="Bolt diameter in mm (12-36)")
    bolt_grade: str = Field(default="8.8")
    n_bolts: int = Field(default=1, ge=1)
    VEd_kN: float = Field(default=0, ge=0, description="Design shear force")
    FtEd_kN: float = Field(default=0, ge=0, description="Design tension force")
    shear_plane: str = Field(default="threaded")


class WeldCheckRequest(BaseModel):
    throat_mm: float = Field(..., gt=0, description="Weld throat thickness")
    length_mm: float = Field(..., gt=0, description="Weld length")
    steel_grade: str = Field(default="S355")
    FEd_kN: float = Field(..., gt=0, description="Design force on weld")


class DeflectionCheckRequest(BaseModel):
    section_name: str
    span_mm: float = Field(..., gt=0)
    load_kN_m: float = Field(default=0, description="UDL in kN/m")
    point_load_kN: float = Field(default=0, description="Point load in kN")


# ============== Load Combination Models ==============

class LoadCaseInput(BaseModel):
    name: str
    type: str = Field(..., description="permanent or variable")
    category: str = Field(default="B", description="EN 1990 load category")
    value: float
    favorable: bool = False


class LoadCombinationRequest(BaseModel):
    load_cases: List[LoadCaseInput]
    approach: str = Field(default="6.10", description="6.10 or 6.10ab")
    limit_state: str = Field(default="STR/GEO")
    include_sls: bool = True


# ============== Project Models ==============

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    client: str = ""
    location: str = ""
    steel_grade: str = "S355"
    national_annex: str = "EC"


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client: Optional[str] = None
    location: Optional[str] = None
    steel_grade: Optional[str] = None
    national_annex: Optional[str] = None
    status: Optional[str] = None


class SaveCalculationRequest(BaseModel):
    name: str
    calc_type: str
    input_data: Dict[str, Any]
    result_data: Dict[str, Any]
    project_id: Optional[str] = None


# ============== Report Models ==============

class ReportRequest(BaseModel):
    calc_type: str = Field(..., description="beam or column")
    results: Dict[str, Any]
    project_info: Optional[Dict[str, str]] = None
