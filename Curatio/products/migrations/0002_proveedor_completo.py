# Generated manually - Actualiza Proveedor al nuevo esquema

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def set_nit_unico(apps, schema_editor):
    """Asigna NIT único a cada proveedor existente."""
    Proveedor = apps.get_model("products", "Proveedor")
    for i, p in enumerate(Proveedor.objects.all(), start=1):
        p.nit = f"0000000{i}-{i % 10}" if i < 10 else f"000000{i}-{i % 10}"
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="proveedor",
            name="nit",
            field=models.CharField(max_length=12, null=True),
        ),
        migrations.AddField(
            model_name="proveedor",
            name="razon_social",
            field=models.CharField(default="", max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proveedor",
            name="nombre_contacto",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proveedor",
            name="telefono_contacto",
            field=models.CharField(default="", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proveedor",
            name="correo_contacto",
            field=models.EmailField(default="noreply@temp.com", max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proveedor",
            name="direccion",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="proveedor",
            name="ciudad",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="proveedor",
            name="estado",
            field=models.CharField(
                choices=[("Activo", "Activo"), ("Inactivo", "Inactivo")],
                default="Activo",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="proveedor",
            name="creado_por",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proveedor",
            name="creado_en",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.RunPython(set_nit_unico, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="proveedor",
            name="nit",
            field=models.CharField(max_length=12, unique=True),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="nombre",
            field=models.CharField(max_length=120),
        ),
        migrations.RemoveField(
            model_name="proveedor",
            name="activo",
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="creado_en",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
