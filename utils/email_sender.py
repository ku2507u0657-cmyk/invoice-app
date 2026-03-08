"""
Email sending utility using smtplib.
Handles invoice emails and reminder emails.
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def get_smtp_connection(config):
    """Create and return an authenticated SMTP connection."""
    server = smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT)
    server.ehlo()
    if config.MAIL_USE_TLS:
        server.starttls()
    server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
    return server


def send_invoice_email(invoice, client, pdf_path: str, config) -> bool:
    """
    Send invoice email to client with PDF attachment.
    Returns True on success, False on failure.
    """
    if not config.MAIL_USERNAME or not config.MAIL_PASSWORD:
        print("[EMAIL] Mail credentials not configured. Skipping email.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Invoice #{invoice.invoice_number} from {config.COMPANY_NAME}"
        msg['From'] = config.MAIL_DEFAULT_SENDER or config.MAIL_USERNAME
        msg['To'] = client.email

        # HTML email body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 30px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
    .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 30px; text-align: center; }}
    .header h1 {{ color: #e94560; margin: 0; font-size: 28px; letter-spacing: 2px; }}
    .header p {{ color: #aaa; margin: 5px 0 0; font-size: 14px; }}
    .body {{ padding: 30px; }}
    .greeting {{ font-size: 18px; color: #1a1a2e; font-weight: 600; margin-bottom: 15px; }}
    .invoice-box {{ background: #f8f9fa; border-left: 4px solid #e94560; border-radius: 6px; padding: 20px; margin: 20px 0; }}
    .invoice-box table {{ width: 100%; border-collapse: collapse; }}
    .invoice-box td {{ padding: 6px 0; font-size: 14px; color: #333; }}
    .invoice-box td:last-child {{ text-align: right; font-weight: 600; }}
    .total-row td {{ font-size: 18px; color: #e94560; border-top: 2px solid #dee2e6; padding-top: 10px; }}
    .pay-btn {{ display: block; text-align: center; background: #e94560; color: white; padding: 15px; border-radius: 8px; text-decoration: none; font-size: 16px; font-weight: 700; margin: 25px 0; letter-spacing: 1px; }}
    .upi-box {{ background: #f0f7ff; border-radius: 8px; padding: 15px; text-align: center; margin: 20px 0; }}
    .upi-box p {{ margin: 5px 0; color: #333; font-size: 14px; }}
    .upi-box .upi-id {{ font-size: 18px; font-weight: 700; color: #1a1a2e; letter-spacing: 1px; }}
    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #888; }}
    .due-badge {{ display: inline-block; background: #fff3cd; color: #856404; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{config.COMPANY_NAME}</h1>
      <p>Invoice #{invoice.invoice_number}</p>
    </div>
    <div class="body">
      <p class="greeting">Dear {client.name},</p>
      <p style="color:#555; font-size:15px; line-height:1.6;">
        Please find your invoice attached for the services provided. 
        Kindly make the payment at your earliest convenience.
      </p>
      
      <div class="invoice-box">
        <table>
          <tr>
            <td style="color:#888">Invoice Number</td>
            <td>#{invoice.invoice_number}</td>
          </tr>
          <tr>
            <td style="color:#888">Invoice Date</td>
            <td>{invoice.created_at.strftime('%d %B %Y')}</td>
          </tr>
          <tr>
            <td style="color:#888">Subtotal</td>
            <td>₹{float(invoice.amount):,.2f}</td>
          </tr>
          <tr>
            <td style="color:#888">GST ({float(invoice.gst_rate):.0f}%)</td>
            <td>₹{float(invoice.gst_amount):,.2f}</td>
          </tr>
          <tr class="total-row">
            <td>Total Amount</td>
            <td>₹{float(invoice.total):,.2f}</td>
          </tr>
        </table>
      </div>

      <p style="text-align:center">
        <span class="due-badge">⏰ Due Date: {invoice.due_date.strftime('%d %B %Y')}</span>
      </p>
      
      <div class="upi-box">
        <p>Pay instantly via UPI</p>
        <p class="upi-id">{config.UPI_ID}</p>
        <p style="color:#888; font-size:12px;">Scan the QR code in the attached PDF to pay</p>
      </div>
      
      <p style="color:#555; font-size:14px;">
        The invoice PDF is attached to this email. For any queries, please contact us at 
        <a href="mailto:{config.COMPANY_EMAIL}" style="color:#e94560">{config.COMPANY_EMAIL}</a>
        or call <a href="tel:{config.COMPANY_PHONE}" style="color:#e94560">{config.COMPANY_PHONE}</a>.
      </p>
    </div>
    <div class="footer">
      <p>{config.COMPANY_NAME} &bull; {config.COMPANY_ADDRESS}</p>
      <p>This is an auto-generated email. Please do not reply to this message.</p>
    </div>
  </div>
</body>
</html>"""

        msg.attach(MIMEText(html_body, 'html'))

        # Attach PDF
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"')
            msg.attach(part)

        server = get_smtp_connection(config)
        server.sendmail(msg['From'], [client.email], msg.as_string())
        server.quit()
        print(f"[EMAIL] Invoice email sent to {client.email}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send invoice email: {str(e)}")
        return False


