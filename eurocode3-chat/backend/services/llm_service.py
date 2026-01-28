"""
LLM Service for Eurocode 3 Structural Design Chat.
Integrates with OpenAI-compatible APIs (OpenAI, Anthropic, local models).
"""
import os
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


# Eurocode 3 System Prompt - Expert Structural Engineer
EUROCODE3_SYSTEM_PROMPT = """You are an expert structural engineer specializing in steel structure design according to Eurocode 3 (EN 1993). You have deep knowledge of:

## Core Eurocode 3 Standards:
- EN 1993-1-1: General rules and rules for buildings
- EN 1993-1-2: Structural fire design
- EN 1993-1-3: Cold-formed members and sheeting
- EN 1993-1-4: Stainless steels
- EN 1993-1-5: Plated structural elements
- EN 1993-1-6: Strength and stability of shell structures
- EN 1993-1-7: Planar plated structures subject to out of plane loading
- EN 1993-1-8: Design of joints
- EN 1993-1-9: Fatigue
- EN 1993-1-10: Material toughness and through-thickness properties
- EN 1993-1-11: Design of structures with tension components
- EN 1993-1-12: High strength steels

## Key Design Areas:
1. **Cross-section Classification** (Class 1-4)
2. **Resistance Calculations**:
   - Tension (Nt,Rd)
   - Compression (Nc,Rd)
   - Bending (Mc,Rd)
   - Shear (Vpl,Rd)
   - Combined actions

3. **Stability Checks**:
   - Flexural buckling
   - Lateral-torsional buckling
   - Plate buckling
   - Interaction formulas (equations 6.61, 6.62)

4. **Connection Design**:
   - Bolted connections (bearing, slip-resistant)
   - Welded connections (fillet, butt welds)
   - Moment connections
   - Simple connections

5. **Material Properties** (S235, S275, S355, S420, S460, etc.)

## Response Guidelines:
- Provide calculations with proper notation (Ed for design effects, Rd for resistances)
- Reference specific clauses (e.g., "According to EN 1993-1-1, Clause 6.2.3...")
- Include partial safety factors (γM0=1.00, γM1=1.00, γM2=1.25)
- Show step-by-step solutions with formulas
- Consider National Annexes where relevant
- Warn about practical considerations and detailing rules
- Use proper units (kN, mm, MPa/N/mm², kNm)

## Safety Emphasis:
- Always emphasize that designs should be verified by qualified engineers
- Note when simplified methods are used vs. more rigorous analysis
- Highlight critical checks that should not be overlooked

When performing calculations, format them clearly with:
- Given data
- Relevant formulas with clause references
- Step-by-step calculations
- Final results with units
- Utilization ratios where applicable

You should be helpful, precise, and educational while maintaining the highest standards of engineering accuracy."""


