from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse

from .views import exportar_excel, obtener_datos_reporte


class ReportesUrlTests(SimpleTestCase):
    def test_reporte_tiene_url_nombrada(self):
        self.assertEqual(reverse("reportes:index"), "/reportes/")


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
