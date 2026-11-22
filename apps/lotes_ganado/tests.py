from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve


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
