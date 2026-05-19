import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

msg = EmailMessage()
msg["From"] = formataddr(("Test Bot", "synapsebiopharma@gmail.com"))
msg["To"] = "divyanshmi999@gmail.com"
msg["Subject"] = "Test Email from Script"
msg.set_content("This is a simple test email. If you receive this, the SMTP is working perfectly!")

try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login("synapsebiopharma@gmail.com", "nwtungnsbcndsxne")
        server.send_message(msg)
    print("Test email sent successfully!")
except Exception as e:
    print(f"Error: {e}")
