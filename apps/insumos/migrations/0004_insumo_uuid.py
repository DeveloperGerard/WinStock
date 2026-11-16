import uuid

from django.db import migrations, models


def populate_insumo_uuids(apps, schema_editor):
    Insumo = apps.get_model("insumos", "Insumo")
    for insumo in Insumo.objects.filter(uuid__isnull=True).iterator():
        insumo.uuid = uuid.uuid4()
        insumo.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("insumos", "0003_alter_insumo_cantidad"),
    ]

    operations = [
        migrations.AddField(
            model_name="insumo",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.RunPython(populate_insumo_uuids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="insumo",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
