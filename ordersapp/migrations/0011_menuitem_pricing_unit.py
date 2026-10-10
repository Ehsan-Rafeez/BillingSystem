from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ordersapp", "0010_menu_category_shop_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="menuitem",
            name="pricing_unit",
            field=models.CharField(
                choices=[
                    ("head", "Per head"),
                    ("kg", "Per kg"),
                    ("daig", "Per daig"),
                    ("plate", "Per plate"),
                    ("piece", "Per piece"),
                    ("package", "Per package"),
                ],
                default="head",
                max_length=20,
            ),
        ),
    ]
