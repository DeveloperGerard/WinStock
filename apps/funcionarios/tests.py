from django import forms
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class LoginPWATemplateTests(SimpleTestCase):
    def test_login_page_links_manifest_and_registers_service_worker(self):
        html = render_to_string("forms/inifunc.html", {"form": forms.Form()})

        self.assertIn('rel="manifest" href="/static/manifest.webmanifest"', html)
        self.assertIn('navigator.serviceWorker.register("/service-worker.js")', html)
