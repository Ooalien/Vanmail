import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from django.db import models

from .models import User, Email, EmailAttachment

logger = logging.getLogger(__name__)


def index(request):

    # Authenticated users view their inbox
    if request.user.is_authenticated:
        return render(request, "mail/inbox.html")

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse("login"))


@csrf_exempt
@login_required
def compose(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    try:
        # Get form data
        recipients = request.POST.get("recipients", "").split(",")
        recipients = [email.strip() for email in recipients if email.strip()]
        subject = request.POST.get("subject", "")
        body = request.POST.get("body", "")
        files = request.FILES.getlist("attachments")

        # Validate recipients first
        for recipient_email in recipients:
            if not User.objects.filter(email=recipient_email.strip()).exists():
                return JsonResponse({
                    "error": f"User not found: {recipient_email}"
                }, status=400)

        # Send via local SMTP
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication

            # Create message
            msg = MIMEMultipart()
            msg['From'] = request.user.email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Add attachments
            for file in files:
                part = MIMEApplication(
                    file.read(),
                    Name=file.name
                )
                part['Content-Disposition'] = f'attachment; filename="{file.name}"'
                msg.attach(part)

            # Send via local SMTP
            with smtplib.SMTP('localhost', 1025) as smtp:
                smtp.send_message(msg)

            return JsonResponse({"message": "Email sent successfully."}, status=201)

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def mailbox(request, mailbox):
    if mailbox == "inbox":
        # Get ONLY received emails (exclude self-sent)
        emails = Email.objects.filter(
            recipients=request.user,
            archived=False
        ).exclude(
            sender=request.user
        ).distinct()
    elif mailbox == "sent":
        emails = Email.objects.filter(
            sender=request.user
        ).order_by("-timestamp").distinct()
    elif mailbox == "archive":
        # Get ONLY archived received emails (exclude self-sent)
        emails = Email.objects.filter(
            recipients=request.user,
            archived=True
        ).exclude(
            sender=request.user
        ).distinct()

    # Return in reverse chronological order and ensure uniqueness
    emails = emails.order_by("-timestamp").distinct()
    return JsonResponse([email.serialize() for email in emails], safe=False)


@csrf_exempt
@login_required
def email(request, email_id):
    try:
        print(f"Loading email {email_id}")  # Debug log
        email = Email.objects.filter(
            pk=email_id
        ).filter(
            models.Q(sender=request.user) | models.Q(recipients=request.user)
        ).first()
        
        if email is None:
            return JsonResponse({"error": "Email not found."}, status=404)
            
    except Email.DoesNotExist:
        return JsonResponse({"error": "Email not found."}, status=404)

    # Handle different request methods
    if request.method == "GET":
        serialized = email.serialize()
        print(f"Serialized email: {serialized}")  # Debug log
        print(f"Attachments: {list(email.attachments.all())}")  # Debug log
        return JsonResponse(serialized)

    elif request.method == "PUT":
        data = json.loads(request.body)
        if data.get("read") is not None:
            email.read = data["read"]
        if data.get("archived") is not None:
            email.archived = data["archived"]
        email.save()
        return HttpResponse(status=204)

    else:
        return JsonResponse({
            "error": "GET or PUT request required."
        }, status=400)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "mail/login.html", {
                "message": "Invalid email and/or password."
            })
    else:
        return render(request, "mail/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "mail/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(email, email, password)
            user.save()
        except IntegrityError as e:
            print(e)
            return render(request, "mail/register.html", {
                "message": "Email address already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "mail/register.html")


@login_required
def download_attachment(request, attachment_id):
    try:
        print(f"Downloading attachment {attachment_id}")  # Debug log
        attachment = EmailAttachment.objects.get(id=attachment_id)
        email = attachment.email
        
        print(f"Found attachment: {attachment.filename}")  # Debug log
        
        # Security check - only allow download if user is sender or recipient
        if request.user != email.sender and request.user not in email.recipients.all():
            print(f"Access denied for user {request.user.email}")  # Debug log
            return HttpResponse("Access denied", status=403)
        
        try:
            # Read the file content
            file_content = attachment.file.read()
            
            print(f"Serving file: {attachment.filename}")  # Debug log
            response = HttpResponse(
                file_content,
                content_type=attachment.content_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
            return response
            
        except IOError as e:
            print(f"Error reading file: {str(e)}")  # Debug log
            return HttpResponse("Error reading file", status=500)
            
    except EmailAttachment.DoesNotExist:
        print(f"Attachment {attachment_id} not found")  # Debug log
        return HttpResponse("Attachment not found", status=404)
    except Exception as e:
        print(f"Error downloading attachment: {str(e)}")  # Debug log
        return HttpResponse(f"Error downloading attachment: {str(e)}", status=500)
