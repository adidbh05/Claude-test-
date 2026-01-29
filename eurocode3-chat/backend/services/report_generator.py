"""
Calculation Report Generator.
Produces structured HTML reports for steel design calculations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import html


class ReportGenerator:
    """Generates HTML calculation reports for export."""

    @staticmethod
    def generate_beam_report(results: Dict[str, Any], project_info: Optional[Dict] = None) -> str:
        """Generate a full beam design check report."""
        pi = project_info or {}
        sp = results.get("section", {})

        report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Beam Design Report — EC3</title>
<style>{ReportGenerator._report_css()}</style>
</head>
<body>
<div class="report">
<header class="report-header">
    <div class="header-left">
        <h1>Beam Design Check</h1>
        <p class="subtitle">EN 1993-1-1</p>
    </div>
    <div class="header-right">
        <table class="info-table">
            <tr><td>Project:</td><td>{html.escape(pi.get('project', 'N/A'))}</td></tr>
            <tr><td>Engineer:</td><td>{html.escape(pi.get('engineer', 'N/A'))}</td></tr>
            <tr><td>Date:</td><td>{datetime.utcnow().strftime('%Y-%m-%d')}</td></tr>
            <tr><td>Ref:</td><td>{html.escape(pi.get('reference', 'N/A'))}</td></tr>
        </table>
    </div>
</header>

<section class="section">
    <h2>1. Section Properties</h2>
    <table class="data-table">
        <tr><th>Property</th><th>Value</th><th>Unit</th></tr>
        <tr><td>Section</td><td colspan="2">{html.escape(str(sp.get('name', 'N/A')))}</td></tr>
        <tr><td>Steel Grade</td><td>{results.get('steel_grade', 'N/A')}</td><td></td></tr>
        <tr><td>Yield Strength f<sub>y</sub></td><td>{results.get('fy', 'N/A')}</td><td>N/mm²</td></tr>
        <tr><td>Height h</td><td>{sp.get('h', 'N/A')}</td><td>mm</td></tr>
        <tr><td>Width b</td><td>{sp.get('b', 'N/A')}</td><td>mm</td></tr>
        <tr><td>Web thickness t<sub>w</sub></td><td>{sp.get('tw', 'N/A')}</td><td>mm</td></tr>
        <tr><td>Flange thickness t<sub>f</sub></td><td>{sp.get('tf', 'N/A')}</td><td>mm</td></tr>
        <tr><td>Area A</td><td>{sp.get('A', 'N/A')}</td><td>mm²</td></tr>
        <tr><td>I<sub>y</sub></td><td>{sp.get('Iy', 'N/A')}</td><td>mm⁴</td></tr>
        <tr><td>W<sub>pl,y</sub></td><td>{sp.get('Wpl_y', 'N/A')}</td><td>mm³</td></tr>
    </table>
</section>"""

        # Classification
        classif = results.get("classification", {})
        report += f"""
<section class="section">
    <h2>2. Cross-Section Classification</h2>
    <p class="clause">({classif.get('clause', 'Table 5.2')})</p>
    <table class="data-table">
        <tr><th>Element</th><th>c/t</th><th>Class</th></tr>
        <tr><td>Flange</td><td>{classif.get('ct_flange', 'N/A')}</td><td class="class-{classif.get('flange_class', '')}">{classif.get('flange_class', 'N/A')}</td></tr>
        <tr><td>Web</td><td>{classif.get('ct_web', 'N/A')}</td><td class="class-{classif.get('web_class', '')}">{classif.get('web_class', 'N/A')}</td></tr>
        <tr><td><strong>Overall</strong></td><td></td><td class="class-{classif.get('overall_class', '')}"><strong>Class {classif.get('overall_class', 'N/A')}</strong></td></tr>
    </table>
    <p>ε = √(235/f<sub>y</sub>) = {classif.get('epsilon', 'N/A')}</p>
</section>"""

        # Bending
        bending = results.get("bending", {})
        report += f"""
<section class="section">
    <h2>3. Bending Resistance</h2>
    <p class="clause">({bending.get('clause', 'Clause 6.2.5')})</p>
    <div class="formula">M<sub>c,Rd</sub> = W × f<sub>y</sub> / γ<sub>M0</sub></div>
    <table class="data-table">
        <tr><td>Section modulus used</td><td>{bending.get('method', 'N/A')}</td></tr>
        <tr><td>W</td><td>{bending.get('W_used_mm3', 'N/A')} mm³</td></tr>
        <tr><td>γ<sub>M0</sub></td><td>{bending.get('gamma_M0', 'N/A')}</td></tr>
        <tr class="result"><td><strong>M<sub>c,Rd</sub></strong></td><td><strong>{bending.get('Mc_Rd_kNm', 'N/A')} kNm</strong></td></tr>
    </table>
</section>"""

        # Shear
        shear = results.get("shear", {})
        report += f"""
<section class="section">
    <h2>4. Shear Resistance</h2>
    <p class="clause">({shear.get('clause', 'Clause 6.2.6')})</p>
    <div class="formula">V<sub>pl,Rd</sub> = A<sub>v</sub> × (f<sub>y</sub> / √3) / γ<sub>M0</sub></div>
    <table class="data-table">
        <tr><td>Shear area A<sub>v</sub></td><td>{shear.get('Av_mm2', 'N/A')} mm²</td></tr>
        <tr class="result"><td><strong>V<sub>pl,Rd</sub></strong></td><td><strong>{shear.get('Vpl_Rd_kN', 'N/A')} kN</strong></td></tr>
    </table>
</section>"""

        # LTB
        ltb = results.get("ltb")
        if ltb:
            report += f"""
<section class="section">
    <h2>5. Lateral-Torsional Buckling</h2>
    <p class="clause">({ltb.get('clause', 'Clause 6.3.2')})</p>
    <div class="formula">M<sub>b,Rd</sub> = χ<sub>LT</sub> × W<sub>y</sub> × f<sub>y</sub> / γ<sub>M1</sub></div>
    <table class="data-table">
        <tr><td>M<sub>cr</sub></td><td>{ltb.get('Mcr_kNm', 'N/A')} kNm</td></tr>
        <tr><td>λ̄<sub>LT</sub></td><td>{ltb.get('lambda_LT', 'N/A')}</td></tr>
        <tr><td>χ<sub>LT</sub></td><td>{ltb.get('chi_LT', 'N/A')}</td></tr>
        <tr class="result"><td><strong>M<sub>b,Rd</sub></strong></td><td><strong>{ltb.get('Mb_Rd_kNm', 'N/A')} kNm</strong></td></tr>
    </table>
</section>"""

        # Deflection
        defl = results.get("deflection")
        if defl:
            report += f"""
<section class="section">
    <h2>6. Deflection Check (SLS)</h2>
    <p class="clause">({defl.get('clause', 'Clause 7.2.1')})</p>
    <table class="data-table">
        <tr><td>Maximum deflection δ</td><td>{defl.get('delta_mm', 'N/A')} mm</td></tr>
        <tr><td>Span ratio</td><td>{defl.get('span_ratio', 'N/A')}</td></tr>
    </table>
</section>"""

        # Utilization Summary
        utils = results.get("utilizations", {})
        report += f"""
<section class="section summary">
    <h2>Summary — Utilization Ratios</h2>
    <table class="data-table utilization-table">
        <tr><th>Check</th><th>Utilization</th><th>Status</th></tr>"""

        for check_name, ratio in utils.items():
            status = "OK" if ratio <= 1.0 else "FAIL"
            bar_pct = min(ratio * 100, 100)
            color = ReportGenerator._utilization_color(ratio)
            report += f"""
        <tr>
            <td>{html.escape(check_name.replace('_', ' ').title())}</td>
            <td>
                <div class="util-bar-bg"><div class="util-bar" style="width:{bar_pct}%;background:{color}"></div></div>
                {round(ratio * 100, 1)}%
            </td>
            <td class="status-{status.lower()}">{status}</td>
        </tr>"""

        max_util = results.get("max_utilization", 0)
        overall = results.get("overall_status", "OK")
        report += f"""
    </table>
    <div class="overall-status status-{overall.lower()}">
        Overall: {overall} — Max Utilization {round(max_util * 100, 1)}%
    </div>
</section>

<footer class="report-footer">
    <p>Generated by Eurocode 3 Design Assistant | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
    <p class="disclaimer">This report is for preliminary design purposes. All calculations must be verified by a qualified structural engineer.</p>
</footer>
</div>
</body>
</html>"""

        return report

    @staticmethod
    def generate_column_report(results: Dict[str, Any], project_info: Optional[Dict] = None) -> str:
        """Generate a column design check report."""
        pi = project_info or {}
        sp = results.get("section", {})

        report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Column Design Report — EC3</title>
