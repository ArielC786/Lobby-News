import os
import smtplib
from email.message import EmailMessage

def send_summary_email():
    sender_email = os.environ.get('GMAIL_ADDRESS')
    app_password = os.environ.get('GMAIL_APP_PASSWORD')
    receiver_email = sender_email  # Sending securely to yourself

    if not sender_email or not app_password:
        print("Missing Gmail credentials. Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD secrets.")
        return

    # Read the generated magazine HTML
    try:
        with open('draft_preview.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("draft_preview.html not found. Make sure the generator ran successfully.")
        return

    # Setup the email body
    msg = EmailMessage()
    msg['Subject'] = 'Here is your Weekly Lobby News Magazine!'
    msg['From'] = f"Lobby News <{sender_email}>"
    msg['To'] = receiver_email
    
    # Set fallback text and attach the full HTML
    msg.set_content("Please enable HTML viewing in your email client to read the Lobby News Magazine.")
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
    send_summary_email()
