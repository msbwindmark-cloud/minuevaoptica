import os
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Copia de seguridad de la base de datos (JSON)"

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, default="backup.json")

    def handle(self, *args, **options):
        out = options["output"]
        with open(out, "w", encoding="utf-8") as f:
            call_command("dumpdata", "--indent", "2", stdout=f)
        self.stdout.write(self.style.SUCCESS(f"Backup guardado en {out}"))