<style>{ReportGenerator._report_css()}</style>
</head>
<body>
<div class="report">
<header class="report-header">
    <div class="header-left">
        <h1>Column Design Check</h1>
        <p class="subtitle">EN 1993-1-1</p>
    </div>
    <div class="header-right">
        <table class="info-table">
            <tr><td>Project:</td><td>{html.escape(pi.get('project', 'N/A'))}</td></tr>
            <tr><td>Engineer:</td><td>{html.escape(pi.get('engineer', 'N/A'))}</td></tr>
            <tr><td>Date:</td><td>{datetime.utcnow().strftime('%Y-%m-%d')}</td></tr>
        </table>
    </div>
</header>

<section class="section">
    <h2>1. Section &amp; Material</h2>
    <table class="data-table">
        <tr><td>Steel Grade</td><td>{results.get('steel_grade', 'N/A')}</td></tr>
        <tr><td>f<sub>y</sub></td><td>{results.get('fy', 'N/A')} N/mm²</td></tr>
        <tr><td>Area A</td><td>{sp.get('A', 'N/A')} mm²</td></tr>
    </table>
</section>"""

        # Compression
        comp = results.get("compression", {})
        report += f"""
<section class="section">
    <h2>2. Cross-Section Compression Resistance</h2>
    <p class="clause">({comp.get('clause', '')})</p>
    <div class="formula">N<sub>c,Rd</sub> = A × f<sub>y</sub> / γ<sub>M0</sub></div>
    <table class="data-table">
        <tr class="result"><td><strong>N<sub>c,Rd</sub></strong></td><td><strong>{comp.get('Nc_Rd_kN', 'N/A')} kN</strong></td></tr>
    </table>
