from __future__ import annotations

from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


def generate_invoice_pdf(
    file_path: str,
    student_name: str,
    class_name: str,
    amount: float,
    paid_date: Optional[str],
    payment_id: str | int,
    status: str,
    student_id: int,
) -> None:
    """
    Generate a professional invoice PDF using the provided template design.
    
    Args:
        file_path: Full path where to save the PDF
        student_name: Student's full name
        class_name: Class name
        amount: Payment amount
        paid_date: Date of payment (YYYY-MM-DD format or None)
        payment_id: Payment ID or invoice number
        status: Payment status ('paid' or 'unpaid')
        student_id: Student ID
    """
    
    # Create PDF document
    doc = SimpleDocTemplate(file_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
    )
    
    # Header section: FACTURE DE PAYMENT title and Date/Invoice#
    header_data = [
        ['FACTURE DE PAYMENT', ''],
    ]
    header_table = Table(header_data, colWidths=[3*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONT', (0, 0), (0, 0), 'Helvetica-Bold', 28),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#000000')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    
    # Date and Invoice info on right side
    invoice_date = paid_date if paid_date and paid_date != "-" else datetime.now().strftime("%d %B %Y")
    invoice_num = f"FAC-{payment_id}" if payment_id != "-" else "FAC-0000"
    
    info_data = [
        [f'Date: {invoice_date}', ''],
        [f'Facture #: {invoice_num}', ''],
    ]
    info_table = Table(info_data, colWidths=[3*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Billed to / Pay to sections
    bill_to_data = [
        ['Facturé à:', 'SchoolFin'],
        [student_name, 'Sened de Gafsa 2190'],
        ['Classe: ' + class_name, 'Tunisie'],
        ['ID Étudiant: ' + str(student_id), ''],
    ]
    
    bill_table = Table(bill_to_data, colWidths=[3.25*inch, 3.25*inch])
    bill_table.setStyle(TableStyle([
        ('FONT', (0, 0), (1, 0), 'Helvetica-Bold', 11),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ]))
    elements.append(bill_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Items table
    status_label = "Payée" if status == "paid" else "Non Payée"
    
    items_data = [
        ['Description', 'Quantité', 'Prix Unitaire', 'Montant'],
        [
            f'Frais de scolarité - Classe {class_name}',
            '1',
            f'${amount:.2f}',
            f'${amount:.2f}'
        ],
    ]
    
    items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
        ('ALIGN', (0, 0), (1, 0), 'LEFT'),
        ('ALIGN', (2, 0), (-1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        # Data rows
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        # Borders
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#000000')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#000000')),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Totals section
    tax_rate = 0.10
    tax_amount = amount * tax_rate
    total_amount = amount + tax_amount
    
    totals_data = [
        ['', '', 'Sous-total', f'${amount:.2f}'],
        ['', '', 'TVA (10%)', f'${tax_amount:.2f}'],
        ['', '', 'Total', f'${total_amount:.2f}'],
    ]
    
    totals_table = Table(totals_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('FONT', (2, 0), (3, 1), 'Helvetica', 10),
        ('FONT', (2, 2), (3, 2), 'Helvetica-Bold', 11),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (2, 2), (-1, 2), 1, colors.HexColor('#000000')),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment Information section
    payment_info_data = [
        ['Informations de Paiement', 'SchoolFin', 'Statut du Paiement'],
        [student_name, 'Sened de Gafsa 2190', status_label],
        ['Classe: ' + class_name, 'Tunisie', f'Facture #: {invoice_num}'],
        ['ID Étudiant: ' + str(student_id), '', f'Date: {invoice_date}'],
    ]
    
    payment_table = Table(payment_info_data, colWidths=[2*inch, 2.25*inch, 1.75*inch])
    payment_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, 0), 'Helvetica-Bold', 11),
        ('FONT', (1, 0), (1, 0), 'Helvetica-Bold', 11),
        ('FONT', (2, 0), (2, 0), 'Helvetica-Bold', 11),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Footer
    footer_text = f"Merci pour votre paiement. | Généré par SchoolFin"
    elements.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(elements)
