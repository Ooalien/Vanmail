import email
from email import policy
from aiosmtpd.controller import Controller
from mail.models import Email, User, EmailAttachment
from django.utils import timezone
import logging
import time
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
import os
from functools import partial

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LocalMailHandler:
    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        envelope.mail_from = address
        return '250 Sender OK'

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        try:
            # Wrap the entire filter().exists() chain in sync_to_async
            exists_check = sync_to_async(
                lambda: User.objects.filter(email=address).exists(),
                thread_sensitive=True
            )
            user_exists = await exists_check()
            
            if not user_exists:
                logger.error(f"Recipient not found: {address}")
                return '550 Recipient not found'
                
            envelope.rcpt_tos.append(address)
            return '250 Recipient OK'
            
        except Exception as e:
            logger.error(f"Error in RCPT handler: {str(e)}")
            return f'451 Requested action aborted: {str(e)}'

    async def handle_DATA(self, server, session, envelope):
        created_emails = []
        try:
            logger.debug(f"Processing mail from: {envelope.mail_from}")
            logger.debug(f"Recipients: {envelope.rcpt_tos}")
            
            # Parse email message
            msg = email.message_from_bytes(envelope.content, policy=policy.default)
            
            # Extract email parts
            subject = msg['subject'] or ''
            body = ''
            attachments = []
            
            # Get body content and attachments
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                    elif part.get_content_disposition() == 'attachment':
                        attachments.append({
                            'filename': part.get_filename(),
                            'content': part.get_payload(decode=True),
                            'content_type': part.get_content_type()
                        })
            else:
                body = msg.get_payload(decode=True).decode()

            # Get sender user using sync_to_async with thread_sensitive=True
            get_user = sync_to_async(User.objects.get, thread_sensitive=True)
            try:
                sender = await get_user(email=envelope.mail_from)
            except User.DoesNotExist:
                logger.error(f"Sender not found: {envelope.mail_from}")
                return '550 Sender not found'

            # Verify all recipients exist before creating any emails
            recipients = []
            for rcpt in envelope.rcpt_tos:
                try:
                    recipient = await get_user(email=rcpt)
                    recipients.append(recipient)
                except User.DoesNotExist:
                    logger.error(f"Recipient not found: {rcpt}")
                    return '550 Recipient not found'

            # Get current minute timestamp
            now = timezone.now()
            minute_timestamp = now.replace(second=0, microsecond=0)

            # Check if this email already exists in this minute
            check_existing = sync_to_async(
                lambda: Email.objects.filter(
                    sender=sender,
                    subject=subject,
                    body=body,
                    timestamp=minute_timestamp
                ).first(),
                thread_sensitive=True
            )
            
            existing_email = await check_existing()
            if existing_email:
                logger.info(f"Found existing email (id: {existing_email.id}), skipping creation")
                return '250 Message accepted for delivery'

            # Create email with specific timestamp
            create_email = sync_to_async(
                lambda s, subj, b, ts: Email.objects.create(
                    sender=s,
                    subject=subj,
                    body=b,
                    timestamp=ts
                ),
                thread_sensitive=True
            )
            
            new_email = await create_email(sender, subject, body, minute_timestamp)
            created_emails.append(new_email)
            
            # Add all recipients to the same email
            add_recipient = sync_to_async(
                new_email.recipients.add,
                thread_sensitive=True
            )
            for recipient in recipients:
                await add_recipient(recipient)
            
            # Handle attachments once for the single email
            for attachment_data in attachments:
                content = ContentFile(attachment_data['content'])
                
                create_attachment = sync_to_async(
                    lambda: EmailAttachment.objects.create(
                        email=new_email,
                        filename=attachment_data['filename'],
                        content_type=attachment_data['content_type']
                    ),
                    thread_sensitive=True
                )
                
                attachment = await create_attachment()
                
                save_file = sync_to_async(
                    attachment.file.save,
                    thread_sensitive=True
                )
                await save_file(
                    attachment_data['filename'],
                    content
                )
            
            return '250 Message accepted for delivery'

        except Exception as e:
            # Clean up any created emails on failure
            for email_obj in created_emails:
                try:
                    delete_email = sync_to_async(
                        lambda e=email_obj: e.delete(),  # Pass email_obj as default argument
                        thread_sensitive=True
                    )
                    await delete_email()
                except Exception as delete_error:
                    logger.error(f"Error deleting email: {delete_error}")
                    
            logger.error(f"Error creating emails: {e}")
            return f'500 Error creating emails: {str(e)}'

        except Exception as e:
            # Clean up any created emails on any error
            if created_emails:
                for email_obj in created_emails:
                    try:
                        delete_email = sync_to_async(
                            lambda e=email_obj: e.delete(),  # Pass email_obj as default argument
                            thread_sensitive=True
                        )
                        await delete_email()
                    except Exception as delete_error:
                        logger.error(f"Error deleting email: {delete_error}")
                        
            logger.error(f"Error processing message: {str(e)}")
            return f'500 Error processing message: {str(e)}'

def run_smtp_server():
    handler = LocalMailHandler()
    controller = Controller(handler, hostname='0.0.0.0', port=1025)
    controller.start()
    logger.info("Local SMTP server running on 0.0.0.0:1025")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.stop() 