</section>"""

        # Buckling y-y
        buck_y = results.get("buckling_y")
        if buck_y:
            report += f"""
<section class="section">
    <h2>3. Flexural Buckling — y-y axis</h2>
    <p class="clause">({buck_y.get('clause', '')})</p>
    <table class="data-table">
        <tr><td>L<sub>cr</sub></td><td>{buck_y.get('Lcr_mm', 'N/A')} mm</td></tr>
        <tr><td>Slenderness L<sub>cr</sub>/i</td><td>{buck_y.get('slenderness', 'N/A')}</td></tr>
        <tr><td>λ̄</td><td>{buck_y.get('lambda_bar', 'N/A')}</td></tr>
        <tr><td>Buckling curve</td><td>{buck_y.get('buckling_curve', 'N/A')}</td></tr>
        <tr><td>χ</td><td>{buck_y.get('chi', 'N/A')}</td></tr>
        <tr class="result"><td><strong>N<sub>b,Rd</sub></strong></td><td><strong>{buck_y.get('Nb_Rd_kN', 'N/A')} kN</strong></td></tr>
        <tr><td>Utilization</td><td>{round(buck_y.get('utilization', 0) * 100, 1)}%</td></tr>
    </table>
</section>"""

        # Buckling z-z
        buck_z = results.get("buckling_z")
        if buck_z:
            report += f"""
<section class="section">
    <h2>4. Flexural Buckling — z-z axis</h2>
    <table class="data-table">
        <tr><td>L<sub>cr</sub></td><td>{buck_z.get('Lcr_mm', 'N/A')} mm</td></tr>
        <tr><td>λ̄</td><td>{buck_z.get('lambda_bar', 'N/A')}</td></tr>
        <tr><td>χ</td><td>{buck_z.get('chi', 'N/A')}</td></tr>
        <tr class="result"><td><strong>N<sub>b,Rd</sub></strong></td><td><strong>{buck_z.get('Nb_Rd_kN', 'N/A')} kN</strong></td></tr>
        <tr><td>Utilization</td><td>{round(buck_z.get('utilization', 0) * 100, 1)}%</td></tr>
    </table>
