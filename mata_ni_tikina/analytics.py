from django.db.models import Count, Sum


def _total(qs, field):
    return qs.aggregate(total=Sum(field))["total"] or 0


def _count_by(qs, field):
    return list(qs.values(field).annotate(total=Count("id")).order_by(field))


def _pct(part, whole):
    return round((part / whole) * 100) if whole else 0


def mnt_dashboard_analysis(reports):
    total_reports = reports.count()
    submitted = reports.filter(status="submitted").count()
    draft = reports.filter(status="draft").count()
    tikinas = reports.exclude(tikina="").values("tikina").distinct().count()

    coordination_qs = reports.model._meta.apps.get_model("mata_ni_tikina", "TikinaCoordinationStatus").objects.filter(report__in=reports)
    dispute_qs = reports.model._meta.apps.get_model("mata_ni_tikina", "TikinaDispute").objects.filter(report__in=reports)
    social_qs = reports.model._meta.apps.get_model("mata_ni_tikina", "TikinaSocialIndicator").objects.filter(report__in=reports)
    income_qs = reports.model._meta.apps.get_model("mata_ni_tikina", "IncomeSourceItem").objects.filter(report__in=reports)
    fund_qs = reports.model._meta.apps.get_model("mata_ni_tikina", "FundCollectionChallenge").objects.filter(report__in=reports)
    rep_challenges = reports.model._meta.apps.get_model("mata_ni_tikina", "TikinaChallengeIndicator").objects.filter(report__in=reports)
    visit_qs = reports.model._meta.apps.get_model("mata_ni_tikina", "TikinaVillageVisit").objects.filter(report__in=reports)

    coordination_counts = list(coordination_qs.values("status").annotate(total=Count("id")).order_by("status"))
    unresolved = dispute_qs.filter(resolution="").values_list("description", flat=True)[:6]
    social_counts = list(social_qs.values("indicator", "trend").annotate(total=Count("id")).order_by("indicator", "trend"))
    income_categories = list(income_qs.values("category").annotate(total=Sum("count_or_amount")).order_by("category"))
    income_trends = _count_by(reports.exclude(income_trend=""), "income_trend")
    infrastructure_trends = _count_by(reports.exclude(infrastructure_trend=""), "infrastructure_trend")

    soli_target = _total(reports, "soli_target_amount")
    soli_collected = _total(reports, "soli_collected_amount")
    soli_balance = _total(reports, "soli_balance_amount")
    fund_challenges = list(fund_qs.filter(selected=True).values("challenge").annotate(total=Count("id")).order_by("-total")[:5])
    rep_yes = (
        reports.filter(reps_attend_meetings="io").count()
        + reports.filter(reps_understand_training_needs="io").count()
        + reports.filter(reps_assist_report_writing="io").count()
        + reports.filter(reps_help_outside_meetings="io").count()
    )
    rep_no = (
        reports.filter(reps_attend_meetings="sega").count()
        + reports.filter(reps_understand_training_needs="sega").count()
        + reports.filter(reps_assist_report_writing="sega").count()
        + reports.filter(reps_help_outside_meetings="sega").count()
    )
    visit_counts = list(visit_qs.values("village_name").annotate(total=Count("id")).order_by("-total")[:5])

    return {
        "overview": {
            "total_reports": total_reports,
            "submitted_reports": submitted,
            "draft_reports": draft,
            "tikinas_covered": tikinas,
            "summary": f"E {total_reports} na ripote ni Mata ni Tikina, {submitted} sa submit ka {draft} draft.",
        },
        "coordination": {
            "status_counts": coordination_counts,
            "unresolved_disputes": list(unresolved),
            "summary": f"E {coordination_qs.count()} na ivakatakilakila ni veisemati kei {dispute_qs.count()} na veileti sa volai.",
        },
        "social_indicators": {
            "trend_counts": social_counts,
            "summary": f"E {social_qs.count()} na itukutuku ni social indicator sa volai.",
        },
        "income": {
            "categories": income_categories,
            "trend_distribution": income_trends,
            "summary": f"E {income_qs.count()} na ivurevure ni lavo sa volai.",
        },
        "infrastructure": {
            "villages_with_phone": _total(reports, "villages_with_phone_count"),
            "villages_with_tv": _total(reports, "villages_with_tv_count"),
            "boats": _total(reports, "boat_count"),
            "vehicles": _total(reports, "vehicle_count"),
            "villages_with_road_access": _total(reports, "villages_with_road_access_count"),
            "new_roads_km": _total(reports, "new_roads_built_km"),
            "trend_distribution": infrastructure_trends,
            "summary": "Infrastructure totals are aggregated from Mata ni Tikina submissions.",
        },
        "government_partnership": {
            "total_assistance": _total(reports, "govt_financial_assistance_amount"),
            "visit_count": _total(reports, "govt_official_visits_count"),
            "summary": f"E {_total(reports, 'govt_official_visits_count')} na veisiko vakamatanitu sa volai.",
        },
        "ngo_partnership": {
            "total_assistance": _total(reports, "ngo_financial_assistance_amount"),
            "equipment_value": _total(reports, "ngo_project_equipment_value"),
            "summary": "NGO assistance and equipment values are aggregated from reports.",
        },
        "finance": {
            "soli_target": soli_target,
            "soli_collected": soli_collected,
            "soli_balance": soli_balance,
            "soli_percent": _pct(soli_collected, soli_target),
            "fund_challenges": fund_challenges,
            "summary": f"Sa kumuni { _pct(soli_collected, soli_target) }% ni soli target.",
        },
        "farmland": {
            "registered_reports": reports.filter(has_registered_farmland="io").count(),
            "lease_count": _total(reports, "farmland_lease_count"),
            "total_acres": _total(reports, "farmland_acres_leased"),
            "summary": f"E {_total(reports, 'farmland_lease_count')} na lease ni qele sa volai.",
        },
        "representation": {
            "yes_answers": rep_yes,
            "no_answers": rep_no,
            "challenge_indicators": list(rep_challenges.filter(selected=True).values("indicator").annotate(total=Count("id")).order_by("-total")[:5]),
            "summary": f"E {rep_yes} na isaunitaro Io kei {rep_no} na isaunitaro Sega.",
        },
        "village_visits": {
            "total_visits": visit_qs.count(),
            "most_visited": visit_counts[0] if visit_counts else None,
            "by_village": visit_counts,
            "summary": f"E {visit_qs.count()} na veisiko ena veikoro sa volai.",
        },
    }
