from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse
from openpyxl import load_workbook

from .views import exportar_excel, obtener_datos_reporte


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
