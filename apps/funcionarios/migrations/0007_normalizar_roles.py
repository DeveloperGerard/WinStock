from django.db import migrations


def normalizar_roles(apps, schema_editor):
    Rol = apps.get_model("funcionarios", "Rol")
    Funcionario = apps.get_model("funcionarios", "Funcionario")
    db_alias = schema_editor.connection.alias

    rol_admin, _ = Rol.objects.using(db_alias).get_or_create(nombre="adm")
    rol_funcionario, _ = Rol.objects.using(db_alias).get_or_create(nombre="fun")

    for nombre_antiguo, rol_actual in (
        ("Admin", rol_admin),
        ("Func", rol_funcionario),
    ):
        roles_antiguos = Rol.objects.using(db_alias).filter(nombre=nombre_antiguo)
        for rol_antiguo in roles_antiguos:
            Funcionario.objects.using(db_alias).filter(
                rol_id=rol_antiguo.pk
            ).update(rol_id=rol_actual.pk)
            rol_antiguo.delete(using=db_alias)

    Funcionario.objects.using(db_alias).filter(is_superuser=True).update(
        rol_id=rol_admin.pk
    )
    Funcionario.objects.using(db_alias).filter(rol__isnull=True).update(
        rol_id=rol_funcionario.pk
    )


def restaurar_roles_antiguos(apps, schema_editor):
    Rol = apps.get_model("funcionarios", "Rol")
    Funcionario = apps.get_model("funcionarios", "Funcionario")
    db_alias = schema_editor.connection.alias

    rol_admin, _ = Rol.objects.using(db_alias).get_or_create(nombre="Admin")
    rol_funcionario, _ = Rol.objects.using(db_alias).get_or_create(nombre="Func")
    rol_admin_actual = Rol.objects.using(db_alias).get(nombre="adm")

    Funcionario.objects.using(db_alias).filter(is_superuser=True).update(
        rol_id=rol_funcionario.pk
    )
    Funcionario.objects.using(db_alias).filter(
        is_superuser=False, rol_id=rol_admin_actual.pk
    ).update(rol_id=rol_admin.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("funcionarios", "0006_alter_funcionario_rol"),
    ]

    operations = [
        migrations.RunPython(normalizar_roles, restaurar_roles_antiguos),
    ]
