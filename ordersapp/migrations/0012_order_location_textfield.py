from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ordersapp", "0011_menuitem_pricing_unit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="location",
            field=models.TextField(blank=True, null=True),
        ),
    ]
