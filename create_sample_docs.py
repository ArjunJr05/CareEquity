import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import os

def set_cell_background(cell, fill_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)

def add_styled_heading(doc, text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    run = h.runs[0]
    if level == 1:
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(29, 78, 216)
        run.font.bold = True
    elif level == 2:
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(30, 58, 138)
        run.font.bold = True
    return h

def generate_patient_document(filename, patient_name, age, sex, height_cm, weight_kg, bmi, sys_bp, dia_bp, hba1c, glucose, chol, smoking, locations, notes):
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(2)
    title_run = title_p.add_run("CAREEQUITY CLINICAL & LAB SUMMARY REPORT")
    title_run.font.size = Pt(20)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(30, 58, 138)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    sub_run = sub_p.add_run(f"Comprehensive Medical Assessment — Patient ID: {patient_name.replace(' ', '_').upper()}")
    sub_run.font.size = Pt(11)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(100, 116, 139)

    add_styled_heading(doc, "1. Patient Demographics & Body Metrics", level=1)
    
    table_demo = doc.add_table(rows=1, cols=4)
    table_demo.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table_demo.rows[0].cells
    for i, htext in enumerate(["Parameter", "Patient Value", "Parameter", "Patient Value"]):
        hdr[i].text = htext
        set_cell_background(hdr[i], "1D4ED8")
        p = hdr[i].paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(9.5)

    demo_data = [
        ("Full Name", patient_name, "Age", f"{age} years"),
        ("Sex / Gender", sex, "BMI (kg/m²)", f"{bmi}"),
        ("Height (cm)", f"{height_cm} cm", "Weight (kg)", f"{weight_kg} kg")
    ]
    for r1, v1, r2, v2 in demo_data:
        row = table_demo.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text = r1, str(v1), r2, str(v2)
        for c in row:
            set_cell_margins(c, top=60, bottom=60, left=80, right=80)
            c.paragraphs[0].runs[0].font.size = Pt(9)

    add_styled_heading(doc, "2. Clinical Vitals & Laboratory Findings", level=1)
    
    table_vitals = doc.add_table(rows=1, cols=4)
    table_vitals.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr2 = table_vitals.rows[0].cells
    for i, htext in enumerate(["Clinical Indicator", "Measured Value", "Reference Range", "Evaluation / Status"]):
        hdr2[i].text = htext
        set_cell_background(hdr2[i], "059669")
        p = hdr2[i].paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(9.5)

    vitals_data = [
        ("Systolic Blood Pressure", f"{sys_bp} mmHg", "90 - 120 mmHg", "Elevated" if sys_bp > 120 else "Normal"),
        ("Diastolic Blood Pressure", f"{dia_bp} mmHg", "60 - 80 mmHg", "Elevated" if dia_bp > 80 else "Normal"),
        ("HbA1c Glycated Hemoglobin", f"{hba1c} %", "< 5.7 %", "Prediabetic / High" if hba1c >= 5.7 else "Normal"),
        ("Fasting Blood Glucose", f"{glucose} mg/dL", "70 - 99 mg/dL", "Elevated" if glucose > 100 else "Normal"),
        ("Total Cholesterol", f"{chol} mg/dL", "< 200 mg/dL", "Borderline High" if chol >= 200 else "Normal"),
        ("Smoking History", smoking, "Non-Smoker", "Monitored" if smoking != "Never" else "Optimal")
    ]
    for ind, val, ref, stat in vitals_data:
        row = table_vitals.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text = ind, val, ref, stat
        for c in row:
            set_cell_margins(c, top=60, bottom=60, left=80, right=80)
            c.paragraphs[0].runs[0].font.size = Pt(9)

    add_styled_heading(doc, "3. Target Geographic Assessment Locations", level=1)
    for idx, (st, cnt) in enumerate(locations, start=1):
        doc.add_paragraph(f"• Location {idx}: {cnt}, {st}, United States")

    add_styled_heading(doc, "4. Clinical Notes & Observations", level=1)
    doc.add_paragraph(notes)

    out_path = os.path.join("e:/CareEquity/sample_patient_docs", filename)
    doc.save(out_path)
    print(f"Generated sample patient document: {out_path}")

os.makedirs("e:/CareEquity/sample_patient_docs", exist_ok=True)

# Generate 3 new structured documents based on the new lab/vitals parameters:
generate_patient_document(
    filename="Patient_Robert_Chen_Clinical_Lab_Record.docx",
    patient_name="Robert Chen",
    age=54, sex="Female", height_cm=170, weight_kg=75, bmi=26.0,
    sys_bp=138, dia_bp=88, hba1c=6.5, glucose=130, chol=210, smoking="Former",
    locations=[("AL", "Limestone County"), ("GA", "Columbia County")],
    notes="Patient presents with elevated blood pressure (138/88 mmHg), prediabetic HbA1c levels (6.5%), and borderline high cholesterol (210 mg/dL). History of former smoking."
)

generate_patient_document(
    filename="Patient_Sarah_Jenkins_Vitals_Summary.docx",
    patient_name="Sarah Jenkins",
    age=42, sex="Female", height_cm=165, weight_kg=62, bmi=22.8,
    sys_bp=118, dia_bp=76, hba1c=5.4, glucose=92, chol=180, smoking="Never",
    locations=[("NC", "Camden County"), ("TN", "Rutherford County")],
    notes="Patient exhibits optimal blood pressure (118/76 mmHg) and normal fasting glucose (92 mg/dL). Routine SDoH monitoring requested."
)

generate_patient_document(
    filename="Patient_Veena_Kumari_Lab_Results.docx",
    patient_name="Veena Kumari",
    age=61, sex="Female", height_cm=158, weight_kg=78, bmi=31.2,
    sys_bp=145, dia_bp=92, hba1c=7.8, glucose=175, chol=235, smoking="Never",
    locations=[("MS", "Hancock County"), ("AL", "Wilcox County")],
    notes="Patient requires immediate SDoH risk assessment due to elevated HbA1c (7.8%), high fasting glucose (175 mg/dL), and stage 2 hypertension (145/92 mmHg)."
)
