# Generated by Django 5.1.3 on 2025-01-07 18:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proiect', '0010_alter_produs_stoc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='produs',
            name='stoc',
        ),
    ]
