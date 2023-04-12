from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OneTimeToken",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("owner_id", models.UUIDField(unique=True)),
                ("expiration_time", models.DateTimeField()),
                ("token", models.CharField(max_length=100)),
            ],
        ),
    ]
