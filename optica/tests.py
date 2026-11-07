from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import Organizacion, Perfil
from .models import Marca, Modelo, Ajustes, Consulta


class OpticaTenantTest(TestCase):
    def setUp(self):
        self.org1 = Organizacion.objects.create(nombre="O1", slug="o1")
        self.org2 = Organizacion.objects.create(nombre="O2", slug="o2")
        self.u1 = User.objects.create_user("g1", password="pass12345")
        self.u2 = User.objects.create_user("g2", password="pass12345")
        Perfil.objects.create(user=self.u1, organizacion=self.org1, rol="gestor")
        Perfil.objects.create(user=self.u2, organizacion=self.org2, rol="gestor")
        self.marca1 = Marca.objects.create(organizacion=self.org1, nombre="Marca1", slug="marca1")
        self.marca2 = Marca.objects.create(organizacion=self.org2, nombre="Marca2", slug="marca2")

    def test_marcas_aisladas(self):
        # filtrado por organizacion
        self.assertEqual(Marca.objects.filter(organizacion=self.org1).count(), 1)
        self.assertEqual(Marca.objects.filter(organizacion=self.org2).count(), 1)

    def test_gestor_solo_ve_sus_modelos(self):
        client = Client(HTTP_HOST="localhost")
        client.login(username="g1", password="pass12345")
        r = client.get(reverse("optica:gestion_marcas"), HTTP_HOST="localhost")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Marca1")
        self.assertNotContains(r, "Marca2")


class PublicFormTest(TestCase):
    def setUp(self):
        self.org = Organizacion.objects.create(nombre="O", slug="o")
        Ajustes.for_org(self.org)

    def test_contacto_crea_consulta(self):
        client = Client(HTTP_HOST="localhost")
        r = client.post(reverse("optica:contacto"), {
            "nombre": "Ana", "telefono": "600123456", "email": "ana@example.com",
            "mensaje": "Hola", "consentimiento": "on",
        }, HTTP_HOST="localhost")
        self.assertIn(r.status_code, (302, 200))
        self.assertEqual(Consulta.objects.filter(organizacion=self.org).count(), 1)

    def test_contacto_rate_limit(self):
        client = Client(HTTP_HOST="localhost")
        for _ in range(6):
            client.post(reverse("optica:contacto"), {
                "nombre": "Ana", "telefono": "600123456", "mensaje": "Hola", "consentimiento": "on",
            }, HTTP_HOST="localhost")
        self.assertLessEqual(Consulta.objects.count(), 5)



class PermissionTest(TestCase):
    def setUp(self):
        self.org = Organizacion.objects.create(nombre="O", slug="o")
        self.user = User.objects.create_user("g", password="pass12345")
        Perfil.objects.create(user=self.user, organizacion=self.org, rol="gestor")

    def test_gestor_no_entra_admin(self):
        client = Client(HTTP_HOST="localhost")
        client.login(username="g", password="pass12345")
        r = client.get("/admin/", HTTP_HOST="localhost")
        self.assertIn(r.status_code, (302, 403))

    def test_visitante_no_borra_modelo(self):
        client = Client(HTTP_HOST="localhost")
        r = client.post("/gestion/modelos/1/borrar/", HTTP_HOST="localhost")
        self.assertIn(r.status_code, (302, 403))


class AuditOpticaTest(TestCase):
    def setUp(self):
        self.org = Organizacion.objects.create(nombre="O", slug="o")
        self.user = User.objects.create_user("g", password="pass12345")
        Perfil.objects.create(user=self.user, organizacion=self.org, rol="gestor")

    def test_crear_marca_audita(self):
        from core.models import Auditoria
        before = Auditoria.objects.count()
        Marca.objects.create(organizacion=self.org, nombre="M", slug="m")
        after = Auditoria.objects.count()
        self.assertGreater(after, before)
        last = Auditoria.objects.order_by("-fecha").first()
        self.assertEqual(last.accion, "crear")
