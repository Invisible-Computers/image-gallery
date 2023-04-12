from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Device",
            fields=[
                (
                    "device_id",
                    models.UUIDField(primary_key=True, serialize=False, unique=True),
                ),
                ("owner_id", models.UUIDField()),
                ("is_vertically_oriented", models.BooleanField(default=False)),
            ],
        ),
    ]
