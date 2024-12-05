import asyncio
from aioimaplib import aioimaplib
from mail.models import Email, User, EmailAttachment
from asgiref.sync import sync_to_async
import logging
import email
from email import policy

logger = logging.getLogger(__name__)

class LocalIMAPHandler:
    def __init__(self):
        self.connections = {}

    async def handle_LOGIN(self, server, username, password):
        try:
            # Verify user credentials
            get_user = sync_to_async(
                lambda: User.objects.get(email=username),
                thread_sensitive=True
            )
            user = await get_user()
            
            if user.check_password(password):
                self.connections[username] = {
                    'user': user,
                    'selected_mailbox': None
                }
                return True
            return False
        except User.DoesNotExist:
            return False

    async def handle_SELECT(self, server, username, mailbox):
        if username not in self.connections:
            return False
        
        self.connections[username]['selected_mailbox'] = mailbox
        
        # Get email count for mailbox
        get_count = sync_to_async(
            lambda: Email.objects.filter(
                recipients__email=username,
                archived=(mailbox.lower() == 'archive')
            ).count(),
            thread_sensitive=True
        )
        count = await get_count()
        
        return count

    async def handle_FETCH(self, server, username, message_set, query):
        if username not in self.connections:
            return []
        
        user = self.connections[username]['user']
        mailbox = self.connections[username]['selected_mailbox']
        
        # Get emails based on mailbox
        get_emails = sync_to_async(
            lambda: Email.objects.filter(
                recipients__email=username,
                archived=(mailbox.lower() == 'archive')
            ).order_by('-timestamp'),
            thread_sensitive=True
        )
        emails = await get_emails()
        
        results = []
        for email_obj in emails:
            msg = email.message.EmailMessage(policy=policy.default)
            msg['From'] = email_obj.sender.email
            msg['To'] = ', '.join([r.email for r in await sync_to_async(email_obj.recipients.all)()]) 
            msg['Subject'] = email_obj.subject
            msg['Date'] = email_obj.timestamp.strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Handle attachments
            if await sync_to_async(email_obj.attachments.exists)():
                msg.make_mixed()
                msg.add_alternative(email_obj.body, subtype='plain')
                
                attachments = await sync_to_async(list)(email_obj.attachments.all())
                for attachment in attachments:
                    file_content = await sync_to_async(attachment.file.read)()
                    msg.add_attachment(
                        file_content,
                        maintype=attachment.content_type.split('/')[0],
                        subtype=attachment.content_type.split('/')[1],
                        filename=attachment.filename
                    )
            else:
                msg.set_content(email_obj.body)
            
            results.append(msg)
        
        return results

def run_imap_server():
    handler = LocalIMAPHandler()
    server = aioimaplib.IMAP4Server(handler, host='0.0.0.0', port=1143)
    
    loop = asyncio.get_event_loop()
    loop.create_task(server.serve_forever())
    
    logger.info("Local IMAP server running on 0.0.0.0:1143")
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        server.close() 