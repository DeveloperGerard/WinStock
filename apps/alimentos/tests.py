from django.test import TestCase
from django.urls import reverse

from .models import Alimento


class AlimentosViewsTests(TestCase):
    def test_inicio_muestra_plantilla_de_alimentos(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "alimentos/alimentos.html")
        self.assertContains(response, "alimentos/alimentos.css")

    def test_crear_alimento(self):
        response = self.client.post(
            reverse("alimentos:crearalimentos"),
            {"nombre": "Avena", "stock_registrado": "25 kg"},
        )

        self.assertRedirects(response, reverse("alimentos:crearalimentos"))
        self.assertTrue(
            Alimento.objects.filter(nombre="Avena", stock_registrado="25 kg").exists()
        )

    def test_modificar_alimento(self):
        alimento = Alimento.objects.create(nombre="Avena", stock_registrado="10 kg")

        page = self.client.get(
            reverse("alimentos:modificar_alimentos", args=[alimento.pk])
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "alimentos/alimentos.css")

        response = self.client.post(
            reverse("alimentos:modificar_alimentos", args=[alimento.pk]),
            {"nombre": "Maíz", "stock_registrado": "15 kg"},
        )

        self.assertRedirects(response, reverse("alimentos:editar_alimentos"))
        alimento.refresh_from_db()
        self.assertEqual(alimento.nombre, "Maíz")
        self.assertEqual(alimento.stock_registrado, "15 kg")

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
        Alimento.objects.create(nombre="Avena", stock_registrado="25 kg")
        Alimento.objects.create(nombre="Maíz", estado=False)

        response = self.client.get(reverse("alimentos:quedastock"))

        self.assertContains(response, "Avena")
        self.assertContains(response, "25 kg")
        self.assertNotContains(response, "Maíz")
        self.assertContains(response, "alimentos/alimentos.css")
