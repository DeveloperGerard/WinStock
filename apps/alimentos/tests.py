from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from .forms import AlimentoForm
from .models import Alimento
from apps.funcionarios.models import Funcionario
from apps.lotes_ganado.models import Lote
from apps.raciones.models import Detalle_racion, Racion_diaria


class AlimentosOfflineTemplateTests(SimpleTestCase):
    def test_snapshot_sin_formulario_ni_token_csrf(self):
        request = RequestFactory().get(
            "/alimentos/",
            {"offline_snapshot": "1"},
        )
        request.user = AnonymousUser()
        html = render_to_string(
            "alimentos/alimentos.html",
            {"alimentos": [], "form": None, "offline_snapshot": True},
            request=request,
        )

        self.assertNotIn('class="alimentos-form"', html)
        self.assertNotIn("csrfmiddlewaretoken", html)
        self.assertIn("Alimentos registrados", html)
        self.assertIn('name="winstock-offline-snapshot"', html)


class AlimentosViewsTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="test1234",
            first_name="Test",
            last_name="Usuario",
            email="test@example.com",
        )
        self.client.force_login(funcionario)

    def test_inicio_muestra_plantilla_inicio(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inicio.html")
        self.assertContains(response, "css/inicio.css")

    def test_inicio_offline_snapshot_is_read_only(self):
        response = self.client.get("/", {"offline_snapshot": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inicio.html")
        self.assertContains(response, 'name="winstock-offline-snapshot"')
        self.assertContains(response, "Existencias de alimentos")

    def test_crear_alimento(self):
        response = self.client.post(
            reverse("alimentos:crearalimentos"),
            {"nombre": "Avena", "stock": "25.00"},
        )

        self.assertRedirects(response, reverse("alimentos:crearalimentos"))
        self.assertTrue(Alimento.objects.filter(nombre="Avena", stock="25.00").exists())

    def test_modificar_alimento(self):
        alimento = Alimento.objects.create(nombre="Avena", stock="10.00")

        page = self.client.get(
            reverse("alimentos:modificar_alimentos", args=[alimento.pk])
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "alimentos/alimentos.css")

        response = self.client.post(
            reverse("alimentos:modificar_alimentos", args=[alimento.pk]),
            {"nombre": "Maíz", "stock": "15.00"},
        )

        self.assertRedirects(response, reverse("alimentos:editar_alimentos"))
        alimento.refresh_from_db()
        self.assertEqual(alimento.nombre, "Maíz")
        self.assertEqual(alimento.stock, 15.00)

    def test_lista_de_edicion_responde(self):
        response = self.client.get(reverse("alimentos:editar_alimentos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alimentos/alimentos.css")

    def test_deshabilitar_alimento_solo_acepta_post(self):
        alimento = Alimento.objects.create(nombre="Avena")
        url = reverse("alimentos:deshabilitar_alimentos", args=[alimento.pk])

        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)

        self.assertRedirects(response, reverse("alimentos:editar_alimentos"))
        alimento.refresh_from_db()
        self.assertFalse(alimento.estado)

    def test_stock_muestra_solo_alimentos_activos(self):
        Alimento.objects.create(nombre="Avena", stock="25.00")
        Alimento.objects.create(nombre="Maíz", estado=False)

        response = self.client.get(reverse("alimentos:quedastock"))

        self.assertContains(response, "Avena")
        self.assertContains(response, "25,00")
        self.assertNotContains(response, "Maíz")
        self.assertContains(response, "alimentos/alimentos.css")

    def test_lista_de_alimentos_muestra_el_stock_actual(self):
        Alimento.objects.create(nombre="Brócoli", stock="12.50")

        response = self.client.get(
            reverse("alimentos:crearalimentos"),
            {"offline_snapshot": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock actual (kg)")
        self.assertContains(response, "12,50")


class AlimentosCsrfTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="csrf-alimentos@example.com",
        )
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(funcionario)

    def test_create_food_post_without_csrf_token_is_rejected(self):
        response = self.client.post(
            reverse("alimentos:crearalimentos"),
            {"nombre": "Avena", "stock": "10.00"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Alimento.objects.filter(nombre="Avena").exists())


class AlimentoValidationAndDatabaseTests(TestCase):
    def test_form_rejects_empty_name_and_negative_stock(self):
        empty_name_form = AlimentoForm(data={"nombre": "", "stock": "0"})
        negative_stock_form = AlimentoForm(
            data={"nombre": "Alimento negativo", "stock": "-10"}
        )

        self.assertFalse(empty_name_form.is_valid())
        self.assertIn("nombre", empty_name_form.errors)
        self.assertFalse(negative_stock_form.is_valid())
        self.assertIn("stock", negative_stock_form.errors)

    def test_database_accepts_negative_stock_without_check_constraint(self):
        alimento = Alimento.objects.create(nombre="Stock negativo", stock="-10.00")

        alimento.refresh_from_db()
        self.assertEqual(alimento.stock, -10.00)


class AlimentoManagementHistoryTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="alimento-historial@example.com",
        )
        self.client.force_login(funcionario)
        self.alimento = Alimento.objects.create(nombre="Avena", stock="20.00")
        self.otro_alimento = Alimento.objects.create(nombre="Maíz", stock="20.00")
        lote = Lote.objects.create(nombre="Lote con ración")
        self.racion = Racion_diaria.objects.create(
            fecha="2026-11-22",
            turno="Mañana",
            lote_id=lote,
            usuario_id=funcionario,
        )
        self.detalle = Detalle_racion.objects.create(
            racion_id=self.racion,
            alimento_id=self.alimento,
            kg="5.00",
        )

    def test_duplicate_food_name_is_accepted_by_edit_form(self):
        response = self.client.post(
            reverse(
                "alimentos:modificar_alimentos",
                args=[self.otro_alimento.pk],
            ),
            {"nombre": self.alimento.nombre, "stock": "20.00"},
        )

        self.assertRedirects(response, reverse("alimentos:editar_alimentos"))
        self.assertEqual(Alimento.objects.filter(nombre="Avena").count(), 2)

    def test_disabling_food_hides_it_from_new_use_and_keeps_history(self):
        response = self.client.post(
            reverse("alimentos:deshabilitar_alimentos", args=[self.alimento.pk])
        )

        self.assertRedirects(response, reverse("alimentos:editar_alimentos"))
        self.alimento.refresh_from_db()
        self.assertFalse(self.alimento.estado)
        self.assertTrue(Detalle_racion.objects.filter(pk=self.detalle.pk).exists())
        self.assertNotContains(
            self.client.get(reverse("alimentos:quedastock")),
            "Avena",
        )
        self.assertContains(
            self.client.get(reverse("alimentos:crearalimentos")),
            "Avena",
        )
        self.assertNotContains(
            self.client.get(reverse("raciones:raciones")),
            "Avena",
        )


class AlimentoTextInjectionTests(TestCase):
    def setUp(self):
        funcionario = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Prueba-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="alimento-xss@example.com",
        )
        self.client.force_login(funcionario)

    def test_sql_and_script_text_is_stored_as_text_and_html_escaped(self):
        nombre = "' OR 1=1 -- <script>alert(1)</script>"
        response = self.client.post(
            reverse("alimentos:crearalimentos"),
            {"nombre": nombre, "stock": "10"},
        )

        self.assertRedirects(response, reverse("alimentos:crearalimentos"))
        self.assertTrue(Alimento.objects.filter(nombre=nombre).exists())
        listing = self.client.get(reverse("alimentos:crearalimentos"))
        self.assertContains(listing, "&#x27; OR 1=1 --")
        self.assertContains(listing, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(listing, "<script>alert(1)</script>")
