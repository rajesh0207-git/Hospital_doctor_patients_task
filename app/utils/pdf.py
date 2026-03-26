from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

def generate_invoice(file_path, billing, patient, doctor):
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    elements = []

    # ✅ LOGO PATH FIX
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    logo_path = os.path.join(BASE_DIR, "assets", "logo.png")

    # =========================
    # 🏥 HEADER SECTION
    # =========================
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=50))

    elements.append(Paragraph("<b>ABC Hospital</b>", styles["Title"]))
    elements.append(Paragraph("Chennai, Tamil Nadu", styles["Normal"]))
    elements.append(Paragraph("Phone: +91 9876543210", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # =========================
    # 🧾 INVOICE DETAILS
    # =========================
    elements.append(Paragraph(f"<b>Invoice ID:</b> {billing.id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))

    elements.append(Spacer(1, 10))

    # =========================
    # 👤 PATIENT DETAILS
    # =========================
    elements.append(Paragraph("<b>Patient Details</b>", styles["Heading2"]))
    elements.append(Paragraph(f"Name: {patient.name}", styles["Normal"]))
    elements.append(Paragraph(f"Phone: {patient.phone}", styles["Normal"]))

    elements.append(Spacer(1, 10))

    # =========================
    # 👨‍⚕️ DOCTOR DETAILS
    # =========================
    elements.append(Paragraph("<b>Doctor Details</b>", styles["Heading2"]))
    elements.append(Paragraph(f"Name: {doctor.name}", styles["Normal"]))
    elements.append(Paragraph(f"Specialization: {doctor.specialization}", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # =========================
    # 💰 BILLING TABLE
    # =========================
    data = [
        ["Description", "Amount (₹)"],
        ["Consultation Fee", billing.consultation_fee],
        ["Additional Charges", billing.additional_charges],
    ]

    gst = round(billing.total_amount * 0.18, 2)
    total = round(billing.total_amount + gst, 2)

    data.append(["GST (18%)", gst])
    data.append(["Total Amount", total])

    table = Table(data, colWidths=[250, 150])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))

    # =========================
    # 🙏 FOOTER
    # =========================
    elements.append(Paragraph("<b>Payment Status:</b> " + billing.payment_status.upper(), styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Thank you for choosing ABC Hospital 🙏", styles["Normal"]))

    # =========================
    # BUILD PDF
    # =========================
    doc.build(elements)