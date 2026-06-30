from django.db import migrations


ROLE_GROUPS = (
    "turaga_ni_koro",
    "mata_ni_tikina",
    "liuliu_ni_yavusa",
    "roko_admin",
)


def create_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for group_name in ROLE_GROUPS:
        Group.objects.get_or_create(name=group_name)


def remove_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=ROLE_GROUPS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_userprofile"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_role_groups, remove_role_groups),
    ]
