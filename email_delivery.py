import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

def send_summary_email(pdf_path=None, html_path='draft_preview.html'):
    sender_email = os.environ.get('GMAIL_ADDRESS')
    app_password = os.environ.get('GMAIL_APP_PASSWORD')
    receiver_email = sender_email

    if not sender_email or not app_password:
        print("Missing Gmail credentials. Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD secrets.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Lobby News — Weekly Carousel PDF'
    msg['From'] = formataddr(("Lobby News", sender_email))
    msg['To'] = receiver_email

    if pdf_path and os.path.exists(pdf_path):
        msg.set_content("Your Lobby News carousel PDF is attached.")
        try:
            with open(pdf_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(pdf_path)
            msg.add_attachment(
                file_data,
                maintype='application',
                subtype='pdf',
                filename=file_name
            )
            print(f"Attached PDF: {file_name}")
        except Exception as e:
            print(f"Failed to attach PDF: {e}")
    else:
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            print(f"{html_path} not found. Make sure the generator ran successfully.")
            return

        msg.set_content("PDF generation was unavailable; the HTML edition is included in this email.")
        msg.add_alternative(html_content, subtype='html')

    try:
        print(f"Connecting to Gmail SMTP to deliver to {receiver_email}...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Check if a PDF carousel was generated
    pdf_candidate = 'Lobby_News_Carousel.pdf'
    send_summary_email(pdf_path=pdf_candidate if os.path.exists(pdf_candidate) else None)
