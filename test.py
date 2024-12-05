import os
import django
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project3.settings')
django.setup()

from mail.models import User

def send_test_email(sender_email, recipient_emails, subject, body, attachment_paths=None):
    try:
        # Verify sender exists
        try:
            sender = User.objects.get(email=sender_email)
        except User.DoesNotExist:
            print(f"Error: Sender {sender_email} not found")
            return False

        # Verify recipients exist
        for recipient_email in recipient_emails:
            if not User.objects.filter(email=recipient_email).exists():
                print(f"Error: Recipient {recipient_email} not found")
                return False

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Add attachments if any
        if attachment_paths:
            for file_path in attachment_paths:
                if not os.path.exists(file_path):
                    print(f"Warning: Attachment {file_path} not found, skipping")
                    continue
                    
                with open(file_path, 'rb') as f:
                    filename = os.path.basename(file_path)
                    part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(part)

        # Send via local SMTP
        with smtplib.SMTP('vanmail', 1025) as smtp:
            smtp.send_message(msg)
            print("Email sent successfully!")
            return True

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    # Example usage
    sender = "alibayar750@gmail.com"  # Must be a registered user
    recipients = ["ali.bayar@um6p.ma"]  # Must be registered users
    subject = "Test Email with Attachment"
    body = "This is a test email sent from the command line script."
    attachments = [
        "./start.sh",
    ]

    send_test_email(sender, recipients, subject, body, attachments)