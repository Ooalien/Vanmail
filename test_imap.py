import imaplib
import email
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from email import policy

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_imap_connection():
    try:
        # IMAP server settings
        IMAP_HOST = 'localhost'
        IMAP_PORT = 1143
        USERNAME = 'user@example.com'  # Replace with a valid user email
        PASSWORD = 'password'      # Replace with the user's password

        # Connect to IMAP server
        logger.info(f"Connecting to IMAP server at {IMAP_HOST}:{IMAP_PORT}")
        imap = imaplib.IMAP4(IMAP_HOST, IMAP_PORT)
        
        # Test CAPABILITY
        logger.info("Testing CAPABILITY command")
        typ, capabilities = imap.capability()
        logger.info(f"Server capabilities: {capabilities}")
        
        # Login
        logger.info(f"Attempting to login as {USERNAME}")
        imap.login(USERNAME, PASSWORD)
        logger.info("Login successful")

        # Test NOOP
        logger.info("Testing NOOP command")
        typ, data = imap.noop()
        logger.info(f"NOOP response: {typ}")

        # Select INBOX
        logger.info("Selecting INBOX")
        typ, data = imap.select('INBOX')
        if typ == 'OK':
            logger.info(f"INBOX contains {data[0].decode()} messages")

            # Search for all messages
            logger.info("Searching for messages")
            typ, messages = imap.search(None, 'UNSEEN')
            
            if messages[0]:
                for num in messages[0].split():
                    logger.info(f"Fetching message {num.decode()}")
                    typ, msg_data = imap.fetch(num, '(RFC822)')
                    if typ == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body, policy=policy.default)
                        logger.info(f"From: {email_message['from']}")
                        logger.info(f"Subject: {email_message['subject']}")
                        logger.info(f"Date: {email_message['date']}")
                        
                        # Print message content
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                    logger.info(f"Content: {part.get_payload(decode=True).decode()}")
                        else:
                            logger.info(f"Content: {email_message.get_payload(decode=True).decode()}")
            else:
                logger.info("No messages in INBOX")
        
        # Logout
        logger.info("Logging out")
        imap.logout()
        logger.info("IMAP test completed successfully")

    except Exception as e:
        logger.error(f"Error during IMAP test: {str(e)}")
        raise

if __name__ == "__main__":
    # Wait a bit for the server to start up
    time.sleep(2)
    test_imap_connection()