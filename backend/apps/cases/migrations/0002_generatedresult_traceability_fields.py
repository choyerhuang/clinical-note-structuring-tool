from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="generatedresult",
            name="generation_warnings",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="generatedresult",
            name="mcg_result",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="generatedresult",
            name="verification_result",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
