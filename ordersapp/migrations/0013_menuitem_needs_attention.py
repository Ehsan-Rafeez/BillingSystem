from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ordersapp", "0012_order_location_textfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="menuitem",
            name="needs_attention",
            field=models.BooleanField(default=False),
        ),
    ]