</section>"""

        # Summary
        utils = results.get("utilizations", {})
        report += """<section class="section summary"><h2>Summary</h2><table class="data-table utilization-table"><tr><th>Check</th><th>Utilization</th><th>Status</th></tr>"""
        for name, ratio in utils.items():
            status = "OK" if ratio <= 1.0 else "FAIL"
            bar_pct = min(ratio * 100, 100)
            color = ReportGenerator._utilization_color(ratio)
            report += f'<tr><td>{html.escape(name.replace("_", " ").title())}</td><td><div class="util-bar-bg"><div class="util-bar" style="width:{bar_pct}%;background:{color}"></div></div>{round(ratio*100,1)}%</td><td class="status-{status.lower()}">{status}</td></tr>'

        overall = results.get("overall_status", "OK")
        max_u = results.get("max_utilization", 0)
        report += f"""</table><div class="overall-status status-{overall.lower()}">Overall: {overall} — Max Utilization {round(max_u*100,1)}%</div></section>
<footer class="report-footer"><p>Generated by Eurocode 3 Design Assistant | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p><p class="disclaimer">This report is for preliminary design purposes. All calculations must be verified by a qualified structural engineer.</p></footer></div></body></html>"""

        return report

    @staticmethod
    def _utilization_color(ratio: float) -> str:
        if ratio <= 0.5:
            return "#4ade80"
        elif ratio <= 0.75:
            return "#fbbf24"
        elif ratio <= 1.0:
            return "#fb923c"
        else:
            return "#f87171"

    @staticmethod
    def _report_css() -> str:
        return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; color: #1a1a2e; line-height: 1.6; }
.report { max-width: 900px; margin: 2rem auto; background: #fff; box-shadow: 0 2px 20px rgba(0,0,0,0.1); }
.report-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 2rem; background: linear-gradient(135deg, #1a2332 0%, #2d3a4f 100%); color: #fff; }
.report-header h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
.report-header .subtitle { opacity: 0.8; font-size: 0.9rem; }
.info-table td { padding: 0.1rem 0.5rem; font-size: 0.85rem; }
.info-table td:first-child { opacity: 0.8; }
.section { padding: 1.5rem 2rem; border-bottom: 1px solid #e5e7eb; }
.section h2 { color: #1a2332; font-size: 1.1rem; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid #4a9eff; }
.clause { color: #6b7280; font-size: 0.8rem; margin-bottom: 0.75rem; font-style: italic; }
.formula { background: #f8fafc; border-left: 3px solid #4a9eff; padding: 0.75rem 1rem; margin: 0.75rem 0; font-family: 'Cambria Math', serif; font-size: 1rem; }
.data-table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; }
.data-table th, .data-table td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #e5e7eb; font-size: 0.9rem; }
.data-table th { background: #f1f5f9; font-weight: 600; color: #334155; }
.data-table .result { background: #eff6ff; }
.data-table .result td { font-weight: 600; color: #1a2332; }
.class-1, .class-2 { color: #16a34a; font-weight: 600; }
.class-3 { color: #ca8a04; font-weight: 600; }
.class-4 { color: #dc2626; font-weight: 600; }
.util-bar-bg { display: inline-block; width: 120px; height: 12px; background: #e5e7eb; border-radius: 6px; overflow: hidden; margin-right: 0.5rem; vertical-align: middle; }
.util-bar { height: 100%; border-radius: 6px; transition: width 0.3s; }
.status-ok { color: #16a34a; font-weight: 700; }
.status-fail { color: #dc2626; font-weight: 700; }
.overall-status { margin-top: 1rem; padding: 1rem; border-radius: 8px; text-align: center; font-size: 1.1rem; font-weight: 700; }
.overall-status.status-ok { background: #f0fdf4; border: 2px solid #16a34a; color: #16a34a; }
.overall-status.status-fail { background: #fef2f2; border: 2px solid #dc2626; color: #dc2626; }
.summary { background: #f8fafc; }
.report-footer { padding: 1.5rem 2rem; text-align: center; color: #6b7280; font-size: 0.8rem; border-top: 2px solid #1a2332; }
.disclaimer { margin-top: 0.5rem; font-style: italic; color: #9ca3af; }
@media print { body { background: #fff; } .report { box-shadow: none; margin: 0; } }
"""
