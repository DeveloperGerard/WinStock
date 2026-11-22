from types import SimpleNamespace

from django import forms
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve


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

    def test_base_template_leaves_installation_to_the_browser(self):
        request = RequestFactory().get("/")
        request.user = SimpleNamespace(rol=SimpleNamespace(nombre="adm"))
        request.resolver_match = resolve("/")
        html = render_to_string("base.html", {"request": request}, request=request)

        self.assertIn('rel="manifest" href="/static/manifest.webmanifest"', html)
        self.assertNotIn("Instalar WinStock", html)
        self.assertNotIn("beforeinstallprompt", html)

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
