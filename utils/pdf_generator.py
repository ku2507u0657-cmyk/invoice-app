"""
PDF generation for invoices using ReportLab.
Generates a professional A4 invoice PDF with UPI QR code.
"""
import os
import io
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, HRFlowable)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas


# Color palette
PRIMARY_COLOR = colors.HexColor('#1a1a2e')
ACCENT_COLOR = colors.HexColor('#e94560')
LIGHT_BG = colors.HexColor('#f8f9fa')
BORDER_COLOR = colors.HexColor('#dee2e6')
TEXT_GRAY = colors.HexColor('#6c757d')
SUCCESS_GREEN = colors.HexColor('#28a745')


def generate_upi_qr(upi_id: str, amount: float, invoice_number: str, company_name: str) -> str:
    """Generate UPI QR code and return path to PNG file."""
    # UPI deep link format
    upi_url = (
        f"upi://pay?pa={upi_id}&pn={company_name.replace(' ', '%20')}"
        f"&am={amount:.2f}&tn=Invoice%20{invoice_number}&cu=INR"
    )
    qr = qrcode.QRCode(version=1, box_size=4, border=2,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to temp file
    qr_path = f"/tmp/qr_{invoice_number}.png"
    img.save(qr_path)
    return qr_path


def generate_invoice_pdf(invoice, client, config) -> str:
    """
    Generate a professional PDF invoice.
    Returns the path to the generated PDF file.
    """
    # Ensure invoices directory exists
    invoices_dir = config.INVOICES_DIR
    os.makedirs(invoices_dir, exist_ok=True)

    pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
    pdf_path = os.path.join(invoices_dir, pdf_filename)

    # Generate QR code
    qr_path = generate_upi_qr(
        config.UPI_ID,
        float(invoice.total),
        invoice.invoice_number,
        config.COMPANY_NAME
    )

    # Create document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    story = []

    # --- HEADER SECTION ---
    header_data = [
        [
            Paragraph(
                f'<font name="Helvetica-Bold" size="22" color="{PRIMARY_COLOR.hexval()}">'
                f'{config.COMPANY_NAME}</font>',
                ParagraphStyle('co', fontSize=22, textColor=PRIMARY_COLOR, fontName='Helvetica-Bold')
            ),
            Paragraph(
                f'<font name="Helvetica-Bold" size="28" color="{ACCENT_COLOR.hexval()}">INVOICE</font>',
                ParagraphStyle('inv', fontSize=28, textColor=ACCENT_COLOR, fontName='Helvetica-Bold', alignment=TA_RIGHT)
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[100*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3*mm))

    # Company details row
    company_info = f"{config.COMPANY_ADDRESS}<br/>{config.COMPANY_PHONE} | {config.COMPANY_EMAIL}"
    if config.COMPANY_GSTIN:
        company_info += f"<br/>GSTIN: {config.COMPANY_GSTIN}"

    inv_details = (
        f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
        f"<b>Date:</b> {invoice.created_at.strftime('%d %B %Y')}<br/>"
        f"<b>Due Date:</b> {invoice.due_date.strftime('%d %B %Y')}<br/>"
        f"<b>Status:</b> {'PAID' if invoice.status == 'paid' else 'UNPAID'}"
    )

    small_style = ParagraphStyle('small', fontSize=9, textColor=TEXT_GRAY, leading=14)
    inv_style = ParagraphStyle('inv_det', fontSize=9, leading=14)

    subheader_data = [[
        Paragraph(company_info, small_style),
        Paragraph(inv_details, inv_style)
    ]]
    subheader_table = Table(subheader_data, colWidths=[100*mm, 80*mm])
    subheader_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(subheader_table)
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR))
    story.append(Spacer(1, 5*mm))

    # --- BILL TO SECTION ---
    bill_to_style = ParagraphStyle('bill_label', fontSize=9, textColor=TEXT_GRAY, fontName='Helvetica-Bold')
    client_style = ParagraphStyle('client', fontSize=11, fontName='Helvetica-Bold', leading=16)
    client_detail_style = ParagraphStyle('client_det', fontSize=9, textColor=TEXT_GRAY, leading=14)

    story.append(Paragraph("BILL TO", bill_to_style))
    story.append(Paragraph(client.name, client_style))
    client_info = f"{client.phone} | {client.email}"
    if client.gst_number:
        client_info += f"<br/>GSTIN: {client.gst_number}"
    story.append(Paragraph(client_info, client_detail_style))
    story.append(Spacer(1, 6*mm))

    # --- ITEMS TABLE ---
    table_header_style = ParagraphStyle('th', fontSize=9, fontName='Helvetica-Bold',
                                         textColor=colors.white)
    table_cell_style = ParagraphStyle('td', fontSize=9, leading=14)

    description = invoice.description or f"Monthly Fee - {invoice.created_at.strftime('%B %Y')}"

    items_data = [
        # Header row
        ['#', 'Description', 'Amount (₹)'],
        ['1', Paragraph(description, table_cell_style),
         Paragraph(f"₹{float(invoice.amount):,.2f}", ParagraphStyle('right', fontSize=9, alignment=TA_RIGHT))],
    ]

    items_table = Table(items_data, colWidths=[10*mm, 120*mm, 50*mm])
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        # Data rows
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BG),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4*mm))

    # --- TOTALS TABLE ---
    totals_style = ParagraphStyle('tot', fontSize=9, alignment=TA_RIGHT)
    totals_bold = ParagraphStyle('tot_bold', fontSize=11, fontName='Helvetica-Bold', alignment=TA_RIGHT)
    totals_label = ParagraphStyle('tot_lbl', fontSize=9, alignment=TA_RIGHT, textColor=TEXT_GRAY)

    totals_data = [
        [Paragraph("Subtotal:", totals_label), Paragraph(f"₹{float(invoice.amount):,.2f}", totals_style)],
        [Paragraph(f"GST ({float(invoice.gst_rate):.0f}%):", totals_label),
         Paragraph(f"₹{float(invoice.gst_amount):,.2f}", totals_style)],
        [Paragraph("<b>TOTAL:</b>", ParagraphStyle('tot_bold_lbl', fontSize=11, fontName='Helvetica-Bold',
                                                    alignment=TA_RIGHT, textColor=ACCENT_COLOR)),
         Paragraph(f"<b>₹{float(invoice.total):,.2f}</b>",
                   ParagraphStyle('grand_tot', fontSize=11, fontName='Helvetica-Bold',
                                   alignment=TA_RIGHT, textColor=ACCENT_COLOR))],
    ]
    if invoice.status == 'paid' and invoice.paid_date:
        totals_data.append([
            Paragraph("<font color='#28a745'>✓ PAID ON:</font>",
                      ParagraphStyle('paid_lbl', fontSize=9, alignment=TA_RIGHT, textColor=SUCCESS_GREEN)),
            Paragraph(f"<font color='#28a745'>{invoice.paid_date.strftime('%d %B %Y')}</font>",
                      ParagraphStyle('paid_val', fontSize=9, alignment=TA_RIGHT, textColor=SUCCESS_GREEN))
        ])

    totals_table = Table(totals_data, colWidths=[100*mm, 80*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 2), (-1, 2), 1, BORDER_COLOR),
        ('LINEBELOW', (0, 2), (-1, 2), 1.5, ACCENT_COLOR),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 8*mm))

    # --- QR CODE + PAYMENT SECTION ---
    qr_section_label = ParagraphStyle('qr_lbl', fontSize=10, fontName='Helvetica-Bold', textColor=PRIMARY_COLOR)
    qr_note_style = ParagraphStyle('qr_note', fontSize=8, textColor=TEXT_GRAY, alignment=TA_CENTER)

    qr_img = Image(qr_path, width=28*mm, height=28*mm)
    pay_info = (
        f"<b>Pay via UPI</b><br/>"
        f"UPI ID: <b>{config.UPI_ID}</b><br/>"
        f"Amount: <b>₹{float(invoice.total):,.2f}</b><br/>"
        f"Ref: Invoice {invoice.invoice_number}"
    )
    pay_style = ParagraphStyle('pay', fontSize=9, leading=15)

    qr_data = [[
        qr_img,
        Paragraph(pay_info, pay_style),
        Paragraph(
            "Please make payment before the due date.<br/>"
            "For queries, contact us at:<br/>"
            f"{config.COMPANY_EMAIL}<br/>{config.COMPANY_PHONE}",
            ParagraphStyle('contact', fontSize=8, textColor=TEXT_GRAY, leading=13)
        )
    ]]
    qr_table = Table(qr_data, colWidths=[32*mm, 80*mm, 68*mm])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(qr_table)

    # --- FOOTER ---
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    story.append(Spacer(1, 2*mm))
    footer_style = ParagraphStyle('footer', fontSize=7, textColor=TEXT_GRAY, alignment=TA_CENTER)
    story.append(Paragraph(
        f"This is a computer-generated invoice and does not require a signature. "
        f"Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')} | {config.COMPANY_NAME}",
        footer_style
    ))

    # Build PDF
    doc.build(story)

    # Clean up temp QR file
    if os.path.exists(qr_path):
        os.remove(qr_path)

    return pdf_filename
