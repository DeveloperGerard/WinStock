from io import BytesIO
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from apps.alimentos.models import Alimento, Movimientos_alimentos
from apps.funcionarios.decorators import rol_requerido
from apps.funcionarios.models import Funcionario
from apps.insumos.models import Categoria, Insumo
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.paginator import Paginator
from apps.raciones.models import Racion_diaria

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
    filtro_insumo = request.GET.get("insumo_q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()

    estado = request.GET.get("estado", "todos").strip()

    alimentos, insumos = obtener_datos_reporte(
        filtro_alimento=filtro_alimento,
        filtro_insumo=filtro_insumo,
        categoria_id=categoria_id,
        estado=estado,
    )

    if request.GET.get("export") == "xlsx":
        return exportar_excel(alimentos, insumos)

    inicio_mes = timezone.localdate().replace(day=1)

    return render(request, "reportes/reportes.html", {
        "alimentos": alimentos,
        "insumos": insumos,
        "categorias": Categoria.objects.order_by("nombre"),
        "categoria_seleccionada": categoria_id,
        "filtro_alimento": filtro_alimento,
        "filtro_insumo": filtro_insumo,
        "fecha_generacion": timezone.localtime(),
        "estado": estado,
        "alimentos_activos": alimentos.filter(estado=True).count(),
        "alimentos_inactivos": alimentos.filter(estado=False).count(),
        "alimentos_sin_stock": alimentos.filter(estado=True, stock__lte=0).count(),
        "insumos_sin_stock": insumos.filter(cantidad=0).count(),
        "inicio_mes": inicio_mes,
        "raciones_mes": Racion_diaria.objects.filter(fecha__gte=inicio_mes).count(),
        "movimientos_mes": Movimientos_alimentos.objects.filter(
            fecha_movimiento__date__gte=inicio_mes
        ).count(),
        "offline_snapshot": request.GET.get("offline_snapshot") == "1",
    })

def obtener_datos_reporte(filtro_alimento="", filtro_insumo="", categoria_id="", estado="todos"):
    alimentos = Alimento.objects.order_by("-estado", "nombre")  # activos primero
    insumos = Insumo.objects.select_related("categoria").order_by("categoria__nombre", "nombre")

    if estado == "activos":
        alimentos = alimentos.filter(estado=True)
    elif estado == "inactivos":
        alimentos = alimentos.filter(estado=False)

    if filtro_alimento:
        alimentos = alimentos.filter(nombre__icontains=filtro_alimento)

    if filtro_insumo:
        insumos = insumos.filter(
            Q(nombre__icontains=filtro_insumo) | Q(categoria__nombre__icontains=filtro_insumo)
        )

    if categoria_id:
        try:
            insumos = insumos.filter(categoria_id=int(categoria_id))
        except (TypeError, ValueError):
            pass

    return alimentos, insumos



def exportar_excel(alimentos, insumos):
    ahora = timezone.localtime()
    alimentos, insumos = list(alimentos), list(insumos)
    sin_stock = sum(1 for i in insumos if i.cantidad == 0)

    wb = Workbook()
    _hoja_resumen(wb.active, ahora, len(alimentos), len(insumos), sin_stock)

    _crear_hoja(
        wb, "Alimentos",
        ["Nombre", "Stock registrado (kg)", "Estado"],
        [[a.nombre, a.stock, "Activo" if a.estado else "Inactivo"] for a in alimentos],
        resaltar_si=lambda fila: fila[2] == "Inactivo",
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


def _hoja_resumen(ws, ahora, n_alimentos, n_insumos, sin_stock):
    ws.title = "Resumen"
    ws["A1"] = "WINSTOCK · Inventario actual del predio"
    ws["A1"].font = Font(size=16, bold=True, color=COLOR_PRIMARIO)
    ws["A2"] = f"Generado el {ahora:%d/%m/%Y %H:%M}"
    ws["A2"].font = Font(italic=True, color="666666")

    filas = [
        ("Alimentos activos", n_alimentos),
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
        ws.cell(6, 1).fill = ws.cell(6, 2).fill = PatternFill("solid", fgColor=COLOR_ALERTA)

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 12
    ws.sheet_view.showGridLines = False

def _crear_hoja(wb, titulo, encabezados, filas, resaltar_si=None, col_suma=None):
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
            if isinstance(celda.value, datetime):
                celda.number_format = "dd/mm/yyyy hh:mm"
            elif isinstance(celda.value, Decimal):
                celda.number_format = "#,##0.00"
                celda.alignment = Alignment(horizontal="right")
            elif isinstance(celda.value, (int, float)):
                celda.alignment = Alignment(horizontal="right")
        if resaltar_si and resaltar_si(fila):
            for celda in ws[numero]:
                celda.fill = PatternFill("solid", fgColor=COLOR_ALERTA)

    # fila de total
    total = ws.max_row + 1
    ws.cell(total, 1, f"Total de registros: {len(filas)}").font = Font(bold=True)
    if col_suma and filas:
        letra = get_column_letter(col_suma)
        celda = ws.cell(total, col_suma, f"=SUM({letra}2:{letra}{total - 1})")
        celda.font = Font(bold=True)
        celda.number_format = "#,##0.00"
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

def _parse_fecha(valor):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _rango_fechas(request):
    """Por defecto: del día 1 del mes en curso a hoy. Máximo 12 meses."""
    hoy = timezone.localdate()
    desde = _parse_fecha(request.GET.get("desde")) or hoy.replace(day=1)
    hasta = _parse_fecha(request.GET.get("hasta")) or hoy
    if desde > hasta:
        desde, hasta = hasta, desde
    if (hasta - desde).days > 366:
        desde = hasta - timedelta(days=366)
    return desde, hasta


def obtener_movimientos(desde, hasta, alimento_id="", tipo="", motivo=""):
    qs = (
        Movimientos_alimentos.objects
        .select_related("alimento", "usuario")
        .filter(fecha_movimiento__date__range=(desde, hasta))
    )
    if alimento_id.isdigit():
        qs = qs.filter(alimento_id=int(alimento_id))
    if tipo == "entradas":
        qs = qs.filter(cantidad__gt=0)
    elif tipo == "salidas":
        qs = qs.filter(cantidad__lt=0)
    if motivo:
        qs = qs.filter(motivo__icontains=motivo)

    resumen = (
        qs.order_by()
        .values("alimento__nombre")
        .annotate(
            entradas=Sum("cantidad", filter=Q(cantidad__gt=0), default=Decimal("0")),
            salidas=Sum("cantidad", filter=Q(cantidad__lt=0), default=Decimal("0")),
            neto=Sum("cantidad", default=Decimal("0")),
        )
        .order_by("alimento__nombre")
    )
    return qs.order_by("-fecha_movimiento", "-id"), list(resumen)


@rol_requerido("adm")
def movimientos(request):
    desde, hasta = _rango_fechas(request)
    alimento_id = request.GET.get("alimento", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    motivo = request.GET.get("motivo", "").strip()

    qs, resumen = obtener_movimientos(desde, hasta, alimento_id, tipo, motivo)

    if request.GET.get("export") == "xlsx":
        return exportar_movimientos(qs, resumen, desde, hasta)

    params = request.GET.copy()
    params.pop("page", None)
    params.pop("export", None)

    return render(request, "reportes/movimientos.html", {
        "page_obj": Paginator(qs, 50).get_page(request.GET.get("page")),
        "resumen": resumen,
        "alimentos": Alimento.objects.order_by("nombre"),
        "desde": desde, "hasta": hasta,
        "alimento_seleccionado": alimento_id,
        "tipo": tipo, "motivo": motivo,
        "querystring": params.urlencode(),
        "fecha_generacion": timezone.localtime(),
    })


def exportar_movimientos(qs, resumen, desde, hasta):
    ahora = timezone.localtime()
    movimientos_lista = list(qs)

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen"
    ws["A1"] = "WINSTOCK · Movimientos de alimentos"
    ws["A1"].font = Font(size=16, bold=True, color=COLOR_PRIMARIO)
    ws["A2"] = f"Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}"
    ws["A3"] = f"Generado el {ahora:%d/%m/%Y %H:%M}"
    ws["A3"].font = Font(italic=True, color="666666")
    ws.column_dimensions["A"].width = 40
    ws.sheet_view.showGridLines = False

    _crear_hoja(
        wb, "Movimientos",
        ["Fecha", "Alimento", "Cantidad (kg)", "Motivo", "Usuario"],
        [
            [
                timezone.localtime(m.fecha_movimiento).replace(tzinfo=None),
                m.alimento.nombre,
                m.cantidad,
                m.motivo or "",
                m.usuario.full_name,
            ]
            for m in movimientos_lista
        ],
        col_suma=3,
    )
    _crear_hoja(
        wb, "Por alimento",
        ["Alimento", "Entradas (kg)", "Salidas (kg)", "Saldo neto (kg)"],
        [[r["alimento__nombre"], r["entradas"], r["salidas"], r["neto"]] for r in resumen],
    )

    buffer = BytesIO()
    wb.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="movimientos-winstock-{desde:%Y%m%d}-{hasta:%Y%m%d}.xlsx"'
    )
    return response