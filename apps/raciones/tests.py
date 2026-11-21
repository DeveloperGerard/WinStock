from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve
from django.urls import reverse

from apps.funcionarios.models import Funcionario


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