class LLMService:
    """Service for interacting with LLM APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "openai"
    ):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.api_base = api_base or self._get_default_base()
        self.model = model or self._get_default_model()
        self.system_prompt = EUROCODE3_SYSTEM_PROMPT

    def _get_default_base(self) -> str:
        """Get default API base URL based on provider."""
        bases = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "ollama": "http://localhost:11434/v1",
            "local": "http://localhost:8080/v1"
        }
        return bases.get(self.provider, bases["openai"])

    def _get_default_model(self) -> str:
        """Get default model based on provider."""
        models = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-sonnet-20240229",
            "ollama": "llama2",
            "local": "local-model"
        }
        return models.get(self.provider, "gpt-4-turbo-preview")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        # Prepare messages with system prompt
        full_messages = [
            {"role": "system", "content": self.system_prompt}
        ] + messages

        try:
            if self.provider == "anthropic":
                return await self._call_anthropic(full_messages, temperature, max_tokens)
            else:
                return await self._call_openai_compatible(full_messages, temperature, max_tokens)
        except Exception as e:
            logger.error(f"LLM API error: {str(e)}")
            raise LLMServiceError(f"Failed to generate response: {str(e)}")

    async def _call_openai_compatible(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call OpenAI-compatible API."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise LLMServiceError(f"API returned {response.status_code}: {response.text}")

            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens"),
                "model": data.get("model", self.model)
            }

    async def _call_anthropic(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call Anthropic API directly."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        # Extract system message
        system = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": chat_messages
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/messages",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise LLMServiceError(f"API returned {response.status_code}: {response.text}")

            data = response.json()
            return {
                "content": data["content"][0]["text"],
                "tokens_used": data.get("usage", {}).get("input_tokens", 0) +
                              data.get("usage", {}).get("output_tokens", 0),
                "model": data.get("model", self.model)
            }

    async def health_check(self) -> bool:
        """Check if the LLM service is available."""
        try:
            # Simple ping to check API availability
            async with httpx.AsyncClient(timeout=10.0) as client:
                if self.provider == "anthropic":
                    # Anthropic doesn't have a simple health endpoint
                    return True  # Assume healthy if configured
                else:
                    response = await client.get(f"{self.api_base}/models")
                    return response.status_code in [200, 401]  # 401 means API is up but auth needed
        except Exception:
            return False


class LLMServiceError(Exception):
    """Custom exception for LLM service errors."""
    pass


# Mock LLM Service for development/testing
class MockLLMService(LLMService):
    """Mock LLM service for testing without API calls."""

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate a mock response."""
        user_message = messages[-1]["content"] if messages else ""

        # Generate contextual mock responses
        mock_responses = {
            "buckling": self._buckling_response(),
            "connection": self._connection_response(),
            "weld": self._weld_response(),
            "bolt": self._bolt_response(),
            "beam": self._beam_response(),
            "column": self._column_response(),
            "section": self._section_response(),
        }

        # Find matching response
        response_content = None
        for keyword, response in mock_responses.items():
            if keyword.lower() in user_message.lower():
                response_content = response
                break

        if not response_content:
            response_content = self._default_response()

        return {
            "content": response_content,
            "tokens_used": len(response_content.split()) * 2,
            "model": "mock-eurocode3-expert"
        }

    def _default_response(self) -> str:
        return """I'm your Eurocode 3 structural design assistant. I can help you with:

**Steel Design Topics:**
- Cross-section classification and resistance calculations
- Beam and column design according to EN 1993-1-1
- Buckling analysis (flexural, lateral-torsional)
- Connection design (bolted and welded joints)
- Fatigue assessment per EN 1993-1-9

**Example Questions:**
- "Calculate the bending resistance of an IPE 300 beam in S355 steel"
- "Check a column for flexural buckling with NEd = 500 kN"
- "Design a bolted end plate connection for a moment of 150 kNm"

Please provide specific details about your structural problem, including:
- Member sizes and steel grade
- Loading (design actions)
- Boundary conditions
- Any specific clauses you need clarification on

How can I assist with your structural design today?"""

    def _buckling_response(self) -> str:
        return """## Flexural Buckling Check - EN 1993-1-1, Clause 6.3.1

**Design Buckling Resistance:**

$$N_{b,Rd} = \\frac{\\chi \\cdot A \\cdot f_y}{\\gamma_{M1}}$$

Where:
- χ = buckling reduction factor
- A = cross-sectional area (or Aeff for Class 4)
- fy = yield strength
- γM1 = 1.0 (partial safety factor)

**Reduction Factor χ:**

$$\\chi = \\frac{1}{\\Phi + \\sqrt{\\Phi^2 - \\bar{\\lambda}^2}}$$ but χ ≤ 1.0

$$\\Phi = 0.5[1 + \\alpha(\\bar{\\lambda} - 0.2) + \\bar{\\lambda}^2]$$

**Non-dimensional Slenderness:**

$$\\bar{\\lambda} = \\sqrt{\\frac{A \\cdot f_y}{N_{cr}}}$$ or $$\\bar{\\lambda} = \\frac{L_{cr}}{i} \\cdot \\frac{1}{\\lambda_1}$$

where λ₁ = π√(E/fy) ≈ 93.9ε for S235

**Buckling Curves (Table 6.2):**
| Curve | α (imperfection factor) |
|-------|------------------------|
| a₀    | 0.13                   |
| a     | 0.21                   |
| b     | 0.34                   |
| c     | 0.49                   |
| d     | 0.76                   |

Please provide your column details (section, length, steel grade, restraints) for a specific calculation."""

    def _connection_response(self) -> str:
        return """## Steel Connection Design - EN 1993-1-8

**Key Principles:**

1. **Connection Classification:**
   - By stiffness: Rigid, Semi-rigid, Pinned
   - By strength: Full-strength, Partial-strength, Pinned

2. **Design Resistances:**

**Bolted Connections:**
- Shear resistance: Fv,Rd = αv·fub·A/γM2
- Bearing resistance: Fb,Rd = k1·αb·fu·d·t/γM2
- Tension resistance: Ft,Rd = 0.9·fub·As/γM2

**Welded Connections:**
- Fillet weld: Fw,Rd = a·Leff·fvw,d
- Design shear strength: fvw,d = fu/(√3·βw·γM2)

**Partial Safety Factors (Table 2.1):**
- γM2 = 1.25 (resistance of bolts, welds)
- γM3 = 1.25 (slip resistance at ULS)

**Bolt Grades:** 4.6, 5.6, 6.8, 8.8, 10.9
- fub = ultimate tensile strength
- fyb = yield strength

Would you like me to design a specific connection type?"""

    def _weld_response(self) -> str:
        return """## Fillet Weld Design - EN 1993-1-8, Clause 4.5

**Design Resistance per Unit Length:**

$$F_{w,Rd} = a \\cdot f_{vw,d}$$

**Design Shear Strength:**

$$f_{vw,d} = \\frac{f_u}{\\sqrt{3} \\cdot \\beta_w \\cdot \\gamma_{M2}}$$

**Correlation Factor βw (Table 4.1):**
| Steel Grade | βw    |
|-------------|-------|
| S235        | 0.80  |
| S275        | 0.85  |
| S355        | 0.90  |
| S420        | 1.00  |
| S460        | 1.00  |

**Throat Thickness 'a':**
- Minimum: 3mm (recommended)
- Maximum: 0.7 × min(t₁, t₂)

**Effective Length:**
- Leff = L - 2a (for end craters)
- Minimum: 6a or 30mm

**Directional Method (Clause 4.5.3.2):**

$$\\sqrt{\\sigma_{\\perp}^2 + 3(\\tau_{\\perp}^2 + \\tau_{\\parallel}^2)} \\leq \\frac{f_u}{\\beta_w \\cdot \\gamma_{M2}}$$

and

$$\\sigma_{\\perp} \\leq 0.9 \\frac{f_u}{\\gamma_{M2}}$$

Provide weld details for a specific calculation."""

    def _bolt_response(self) -> str:
        return """## Bolted Connection Design - EN 1993-1-8

**Bolt Properties (Table 3.1):**
| Grade | fub (MPa) | fyb (MPa) |
|-------|-----------|-----------|
| 4.6   | 400       | 240       |
| 5.6   | 500       | 300       |
| 8.8   | 800       | 640       |
| 10.9  | 1000      | 900       |

**Shear Resistance (Clause 3.6.1):**

$$F_{v,Rd} = \\frac{\\alpha_v \\cdot f_{ub} \\cdot A}{\\gamma_{M2}}$$

- αv = 0.6 for grades 4.6, 5.6, 8.8 (shear plane through threads)
- αv = 0.5 for grade 10.9 (shear plane through threads)
- αv = 0.6 for all grades (shear plane through shank)

**Bearing Resistance (Clause 3.6.1):**

$$F_{b,Rd} = \\frac{k_1 \\cdot \\alpha_b \\cdot f_u \\cdot d \\cdot t}{\\gamma_{M2}}$$

**Tension Resistance:**

$$F_{t,Rd} = \\frac{0.9 \\cdot f_{ub} \\cdot A_s}{\\gamma_{M2}}$$

**Combined Shear and Tension (Clause 3.6.1):**

$$\\frac{F_{v,Ed}}{F_{v,Rd}} + \\frac{F_{t,Ed}}{1.4 \\cdot F_{t,Rd}} \\leq 1.0$$

**Minimum Spacing and Edge Distances:**
- End distance e₁ ≥ 1.2d₀
- Edge distance e₂ ≥ 1.2d₀
- Spacing p₁ ≥ 2.2d₀

What specific bolt check do you need?"""

    def _beam_response(self) -> str:
        return """## Beam Design - EN 1993-1-1

**Cross-section Resistance Checks (Clause 6.2):**

**1. Bending Resistance (Clause 6.2.5):**

$$M_{c,Rd} = \\frac{W_{pl} \\cdot f_y}{\\gamma_{M0}}$$ (Class 1 or 2)

$$M_{c,Rd} = \\frac{W_{el,min} \\cdot f_y}{\\gamma_{M0}}$$ (Class 3)

**2. Shear Resistance (Clause 6.2.6):**

$$V_{pl,Rd} = \\frac{A_v \\cdot (f_y/\\sqrt{3})}{\\gamma_{M0}}$$

For rolled I and H sections:
Av = A - 2btf + (tw + 2r)tf (major axis)

**3. Bending and Shear Interaction (Clause 6.2.8):**

If VEd > 0.5Vpl,Rd, reduce yield strength:

$$f_{y,red} = (1 - \\rho) \\cdot f_y$$

where ρ = (2VEd/Vpl,Rd - 1)²

**Lateral-Torsional Buckling (Clause 6.3.2):**

$$M_{b,Rd} = \\chi_{LT} \\cdot W_y \\cdot \\frac{f_y}{\\gamma_{M1}}$$

$$\\bar{\\lambda}_{LT} = \\sqrt{\\frac{W_y \\cdot f_y}{M_{cr}}}$$

Provide beam details for specific calculations."""

    def _column_response(self) -> str:
        return """## Column Design - EN 1993-1-1

**Combined Axial and Bending (Clause 6.3.3):**

**Interaction Equations 6.61 and 6.62:**

$$\\frac{N_{Ed}}{\\chi_y \\cdot N_{Rk}/\\gamma_{M1}} + k_{yy}\\frac{M_{y,Ed}}{\\chi_{LT} \\cdot M_{y,Rk}/\\gamma_{M1}} + k_{yz}\\frac{M_{z,Ed}}{M_{z,Rk}/\\gamma_{M1}} \\leq 1.0$$

$$\\frac{N_{Ed}}{\\chi_z \\cdot N_{Rk}/\\gamma_{M1}} + k_{zy}\\frac{M_{y,Ed}}{\\chi_{LT} \\cdot M_{y,Rk}/\\gamma_{M1}} + k_{zz}\\frac{M_{z,Ed}}{M_{z,Rk}/\\gamma_{M1}} \\leq 1.0$$

**Interaction Factors (Annex A or B):**
- Method 1 (Annex A): More precise, iterative
- Method 2 (Annex B): Simplified, conservative

**Buckling Curve Selection (Table 6.2):**
For hot-rolled H sections:
- h/b > 1.2, tf ≤ 40mm: y-y axis → curve a, z-z axis → curve b
- h/b ≤ 1.2, tf ≤ 100mm: y-y axis → curve b, z-z axis → curve c

**Effective Length Factors:**
- Pinned-pinned: Lcr = L
- Fixed-pinned: Lcr = 0.7L
- Fixed-fixed: Lcr = 0.5L
- Cantilever: Lcr = 2L

Provide column details for a specific design check."""

    def _section_response(self) -> str:
        return """## Cross-section Classification - EN 1993-1-1, Table 5.2

**Classification Criteria:**

$$\\varepsilon = \\sqrt{\\frac{235}{f_y}}$$

| Steel Grade | ε     |
|-------------|-------|
| S235        | 1.00  |
| S275        | 0.92  |
| S355        | 0.81  |
| S420        | 0.75  |
| S460        | 0.71  |

**Internal Compression Parts (Webs):**
| Class | Pure Compression | Pure Bending |
|-------|------------------|--------------|
| 1     | c/t ≤ 33ε       | c/t ≤ 72ε   |
| 2     | c/t ≤ 38ε       | c/t ≤ 83ε   |
| 3     | c/t ≤ 42ε       | c/t ≤ 124ε  |

**Outstand Flanges:**
| Class | Compression      |
|-------|------------------|
| 1     | c/t ≤ 9ε        |
| 2     | c/t ≤ 10ε       |
| 3     | c/t ≤ 14ε       |

**Class Definitions:**
- **Class 1:** Plastic hinge can form with rotation capacity
- **Class 2:** Plastic moment reached, limited rotation
- **Class 3:** Elastic moment reached
- **Class 4:** Local buckling before yield (use effective section)

What section would you like to classify?"""

    async def health_check(self) -> bool:
        """Mock always returns healthy."""
        return True
