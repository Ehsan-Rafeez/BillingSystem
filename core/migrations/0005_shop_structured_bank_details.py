from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_shop_invoice_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="bank_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="shop",
            name="bank_account_title",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="shop",
            name="bank_account_number",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="shop",
            name="bank_iban",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="shop",
            name="bank_branch",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="shop",
            name="bank_branch_code",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="shop",
            name="bank_swift_code",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="shop",
            name="bank_payment_instructions",
            field=models.TextField(blank=True),
        ),
    ]
