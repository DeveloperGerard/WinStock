from types import SimpleNamespace

from django import forms
from django.template.loader import render_to_string
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import path, resolve, reverse

from apps.alimentos.models import Alimento, Movimientos_alimentos
from apps.lotes_ganado.models import Lote
from apps.raciones.models import Detalle_racion, Racion_diaria
from .forms import CrearFuncionarioForm
from .models import Funcionario, Rol


class LoginPWATemplateTests(SimpleTestCase):
    def test_login_page_links_manifest_and_registers_service_worker(self):
        html = render_to_string("forms/inifunc.html", {"form": forms.Form()})

        self.assertIn('rel="manifest" href="/static/manifest.webmanifest"', html)
        self.assertIn('navigator.serviceWorker.register("/service-worker.js")', html)

    def test_service_worker_caches_the_home_snapshot_for_offline_use(self):
        response = self.client.get("/service-worker.js")
        script = b"".join(response.streaming_content).decode()

        self.assertIn("['/', '/?offline_snapshot=1']", script)
        self.assertIn("'/static/css/inicio.css'", script)
        self.assertNotIn("['/', '/alimentos/?offline_snapshot=1']", script)

    def test_base_template_offers_pwa_installation(self):
        request = RequestFactory().get("/")
        request.user = SimpleNamespace(rol=SimpleNamespace(nombre="adm"))
        request.resolver_match = resolve("/")
        html = render_to_string("base.html", {"request": request}, request=request)

        self.assertIn('rel="manifest" href="/static/manifest.webmanifest"', html)
        self.assertIn('id="install-app"', html)
        self.assertIn('id="install-help"', html)
        self.assertIn("beforeinstallprompt", html)
        self.assertIn("Añadir a pantalla de inicio", html)

    def test_accounts_offline_snapshot_is_read_only(self):
        request = RequestFactory().get("/cuentas/", {"offline_snapshot": "1"})
        request.user = SimpleNamespace(rol=SimpleNamespace(nombre="adm"))
        request.resolver_match = resolve("/cuentas/")
        html = render_to_string(
            "cuentas.html",
            {"funcionarios": [], "offline_snapshot": True},
            request=request,
        )

        self.assertIn('name="winstock-offline-snapshot"', html)
        self.assertNotIn("Crear funcionario", html)
        self.assertNotIn("csrfmiddlewaretoken", html)


class LoginCredentialErrorsTests(TestCase):
    def test_invalid_credentials_show_the_same_generic_error(self):
        Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Segura-2026!",
            first_name="Usuario",
            last_name="Prueba",
            email="login-prueba@example.com",
        )
        url = reverse("funcionarios:iniciarSesion")
        responses = [
            self.client.post(
                url,
                {"username": "11111111-1", "password": "Clave-incorrecta-2026!"},
            ),
            self.client.post(
                url,
                {"username": "12345678-5", "password": "Clave-Segura-2026!"},
            ),
        ]

        errors = []
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["form"].non_field_errors()), 1)
            errors.append(str(response.context["form"].non_field_errors()[0]))

        self.assertEqual(errors[0], errors[1])


class FuncionarioAccountCreationTests(TestCase):
    def setUp(self):
        admin_role, _ = Rol.objects.get_or_create(nombre="adm")
        admin = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Admin-2026!",
            first_name="Admin",
            last_name="Prueba",
            email="admin-prueba@example.com",
            rol=admin_role,
        )
        self.client.force_login(admin)

    def test_admin_creates_an_active_funcionario_account(self):
        funcionario_role = Rol.objects.get(nombre="fun")
        response = self.client.post(
            reverse("funcionarios:crearFuncionario"),
            {
                "rut": "22222222-2",
                "first_name": "Ana",
                "last_name": "Prueba",
                "email": "ana-prueba@example.com",
                "password1": "Clave-Nueva-2026!",
                "password2": "Clave-Nueva-2026!",
                "rol": str(funcionario_role.pk),
            },
        )

        self.assertRedirects(response, reverse("funcionarios:cuentas"))
        nuevo_funcionario = Funcionario.objects.get(rut="22222222-2")
        self.assertTrue(nuevo_funcionario.is_active)
        self.assertEqual(nuevo_funcionario.rol.nombre, "fun")


