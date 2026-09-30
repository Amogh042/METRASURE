import os
import uuid
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.core.config import settings

# backend/reports, independent of the process cwd
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")

def generate_report_pdf(report, test, instrument, technician, test_results):
    """
    Generates an OIML R-76-2 formatted PDF report.
    """
    # Create directory if not exists
    os.makedirs(REPORTS_DIR, exist_ok=True)

    file_path = os.path.join(REPORTS_DIR, f"{report.report_number}.pdf")
    
    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        spaceAfter=12,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        spaceAfter=20,
        alignment=1,
        textColor=colors.red
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceBefore=15,
        spaceAfter=6,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    elements = []
    
    # 1. Header & Title
    elements.append(Paragraph("PROTOTYPE TEST REPORT", title_style))
    elements.append(Paragraph(
        "CRITICAL NOTICE: This is a prototype test report generated according to the configured OIML test-report structure. "
        "It is NOT an officially approved legal certificate.", 
        subtitle_style
    ))
    
    # 2. General Information
    elements.append(Paragraph("1. General Information", header_style))
    
    # Generate QR Code
    verify_url = f"{settings.FRONTEND_URL.rstrip('/')}/verify/{report.verification_token}"
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(REPORTS_DIR, f"qr_{report.report_number}.png")
    qr_img.save(qr_path)
    
    # Layout General Info with QR on the right
    gen_data = [
        ["Report Number:", report.report_number, Image(qr_path, width=1.5*inch, height=1.5*inch)],
        ["Date of Issue:", report.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"), ""],
        ["Testing Laboratory:", "MetraSure Demo Laboratory (SIH26035)", ""],
        ["Technician:", technician.username.capitalize(), ""]
    ]
    
    t_gen = Table(gen_data, colWidths=[4*cm, 8*cm, 4*cm])
    t_gen.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (2,0), (2,3)), # Span QR code
    ]))
    elements.append(t_gen)
    elements.append(Spacer(1, 10))
    
    # 3. Instrument Identification
    elements.append(Paragraph("2. Instrument Identification", header_style))
    inst_data = [
        ["Manufacturer:", instrument.manufacturer, "Accuracy Class:", instrument.accuracy_class],
        ["Model / Type:", instrument.model, "Verification Interval (e):", f"{instrument.verification_interval} {instrument.unit}"],
        ["Serial Number:", instrument.serial_number, "Max Capacity:", f"{instrument.max_capacity} {instrument.unit}"],
        ["Instrument Type:", "NAWI", "Min Capacity:", f"{instrument.min_capacity} {instrument.unit}"]
    ]
    t_inst = Table(inst_data, colWidths=[3.5*cm, 5*cm, 4.5*cm, 3.5*cm])
    t_inst.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_inst)
    elements.append(Spacer(1, 10))
    
    # 4. Detailed Test Results (BEFORE Final Verdict)
    elements.append(Paragraph("3. Detailed Measurement Results", header_style))
    
    # Group results by module
    modules = {}
    for r in test_results:
        modules.setdefault(r.test_module, []).append(r)
        
    for mod_name, results in modules.items():
        elements.append(Paragraph(f"<b>Test Module: {mod_name}</b>", styles['Heading3']))
        
        # Build Table
        table_data = [["Load", "Indication", "Error", "MPE", "Result", "Rule ID"]]
        unit = instrument.unit

        for r in results:
            row_result = r.result
            if row_result == "FAIL":
                row_result = "FAIL (*)"

            if r.measurement is not None:
                load = f"{r.measurement.test_load:g} {unit}"
                indication = f"{r.measurement.indicated_value:g} {unit}"
                error = f"{r.calculated_error:.4f} {unit}"
            elif mod_name == "Repeatability":
                # Single module-level result: show the spread (max - min) of the repeated indications
                reps = [m for m in test.measurements if m.test_module == "Repeatability"]
                load = f"{reps[0].test_load:g} {unit}" if reps else "-"
                indication = f"{min(m.indicated_value for m in reps):g}–{max(m.indicated_value for m in reps):g} {unit}" if reps else "-"
                error = f"{r.calculated_error:.4f} {unit} (max-min)"
            else:
                load, indication = "-", "-"
                error = f"{r.calculated_error:.4f} {unit}"

            table_data.append([
                load,
                indication,
                error,
                f"±{r.permissible_error:.4f} {unit}",
                row_result,
                r.rule.rule_id if r.rule else "-"
            ])

        t_res = Table(table_data, colWidths=[2.2*cm, 3.2*cm, 3.6*cm, 2.6*cm, 1.9*cm, 3.5*cm])
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#334155")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))

        # Color the Result column
        for i, row in enumerate(table_data[1:], start=1):
            if "FAIL" in row[4]:
                t_res.setStyle(TableStyle([
                    ('TEXTCOLOR', (4, i), (4, i), colors.red),
                    ('FONTNAME', (4, i), (4, i), 'Helvetica-Bold')
                ]))
            else:
                t_res.setStyle(TableStyle([
                    ('TEXTCOLOR', (4, i), (4, i), colors.green)
                ]))
                
        elements.append(t_res)
        elements.append(Spacer(1, 10))
    
    # 5. Overall Result (AFTER detailed results)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("4. Overall Result", header_style))
    
    overall_color = colors.green if report.final_result == "PASS" else colors.red
    verdict_style = ParagraphStyle(
        'Verdict',
        parent=normal_style,
        fontSize=14,
        fontName='Helvetica-Bold',
        spaceBefore=6,
        spaceAfter=12,
    )
    elements.append(Paragraph(f"FINAL VERDICT: <font color='{overall_color}'>{report.final_result}</font>", verdict_style))
    
    # 6. Signatures
    elements.append(Spacer(1, 40))
    sig_data = [
        ["_________________________", "_________________________"],
        ["Technician Signature", "Reviewing Officer Signature"],
        [technician.username.capitalize(), "System Administrator"]
    ]
    t_sig = Table(sig_data, colWidths=[8*cm, 8*cm])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Oblique'),
        ('TEXTCOLOR', (0,1), (-1,1), colors.gray),
    ]))
    elements.append(t_sig)
    
    # Build
    doc.build(elements)
    
    # Cleanup QR image
    if os.path.exists(qr_path):
        os.remove(qr_path)
        
    return file_path
