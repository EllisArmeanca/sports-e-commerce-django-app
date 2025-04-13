from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from django.utils.timezone import now
from django.core.mail import mail_admins
from django.utils.html import format_html

import time

# Dicționar pentru a ține evidența încercărilor eșuate
failed_logins = {}

@receiver(user_login_failed)
def detect_failed_logins(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'Unknown')
    ip_address = get_client_ip(request)
    current_time = time.time()

    if username not in failed_logins:
        failed_logins[username] = []

    failed_logins[username].append(current_time)

    failed_logins[username] = [
        t for t in failed_logins[username] if current_time - t <= 120 #2,in
    ]

    if len(failed_logins[username]) == 3:
        subject = "Logari suspecte"
        plain_message = (
            f"Username: {username}\n"
            f"IP: {ip_address}\n"
            f"Au fost detectate 3 încercări eșuate de logare în mai puțin de 2 minute."
        )
        html_message = format_html(
            "<h1 style='color: red;'>Logari suspecte</h1>"
            "<p><strong>Username:</strong> {}</p>"
            "<p><strong>IP:</strong> {}</p>"
            "<p>Au fost detectate 3 încercări eșuate de logare în mai puțin de 2 minute.</p>",
            username,
            ip_address,
        )

        mail_admins(subject, plain_message, html_message=html_message)

        failed_logins.pop(username)

def get_client_ip(request):
    """Functie utilitara pentru a extrage adresa IP a clientului."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')
