from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_shop_subscription_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="invoice_shop_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="shop",
            name="invoice_logo",
            field=models.FileField(blank=True, upload_to="shop_logos/"),
        ),
        migrations.AddField(
            model_name="shop",
            name="invoice_bank_details",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="shop",
            name="show_invoice_shop_name",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="shop",
            name="show_invoice_logo",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="shop",
            name="show_invoice_bank_details",
            field=models.BooleanField(default=True),
        ),
    ]
