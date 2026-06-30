"""
Usage: python manage.py load_lau_data

Creates the 13 official Tikina and 72 Koro from the Lau Provincial Council
register. Safe to run multiple times.
"""

from django.core.management.base import BaseCommand

from koro.models import Koro
from tikina.models import Tikina


LAU_DATA = [
    {
        "number": 1,
        "name": "LAKEBA",
        "koro_turaga": "TUBOU",
        "island_group": "Central Lau",
        "koro": [
            ("TUBOU", True, ""),
            ("NASAQALAU", False, ""),
            ("VAKANO", False, ""),
            ("YADRANA", False, ""),
            ("NUKUNUKU", False, ""),
            ("WAITABU", False, ""),
            ("WACIWACI", False, ""),
            ("LEVUKA", False, ""),
        ],
    },
    {
        "number": 2,
        "name": "NAYAU",
        "koro_turaga": "NAROCIVO",
        "island_group": "Central Lau",
        "koro": [("NAROCIVO", True, ""), ("SALIA", False, ""), ("LIKU", False, "")],
    },
    {
        "number": 3,
        "name": "ONEATA",
        "koro_turaga": "WAIQORI",
        "island_group": "Northern Lau",
        "koro": [("WAIQORI", True, ""), ("DAKUILOA", False, "")],
    },
    {
        "number": 4,
        "name": "MOCE",
        "koro_turaga": "NASAU",
        "island_group": "Central Lau",
        "koro": [("NASAU", True, ""), ("KOROTOLU", False, "")],
    },
    {
        "number": 5,
        "name": "KABARA",
        "koro_turaga": "NAIKELEYAGA",
        "island_group": "Southern Lau",
        "koro": [
            ("NAIKELEYAGA", True, ""),
            ("TOKALAU", False, ""),
            ("LOMATI", False, ""),
            ("UDU", False, ""),
            ("KOMO", False, ""),
            ("NAMUKA", False, ""),
        ],
    },
    {
        "number": 6,
        "name": "FULAGA",
        "koro_turaga": "MUANAICAKE",
        "island_group": "Southern Lau",
        "koro": [
            ("MUANAICAKE", True, ""),
            ("MUANAIRA", False, ""),
            ("NAIVIDAMU", False, ""),
            ("OGEA", False, ""),
        ],
    },
    {
        "number": 7,
        "name": "ONO-I-LAU",
        "koro_turaga": "NUKUNI",
        "island_group": "Southern Lau",
        "koro": [
            ("NUKUNI", True, ""),
            ("MATOKANA", False, ""),
            ("LOVONI", False, ""),
            ("DOI", False, ""),
            ("VATOA", False, ""),
        ],
    },
    {
        "number": 8,
        "name": "LOMALOMA",
        "koro_turaga": "LOMALOMA",
        "island_group": "Northern Lau",
        "koro": [
            ("LOMALOMA", True, ""),
            ("SAWANA", False, ""),
            ("NAROCIVO", False, ""),
            ("SUSUI", False, ""),
            ("DAKUILOMALOMA", False, ""),
            ("URUONE", False, ""),
            ("LEVUKANA", False, ""),
            ("NAMALATA", False, ""),
            ("TUVUCA", False, ""),
        ],
    },
    {
        "number": 9,
        "name": "MUALEVU",
        "koro_turaga": "MUALEVU",
        "island_group": "Northern Lau",
        "koro": [
            ("MUALEVU", True, ""),
            ("MAVANA", False, ""),
            ("DALICONI", False, ""),
            ("MUAMUA", False, ""),
            ("MALAKA", False, ""),
            ("BOITACI", False, ""),
            ("CIKOBIA", False, ""),
            ("AVEA", False, ""),
        ],
    },
    {
        "number": 10,
        "name": "CICIA",
        "koro_turaga": "TARUKUA",
        "island_group": "Central Lau",
        "koro": [
            ("TARUKUA", True, ""),
            ("MABULA", False, ""),
            ("NACEVA", False, ""),
            ("NATOKALAU", False, ""),
            ("LOMATI", False, ""),
        ],
    },
    {
        "number": 11,
        "name": "MOALA",
        "koro_turaga": "NAROI",
        "island_group": "Central Lau",
        "koro": [
            ("NAROI", True, ""),
            ("KETEIRA", False, ""),
            ("VUNUKU", False, ""),
            ("MALOKU", False, ""),
            ("CAKOVA", False, ""),
            ("VADRA", False, ""),
            ("MUAIKACUNI", False, ""),
            ("NASOKI", False, ""),
        ],
    },
    {
        "number": 12,
        "name": "MATUKU",
        "koro_turaga": "YAROI",
        "island_group": "Central Lau",
        "koro": [
            ("YAROI", True, ""),
            ("MAKADRU", False, ""),
            ("QALIKARUA", False, ""),
            ("LEVUKAIDAKU", False, ""),
            ("RAVIRAVI", False, ""),
            ("LOMATI", False, ""),
            ("NATOKALAU", False, ""),
        ],
    },
    {
        "number": 13,
        "name": "TOTOYA",
        "koro_turaga": "TOVU",
        "island_group": "Central Lau",
        "koro": [
            ("TOVU", True, ""),
            ("KETEI", False, ""),
            ("DRAVUWALU", False, ""),
            ("UDU", False, ""),
            ("TAIRA", False, "VANUAVATU"),
        ],
    },
]


class Command(BaseCommand):
    help = "Load official Lau Tikina and Koro data"

    def handle(self, *args, **kwargs):
        for tikina_data in LAU_DATA:
            tikina, created = Tikina.objects.get_or_create(
                number=tikina_data["number"],
                defaults={
                    "name": tikina_data["name"],
                    "koro_turaga": tikina_data["koro_turaga"],
                    "official_koro_count": len(tikina_data["koro"]),
                    "island_group": tikina_data["island_group"],
                },
            )
            tikina.name = tikina_data["name"]
            tikina.koro_turaga = tikina_data["koro_turaga"]
            tikina.official_koro_count = len(tikina_data["koro"])
            tikina.island_group = tikina_data["island_group"]
            tikina.save()

            action = "Created" if created else "Updated"
            self.stdout.write(f"{action}: Tikina {tikina.number}. {tikina.name}")

            for koro_name, is_turaga, notes in tikina_data["koro"]:
                if is_turaga:
                    tikina.koro.filter(is_koro_turaga=True).exclude(name=koro_name).update(is_koro_turaga=False)

                koro, k_created = Koro.objects.get_or_create(
                    name=koro_name,
                    tikina=tikina,
                    defaults={"is_koro_turaga": is_turaga, "notes": notes},
                )
                koro.is_koro_turaga = is_turaga
                koro.notes = notes
                koro.save()

                k_action = "  + Created" if k_created else "  . Updated"
                turaga_flag = " [Koro Turaga]" if is_turaga else ""
                note = f" ({notes})" if notes else ""
                self.stdout.write(f"{k_action}: {koro.name}{note}{turaga_flag}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {Tikina.objects.count()} Tikina, {Koro.objects.count()} Koro loaded."
            )
        )
