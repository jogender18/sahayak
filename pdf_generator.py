import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def generate_agreement_pdf(agreement: dict, verify_url: str) -> io.BytesIO:
    """
    Generates a simplified, legal-tone wage agreement PDF for informal daily-wage labor.
    Structured clearly with short readable sentences, explicit penalty terms,
    parties identification, signature blocks, and scannable QR verification code.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Document Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0f172a')
    )

    meta_bar_style = ParagraphStyle(
        'MetaBar',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    meta_bar_right = ParagraphStyle(
        'MetaBarRight',
        parent=meta_bar_style,
        alignment=TA_RIGHT
    )

    sec_heading_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=6,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14.5,
        textColor=colors.HexColor('#1e293b')
    )

    body_bold = ParagraphStyle(
        'BodyDarkBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    callout_text = ParagraphStyle(
        'CalloutText',
        parent=body_style,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0f172a')
    )

    penalty_text = ParagraphStyle(
        'PenaltyText',
        parent=body_style,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#991b1b')
    )

    small_center = ParagraphStyle(
        'SmallCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#475569')
    )

    small_bold_center = ParagraphStyle(
        'SmallBoldCenter',
        parent=small_center,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#166534')
    )

    story = []

    # 1. Header: WAGE AGREEMENT + Ref ID & Date
    story.append(Paragraph("WAGE AGREEMENT", title_style))
    story.append(Spacer(1, 4))

    meta_table_data = [
        [
            Paragraph(f"<b>Agreement Reference ID:</b> {agreement['id']}", meta_bar_style),
            Paragraph(f"<b>Date:</b> {agreement['created_at'].split()[0] if ' ' in agreement['created_at'] else agreement['created_at']}", meta_bar_right)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[4.2 * inch, 3.1 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Safe field extractions with fallbacks
    start_date_val = str(agreement.get('start_date') or '').strip() or str(agreement.get('created_at', '')).split()[0]
    owner_name_val = str(agreement.get('owner_name') or 'Owner / Contractor').strip()
    owner_phone_val = str(agreement.get('owner_phone') or 'Not provided').strip()
    worker_name_val = str(agreement.get('worker_name') or 'Worker / Laborer').strip()
    worker_phone_val = str(agreement.get('worker_phone') or 'Not provided').strip()
    work_desc_val = str(agreement.get('work_description') or 'General labor and trade services').strip()
    duration_val = str(agreement.get('duration') or 'As mutually agreed / Until completion').strip()
    location_val = str(agreement.get('work_location') or 'As mutually agreed at worksite').strip()
    payment_sched_val = str(agreement.get('payment_schedule') or 'weekly').strip().title()

    try:
        raw_w = str(agreement.get('wage_amount', 0)).replace(',', '').replace('₹', '').replace('Rs.', '').strip()
        wage_num = float(raw_w) if raw_w else 0.0
        wage_rate_formatted = f"Rs. {wage_num:,.2f}"
    except (ValueError, TypeError):
        wage_rate_formatted = f"Rs. {agreement.get('wage_amount', '0.00')}"

    # 2. Background Section (Parties)
    story.append(Paragraph("1. PARTIES & BACKGROUND", sec_heading_style))
    
    bg_p1 = (
        f"This Wage Agreement is entered into on <b>{start_date_val}</b> between:"
    )
    story.append(Paragraph(bg_p1, body_style))
    story.append(Spacer(1, 4))

    party_box_data = [
        [
            Paragraph(f"<b>Owner / Contractor:</b> {owner_name_val}<br/><b>Phone:</b> {owner_phone_val} <i>(\"Owner\")</i>", body_style),
            Paragraph(f"<b>Worker / Laborer:</b> {worker_name_val}<br/><b>Phone:</b> {worker_phone_val} <i>(\"Worker\")</i>", body_style)
        ]
    ]
    party_table = Table(party_box_data, colWidths=[3.6 * inch, 3.6 * inch])
    party_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#eff6ff')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#bfdbfe')),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#bbf7d0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(party_table)
    story.append(Spacer(1, 10))

    # 3. Description of Work
    story.append(Paragraph("2. DESCRIPTION OF WORK", sec_heading_style))
    work_text = f"The Worker agrees to perform the following work:<br/><b>{work_desc_val}</b>"
    work_box = Table([[Paragraph(work_text, callout_text)]], colWidths=[7.3 * inch])
    work_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(work_box)
    story.append(Spacer(1, 10))

    # 4. Wage and Payment Section
    story.append(Paragraph("3. WAGE AND PAYMENT", sec_heading_style))
    
    # Handle unit prefix cleanly so we never get "per per day"
    raw_unit = str(agreement.get('wage_unit') or 'per day').strip()
    if raw_unit.lower().startswith('per '):
        unit_display = raw_unit
    else:
        unit_display = f"per {raw_unit}"

    wage_text = (
        f"• <b>Agreed Wage:</b> Owner agrees to pay Worker <b>{wage_rate_formatted}</b> {unit_display}.<br/>"
        f"• <b>Payment Schedule:</b> Payment will be made on the following schedule: <b>{payment_sched_val}</b>."
    )
    wage_box = Table([[Paragraph(wage_text, callout_text)]], colWidths=[7.3 * inch])
    wage_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(wage_box)
    story.append(Spacer(1, 10))

    # 5. Penalty Clause (clearly highlighted)
    story.append(Paragraph("4. PENALTY FOR LATE PAYMENT", sec_heading_style))
    penalty_val = str(agreement.get('late_penalty') or '').strip() or "Standard mutual dispute resolution / No additional penalty specified"
    penalty_content = (
        f"If payment is delayed beyond the agreed schedule, the following penalty applies:<br/>"
        f"<b>{penalty_val}</b>"
    )
    penalty_box = Table([[Paragraph(penalty_content, penalty_text)]], colWidths=[7.3 * inch])
    penalty_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#fca5a5')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(penalty_box)
    story.append(Spacer(1, 10))

    # 6. Work Duration & Location
    story.append(Paragraph("5. WORK DURATION & LOCATION", sec_heading_style))
    duration_text = (
        f"• <b>Schedule:</b> Work under this Agreement shall begin on <b>{start_date_val}</b> and continue for <b>{duration_val}</b>.<br/>"
        f"• <b>Location:</b> <b>{location_val}</b>."
    )
    duration_box = Table([[Paragraph(duration_text, callout_text)]], colWidths=[7.3 * inch])
    duration_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(duration_box)
    story.append(Spacer(1, 12))

    # 7. QR Code & Confirmation / Signatures Footer
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f172a", back_color="white")
    
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    reportlab_qr = Image(qr_buffer, width=1.05 * inch, height=1.05 * inch)

    # Signatures
    sig_owner = [
        Spacer(1, 24),
        HRFlowable(width="80%", thickness=1, color=colors.HexColor('#475569'), spaceAfter=4),
        Paragraph("<b>Signature / Thumb Impression</b>", small_center),
        Paragraph(f"Owner: {agreement['owner_name']}", small_center)
    ]

    sig_worker = [
        Spacer(1, 24),
        HRFlowable(width="80%", thickness=1, color=colors.HexColor('#475569'), spaceAfter=4),
        Paragraph("<b>Signature / Thumb Impression</b>", small_center),
        Paragraph(f"Worker: {agreement['worker_name']}", small_center)
    ]

    qr_block = [
        reportlab_qr,
        Paragraph("SCAN TO VERIFY", small_bold_center),
        Paragraph("Digital Proof of Accord", small_center)
    ]

    sig_table = Table([[sig_owner, qr_block, sig_worker]], colWidths=[2.6 * inch, 2.0 * inch, 2.6 * inch])
    sig_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(KeepTogether([
        Paragraph("<b>6. CONFIRMATION OF TERMS</b>", sec_heading_style),
        Paragraph("Both parties confirm and agree to these terms. This digital record serves as binding proof of the agreed wage terms.", body_style),
        Spacer(1, 6),
        sig_table,
        Spacer(1, 6),
        Paragraph(f"Agreement ID: <b>{agreement['id']}</b> | Official Verification Portal: <u>{verify_url}</u>", small_center)
    ]))

    doc.build(story)
    buffer.seek(0)
    return buffer
