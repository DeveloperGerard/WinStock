from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve, reverse
from openpyxl import load_workbook

from .views import exportar_excel, obtener_datos_reporte
from apps.alimentos.models import Alimento
from apps.funcionarios.models import Funcionario, Rol
from apps.insumos.models import Categoria, Insumo
from apps.lotes_ganado.models import Lote
from apps.raciones.models import Racion_diaria


class ReportesUrlTests(SimpleTestCase):
    def test_reporte_tiene_url_nombrada(self):
        self.assertEqual(reverse("reportes:index"), "/reportes/")


class ReportesOfflineTemplateTests(SimpleTestCase):
    def test_snapshot_disables_filters_and_export(self):
        request = RequestFactory().get("/reportes/", {"offline_snapshot": "1"})
        request.user = SimpleNamespace(rol=SimpleNamespace(nombre="adm"))
        request.resolver_match = resolve("/reportes/")
        html = render_to_string(
            "reportes/reportes.html",
            {
                "alimentos": [],
                "funcionarios": [],
                "insumos": [],
                "categorias": [],
                "categoria_seleccionada": "",
                "filtro_alimento": "",
                "filtro_funcionario": "",
                "filtro_insumo": "",
                "fecha_generacion": None,
                "insumos_sin_stock": 0,
                "offline_snapshot": True,
            },
            request=request,
        )

        self.assertIn('name="winstock-offline-snapshot"', html)
        self.assertNotIn("Exportar Excel", html)
        self.assertNotIn("<form", html)
        self.assertNotIn("csrfmiddlewaretoken", html)


class ReportesExcelTests(SimpleTestCase):
    def test_exportacion_excel_tiene_tipo_y_nombre(self):
        response = exportar_excel([], [], [])

        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("reporte-winstock-", response["Content-Disposition"])
        self.assertIn(".xlsx", response["Content-Disposition"])
        self.assertGreater(len(response.content), 1000)

    def test_exportacion_excel_incluye_stock_actual_de_alimentos(self):
        alimento = SimpleNamespace(nombre="Avena", stock=Decimal("25.00"))

        response = exportar_excel([alimento], [], [])
        workbook = load_workbook(BytesIO(response.content), data_only=True)

        self.assertEqual(workbook["Alimentos"]["B1"].value, "Stock actual (kg)")
        self.assertEqual(workbook["Alimentos"]["B2"].value, Decimal("25.00"))


class ReportesFiltrosTests(SimpleTestCase):
    def test_busquedas_se_aplican_solo_a_su_categoria(self):
        with (
            patch("apps.reportes.views.Alimento") as alimento_model,
            patch("apps.reportes.views.Funcionario") as funcionario_model,
            patch("apps.reportes.views.Insumo") as insumo_model,
        ):
            alimentos = alimento_model.objects.filter.return_value
            alimentos.order_by.return_value = alimentos

            funcionarios = funcionario_model.objects.filter.return_value
            funcionarios.select_related.return_value = funcionarios
            funcionarios.order_by.return_value = funcionarios

            insumos = insumo_model.objects.select_related.return_value
            insumos.order_by.return_value = insumos

            resultado = obtener_datos_reporte(
                filtro_alimento="avena",
                filtro_funcionario="12345678-9",
                filtro_insumo="filtro",
            )

        self.assertIs(resultado[0], alimentos.filter.return_value)
        self.assertIs(resultado[1], funcionarios.filter.return_value)
        self.assertIs(resultado[2], insumos.filter.return_value)
        alimento_model.objects.filter.assert_called_once_with(estado=True)
        alimentos.filter.assert_called_once_with(nombre__icontains="avena")
        funcionario_model.objects.filter.assert_called_once_with(is_active=True)
        self.assertEqual(funcionarios.filter.call_count, 1)
        self.assertEqual(insumos.filter.call_count, 1)


class ReportInventoryRefreshTests(TestCase):
    def setUp(self):
        admin_role, _ = Rol.objects.get_or_create(nombre="adm")
        admin = Funcionario.objects.create_user(
            rut="11111111-1",
            password="Clave-Admin-2026!",
            first_name="Admin",
            last_name="Reporte",
            email="admin-reporte@example.com",
            rol=admin_role,
        )
        self.client.force_login(admin)
        self.alimento = Alimento.objects.create(nombre="Avena", stock="20.00")
        categoria, _ = Categoria.objects.get_or_create(nombre="Herramientas")
        self.insumo = Insumo.objects.create(
            nombre="Filtro",
            cantidad=5,
            unidad="Unidades",
            categoria=categoria,
        )
        self.lote = Lote.objects.create(nombre="Lote de reporte")

    def test_report_shows_current_stock_after_ration_but_not_adjustment_history(self):
        ration_response = self.client.post(
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
                "detalles-0-kg": "5.00",
            },
        )
        self.assertRedirects(ration_response, reverse("raciones:raciones"))
        self.alimento.refresh_from_db()
        self.assertEqual(self.alimento.stock, Decimal("15.00"))

        response = self.client.get(reverse("reportes:index"))

        self.assertEqual(response.status_code, 200)
        alimento_en_reporte = response.context["alimentos"].get(pk=self.alimento.pk)
        insumo_en_reporte = response.context["insumos"].get(pk=self.insumo.pk)
        self.assertEqual(alimento_en_reporte.stock, Decimal("15.00"))
        self.assertEqual(insumo_en_reporte.cantidad, 5)
        self.assertContains(response, "15")
        self.assertContains(response, "5")
        self.assertNotContains(response, "ajustes de stock registrados")


class ReportSearchInjectionTests(TestCase):
    def test_sql_like_text_is_treated_as_a_literal_search_value(self):
        literal_match = Alimento.objects.create(
            nombre="' OR 1=1 -- Avena",
            stock="10.00",
        )
        other_alimento = Alimento.objects.create(
            nombre="Maíz",
            stock="20.00",
        )

        alimentos, _, _ = obtener_datos_reporte(filtro_alimento="' OR 1=1 --")

        self.assertEqual(list(alimentos), [literal_match])
        self.assertNotIn(other_alimento, alimentos)
