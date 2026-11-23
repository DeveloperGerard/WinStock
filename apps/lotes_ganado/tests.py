from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve, reverse

from apps.funcionarios.models import Funcionario
from apps.alimentos.models import Alimento
from apps.raciones.models import Detalle_racion, Racion_diaria
from .models import Lote


class LotesOfflineTemplateTests(SimpleTestCase):
    def test_snapshot_shows_read_only_list(self):
        request = RequestFactory().get("/ganado/lotes/", {"offline_snapshot": "1"})
        request.user = AnonymousUser()
        request.resolver_match = resolve("/ganado/lotes/")
        html = render_to_string(
            "lista_lotes.html",
            {"lotes": [], "q": "", "estado": "", "offline_snapshot": True},
            request=request,
        )

        self.assertIn('name="winstock-offline-snapshot"', html)
        self.assertNotIn("Nuevo lote", html)
        self.assertNotIn("<form", html)
        self.assertNotIn("csrfmiddlewaretoken", html)


class LoteRegistrationTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="lote-prueba@example.com",
        )
        self.client.force_login(funcionario)

    def test_valid_lote_is_created_and_available_for_rations(self):
        response = self.client.post(
            reverse("ganado:crear_lote"),
            {"nombre": "vacas en producción", "cantidad": "120", "activo": "on"},
        )

        self.assertRedirects(response, reverse("ganado:lotes"))
        lote = Lote.objects.get(nombre="vacas en producción", cantidad=120)
        self.assertTrue(lote.activo)

        raciones_response = self.client.get(reverse("raciones:raciones"))
        self.assertContains(raciones_response, "vacas en producción - 120")


class LoteEditHistoryTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="lote-edicion@example.com",
        )
        self.client.force_login(funcionario)
        alimento = Alimento.objects.create(nombre="Avena", stock="50.00")
        self.lote = Lote.objects.create(
            nombre="Lote de prueba",
            cantidad=120,
            activo=True,
        )
        self.raciones = [
            Racion_diaria.objects.create(
                fecha=fecha,
                turno=turno,
                lote_id=self.lote,
                usuario_id=funcionario,
            )
            for fecha, turno in (("2026-11-20", "Mañana"), ("2026-11-21", "Tarde"))
        ]
        for racion, kilos in zip(self.raciones, ("20.00", "10.00")):
            Detalle_racion.objects.create(
                racion_id=racion,
                alimento_id=alimento,
                kg=kilos,
            )

    def test_editing_lote_keeps_previous_rations_and_details(self):
        response = self.client.post(
            reverse("ganado:editar_lote", kwargs={"uuid": self.lote.uuid}),
            {"nombre": "Lote actualizado", "cantidad": "110", "activo": "on"},
        )

        self.assertRedirects(response, reverse("ganado:lotes"))
        self.lote.refresh_from_db()
        self.assertEqual(self.lote.cantidad, 110)
        self.assertEqual(Racion_diaria.objects.filter(lote_id=self.lote).count(), 2)
        self.assertCountEqual(
            list(
                Detalle_racion.objects.filter(racion_id__in=self.raciones)
                .values_list("kg", flat=True)
            ),
            [20, 10],
        )


class LoteTextInjectionTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="lote-xss@example.com",
        )
        self.client.force_login(funcionario)

    def test_script_in_lote_name_is_html_escaped(self):
        nombre = "<script>alert(1)</script>"
        response = self.client.post(
            reverse("ganado:crear_lote"),
            {"nombre": nombre, "cantidad": "5", "activo": "on"},
        )

        self.assertRedirects(response, reverse("ganado:lotes"))
        self.assertTrue(Lote.objects.filter(nombre=nombre).exists())
        listing = self.client.get(reverse("ganado:lotes"))
        self.assertContains(listing, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(listing, "<script>alert(1)</script>")
