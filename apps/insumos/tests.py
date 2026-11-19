import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from .views import InsumoDeleteView, crear_insumo, lista_insumos


class ListaInsumosTests(SimpleTestCase):
    def test_selected_category_filters_inventory(self):
        request = RequestFactory().get("/insumos/", {"categoria": "3"})
        request.user = SimpleNamespace(is_authenticated=True)
        categoria = object()

        with (
            patch("apps.insumos.views.Insumo") as insumo_model,
            patch("apps.insumos.views.FiltroCategoriaForm") as form_class,
            patch("apps.insumos.views.render") as render,
        ):
            queryset = insumo_model.objects.select_related.return_value
            queryset.order_by.return_value = queryset
            form = form_class.return_value
            form.is_valid.return_value = True
            form.cleaned_data = {"categoria": categoria}

            lista_insumos(request)

        queryset.filter.assert_called_once_with(categoria=categoria)
        self.assertTrue(render.call_args.args[2]["categoria_seleccionada"])


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


class InsumoDeleteViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.uuid = uuid.uuid4()
        self.url = reverse("insumos:eliminar", kwargs={"uuid": self.uuid})
        self.insumo = SimpleNamespace(nombre="Filtro hidráulico", delete=Mock())

    def test_get_displays_confirmation_without_deleting(self):
        request = self.factory.get(self.url)
        request.user = SimpleNamespace(is_authenticated=True)

        with patch.object(InsumoDeleteView, "get_object", return_value=self.insumo):
            response = InsumoDeleteView.as_view()(request, uuid=self.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Esta acción no se puede deshacer.")
        self.insumo.delete.assert_not_called()

    def test_post_deletes_and_redirects_to_inventory(self):
        request = self.factory.post(self.url)
        request.user = SimpleNamespace(is_authenticated=True)

        with patch.object(InsumoDeleteView, "get_object", return_value=self.insumo):
            response = InsumoDeleteView.as_view()(request, uuid=self.uuid)

        self.insumo.delete.assert_called_once_with()
        self.assertRedirects(
            response,
            reverse("insumos:lista"),
            fetch_redirect_response=False,
        )
