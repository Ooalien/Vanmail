import asyncio
from aiosmtpd.controller import Controller
from mail.models import Email, User, EmailAttachment
from asgiref.sync import sync_to_async
import logging
import email
from email import policy
import socket

logger = logging.getLogger(__name__)

class IMAPProtocol(asyncio.Protocol):
    def __init__(self):
        self.connections = {}
        self.transport = None
        self.buffer = ''
        self.current_tag = None
        self.current_user = None
        self.capabilities = [
            'IMAP4rev1',
            'AUTH=PLAIN',
            'LOGINDISABLED',
            'STARTTLS',
            'LITERAL+',
            'MULTIAPPEND',
            'UNSELECT',
            'IDLE'
        ]

    def connection_made(self, transport):
        self.transport = transport
        self.send_response('* OK IMAP4rev1 Server Ready')
        self.send_response(f'* CAPABILITY {" ".join(self.capabilities)}')

    def data_received(self, data):
        try:
            message = data.decode().strip()
            if not message:
                return

            parts = message.split(' ')
            if len(parts) < 2:
                return

            self.current_tag = parts[0]
            command = parts[1].upper()

            if command == 'CAPABILITY':
                self.handle_capability()
            elif command == 'LOGIN':
                asyncio.create_task(self.handle_login(parts[2:]))
            elif command == 'SELECT':
                asyncio.create_task(self.handle_select(parts[2:]))
            elif command == 'FETCH':
                asyncio.create_task(self.handle_fetch(parts[2:]))
            elif command == 'SEARCH':
                asyncio.create_task(self.handle_search(parts[2:]))
            elif command == 'LOGOUT':
                self.handle_logout()
            elif command == 'NOOP':
                self.handle_noop()
            else:
                self.send_response(f'{self.current_tag} BAD Unknown command')

        except Exception as e:
            logger.error(f"Error processing IMAP command: {str(e)}")
            self.send_response(f'{self.current_tag} BAD Error processing command')

    def handle_capability(self):
        self.send_response(f'* CAPABILITY {" ".join(self.capabilities)}')
        self.send_response(f'{self.current_tag} OK CAPABILITY completed')

    def handle_noop(self):
        self.send_response(f'{self.current_tag} OK NOOP completed')

    async def handle_login(self, args):
        if len(args) != 2:
            self.send_response(f'{self.current_tag} BAD Invalid login format')
            return

        username, password = args
        username = username.strip('"').strip("'")
        password = password.strip('"').strip("'")

        try:
            get_user = sync_to_async(
                lambda: User.objects.get(email=username),
                thread_sensitive=True
            )
            user = await get_user()
            
            if user.check_password(password):
                self.current_user = user
                self.connections[username] = {
                    'user': user,
                    'selected_mailbox': None
                }
                self.send_response(f'* CAPABILITY {" ".join(self.capabilities)}')
                self.send_response(f'{self.current_tag} OK LOGIN completed')
            else:
                self.send_response(f'{self.current_tag} NO Invalid credentials')
        except User.DoesNotExist:
            self.send_response(f'{self.current_tag} NO Invalid credentials')

    async def handle_select(self, args):
        if not self.current_user:
            self.send_response(f'{self.current_tag} NO Not authenticated')
            return

        if len(args) != 1:
            self.send_response(f'{self.current_tag} BAD Invalid SELECT format')
            return

        mailbox = args[0].strip('"').lower()
        self.connections[self.current_user.email]['selected_mailbox'] = mailbox

        get_count = sync_to_async(
            lambda: Email.objects.filter(
                recipients__email=self.current_user.email,
                archived=(mailbox == 'archive')
            ).count(),
            thread_sensitive=True
        )
        count = await get_count()

        self.send_response(f'* {count} EXISTS')
        self.send_response(f'{self.current_tag} OK [READ-WRITE] SELECT completed')

    async def handle_fetch(self, args):
        if not self.current_user:
            self.send_response(f'{self.current_tag} NO Not authenticated')
            return

        if len(args) < 2:
            self.send_response(f'{self.current_tag} BAD Invalid FETCH format')
            return

        message_set = args[0]
        query = args[1].strip('()')

        mailbox = self.connections[self.current_user.email]['selected_mailbox']
        if not mailbox:
            self.send_response(f'{self.current_tag} NO No mailbox selected')
            return

        # Get emails based on mailbox
        get_emails = sync_to_async(
            lambda: list(Email.objects.filter(
                recipients__email=self.current_user.email,
                archived=(mailbox.lower() == 'archive')
            ).order_by('-timestamp')),
            thread_sensitive=True
        )
        emails = await get_emails()

        try:
            for idx, email_obj in enumerate(emails, 1):
                if str(idx) not in message_set:
                    continue

                msg = email.message.EmailMessage(policy=policy.default)
                msg['From'] = email_obj.sender.email
                msg['To'] = ', '.join([r.email for r in await sync_to_async(email_obj.recipients.all)()])
                msg['Subject'] = email_obj.subject
                msg['Date'] = email_obj.timestamp.strftime("%a, %d %b %Y %H:%M:%S %z")

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

                # Send the message data
                self.send_response(f'* {idx} FETCH (RFC822 {{{len(str(msg))}}}\r\n{str(msg)}\r\n)')

            self.send_response(f'{self.current_tag} OK FETCH completed')
        except Exception as e:
            logger.error(f"Fetch error: {str(e)}")
            self.send_response(f'{self.current_tag} NO Fetch failed: {str(e)}')

    async def handle_search(self, args):
        if not self.current_user:
            self.send_response(f'{self.current_tag} NO Not authenticated')
            return

        mailbox = self.connections[self.current_user.email]['selected_mailbox']
        if not mailbox:
            self.send_response(f'{self.current_tag} NO No mailbox selected')
            return

        # Parse search criteria
        search_type = 'ALL'
        if args:
            search_type = args[0].upper()

        # Build query based on search type
        query_filters = {
            'recipients__email': self.current_user.email,
            'archived': (mailbox.lower() == 'archive')
        }

        if search_type == 'UNSEEN':
            query_filters['read'] = False

        # Get emails based on criteria
        get_emails = sync_to_async(
            lambda: list(Email.objects.filter(**query_filters).order_by('-timestamp').values_list('id', flat=True)),
            thread_sensitive=True
        )
        
        try:
            email_ids = await get_emails()
            message_numbers = [str(i) for i in range(1, len(email_ids) + 1)]
            
            if message_numbers:
                self.send_response(f'* SEARCH {" ".join(message_numbers)}')
            else:
                self.send_response('* SEARCH')
            
            self.send_response(f'{self.current_tag} OK SEARCH completed')
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            self.send_response(f'{self.current_tag} NO Search failed: {str(e)}')

    def handle_logout(self):
        if self.current_user:
            if self.current_user.email in self.connections:
                del self.connections[self.current_user.email]
            self.current_user = None
        self.send_response('* BYE IMAP4 Server logging out')
        self.send_response(f'{self.current_tag} OK LOGOUT completed')
        self.transport.close()

    def send_response(self, response):
        try:
            if self.transport and not self.transport.is_closing():
                self.transport.write(f'{response}\r\n'.encode())
            else:
                logger.error("Transport is closed or closing")
        except Exception as e:
            logger.error(f"Error sending response: {str(e)}")

def run_imap_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    server = loop.create_server(
        IMAPProtocol,
        host='0.0.0.0',
        port=1143
    )
    
    logger.info("Local IMAP server running on 0.0.0.0:1143")
    
    try:
        loop.run_until_complete(server)
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close() 