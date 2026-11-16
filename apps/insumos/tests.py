from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from .views import crear_insumo


class CrearInsumoViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse("insumos:crear")

    @patch("apps.insumos.views.InsumoForm")
    def test_valid_post_saves_and_redirects_to_inventory(self, form_class):
        form = form_class.return_value
        form.is_valid.return_value = True
        request = self.factory.post(self.url, {"nombre": "Filtro hidráulico"})
        request.user = SimpleNamespace(is_authenticated=True)

        response = crear_insumo(request)

        form.save.assert_called_once_with()
        self.assertRedirects(
            response,
            reverse("insumos:lista"),
            fetch_redirect_response=False,
        )

    @patch("apps.insumos.views.InsumoForm")
    def test_invalid_post_renders_form_without_saving(self, form_class):
        form = form_class.return_value
        form.is_valid.return_value = False
        request = self.factory.post(self.url, {})
        request.user = SimpleNamespace(is_authenticated=True)

        response = crear_insumo(request)

        form.save.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registrar insumo")
