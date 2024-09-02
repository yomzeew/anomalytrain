# email_utils.py
from flask_mail import Message
from flask import flash

def send_email(mail, subject, recipient, body, sender=None):
    """
    Send an email using Flask-Mail.

    :param mail: The Flask-Mail instance.
    :param subject: The subject of the email.
    :param recipient: The recipient's email address.
    :param body: The body content of the email.
    :param sender: Optional sender email address (defaults to MAIL_DEFAULT_SENDER).
    :return: None
    """
    if not subject or not recipient or not body:
        flash('All fields are required!')
        return
    msg = Message(subject, recipients=[recipient])
    msg.html = body  # Pass the HTML content here
    try:
        mail.send(msg)
        flash('Email sent successfully!')
    except Exception as e:
        flash(f'Failed to send email: {e}')
