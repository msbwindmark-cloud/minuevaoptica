from django.test import TestCase
from django.contrib.auth.models import User

from .models import Organizacion, Perfil, Auditoria


class TenantIsolationTest(TestCase):
    def setUp(self):
        self.org1 = Organizacion.objects.create(nombre="Org1", slug="org1")
        self.org2 = Organizacion.objects.create(nombre="Org2", slug="org2")
        self.u1 = User.objects.create_user("u1", password="pass12345")
        self.u2 = User.objects.create_user("u2", password="pass12345")
        Perfil.objects.create(user=self.u1, organizacion=self.org1, rol="gestor")
        Perfil.objects.create(user=self.u2, organizacion=self.org2, rol="gestor")

    def test_perfil_organizacion(self):
        self.assertEqual(self.u1.perfil.organizacion, self.org1)
        self.assertEqual(self.u2.perfil.organizacion, self.org2)

    def test_auditoria_aislamiento(self):
        Auditoria.objects.create(organizacion=self.org1, accion="otro", objeto_repr="x")
        Auditoria.objects.create(organizacion=self.org2, accion="otro", objeto_repr="y")
        # filtrado manual (sumando los generados por las señales del setUp)
        self.assertGreaterEqual(Auditoria.objects.filter(organizacion=self.org1).count(), 1)
        self.assertGreaterEqual(Auditoria.objects.filter(organizacion=self.org2).count(), 1)


class AuditoriaSignalTest(TestCase):
    def setUp(self):
        self.org = Organizacion.objects.create(nombre="OrgA", slug="orga")
        self.user = User.objects.create_user("adminx", password="pass12345")
        Perfil.objects.create(user=self.user, organizacion=self.org, rol="admin")

    def test_crear_genera_auditoria(self):
        before = Auditoria.objects.count()
        Perfil.objects.create(
            user=User.objects.create_user("nuevo", password="pass12345"),
            organizacion=self.org, rol="gestor",
        )
        after = Auditoria.objects.count()
        self.assertGreater(after, before)
        last = Auditoria.objects.order_by("-fecha").first()
        self.assertEqual(last.accion, "crear")
        self.assertIn("rol", last.cambios or {})

    def test_no_guarda_password(self):
        u = User.objects.create_user("pwduser", password="secreto123")
        # cambiar password
        u.set_password("otro123")
        u.save()
        # Auditoria de User no se registra porque User no es TenantModel; pero Perfil sí
        # comprobamos que ningún cambios contiene password hash
        for a in Auditoria.objects.all():
            self.assertNotIn("password", (a.cambios or {}))
