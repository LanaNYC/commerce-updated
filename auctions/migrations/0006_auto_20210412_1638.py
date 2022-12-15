# Generated by Django 3.1.4 on 2021-04-12 16:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0005_listings_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listings',
            name='category',
        ),
        migrations.AddField(
            model_name='listings',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='auctions.categories'),
        ),
    ]