class PasswordStorageAndLengthTests(TestCase):
    def test_password_is_hashed_but_eleven_characters_are_accepted(self):
        funcionario_role, _ = Rol.objects.get_or_create(nombre="fun")
        base_data = {
            "first_name": "Paula",
            "last_name": "Prueba",
            "rol": str(funcionario_role.pk),
            "password1": "A!bc1234567",
            "password2": "A!bc1234567",
        }
        eleven_character_form = CrearFuncionarioForm(
            {
                **base_data,
                "rut": "22222222-2",
                "email": "password-once@example.com",
            }
        )
        eight_character_form = CrearFuncionarioForm(
            {
                **base_data,
                "rut": "33333333-3",
                "email": "password-ocho@example.com",
                "password1": "A!bc1234",
                "password2": "A!bc1234",
            }
        )
        seven_character_form = CrearFuncionarioForm(
            {
                **base_data,
                "rut": "44444444-4",
                "email": "password-siete@example.com",
                "password1": "A!bc123",
                "password2": "A!bc123",
            }
        )

        self.assertTrue(eleven_character_form.is_valid(), eleven_character_form.errors)
        self.assertTrue(eight_character_form.is_valid(), eight_character_form.errors)
        self.assertFalse(seven_character_form.is_valid())

        funcionario = eleven_character_form.save()
        funcionario.refresh_from_db()
        self.assertTrue(funcionario.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(funcionario.check_password("A!bc1234567"))
        self.assertNotEqual(funcionario.password, "A!bc1234567")


class DeactivatedFuncionarioHistoryTests(TestCase):
    def setUp(self):
        admin_role, _ = Rol.objects.get_or_create(nombre="adm")
        admin = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Admin-2026!",
            first_name="Admin",
            last_name="Prueba",
            email="admin-historial@example.com",
            rol=admin_role,
        )
        self.client.force_login(admin)
        self.funcionario = Funcionario.objects.create_user(
            rut="22222222-2",
            password="Clave-Funcionario-2026!",
            first_name="Usuario",
            last_name="Historial",
            email="funcionario-historial@example.com",
        )
        alimento = Alimento.objects.create(nombre="Avena", stock="20.00")
        lote = Lote.objects.create(nombre="Lote con historial")
        self.racion = Racion_diaria.objects.create(
            fecha="2026-11-22",
            turno="Mañana",
            lote_id=lote,
            usuario_id=self.funcionario,
        )
        Detalle_racion.objects.create(
            racion_id=self.racion,
            alimento_id=alimento,
            kg="5.00",
        )
        self.movimiento = Movimientos_alimentos.objects.create(
            alimento=alimento,
            cantidad="-5.00",
            usuario=self.funcionario,
            motivo="Consumo de prueba",
        )

    def test_disabling_account_preserves_existing_rations_and_movements(self):
        response = self.client.post(
            reverse(
                "funcionarios:desabilitarFuncionario",
                kwargs={"uuid": self.funcionario.uuid},
            )
        )

        self.assertRedirects(response, reverse("funcionarios:cuentas"))
        self.funcionario.refresh_from_db()
        self.assertFalse(self.funcionario.is_active)
        self.assertEqual(self.racion.usuario_id, self.funcionario)
        self.assertEqual(self.movimiento.usuario, self.funcionario)
        self.assertEqual(Detalle_racion.objects.filter(racion_id=self.racion).count(), 1)


def _raise_test_server_error(request):
    raise RuntimeError("detalle interno confidencial")


urlpatterns = [path("error-de-prueba/", _raise_test_server_error)]


class ProductionErrorResponseTests(TestCase):
    @override_settings(
        ROOT_URLCONF="apps.funcionarios.tests",
        DEBUG=False,
        ALLOWED_HOSTS=["testserver"],
    )
    def test_server_errors_do_not_expose_debug_details_to_client(self):
        client = Client(raise_request_exception=False)

        error_response = client.get("/error-de-prueba/")
        missing_response = client.get("/ruta-inexistente/")

        self.assertEqual(error_response.status_code, 500)
        self.assertNotContains(error_response, "RuntimeError", status_code=500)
        self.assertNotContains(
            error_response,
            "detalle interno confidencial",
            status_code=500,
        )
        self.assertEqual(missing_response.status_code, 404)
        self.assertNotContains(missing_response, "Resolver404", status_code=404)


class FuncionarioTextInjectionTests(TestCase):
    def setUp(self):
        admin_role, _ = Rol.objects.get_or_create(nombre="adm")
        admin = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Admin-2026!",
            first_name="Admin",
            last_name="Seguridad",
            email="admin-seguridad@example.com",
            rol=admin_role,
        )
        self.client.force_login(admin)

    def test_script_in_name_is_stored_as_text_and_html_escaped(self):
        nombre = "<script>alert(1)</script>"
        funcionario_role = Rol.objects.get(nombre="fun")
        response = self.client.post(
            reverse("funcionarios:crearFuncionario"),
            {
                "rut": "22222222-2",
                "first_name": nombre,
                "last_name": "Prueba",
                "email": "script-funcionario@example.com",
                "password1": "Clave-Nueva-2026!",
                "password2": "Clave-Nueva-2026!",
                "rol": str(funcionario_role.pk),
            },
        )

        self.assertRedirects(response, reverse("funcionarios:cuentas"))
        self.assertTrue(Funcionario.objects.filter(first_name=nombre).exists())
        listing = self.client.get(reverse("funcionarios:cuentas"))
        self.assertContains(listing, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(listing, "<script>alert(1)</script>")
