from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .forms import LoteForm
from .models import Lote
from apps.inventarios.acceso import inventario_requerido


@login_required
@inventario_requerido("lotes")
def lista_lotes(request):
    offline_snapshot = request.GET.get('offline_snapshot') == '1'
    lotes = Lote.objects.all().order_by('-activo', 'nombre')

    # Filtros opcionales: ?q=texto&estado=activos|inactivos
    q = '' if offline_snapshot else request.GET.get('q', '').strip()
    estado = '' if offline_snapshot else request.GET.get('estado', '')

    if q:
        lotes = lotes.filter(nombre__icontains=q)
    if estado == 'activos':
        lotes = lotes.filter(activo=True)
    elif estado == 'inactivos':
        lotes = lotes.filter(activo=False)

    return render(request, 'lista_lotes.html', {
        'lotes': lotes,
        'q': q,
        'estado': estado,
        'offline_snapshot': offline_snapshot,
    })


@login_required
@inventario_requerido("lotes")
def crear_lote(request):
    if request.method == 'POST':
        form = LoteForm(request.POST)
        if form.is_valid():
            lote = form.save()
            messages.success(request, f'Lote "{lote.nombre}" creado correctamente.')
            return redirect('ganado:lotes')
    else:
        form = LoteForm()

    return render(request, 'ingresar_lote.html', {
        'form': form,
        'titulo': 'Nuevo lote',
    })

@login_required
@inventario_requerido("lotes")
def editar_lote(request, uuid):
    lote = get_object_or_404(Lote, uuid=uuid)

    if request.method == 'POST':
        form = LoteForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lote actualizado correctamente.')
            return redirect('ganado:lotes')
    else:
        form = LoteForm(instance=lote)

    return render(request, 'ingresar_lote.html', {
        'form': form,
        'lote': lote,
        'titulo': 'Editar lote',
    })


@login_required
@require_POST
@inventario_requerido("lotes")
def cambiar_estado_lote(request, uuid):
    """Habilita o deshabilita el lote (borrado lógico)."""
    lote = get_object_or_404(Lote, uuid=uuid)
    lote.activo = not lote.activo
    lote.save(update_fields=['activo'])

    estado = 'habilitado' if lote.activo else 'deshabilitado'
    messages.success(request, f'Lote "{lote.nombre}" {estado}.')
    return redirect('ganado:lotes')


@login_required
@inventario_requerido("lotes")
def eliminar_lote(request, uuid):
    """Borrado real, con página de confirmación (GET) y borrado (POST)."""
    lote = get_object_or_404(Lote, uuid=uuid)

    if request.method == 'POST':
        nombre = lote.nombre
        lote.delete()
        messages.success(request, f'Lote "{nombre}" eliminado.')
        return redirect('ganado:lotes')

    return render(request, 'eliminar_lote.html', {'lote': lote})