from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ordersapp", "0009_tenant_shop_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="menucategory",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AddConstraint(
            model_name="menucategory",
            constraint=models.UniqueConstraint(
                fields=("shop", "name"),
                name="unique_menu_category_per_shop",
            ),
        ),
    ]
