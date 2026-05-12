import math
import io
import csv
import streamlit as st

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def compute_line_angles(lead_angle, spread_angle, line_count):
    if line_count <= 1 or abs(spread_angle) < 1e-6:
        return [lead_angle] * line_count
    step = spread_angle / (line_count - 1)
    half = spread_angle / 2
    return [lead_angle - half + i * step for i in range(line_count)]


def compute_results(
    line_tension,
    line_count,
    lead_h,
    lead_v,
    spread,
    daf,
    sf,
):
    angles_h = compute_line_angles(lead_h, spread, line_count)
    line_data = []
    sum_fx = sum_fy = sum_fz = 0.0
    for i, theta_h in enumerate(angles_h, start=1):
        t_dyn = line_tension * daf
        theta_h_rad = math.radians(theta_h)
        theta_v_rad = math.radians(lead_v)
        th = t_dyn * math.cos(theta_v_rad)
        fz = t_dyn * math.sin(theta_v_rad)
        fx = th * math.cos(theta_h_rad)
        fy = th * math.sin(theta_h_rad)
        sum_fx += fx
        sum_fy += fy
        sum_fz += fz
        line_data.append(
            {
                "Line": f"Line {i}",
                "T (kN)": f"{line_tension:.3f}",
                "T×DAF (kN)": f"{t_dyn:.3f}",
                "H angle (°)": f"{theta_h:.2f}",
                "V angle (°)": f"{lead_v:.2f}",
                "Fx (kN)": f"{fx:.3f}",
                "Fy (kN)": f"{fy:.3f}",
                "Fz (kN)": f"{fz:.3f}",
            }
        )
    h = math.hypot(sum_fx, sum_fy)
    r = math.sqrt(sum_fx**2 + sum_fy**2 + sum_fz**2)
    design_load = r * sf
    horiz_dir = math.degrees(math.atan2(sum_fy, sum_fx)) if h > 1e-9 else 0.0
    return {
        "line_data": line_data,
        "sum_fx": sum_fx,
        "sum_fy": sum_fy,
        "sum_fz": sum_fz,
        "H": h,
        "R": r,
        "Design Load": design_load,
        "Horizontal direction": horiz_dir,
    }


# ...existing code...

def make_csv(results, capacity=None, daf=1.0, sf=1.5):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Mode", "Simplified"])
    writer.writerow(["DAF", f"{daf:.3f}"])
    writer.writerow(["SF", f"{sf:.3f}"])
    writer.writerow([])
    writer.writerow(["Computed Results"])
    writer.writerow(["Horizontal resultant, H (kN)", f"{results['H']:.3f}"])
    writer.writerow(["Total resultant, R (kN)", f"{results['R']:.3f}"])
    writer.writerow(["Design load, R×SF (kN)", f"{results['Design Load']:.3f}"])
    if capacity is not None:
        utilization = results["R"] / capacity * 100 if capacity > 0 else 0.0
        writer.writerow(["Capacity (kN)", f"{capacity:.3f}"])
        writer.writerow(["Utilization (%)", f"{utilization:.1f}"])
    writer.writerow([])
    writer.writerow(["ΣFx", f"{results['sum_fx']:.3f}"])
    writer.writerow(["ΣFy", f"{results['sum_fy']:.3f}"])
    writer.writerow(["ΣFz", f"{results['sum_fz']:.3f}"])
    writer.writerow(["Horizontal direction", f"{results['Horizontal direction']:.2f}"])
    writer.writerow([])
    header = ["Line", "T (kN)", "T×DAF (kN)", "H angle (°)", "V angle (°)", "Fx (kN)", "Fy (kN)", "Fz (kN)"]
    writer.writerow(header)
    for row in results["line_data"]:
        writer.writerow([row[col] for col in header])
    return output.getvalue().encode("utf-8")


def make_pdf(results, capacity=None, daf=1.0, sf=1.5):
    if not PDF_AVAILABLE:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, "Mooring Line Resultant Calculator", ln=True)
    pdf.cell(0, 6, f"Mode: Simplified", ln=True)
    pdf.cell(0, 6, f"DAF: {daf:.3f}", ln=True)
    pdf.cell(0, 6, f"SF: {sf:.3f}", ln=True)
    # ... rest unchanged ...


def main():
    st.title("Mooring Line Resultant Calculator")
    st.write("Choose simplified or detailed mode. Angles are in degrees.")

    mode = st.selectbox("Construction / Calculation mode", ["Simplified", "Detailed"])
    daf = st.number_input(
        "Dynamic amplification factor (DAF)",
        value=1.00,
        min_value=0.0,
        step=0.01,
        format="%.3f",
        key="daf",
    )
    st.write("Typical: 1.0–1.8 depending on exposure.")
    sf = st.number_input(
        "Safety factor (SF)",
        value=1.50,
        min_value=0.01,
        step=0.01,
        format="%.3f",
        key="sf",
    )
    st.write("Design load = resultant × SF.")
    # ... rest unchanged ...

        if st.button("Submit"):
            results = compute_results(
                line_tension,
                line_count,
                lead_h,
                lead_v,
                spread,
                daf,
                sf,
            )
            # ... rest unchanged ...
            csv_bytes = make_csv(results, capacity=bollard_capacity if bollard_capacity > 0 else None, daf=daf, sf=sf)
            st.download_button(
                "Download CSV",
                data=csv_bytes,
                file_name="mooring_results.csv",
                mime="text/csv",
            )

            if PDF_AVAILABLE:
                pdf_bytes = make_pdf(results, capacity=bollard_capacity if bollard_capacity > 0 else None, daf=daf, sf=sf)
                st.download_button(
                    "Download PDF",
                    data=pdf_bytes,
                    file_name="mooring_results.pdf",
                    mime="application/pdf",
                )