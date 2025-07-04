# Generated by Django 4.2.21 on 2025-06-10 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20)),
                ('service', models.CharField(choices=[('wedding', 'Wedding'), ('portrait', 'Portrait'), ('product', 'Product'), ('event', 'Event')], max_length=50)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