def send_reminder_email(invoice, client, config) -> bool:
    """
    Send a payment reminder email for an overdue invoice.
    Returns True on success, False on failure.
    """
    if not config.MAIL_USERNAME or not config.MAIL_PASSWORD:
        print("[EMAIL] Mail credentials not configured. Skipping reminder.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"⚠️ Payment Reminder - Invoice #{invoice.invoice_number} Overdue"
        msg['From'] = config.MAIL_DEFAULT_SENDER or config.MAIL_USERNAME
        msg['To'] = client.email

        days_overdue = (datetime.utcnow().date() - invoice.due_date).days

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 30px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
    .header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; }}
    .header h1 {{ color: #fff; margin: 0; font-size: 24px; }}
    .header p {{ color: #ffcccc; margin: 5px 0 0; }}
    .body {{ padding: 30px; }}
    .overdue-box {{ background: #fff5f5; border: 2px solid #dc3545; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
    .overdue-amount {{ font-size: 32px; font-weight: 900; color: #dc3545; }}
    .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    .info-table td {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 14px; }}
    .info-table td:last-child {{ font-weight: 600; text-align: right; }}
    .upi-box {{ background: #f0f7ff; border-radius: 8px; padding: 15px; text-align: center; }}
    .upi-id {{ font-size: 20px; font-weight: 700; color: #1a1a2e; letter-spacing: 1px; }}
    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #888; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚠️ Payment Reminder</h1>
      <p>From {config.COMPANY_NAME}</p>
    </div>
    <div class="body">
      <p style="font-size:18px; font-weight:600; color:#1a1a2e">Dear {client.name},</p>
      <p style="color:#555; line-height:1.6">
        This is a friendly reminder that your payment for Invoice #{invoice.invoice_number} 
        is <strong style="color:#dc3545">{days_overdue} day{'s' if days_overdue != 1 else ''} overdue</strong>. 
        Please clear the outstanding amount at the earliest.
      </p>
      
      <div class="overdue-box">
        <p style="margin:0; color:#888; font-size:13px">Outstanding Amount</p>
        <div class="overdue-amount">₹{float(invoice.total):,.2f}</div>
        <p style="margin:5px 0 0; color:#dc3545; font-size:13px">Due since {invoice.due_date.strftime('%d %B %Y')}</p>
      </div>
      
      <table class="info-table">
        <tr><td style="color:#888">Invoice #</td><td>{invoice.invoice_number}</td></tr>
        <tr><td style="color:#888">Original Due Date</td><td>{invoice.due_date.strftime('%d %B %Y')}</td></tr>
        <tr><td style="color:#888">Days Overdue</td><td style="color:#dc3545">{days_overdue} days</td></tr>
      </table>
      
      <div class="upi-box">
        <p style="margin:0 0 8px; font-weight:600">Pay Now via UPI</p>
        <p class="upi-id">{config.UPI_ID}</p>
        <p style="color:#888; font-size:12px; margin:5px 0 0">Use any UPI app to scan and pay instantly</p>
      </div>
      
      <p style="color:#888; font-size:13px; margin-top:20px">
        For queries, contact: <a href="mailto:{config.COMPANY_EMAIL}" style="color:#e94560">{config.COMPANY_EMAIL}</a> 
        | {config.COMPANY_PHONE}
      </p>
    </div>
    <div class="footer">
      <p>{config.COMPANY_NAME} &bull; {config.COMPANY_ADDRESS}</p>
      <p>This is an automated payment reminder.</p>
    </div>
  </div>
</body>
</html>"""

        msg.attach(MIMEText(html_body, 'html'))
        server = get_smtp_connection(config)
        server.sendmail(msg['From'], [client.email], msg.as_string())
        server.quit()
        print(f"[EMAIL] Reminder sent to {client.email} for invoice {invoice.invoice_number}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send reminder: {str(e)}")
        return False
