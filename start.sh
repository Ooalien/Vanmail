#!/bin/bash

# Start the SMTP server in the background
python run_smtp.py &

# Start the IMAP server in the background
python run_imap.py &

# Wait for SMTP server to start
sleep 5

# Start Django server
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:5000 