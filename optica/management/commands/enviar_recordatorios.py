from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from .models import RecordatorioRevision


class Command(BaseCommand):
    help = "Envía recordatorios de revisión anual pendientes"

    def handle(self, *args, **options):
        hoy = date.today()
        qs = RecordatorioRevision.objects.filter(enviado=False)
        enviados = 0
        for r in qs:
            if (hoy - r.fecha_ultima_revision).days >= 365:
                try:
                    send_mail(
                        subject="Recordatorio de revisión de vista",
                        message=f"Hola {r.nombre}, ha pasado un año desde tu última revisión. ¿Quieres pedir cita?",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[r.email],
                        fail_silently=True,
                    )
                    r.enviado = True
                    r.fecha_envio = None
                    r.save(update_fields=["enviado"])
                    enviados += 1
                except Exception:
                    pass
        self.stdout.write(self.style.SUCCESS(f"Recordatorios enviados: {enviados}"))