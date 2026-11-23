from decimal import Decimal

from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve
from django.urls import reverse

from apps.alimentos.models import Alimento, Movimientos_alimentos
from apps.funcionarios.models import Funcionario
from apps.lotes_ganado.models import Lote
from .forms import DetalleRacionForm
from apps.raciones.models import Detalle_racion, Racion_diaria


class RacionesOfflineTemplateTests(SimpleTestCase):
    def test_snapshot_shows_history_without_mutation_form(self):
        request = RequestFactory().get("/raciones/", {"offline_snapshot": "1"})
        request.user = AnonymousUser()
        request.resolver_match = resolve("/raciones/")
        html = render_to_string(
            "raciones/raciones.html",
            {
                "form": None,
                "formset": None,
                "ultimas_raciones": [],
                "offline_snapshot": True,
            },
            request=request,
        )

        self.assertIn('name="winstock-offline-snapshot"', html)
        self.assertIn("Últimas raciones registradas", html)
        self.assertNotIn("Guardar ración y descontar stock", html)
        self.assertNotIn("csrfmiddlewaretoken", html)


class RacionesOfflineViewTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="test1234",
            first_name="Test",
            last_name="Usuario",
            email="test@example.com",
        )
        self.client.force_login(funcionario)

    def test_offline_snapshot_route_returns_read_only_history(self):
        response = self.client.get(
            reverse("raciones:raciones"),
            {"offline_snapshot": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="winstock-offline-snapshot"')
        self.assertContains(response, "Últimas raciones registradas")
        self.assertNotContains(response, "Guardar ración y descontar stock")
        self.assertNotContains(response, "csrfmiddlewaretoken")


class RacionesStockViewTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="test1234",
            first_name="Test",
            last_name="Usuario",
            email="test@example.com",
        )
        self.client.force_login(funcionario)
        self.alimento = Alimento.objects.create(nombre="Avena", stock="10.00")
        self.lote = Lote.objects.create(nombre="Lote de prueba")

    def _post_racion(self, kg):
        return self.client.post(
            reverse("raciones:raciones"),
            {
                "fecha": "2026-11-22",
                "turno": "Mañana",
                "lote_id": self.lote.pk,
                "detalles-TOTAL_FORMS": "1",
                "detalles-INITIAL_FORMS": "0",
                "detalles-MIN_NUM_FORMS": "0",
                "detalles-MAX_NUM_FORMS": "1000",
                "detalles-0-alimento": self.alimento.pk,
                "detalles-0-kg": kg,
            },
        )

    def test_crear_racion_descuenta_stock_y_registra_movimiento(self):
        response = self._post_racion("2.50")

        self.assertRedirects(response, reverse("raciones:raciones"))
        self.alimento.refresh_from_db()
        self.assertEqual(self.alimento.stock, 7.50)
        self.assertEqual(Racion_diaria.objects.count(), 1)
        self.assertEqual(Detalle_racion.objects.get().kg, 2.50)
        self.assertEqual(Movimientos_alimentos.objects.get().cantidad, -2.50)

    def test_stock_insuficiente_no_crea_racion_ni_modifica_stock(self):
        response = self._post_racion("12.00")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock insuficiente de Avena")
        self.alimento.refresh_from_db()
        self.assertEqual(self.alimento.stock, 10.00)
        self.assertEqual(Racion_diaria.objects.count(), 0)
        self.assertEqual(Movimientos_alimentos.objects.count(), 0)


class RacionesCsrfTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="csrf-raciones@example.com",
        )
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(funcionario)
        self.alimento = Alimento.objects.create(nombre="Avena", stock="10.00")
        self.lote = Lote.objects.create(nombre="Lote de prueba")

    def test_create_ration_post_without_csrf_token_is_rejected(self):
        response = self.client.post(
            reverse("raciones:raciones"),
            {
                "fecha": "2026-11-22",
                "turno": "Mañana",
                "lote_id": self.lote.pk,
                "detalles-TOTAL_FORMS": "1",
                "detalles-INITIAL_FORMS": "0",
                "detalles-MIN_NUM_FORMS": "0",
                "detalles-MAX_NUM_FORMS": "1000",
                "detalles-0-alimento": self.alimento.pk,
                "detalles-0-kg": "2.50",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.alimento.refresh_from_db()
        self.assertEqual(self.alimento.stock, 10.00)
        self.assertEqual(Racion_diaria.objects.count(), 0)


class RepeatedFoodDetailsTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="racion-repetida@example.com",
        )
        self.client.force_login(funcionario)
        self.alimento = Alimento.objects.create(nombre="Avena", stock="50.00")
        self.lote = Lote.objects.create(nombre="Lote de prueba")

    def test_repeated_food_rows_are_saved_as_separate_details(self):
        response = self.client.post(
            reverse("raciones:raciones"),
            {
                "fecha": "2026-11-22",
                "turno": "Mañana",
                "lote_id": self.lote.pk,
                "detalles-TOTAL_FORMS": "2",
                "detalles-INITIAL_FORMS": "0",
                "detalles-MIN_NUM_FORMS": "0",
                "detalles-MAX_NUM_FORMS": "1000",
                "detalles-0-alimento": self.alimento.pk,
                "detalles-0-kg": "20.00",
                "detalles-1-alimento": self.alimento.pk,
                "detalles-1-kg": "10.00",
            },
        )

        self.assertRedirects(response, reverse("raciones:raciones"))
        self.alimento.refresh_from_db()
        self.assertEqual(self.alimento.stock, 20.00)
        self.assertCountEqual(
            list(Detalle_racion.objects.values_list("kg", flat=True)),
            [20, 10],
        )


class RacionDetailConstraintTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="detalle-validacion@example.com",
        )
        self.alimento = Alimento.objects.create(nombre="Avena", stock="20.00")
        lote = Lote.objects.create(nombre="Lote de prueba")
        self.racion = Racion_diaria.objects.create(
            fecha="2026-11-22",
            turno="Mañana",
            lote_id=lote,
            usuario_id=funcionario,
        )

    def test_form_rejects_non_positive_kilos(self):
        for kilos in ("0", "-3"):
            form = DetalleRacionForm(
                data={"alimento": self.alimento.pk, "kg": kilos}
            )
            self.assertFalse(form.is_valid(), kilos)

    def test_database_accepts_non_positive_kilos_without_check_constraint(self):
        details = [
            Detalle_racion.objects.create(
                racion_id=self.racion,
                alimento_id=self.alimento,
                kg=kilos,
            )
            for kilos in ("0", "-3")
        ]

        for detail in details:
            detail.refresh_from_db()
        self.assertEqual([detail.kg for detail in details], [Decimal("0"), Decimal("-3")])
