from django.shortcuts import render
from .models import Alimento


def Registraralimentos(request):
    alimentos = Alimento.objects.all()
    return render(request, 'alimentos/registrar_alimentos.html', {'alimentos': alimentos})

def Editaralimentos(request):
    alimentos = Alimento.objects.all()
    return render(request, 'alimentos/editar_alimentos.html', {'alimentos': alimentos})

def desabilitar_alimentos(request):
    alimentos = Alimento.objects.all()
    return render(request, 'alimentos/deshabilitar_alimentos.html', {'alimentos': alimentos})

def modificar_alimentos(request):
    alimentos = Alimento.objects.all()
    return render(request, 'alimentos/modificar_alimentos.html', {'alimentos': alimentos})

def quedastock(request):
    alimentos = Alimento.objects.all()
    return render(request, 'alimentos/quedastock.html', {'alimentos': alimentos})