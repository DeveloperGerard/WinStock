from django.conf import settings
from django.db import migrations

INVENTARIOS = [("alimentos", "Alimentos"), ("insumos", "Insumos"), ("lotes", "Lotes")]


def precrear(apps, schema_editor):
    Inventario = apps.get_model("inventarios", "Inventario")
    Usuario = apps.get_model(settings.AUTH_USER_MODEL)
    no_admins = list(Usuario.objects.exclude(rol__nombre="adm"))
    for clave, nombre in INVENTARIOS:
        inv, _ = Inventario.objects.get_or_create(clave=clave, defaults={"nombre": nombre})
        inv.usuarios.add(*no_admins)


class Migration(migrations.Migration):
    dependencies = [("inventarios", "0001_initial")]
    operations = [migrations.RunPython(precrear, migrations.RunPython.noop)]