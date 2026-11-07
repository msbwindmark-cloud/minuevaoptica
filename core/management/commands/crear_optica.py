from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Organizacion, Perfil


class Command(BaseCommand):
    help = "Crea una organización y su usuario gestor"

    def add_arguments(self, parser):
        parser.add_argument("nombre", type=str)
        parser.add_argument("username", type=str)
        parser.add_argument("--password", type=str, required=True)
        parser.add_argument("--email", type=str, default="")

    def handle(self, *args, **options):
        nombre = options["nombre"]
        username = options["username"]
        password = options["password"]
        email = options["email"]
        slug = nombre.lower().replace(" ", "-")[:80]
        org, created = Organizacion.objects.get_or_create(slug=slug, defaults={"nombre": nombre})
        if not created:
            org.nombre = nombre
            org.save()
        user, ucreated = User.objects.get_or_create(username=username, defaults={"email": email})
        user.set_password(password)
        user.is_staff = False
        user.is_superuser = False
        user.save()
        perfil, _ = Perfil.objects.get_or_create(user=user, defaults={"organizacion": org, "rol": "gestor"})
        perfil.organizacion = org
        perfil.rol = "gestor"
        perfil.save()
        self.stdout.write(self.style.SUCCESS(f"Organización '{org}' y usuario '{user.username}' listos."))
