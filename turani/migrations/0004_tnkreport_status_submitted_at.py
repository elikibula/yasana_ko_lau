from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("turani", "0003_tnkreport_toilet_wastewater_challenges_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tnkreport",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("submitted", "Submitted"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="tnkreport",
            name="submitted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
