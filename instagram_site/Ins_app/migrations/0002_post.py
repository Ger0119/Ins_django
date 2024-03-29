# Generated by Django 4.1.2 on 2022-10-28 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Ins_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("like", models.IntegerField(verbose_name="Like")),
                ("comment", models.IntegerField(verbose_name="Comment")),
                ("count", models.IntegerField(verbose_name="Post Count")),
                ("label", models.CharField(max_length=100, verbose_name="Post Date")),
            ],
        ),
    ]
