from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_apitoken"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="subscription_plan",
            field=models.CharField(
                choices=[("basic", "Basic"), ("standard", "Standard"), ("premium", "Premium")],
                default="basic",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="shop",
            name="subscription_status",
            field=models.CharField(
                choices=[
                    ("trial", "Trial"),
                    ("active", "Active"),
                    ("past_due", "Past due"),
                    ("suspended", "Suspended"),
                    ("cancelled", "Cancelled"),
                ],
                default="trial",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="shop",
            name="subscription_starts_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="shop",
            name="subscription_expires_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="shop",
            name="subscription_notes",
            field=models.TextField(blank=True),
        ),
    ]
