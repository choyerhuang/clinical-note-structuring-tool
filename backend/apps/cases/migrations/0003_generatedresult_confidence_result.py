from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0002_generatedresult_traceability_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="generatedresult",
            name="confidence_result",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
