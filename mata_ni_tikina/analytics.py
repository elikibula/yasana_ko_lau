from django.db.models import Count, Sum


def _choice_map(choices):
    return dict(choices)


def _total(qs, field):
    return qs.aggregate(total=Sum(field))["total"] or 0


def _count_by(qs, field):
    return list(qs.values(field).annotate(total=Count("id")).order_by(field))


def _pct(part, whole):
    return round((part / whole) * 100) if whole else 0


def _display(value, fallback="-"):
    return value if value not in (None, "") else fallback


def _yes_no(value):
    return _choice_map((("io", "Io"), ("sega", "Sega"))).get(value, "-")


def _choice_label(choices, value):
    return _choice_map(choices).get(value, _display(value))


def _bar_rows(rows, label_key="label", value_key="total"):
    max_value = max([row[value_key] or 0 for row in rows], default=0)
    return [{**row, "percent": _pct(row[value_key] or 0, max_value)} for row in rows]


def _report_period(report):
    return f"{report.quarter} {report.year}"


def _latest_report_analysis(report):
    if not report:
        return {
            "exists": False,
            "title": "Se bera na ripote",
            "summary": "Ni sa vakaleweni e dua na ripote, ena basika eke na itukutuku ni ripote vou duadua.",
            "metric_cards": [],
            "alerts": [],
            "koro": {"rows": [], "installed": 0, "total": 0, "percent": 0},
            "finance": {"soli_percent": 0, "savings_rows": []},
            "bose_chart": [],
            "disputes": [],
            "education_rows": [],
            "village_visit_rows": [],
            "decisions": [],
        }

    koro_rows = [
        {
            "village": _display(row.village_name),
            "leader": _display(row.traditional_leader),
            "installed": _yes_no(row.installed),
            "needs_attention": row.installed != "io",
        }
        for row in report.koro_under_tikina.all()
    ]
    koro_total = len(koro_rows)
    koro_installed = len([row for row in koro_rows if row["installed"] == "Io"])

    visit_rows = [
        {
            "date": visit.visit_date.strftime("%d/%m/%Y") if visit.visit_date else "-",
            "village": _display(visit.village_name),
            "role": _display(visit.role_performed),
            "confirmation": _display(visit.turaga_ni_koro_confirmation),
        }
        for visit in report.village_visits.all()[:8]
    ]
    dispute_rows = [
        {
            "description": _display(dispute.description),
            "resolution": _display(dispute.resolution, "Se bera ni volai na kena i wali"),
            "open": not bool(dispute.resolution),
        }
        for dispute in report.disputes.all()[:8]
    ]
    education_rows = [
        {
            "training": _display(item.training_type),
            "leader": _display(item.training_leader),
            "participants": item.participants_count or 0,
            "benefit": _display(item.benefit),
        }
        for item in report.education_trainings.all()[:8]
    ]
    savings_rows = [
        {
            "funds_held": _yes_no(row.funds_held),
            "bank": row.get_bank_display(),
        }
        for row in report.savings_accounts.all()
    ]
    bose_chart = _bar_rows(
        [
            {"label": "Turaga", "total": report.council_turaga_count or 0},
            {"label": "Marama", "total": report.council_marama_count or 0},
            {"label": "Daunivakasala", "total": report.council_daunivakasala_count or 0},
        ]
    )
    decisions = [
        {"label": "Lewa ni Matabose me baleta na Vuli", "value": _display(report.education_next_quarter_decision)},
        {"label": "Lewa ni Matabose me baleta nai vurevure ni lavo", "value": _display(report.income_council_decision)},
        {"label": "Lewa ni Matabose me baleta na veivakatorocaketaki", "value": _display(report.development_council_decision)},
        {"label": "Lewa ni Matabose me baleta na vakailesilesi", "value": _display(report.reps_council_decision)},
    ]

    alerts = []
    if report.has_development_plan != "io":
        alerts.append("E gadrevi me vakadeitaki na Tuvatuva ni Veivakatorocaketaki.")
    if koro_total and koro_installed < koro_total:
        alerts.append(f"E {koro_total - koro_installed} na Koro e se sega ni Buli oti vakavanua.")
    if report.soli_balance_amount:
        alerts.append(f"E vo tiko ${report.soli_balance_amount:,.2f} me kumuni ena Soli.")
    if any(row["open"] for row in dispute_rows):
        alerts.append("E tiko na veileti/leqa e se bera ni volai na kena i wali.")
    if not visit_rows:
        alerts.append("Se bera ni volai na veisiko ena veikoro.")
    if not alerts:
        alerts.append("E sega ni laurai e dua na ka bibi me vakatotolotaki ena ripote qo.")

    return {
        "exists": True,
        "title": f"{report.tikina} - {_report_period(report)}",
        "summary": f"Ripote vou duadua: {report.tikina}, {_report_period(report)}.",
        "metric_cards": [
            {"label": "Lewe ni Tikina", "value": report.tikina_population or 0},
            {"label": "Wiliwili ni Bose", "value": report.council_total_attendees or 0},
            {"label": "Soli sa Kumuni", "value": report.soli_collected_amount or 0, "money": True},
            {"label": "Veisiko ena Koro", "value": report.village_visits.count()},
        ],
        "alerts": alerts,
        "koro": {
            "rows": koro_rows,
            "installed": koro_installed,
            "total": koro_total,
            "percent": _pct(koro_installed, koro_total),
        },
        "finance": {
            "soli_target": report.soli_target_amount or 0,
            "soli_collected": report.soli_collected_amount or 0,
            "soli_balance": report.soli_balance_amount or 0,
            "soli_percent": _pct(report.soli_collected_amount or 0, report.soli_target_amount or 0),
            "savings_rows": savings_rows,
        },
        "bose_chart": bose_chart,
        "disputes": dispute_rows,
        "education_rows": education_rows,
        "village_visit_rows": visit_rows,
        "decisions": decisions,
        "status": report.get_status_display(),
    }


