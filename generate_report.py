import os
import sqlite3
import qrcode
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table,
                                TableStyle, PageBreak, HRFlowable)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import ast

# ---------- Setup ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "anomalies.db")

# ---------- Connect DB ----------
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT * FROM anomalies")
anomalies = cursor.fetchall()
conn.close()

# ---------- PDF Styles ----------
styles = getSampleStyleSheet()
title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=18, alignment=1, textColor=colors.darkblue)
section_header = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=12, textColor=colors.white, backColor=colors.darkblue, spaceAfter=6, alignment=1)
normal_style = styles['Normal']
filename_style = ParagraphStyle('FileName', fontSize=9, textColor=colors.grey, alignment=1)
info_style = ParagraphStyle('Info', fontSize=10)

# ---------- PDF Document ----------
def header_footer(canvas, doc):
    canvas.saveState()
    # Header
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.darkblue)
    canvas.drawString(inch, A4[1] - 0.5 * inch, "Hornbill Technology – Thermal Inspection Report")
    # Footer with page number
    canvas.setFillColor(colors.black)
    page_num = canvas.getPageNumber()
    canvas.drawRightString(A4[0] - inch, 0.5 * inch, f"Page {page_num}")
    canvas.restoreState()

doc = SimpleDocTemplate(os.path.join(BASE_DIR, "anomaly_report.pdf"),
                        pagesize=A4,
                        rightMargin=30, leftMargin=30, topMargin=50, bottomMargin=50)

elements = []

# ---------- Loop through anomalies ----------
for anomaly in anomalies:
    (anomaly_id, category, priority, size, loss, temperature, parameters,
     remedial_action, comment, latitude, longitude, thermal_img, rgb_img) = anomaly

    # ---------- Parse parameters ----------
    try:
        # If stored as dict string
        parameters_dict = ast.literal_eval(parameters) if isinstance(parameters, str) else parameters
        voltage = parameters_dict.get('voltage', 'N/A')
        current = parameters_dict.get('current', 'N/A')
    except:
        # If stored as comma-separated string
        try:
            voltage, current = parameters.split(',')
        except:
            voltage, current = 'N/A', 'N/A'

    parameters_paragraph = Paragraph(f"Voltage: {voltage}<br/>Current: {current}", normal_style)

    # ---------- Title ----------
    elements.append(Paragraph(f"Anomaly Report – {category}", title_style))
    elements.append(Spacer(1, 12))

    # ---------- Generate QR code ----------
    maps_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
    qr = qrcode.make(maps_url)
    qr_path = os.path.join(BASE_DIR, "images", f"qr_{anomaly_id}.png")
    qr.save(qr_path)

    # ---------- Images with filenames ----------
    thermal_filename = Paragraph(f"{os.path.basename(thermal_img)}", filename_style)
    rgb_filename = Paragraph(f"{os.path.basename(rgb_img)}", filename_style)
    thermal_image = Image(os.path.join(BASE_DIR, thermal_img), width=200, height=150)
    rgb_image = Image(os.path.join(BASE_DIR, rgb_img), width=200, height=150)

    img_table = Table(
        [[thermal_filename, rgb_filename],
         [thermal_image, rgb_image]],
        colWidths=[250, 250]
    )
    img_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,1), (-1,1), 1, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('TOPPADDING', (1,0), (-1,-1), 4),
    ]))
    elements.append(img_table)
    elements.append(Spacer(1, 12))

    # ---------- Info Table with 2-row blocks ----------
    priority_color = {
        "Critical": colors.red,
        "High": colors.orange,
        "Medium": colors.yellow,
        "Low": colors.green
    }.get(priority, colors.lightgrey)

    blocks = [
        (["Category", "Priority", "Size", "Loss"], [category, priority, size, loss]),
        (["Temperature", "Parameters", "Remedial Action", "Comment"], [
            f"{temperature} °C",
            parameters_paragraph,
            remedial_action,
            comment
        ]),
        (["Latitude", "Longitude", "-", "-"], [latitude, longitude, "-", "-"])
    ]

    elements.append(Paragraph("Anomaly Details", section_header))
    for block in blocks:
        headers, values = block
        table_data = [headers, values]
        table = Table(table_data, colWidths=[120]*4)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (0,1), (-1,1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (1,0), (-1,-1), 6)
        ])
        # Highlight priority cell
        if "Priority" in headers:
            idx = headers.index("Priority")
            style.add('BACKGROUND', (idx,1), (idx,1), priority_color)
            style.add('TEXTCOLOR', (idx,1), (idx,1), colors.white)
            style.add('FONTNAME', (idx,1), (idx,1), 'Helvetica-Bold')
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 12))

    # ---------- Location + QR ----------
    elements.append(Paragraph("Location & QR Code", section_header))
    location_info = Paragraph(f"<b>Location:</b> {latitude}, {longitude}", info_style)
    qr_img = Image(qr_path, width=80, height=80)
    loc_table = Table([[location_info, qr_img]], colWidths=[400, 100])
    loc_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER')
    ]))
    elements.append(loc_table)

    elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    elements.append(PageBreak())

# ---------- Build PDF ----------
doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)

print("✅ Multi-page PDF generated with real Voltage & Current values: anomaly_report.pdf")
