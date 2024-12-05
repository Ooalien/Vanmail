import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project3.settings')
django.setup()

# Import after Django setup
from mail.imap_server import run_imap_server

if __name__ == '__main__':
    run_imap_server() 