def _all_time_analysis(reports):
    report_list = list(reports)
    timeline_rows = []
    for report in sorted(report_list, key=lambda item: (item.year, item.created_at)):
        timeline_rows.append(
            {
                "period": _report_period(report),
                "tikina": _display(report.tikina),
                "population": report.tikina_population or 0,
                "soli": report.soli_collected_amount or 0,
                "bose": report.council_total_attendees or 0,
                "visits": report.village_visits.count(),
                "disputes": report.disputes.count(),
            }
        )

    soli_max = max([row["soli"] for row in timeline_rows], default=0)
    population_max = max([row["population"] for row in timeline_rows], default=0)
    timeline_rows = [
        {
            **row,
            "soli_percent": _pct(row["soli"], soli_max),
            "population_percent": _pct(row["population"], population_max),
        }
        for row in timeline_rows
    ]

    return {
        "timeline_rows": timeline_rows,
        "latest_rows": list(reversed(timeline_rows[-6:])),
        "submitted_percent": _pct(reports.filter(status="submitted").count(), reports.count()),
        "draft_percent": _pct(reports.filter(status="draft").count(), reports.count()),
    }


def mnt_dashboard_analysis(reports):
    report_model = reports.model
    latest_report = reports.prefetch_related(
        "koro_under_tikina",
        "disputes",
        "education_trainings",
        "savings_accounts",
        "village_visits",
    ).first()
    total_reports = reports.count()
    submitted = reports.filter(status="submitted").count()
    draft = reports.filter(status="draft").count()
    tikinas = reports.exclude(tikina="").values("tikina").distinct().count()

    coordination_model = report_model._meta.apps.get_model("mata_ni_tikina", "TikinaCoordinationStatus")
    social_model = report_model._meta.apps.get_model("mata_ni_tikina", "TikinaSocialIndicator")
    income_model = report_model._meta.apps.get_model("mata_ni_tikina", "IncomeSourceItem")
    fund_model = report_model._meta.apps.get_model("mata_ni_tikina", "FundCollectionChallenge")
    rep_model = report_model._meta.apps.get_model("mata_ni_tikina", "TikinaChallengeIndicator")
    coordination_qs = coordination_model.objects.filter(report__in=reports)
    dispute_qs = report_model._meta.apps.get_model("mata_ni_tikina", "TikinaDispute").objects.filter(report__in=reports)
    social_qs = social_model.objects.filter(report__in=reports)
    income_qs = income_model.objects.filter(report__in=reports)
    fund_qs = fund_model.objects.filter(report__in=reports)
    rep_challenges = rep_model.objects.filter(report__in=reports)
    visit_qs = report_model._meta.apps.get_model("mata_ni_tikina", "TikinaVillageVisit").objects.filter(report__in=reports)

    coordination_counts = _bar_rows([
        {"label": _choice_label(coordination_model._meta.get_field("status").choices, row["status"]), "total": row["total"]}
        for row in coordination_qs.values("status").annotate(total=Count("id")).order_by("status")
    ])
    unresolved = dispute_qs.filter(resolution="").values_list("description", flat=True)[:6]
    social_counts = [
        {
            "indicator": _choice_label(social_model._meta.get_field("indicator").choices, row["indicator"]),
            "trend": _choice_label(social_model._meta.get_field("trend").choices, row["trend"]),
            "total": row["total"],
        }
        for row in social_qs.values("indicator", "trend").annotate(total=Count("id")).order_by("indicator", "trend")
    ]
    income_categories = _bar_rows([
        {
            "label": _choice_label(income_model._meta.get_field("category").choices, row["category"]),
            "total": row["total"] or 0,
        }
        for row in income_qs.values("category").annotate(total=Sum("count_or_amount")).order_by("category")
    ])
    income_trends = _bar_rows([
        {"label": _choice_label(report_model.TREND_CHOICES, row["income_trend"]), "total": row["total"]}
        for row in _count_by(reports.exclude(income_trend=""), "income_trend")
    ])
    infrastructure_trends = _bar_rows([
        {"label": _choice_label(report_model.TREND_CHOICES, row["infrastructure_trend"]), "total": row["total"]}
        for row in _count_by(reports.exclude(infrastructure_trend=""), "infrastructure_trend")
    ])

    soli_target = _total(reports, "soli_target_amount")
    soli_collected = _total(reports, "soli_collected_amount")
    soli_balance = _total(reports, "soli_balance_amount")
    fund_challenges = _bar_rows([
        {
            "label": _choice_label(fund_model._meta.get_field("challenge").choices, row["challenge"]),
            "total": row["total"],
        }
        for row in fund_qs.filter(selected=True).values("challenge").annotate(total=Count("id")).order_by("-total")[:5]
    ])
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
    visit_counts = _bar_rows([
        {"label": row["village_name"] or "-", "total": row["total"]}
        for row in visit_qs.values("village_name").annotate(total=Count("id")).order_by("-total")[:5]
    ])
    challenge_indicators = _bar_rows([
        {
            "label": _choice_label(rep_model._meta.get_field("indicator").choices, row["indicator"]),
            "total": row["total"],
        }
        for row in rep_challenges.filter(selected=True).values("indicator").annotate(total=Count("id")).order_by("-total")[:5]
    ])

    return {
        "latest": _latest_report_analysis(latest_report),
        "all_time": _all_time_analysis(reports.prefetch_related("village_visits", "disputes")),
        "overview": {
            "total_reports": total_reports,
            "submitted_reports": submitted,
            "draft_reports": draft,
            "tikinas_covered": tikinas,
            "summary": f"E {total_reports} na ripote ni Mata ni Tikina: {submitted} sa vakau, {draft} e se draft.",
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
            "challenge_indicators": challenge_indicators,
            "summary": f"E {rep_yes} na isaunitaro Io kei {rep_no} na isaunitaro Sega.",
        },
        "village_visits": {
            "total_visits": visit_qs.count(),
            "most_visited": visit_counts[0] if visit_counts else None,
            "by_village": visit_counts,
            "summary": f"E {visit_qs.count()} na veisiko ena veikoro sa volai.",
        },
    }
