# VanMail Service

VanMail is a self-hosted email service that provides SMTP and IMAP functionality through Docker containers. It's designed to be easy to set up and integrate with existing applications.

## Features

- SMTP Server (Port 1025)
- IMAP Server (Port 1143)
- Web Interface (Port 5000)
- File Attachment Support
- Docker-based deployment
- Django Admin Interface

## Quick Start

### Prerequisites

- Docker
- Docker Compose
- Git

### Installation

1. Clone the repository:
```
git clone https://github.com/Ooalien/Vanmail.git

cd vanmail
```

2. Build and start the containers:
```
docker-compose up --build
```

The service will be available at:
- Web Interface: http://localhost:5000
- SMTP Server: localhost:1025
- IMAP Server: localhost:1143

## Configuration

### Environment Variables

The following environment variables can be configured in `docker-compose.yml`:
environment:

DEBUG=1
DOCKER_ENV=1


### Ports

Default port mappings:
- 5000: Django web server
- 1025: SMTP server
- 1143: IMAP server

You can modify these in the `docker-compose.yml` file if needed.

## Usage

### Sending Emails

To send emails through the SMTP server:
#### python
```
import smtplib
from email.message import EmailMessage
msg = EmailMessage()
msg.set_content("Email content")
msg["Subject"] = "Test Subject"
msg["From"] = "sender@example.com"
msg["To"] = "recipient@example.com"
with smtplib.SMTP("localhost", 1025) as server:
server.send_message(msg)
```

### Reading Emails (IMAP)

To read emails through the IMAP server:
#### python
```
import imaplib
import email
#Connect to IMAP server
imap = imaplib.IMAP4("localhost", 1143)
imap.login("user@example.com", "password")
#Select inbox
imap.select("INBOX")
#Search for all emails
_, messages = imap.search(None, "ALL")for num in messages[0].split(): , msg = imap.fetch(num, "(RFC822)")
email_body = msg[0][1]
email_message = email.message_from_bytes(email_body)
print(f"Subject: {email_message['subject']}")

```

## Development

### Running Tests
```
docker-compose exec web python manage.py test
```

### Accessing Django Admin

1. Create a superuser:
```
docker-compose exec web python manage.py createsuperuser
```

2. Access the admin interface at http://localhost:5000/admin

## Troubleshooting

### Common Issues

1. Port conflicts:
   - Ensure ports 5000, 1025, and 1143 are not in use
   - Modify port mappings in docker-compose.yml if needed

2. Connection refused:
   - Check if containers are running: `docker-compose ps`
   - Verify network settings in docker-compose.yml