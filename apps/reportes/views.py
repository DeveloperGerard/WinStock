from io import BytesIO

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from apps.alimentos.models import Alimento
from apps.funcionarios.decorators import rol_requerido
from apps.funcionarios.models import Funcionario
from apps.insumos.models import Categoria, Insumo

COLOR_PRIMARIO = "2E7D32"   # verde del sidebar, cámbialo si quieres
COLOR_ALERTA = "FDE2E2"
BORDE = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    top=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)


@rol_requerido("adm")
def index(request):
    filtro_alimento = request.GET.get("alimento_q", "").strip()
    filtro_funcionario = request.GET.get("funcionario_q", "").strip()
    filtro_insumo = request.GET.get("insumo_q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()

    alimentos, funcionarios, insumos = obtener_datos_reporte(
        filtro_alimento=filtro_alimento,
        filtro_funcionario=filtro_funcionario,
        filtro_insumo=filtro_insumo,
        categoria_id=categoria_id,
    )

    export = request.GET.get("export")
    if export == "xlsx":
        return exportar_excel(alimentos, funcionarios, insumos)

    return render(
        request,
        "reportes/reportes.html",
        {
            "alimentos": alimentos,
            "funcionarios": funcionarios,
            "insumos": insumos,
            "categorias": Categoria.objects.order_by("nombre"),
            "categoria_seleccionada": categoria_id,
            "filtro_alimento": filtro_alimento,
            "filtro_funcionario": filtro_funcionario,
            "filtro_insumo": filtro_insumo,
            "fecha_generacion": timezone.localtime(),
            "insumos_sin_stock": insumos.filter(cantidad=0).count(),
            "offline_snapshot": request.GET.get("offline_snapshot") == "1",
        },
    )


def obtener_datos_reporte(
    filtro_alimento="",
    filtro_funcionario="",
    filtro_insumo="",
    categoria_id="",
):
    alimentos = Alimento.objects.filter(estado=True).order_by("nombre")
    funcionarios = (
        Funcionario.objects.filter(is_active=True)
        .select_related("rol")
        .order_by("last_name", "first_name")
    )
    insumos = Insumo.objects.select_related("categoria").order_by(
        "categoria__nombre", "nombre"
    )

    if filtro_alimento:
        alimentos = alimentos.filter(nombre__icontains=filtro_alimento)

    if filtro_funcionario:
        funcionarios = funcionarios.filter(
            Q(first_name__icontains=filtro_funcionario)
            | Q(last_name__icontains=filtro_funcionario)
            | Q(rut__icontains=filtro_funcionario)
            | Q(email__icontains=filtro_funcionario)
        )

    if filtro_insumo:
        insumos = insumos.filter(
            Q(nombre__icontains=filtro_insumo)
            | Q(categoria__nombre__icontains=filtro_insumo)
        )

    if categoria_id:
        try:
            insumos = insumos.filter(categoria_id=int(categoria_id))
        except (TypeError, ValueError):
            pass

    return alimentos, funcionarios, insumos



def exportar_excel(alimentos, funcionarios, insumos):
    ahora = timezone.localtime()
    alimentos, funcionarios, insumos = list(alimentos), list(funcionarios), list(insumos)
    sin_stock = sum(1 for i in insumos if i.cantidad == 0)

    wb = Workbook()
    _hoja_resumen(wb.active, ahora, len(alimentos), len(funcionarios), len(insumos), sin_stock)

    _crear_hoja(
        wb, "Alimentos",
        ["Nombre", "Stock registrado", "Estado"],
        [[a.nombre, a.stock_registrado, "Activo"] for a in alimentos],
    )
    _crear_hoja(
        wb, "Funcionarios",
        ["Nombre completo", "RUT", "Correo", "Rol", "Estado"],
        [
            [
                f.full_name,
                f.rut,
                f.email,
                f.rol.get_nombre_display() if f.rol else "Sin rol",
                "Activo",
            ]
            for f in funcionarios
        ],
    )
    _crear_hoja(
        wb, "Insumos",
        ["Nombre", "Categoría", "Cantidad", "Unidad", "Estado"],
        [
            [
                i.nombre,
                i.categoria.nombre if i.categoria else "Sin categoría",
                i.cantidad,
                i.get_unidad_display(),
                "Sin stock" if i.cantidad == 0 else "Disponible",
            ]
            for i in insumos
        ],
        resaltar_si=lambda fila: fila[2] == 0,
    )

    buffer = BytesIO()
    wb.save(buffer)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="reporte-winstock-{ahora:%Y-%m-%d}.xlsx"'
    )
    return response


def _hoja_resumen(ws, ahora, n_alimentos, n_funcionarios, n_insumos, sin_stock):
    ws.title = "Resumen"
    ws["A1"] = "WINSTOCK · Reporte actual del predio"
    ws["A1"].font = Font(size=16, bold=True, color=COLOR_PRIMARIO)
    ws["A2"] = f"Generado el {ahora:%d/%m/%Y %H:%M}"
    ws["A2"].font = Font(italic=True, color="666666")

    filas = [
        ("Alimentos activos", n_alimentos),
        ("Funcionarios activos", n_funcionarios),
        ("Insumos registrados", n_insumos),
        ("Insumos sin stock", sin_stock),
    ]
    for idx, (etiqueta, valor) in enumerate(filas, start=4):
        ws.cell(idx, 1, etiqueta).font = Font(bold=True)
        celda = ws.cell(idx, 2, valor)
        celda.alignment = Alignment(horizontal="center")
        for c in (ws.cell(idx, 1), celda):
            c.border = BORDE
    if sin_stock:
        ws.cell(7, 1).fill = ws.cell(7, 2).fill = PatternFill("solid", fgColor=COLOR_ALERTA)

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 12
    ws.sheet_view.showGridLines = False


def _crear_hoja(wb, titulo, encabezados, filas, resaltar_si=None):
    ws = wb.create_sheet(titulo)
    ws.append(encabezados)

    for celda in ws[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=COLOR_PRIMARIO)
        celda.alignment = Alignment(horizontal="center", vertical="center")
        celda.border = BORDE
    ws.row_dimensions[1].height = 22

    for fila in filas:
        ws.append(fila)
        numero = ws.max_row
        for celda in ws[numero]:
            celda.border = BORDE
            if isinstance(celda.value, (int, float)):
                celda.alignment = Alignment(horizontal="right")
        if resaltar_si and resaltar_si(fila):
            for celda in ws[numero]:
                celda.fill = PatternFill("solid", fgColor=COLOR_ALERTA)

    # fila de total
    total = ws.max_row + 1
    ws.cell(total, 1, "TOTAL").font = Font(bold=True)
    ws.cell(total, 2, len(filas)).font = Font(bold=True)
    for celda in ws[total]:
        celda.fill = PatternFill("solid", fgColor="E8F5E9")
        celda.border = BORDE

    # ajustar ancho de columnas al contenido
    for col in range(1, len(encabezados) + 1):
        ancho = max(len(str(c.value or "")) for c in ws[get_column_letter(col)])
        ws.column_dimensions[get_column_letter(col)].width = min(ancho + 4, 45)

    ws.freeze_panes = "A2"
    if filas:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(encabezados))}{len(filas) + 1}"