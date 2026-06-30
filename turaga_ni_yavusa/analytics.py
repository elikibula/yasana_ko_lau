from django.db.models import Count, Sum


def _total(qs, field):
    return qs.aggregate(total=Sum(field))["total"] or 0


def _pct(part, whole):
    return round((part / whole) * 100) if whole else 0


def _count_by(qs, field):
    return list(qs.values(field).annotate(total=Count("id")).order_by(field))


def tny_dashboard_analysis(reports):
    total_reports = reports.count()
    submitted = reports.filter(status="submitted").count()
    draft = reports.filter(status="draft").count()
    residents = _total(reports, "resident_turaga_count") + _total(reports, "resident_marama_count") + _total(reports, "resident_gone_count")
    away = _total(reports, "away_turaga_count") + _total(reports, "away_marama_count") + _total(reports, "away_gone_count")
    total_people = residents + away
    vakoro_yes = reports.filter(attends_bose_vakoro="io").count()
    tikina_yes = reports.filter(attends_bose_ni_tikina="io").count()
    church_follow_yes = reports.filter(church_follows_vanua_program="io").count()
    church_needs_yes = reports.filter(church_meets_vanua_needs="io").count()

    return {
        "overview": {
            "total_reports": total_reports,
            "submitted_reports": submitted,
            "draft_reports": draft,
            "yavusa_covered": reports.exclude(yavusa="").values("yavusa").distinct().count(),
            "vanua_covered": reports.exclude(vanua="").values("vanua").distinct().count(),
            "summary": f"E {total_reports} na ripote ni Turaga ni Yavusa, {submitted} sa submit ka {draft} draft.",
        },
        "bosevanua": {
            "meeting_frequency": _count_by(reports, "bosevanua_meeting_frequency"),
            "turaga_ni_mataqali": _total(reports, "bosevanua_turaga_ni_mataqali_count"),
            "liuliu_ni_tokatoka": _total(reports, "bosevanua_liuliu_ni_tokatoka_count"),
            "lewe_ni_yavusa": _total(reports, "bosevanua_lewe_ni_yavusa_count"),
            "genealogy_recorded": _total(reports, "genealogy_recorded_count"),
            "genealogy_removed": _total(reports, "genealogy_removed_count"),
            "summary": f"E {_total(reports, 'genealogy_recorded_count')} sa volai ena iVola ni Kawa Bula.",
        },
        "titles": {
            "confirmed_total": _total(reports, "confirmed_titles_this_period"),
            "by_quarter": list(reports.values("quarter", "year").annotate(total=Sum("confirmed_titles_this_period")).order_by("-year", "quarter")),
            "summary": f"E {_total(reports, 'confirmed_titles_this_period')} na itutu sa vakadeitaki ena ripote oqo.",
        },
        "heritage": {
            "language_custom_logged": reports.exclude(language_custom_initiatives="").count(),
            "land_logged": reports.exclude(land_initiatives="").count(),
            "fishing_ground_logged": reports.exclude(fishing_ground_initiatives="").count(),
            "summary": "Heritage activity counts are based on whether initiatives were recorded.",
        },
        "outreach": {
            "resident_total": residents,
            "away_total": away,
            "away_percent": _pct(away, total_people),
            "visitation_plan_percent": _pct(reports.filter(has_member_visitation_plan="io").count(), total_reports),
            "summary": f"E {residents} era tiko ena koro; {away} era tiko tani.",
        },
        "attendance": {
            "bose_vakoro_percent": _pct(vakoro_yes, total_reports),
            "bose_ni_tikina_percent": _pct(tikina_yes, total_reports),
            "summary": f"{_pct(vakoro_yes, total_reports)}% e tiko ena Bose Vakoro; {_pct(tikina_yes, total_reports)}% ena Bose ni Tikina.",
        },
        "church_relations": {
            "church_count": _total(reports, "churches_in_yavusa_count"),
            "following_program_percent": _pct(church_follow_yes, total_reports),
            "meeting_needs_percent": _pct(church_needs_yes, total_reports),
            "summary": f"E {_total(reports, 'churches_in_yavusa_count')} na lotu sa volai ena Yavusa.",
        },
    }
