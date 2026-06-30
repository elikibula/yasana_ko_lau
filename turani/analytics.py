from django.db.models import Count, Q, Sum

from .models import (
    Business,
    BusinessTraining,
    CorrectionReturnee,
    CropCount,
    CulturalKnowledge,
    DisabilityCount,
    ElectricitySource,
    EvacuationCentreMaterial,
    HealthConditionCount,
    HousingCount,
    IVDPImplementationSchedule,
    IVDPProject,
    LawOffence,
    PopulationAgeGroup,
    ToiletType,
    TraditionalTitleStatus,
    Training,
    VillageAssetSaving,
    VillageCommittee,
    VillageMeetingDecision,
    Visit,
    WasteManagement,
    WaterCommitteeMember,
    WaterCommitteeQuestion,
    WaterSource,
)


NO_DATA = "No data available"
YES = "io"
NO = "sega"


def _total(qs, field):
    return qs.aggregate(total=Sum(field))["total"] or 0


def _choice_label(choices, value):
    return dict(choices).get(value, value or "-")


def _safe_text(value):
    return value if value not in (None, "") else "-"


def _top_item(items, label_key="label", value_key="total"):
    return max(items, key=lambda item: item.get(value_key) or 0, default=None)


def _group_sum(qs, group_field, sum_field, choices=None, order_by="-total"):
    rows = (
        qs.values(group_field)
        .annotate(total=Sum(sum_field))
        .order_by(order_by)
    )
    results = []
    for row in rows:
        label = _choice_label(choices, row[group_field]) if choices else row[group_field] or "-"
        results.append(
            {
                "key": row[group_field],
                "label": label,
                group_field: label,
                "total": row["total"] or 0,
            }
        )
    return results


def _group_count(qs, group_field, choices=None, order_by="-total"):
    rows = (
        qs.values(group_field)
        .annotate(total=Count("id"))
        .order_by(order_by)
    )
    results = []
    for row in rows:
        label = _choice_label(choices, row[group_field]) if choices else row[group_field] or "-"
        results.append(
            {
                "key": row[group_field],
                "label": label,
                group_field: label,
                "total": row["total"] or 0,
            }
        )
    return results


def _flat_values(qs, field, limit=8):
    values = (
        qs.exclude(**{field: ""})
        .values_list(field, flat=True)
        .distinct()
        .order_by(field)[:limit]
    )
    return list(values)


def _latest_reports(reports):
    return [
        {
            "village": report.village,
            "district": report.district,
            "quarter": report.quarter,
            "year": report.year,
            "status": report.get_status_display(),
            "report_date": report.submitted_at or report.created_at,
        }
        for report in reports[:5]
    ]


def _recommend(priority, title, text):
    return {"priority": priority, "title": title, "text": text, "detail": text}


def _querysets(reports):
    return {
        "visits": Visit.objects.filter(report__in=reports),
        "decisions": VillageMeetingDecision.objects.filter(report__in=reports),
        "committees": VillageCommittee.objects.filter(report__in=reports),
        "law": LawOffence.objects.filter(report__in=reports),
        "returnees": CorrectionReturnee.objects.filter(report__in=reports),
        "trainings": Training.objects.filter(report__in=reports),
        "population": PopulationAgeGroup.objects.filter(report__in=reports),
        "housing": HousingCount.objects.filter(report__in=reports),
        "water_sources": WaterSource.objects.filter(report__in=reports),
        "water_answers": WaterCommitteeQuestion.objects.filter(report__in=reports),
        "water_members": WaterCommitteeMember.objects.filter(report__in=reports),
        "waste": WasteManagement.objects.filter(report__in=reports),
        "toilets": ToiletType.objects.filter(report__in=reports),
        "electricity": ElectricitySource.objects.filter(report__in=reports),
        "health": HealthConditionCount.objects.filter(report__in=reports),
        "disabilities": DisabilityCount.objects.filter(report__in=reports),
        "crops": CropCount.objects.filter(report__in=reports),
        "ivdp": IVDPProject.objects.filter(report__in=reports),
        "schedule": IVDPImplementationSchedule.objects.filter(report__in=reports),
        "businesses": Business.objects.filter(report__in=reports),
        "business_trainings": BusinessTraining.objects.filter(report__in=reports),
        "assets": VillageAssetSaving.objects.filter(report__in=reports),
        "evacuation": EvacuationCentreMaterial.objects.filter(report__in=reports),
        "titles": TraditionalTitleStatus.objects.filter(report__in=reports),
        "culture": CulturalKnowledge.objects.filter(report__in=reports),
    }


def tnk_dashboard_analysis(reports):
    """
    Build a template-ready analysis dictionary for all visible TNK reports.

    The dashboard view supplies a queryset already filtered for the current user.
    This function keeps all child queries scoped through report__in=reports and
    returns safe defaults when no data has been entered yet.
    """
    reports = reports.order_by("-year", "-created_at")
    qs = _querysets(reports)
    recommendations = []

    report_count = reports.count()
    latest_report = reports.first()
    submitted_reports = reports.filter(status="submitted").count()
    draft_reports = reports.filter(status="draft").count()
    periods = list(
        reports.values("quarter", "year")
        .distinct()
        .order_by("-year", "quarter")
    )

    overview = {
        "total_reports": report_count,
        "submitted_reports": submitted_reports,
        "draft_reports": draft_reports,
        "villages_covered": reports.exclude(village="").values("village").distinct().count(),
        "districts_covered": reports.exclude(district="").values("district").distinct().count(),
        "quarters_covered": len(periods),
        "latest_report": {
            "village": latest_report.village,
            "district": latest_report.district,
            "quarter": latest_report.quarter,
            "year": latest_report.year,
            "status": latest_report.get_status_display(),
            "report_date": latest_report.submitted_at or latest_report.created_at,
        }
        if latest_report
        else None,
        "available_periods": periods,
        "latest_reports": _latest_reports(reports),
    }

    population_by_gender = _group_sum(qs["population"], "gender", "count", PopulationAgeGroup.GENDER)
    population_by_age = _group_sum(qs["population"], "age_group", "count", PopulationAgeGroup.AGE_GROUP)
    total_population = _total(qs["population"], "count")
    largest_age = _top_item(population_by_age)
    population_summary = (
        f"E {total_population} na lewe ni koro sa volai. Na iwasewase levu duadua: "
        f"{largest_age['label']} ({largest_age['total']})."
        if total_population and largest_age
        else NO_DATA
    )
    population = {
        "total_population": total_population,
        "by_gender": population_by_gender,
        "by_age_group": population_by_age,
        "largest_age_group": largest_age or {"label": "-", "total": 0},
        "summary": population_summary,
    }

    total_households = _total(reports, "household_count")
    housing_by_type = _group_sum(qs["housing"], "house_type", "count", HousingCount.HOUSE_TYPE)
    housing_by_material = _group_sum(qs["housing"], "material", "count", HousingCount.MATERIAL)
    housing_matrix = (
        qs["housing"]
        .values("house_type", "material")
        .annotate(total=Sum("count"))
        .order_by("house_type", "material")
    )
    most_common_type = _top_item(housing_by_type)
    most_common_material = _top_item(housing_by_material)
    housing_issues = []
    if total_households == 0:
        housing_issues.append("E sega ni volai na iwiliwili ni matavuvale.")
    if not qs["housing"].exists():
        housing_issues.append("E sega ni volai na mataqali vale kei na kena iyaya.")
    housing = {
        "total_households": total_households,
        "by_house_type": housing_by_type,
        "by_material": housing_by_material,
        "matrix": [
            {
                "house_type": _choice_label(HousingCount.HOUSE_TYPE, row["house_type"]),
                "material": _choice_label(HousingCount.MATERIAL, row["material"]),
                "total": row["total"] or 0,
            }
            for row in housing_matrix
        ],
        "most_common_house_type": most_common_type or {"label": "-", "total": 0},
        "most_common_material": most_common_material or {"label": "-", "total": 0},
        "summary": (
            f"E {total_households} na matavuvale. Na vale e levu duadua: "
            f"{most_common_type['label'] if most_common_type else '-'}."
            if total_households or most_common_type
            else NO_DATA
        ),
        "issues": housing_issues,
    }

    committees_exist = qs["committees"].filter(exists=YES)
    committees_not_exist = qs["committees"].filter(exists=NO)
    weak_committees = qs["committees"].filter(
        Q(meetings_last_3_months=0) | (Q(male_members=0) & Q(female_members=0))
    )
    committees = {
        "existing_committees": committees_exist.count(),
        "missing_committees": committees_not_exist.count(),
        "exist": [
            _choice_label(VillageCommittee.COMMITTEE_TYPES, value)
            for value in committees_exist.values_list("committee_type", flat=True).distinct()
        ],
        "not_exist": [
            _choice_label(VillageCommittee.COMMITTEE_TYPES, value)
            for value in committees_not_exist.values_list("committee_type", flat=True).distinct()
        ],
        "male_members": _total(qs["committees"], "male_members"),
        "female_members": _total(qs["committees"], "female_members"),
        "meetings_last_3_months": _total(qs["committees"], "meetings_last_3_months"),
        "weak_committees": [
            {
                "name": _choice_label(VillageCommittee.COMMITTEE_TYPES, item.committee_type),
                "members": item.male_members + item.female_members,
                "meetings": item.meetings_last_3_months,
            }
            for item in weak_committees[:8]
        ],
        "summary": (
            f"E {committees_exist.count()} na komiti e tiko; e {weak_committees.count()} e gadrevi me vaqaqacotaki."
        ),
    }

    implemented = qs["decisions"].filter(implemented=YES).count()
    unimplemented = qs["decisions"].filter(implemented=NO).count()
    decision_reasons = _flat_values(qs["decisions"], "reason_not_implemented")
    meetings = {
        "village_meetings": _total(reports, "village_meetings_count"),
        "bose_vanua_meetings": _total(reports, "bose_vanua_count"),
        "total_decisions": qs["decisions"].count(),
        "major_decisions": qs["decisions"].count(),
        "implemented_decisions": implemented,
        "unimplemented_decisions": unimplemented,
        "reasons_not_implemented": decision_reasons,
        "action_recommendations": [
            "Vakadeitaka na gauna kei na tamata me qarava na veilewa e se bera.",
            "Vola na vuna ni veilewa kece e sega ni vakayacori.",
        ]
        if unimplemented
        else ["Tomana na vakamuri ni veilewa sa vakayacori."],
        "summary": (
            f"E {qs['decisions'].count()} na lewa bibi sa volai; {implemented} sa vakayacori."
            if qs["decisions"].exists()
            else NO_DATA
        ),
    }

    visits_by_type = _group_count(qs["visits"], "visit_type", Visit.VISIT_TYPE)
    visits = {
        "total_visits": qs["visits"].count(),
        "by_type": visits_by_type,
        "latest": [
            {
                "officer": item.officer_name,
                "type": item.get_visit_type_display(),
                "date": item.visit_date,
                "purpose": _safe_text(item.purpose),
            }
            for item in qs["visits"].order_by("-visit_date", "-id")[:5]
        ],
        "officers": _flat_values(qs["visits"], "officer_name"),
        "purposes": _flat_values(qs["visits"], "purpose"),
        "summary": (
            f"E {qs['visits'].count()} na veisiko sa volai mai na veitabana eso."
            if qs["visits"].exists()
            else NO_DATA
        ),
    }

    law_by_type = _group_sum(qs["law"], "offence_name", "count")
    reported_count = qs["law"].filter(reported_to_law=YES).aggregate(total=Sum("count"))["total"] or 0
    not_reported_count = qs["law"].filter(reported_to_law=NO).aggregate(total=Sum("count"))["total"] or 0
    total_offences = _total(qs["law"], "count")
    common_offence = _top_item(law_by_type)
    law = {
        "total_offences": total_offences,
        "by_type": law_by_type,
        "reported": reported_count,
        "not_reported": not_reported_count,
        "reported_offences": reported_count,
        "unreported_offences": not_reported_count,
        "reasons_not_reported": _flat_values(qs["law"], "reason_not_reported"),
        "common_offence_types": law_by_type[:5],
        "common_offences": [
            {"offence_type": row["label"], "total": row["total"]}
            for row in law_by_type[:5]
        ],
        "concerns": [
            f"Na cala e laurai vakalevu: {common_offence['label']} ({common_offence['total']})."
        ]
        if common_offence
        else [],
        "summary": (
            f"E {total_offences} na basu lawa sa volai; {reported_count} sa ripotetaki."
            if total_offences
            else NO_DATA
        ),
    }

    returnees_total = qs["returnees"].count()
    returnees = {
        "total_returnees": returnees_total,
        "rehabilitation_done": qs["returnees"].exclude(rehabilitation_done="").count(),
        "rehabilitation_not_done": qs["returnees"].filter(rehabilitation_done="").count(),
        "current_activities": _flat_values(qs["returnees"], "current_activity"),
        "recommendations": [
            "Cakava e dua na tuvatuva ni veivakacokotaki kei na veitaratara vakawasoma."
        ]
        if returnees_total
        else ["E sega ni volai e dua na gone suka mai."],
        "summary": (
            f"E {returnees_total} na gone suka mai sa volai."
            if returnees_total
            else NO_DATA
        ),
    }

    trainings_by_type = _group_count(qs["trainings"], "training_type", Training.TRAINING_TYPE)
    total_participants = _total(qs["trainings"], "participants_count")
    trainings = {
        "total_trainings": qs["trainings"].count(),
        "by_type": trainings_by_type,
        "organisations": _flat_values(qs["trainings"], "organization"),
        "participants_count": total_participants,
        "outcomes": _flat_values(qs["trainings"], "outcome"),
        "gaps": ["E se gadrevi na vuli ni bisinisi kei na tuvatuva ni IVDP."]
        if not trainings_by_type
        else [],
        "summary": (
            f"E {qs['trainings'].count()} na vuli kei na veivakararamataki sa volai."
            if qs["trainings"].exists()
            else NO_DATA
        ),
    }

    selected_water_source_rows = _group_count(
        qs["water_sources"].filter(selected=True),
        "source",
        WaterSource.SOURCE,
    )
    selected_water_sources = [item["label"] for item in selected_water_source_rows]
    water_yes = qs["water_answers"].filter(answer=True).count()
    water_no = qs["water_answers"].filter(answer=False).count()
    water_sanitation = {
        "sources": selected_water_source_rows,
        "water_sources_selected": selected_water_sources,
        "committee_answers_yes": water_yes,
        "committee_answers_no": water_no,
        "committee_answers": [
            {"question": item.question, "answer": "Io" if item.answer else "Sega"}
            for item in qs["water_answers"][:8]
        ],
        "committee_members": list(qs["water_members"].values_list("name", flat=True)[:10]),
        "committee_members_count": qs["water_members"].count(),
        "water_challenges": _flat_values(reports, "water_challenges"),
        "responsible_agency": _flat_values(reports, "water_problem_responsible_agency"),
        "toilet_types": _group_sum(qs["toilets"], "toilet_type", "count", ToiletType.TOILET_TYPE),
        "wastewater_challenges": _flat_values(reports, "toilet_wastewater_challenges"),
        "wastewater_agency": _flat_values(reports, "toilet_wastewater_agency"),
        "waste_management": [
            {
                "village_dump": item.get_village_dump_display(),
                "boundary_clean": item.get_village_boundary_clean_display(),
                "household_dump": item.get_household_dump_display(),
                "garbage_truck": item.get_garbage_truck_display(),
            }
            for item in qs["waste"][:3]
        ],
        "waste_records": qs["waste"].count(),
        "summary": (
            f"E {len(selected_water_sources)} na vurevure ni wai sa digitaki; "
            f"{water_yes} na isaunitaro ni komiti ni wai e Io."
        ),
    }

    electricity_sources = _group_sum(qs["electricity"], "source", "house_count", ElectricitySource.SOURCE)
    main_electricity = _top_item(electricity_sources)
    electricity = {
        "sources": electricity_sources,
        "sources_recorded": len(electricity_sources),
        "total_house_count": _total(qs["electricity"], "house_count"),
        "main_source": main_electricity or {"label": "-", "total": 0},
        "summary": (
            f"Na ivurevure levu ni livaliva: {main_electricity['label']}."
            if main_electricity
            else NO_DATA
        ),
    }

    health_by_name = _group_sum(qs["health"], "condition_name", "count")
    disability_by_name = _group_sum(qs["disabilities"], "disability_name", "count")
    major_health = _top_item(health_by_name)
    health = {
        "conditions_by_name": health_by_name,
        "conditions_by_age": _group_sum(qs["health"], "age_group", "count", HealthConditionCount.AGE_GROUP),
        "disabilities_by_name": disability_by_name,
        "disabilities_by_age": _group_sum(qs["disabilities"], "age_group", "count", DisabilityCount.AGE_GROUP),
        "major_concerns": health_by_name[:5],
        "major_conditions": health_by_name[:5],
        "total_disabilities": _total(qs["disabilities"], "count"),
        "summary": (
            f"Na mate e laurai vakalevu: {major_health['label']} ({major_health['total']})."
            if major_health
            else NO_DATA
        ),
    }

    crop_by_category = _group_sum(qs["crops"], "category", "plantation_count", CropCount.CROP_CATEGORY)
    crop_by_name = _group_sum(qs["crops"], "crop_name", "plantation_count")
    crops = {
        "by_category": crop_by_category,
        "by_crop_name": crop_by_name,
        "major_crops": crop_by_name[:5],
        "summary": (
            f"E {sum(item['total'] for item in crop_by_name)} na teitei/kakana sa volai."
            if crop_by_name
            else NO_DATA
        ),
        "food_security_notes": (
            ["E tiko na ivakadinadina ni kakana draudrau kei na kakana dina."]
            if crop_by_category
            else ["E se gadrevi me volai na teitei kei na kakana e tiko."]
        ),
    }

    ivdp_by_priority = _group_count(qs["ivdp"], "priority_area", IVDPProject.PRIORITY_AREA)
    schedule_items = list(qs["schedule"])
    average_progress = (
        round(sum(item.progress_percentage() for item in schedule_items) / len(schedule_items))
        if schedule_items
        else 0
    )
    progress_buckets = [
        {
            "status": "Completed",
            "total": sum(1 for item in schedule_items if item.progress_percentage() == 100),
        },
        {
            "status": "In progress",
            "total": sum(1 for item in schedule_items if 0 < item.progress_percentage() < 100),
        },
        {
            "status": "Not started",
            "total": sum(1 for item in schedule_items if item.progress_percentage() == 0),
        },
    ]
    ivdp = {
        "total_projects": qs["ivdp"].count(),
        "by_priority_area": ivdp_by_priority,
        "applications_prepared": qs["ivdp"].filter(application_prepared=YES).count(),
        "materials_received": qs["ivdp"].filter(materials_received=YES).count(),
        "unfinished_reasons": _flat_values(qs["ivdp"], "problem_reason"),
        "solutions": _flat_values(qs["ivdp"], "solution"),
        "schedule_items": len(schedule_items),
        "schedule_progress": average_progress,
        "status_breakdown": progress_buckets,
        "recommendations": [
            "Vakadeitaka na kerekere kei na iyaya ni tuvatuva IVDP e se tu vakadredre."
        ]
        if qs["ivdp"].exclude(problem_reason="").exists()
        else ["Tomana na kena vakamuri na ituvatuva IVDP."],
        "summary": (
            f"E {qs['ivdp'].count()} na project IVDP; average progress {average_progress}%."
            if qs["ivdp"].exists() or schedule_items
            else NO_DATA
        ),
    }

    business_by_type = _group_count(qs["businesses"], "business_type")
    business_trainings = {
        "total": qs["business_trainings"].count(),
        "organisations": _flat_values(qs["business_trainings"], "organization"),
        "participants": _total(qs["business_trainings"], "participants_count"),
        "outcomes": _flat_values(qs["business_trainings"], "outcome"),
    }
    business = {
        "total_businesses": qs["businesses"].count(),
        "licensed": qs["businesses"].filter(licensed=YES).count(),
        "unlicensed": qs["businesses"].filter(licensed=NO).count(),
        "business_types": business_by_type,
        "by_type": business_by_type,
        "years_running": _flat_values(qs["businesses"], "years_running"),
        "training_summary": business_trainings,
        "opportunities": [
            "Vukea na bisinisi me vakalaiseni ka semati ki na vuli ni vakatubuilavo."
        ]
        if qs["businesses"].filter(licensed=NO).exists()
        else ["E rawa ni vakalevutaki na vuli ni cicivaki bisinisi."],
        "summary": (
            f"E {qs['businesses'].count()} na bisinisi sa volai; "
            f"{qs['businesses'].filter(licensed=YES).count()} sa vakalaiseni."
            if qs["businesses"].exists()
            else NO_DATA
        ),
    }

    assets = {
        "total_assets": qs["assets"].count(),
        "answers": [
            {
                "question": item.question,
                "answer": item.get_answer_display(),
                "description": _safe_text(item.description),
            }
            for item in qs["assets"]
        ],
        "descriptions": _flat_values(qs["assets"], "description"),
        "summary": (
            "Sa volai na iyau/lavo ni koro."
            if qs["assets"].exists()
            else NO_DATA
        ),
    }

    latest = latest_report
    evacuation_materials = [
        item["label"]
        for item in _group_count(
            qs["evacuation"].filter(selected=True),
            "material",
            EvacuationCentreMaterial.MATERIAL,
        )
    ]
    readiness_score = 0
    if latest:
        readiness_score += 1 if latest.disaster_current_plan else 0
        readiness_score += 1 if latest.disaster_future_plan else 0
        readiness_score += 1 if latest.has_evacuation_centre == YES else 0
        readiness_score += 1 if latest.evacuation_centre_capacity else 0
        readiness_score += 1 if latest.has_male_female_restrooms == YES else 0
        readiness_score += 1 if latest.climate_change_solution_done == YES else 0
    readiness_score += 1 if evacuation_materials else 0
    readiness_status = "Strong" if readiness_score >= 5 else "Moderate" if readiness_score >= 3 else "Needs attention"
    disaster_climate = {
        "yaubula_current_plan": _safe_text(latest.yaubula_current_plan if latest else ""),
        "yaubula_management_plan": _safe_text(latest.yaubula_management_plan if latest else ""),
        "disaster_current_plan": _safe_text(latest.disaster_current_plan if latest else ""),
        "disaster_future_plan": _safe_text(latest.disaster_future_plan if latest else ""),
        "has_evacuation_centre": latest.get_has_evacuation_centre_display() if latest else "-",
        "evacuation_capacity": latest.evacuation_centre_capacity if latest else 0,
        "has_restrooms": latest.get_has_male_female_restrooms_display() if latest else "-",
        "evacuation_materials": evacuation_materials,
        "climate_change_impact": latest.get_climate_change_impact_display() if latest else "-",
        "climate_change_impact_details": _safe_text(latest.climate_change_impact_details if latest else ""),
        "climate_change_solution_done": latest.get_climate_change_solution_done_display() if latest else "-",
        "climate_change_solution_details": _safe_text(latest.climate_change_solution_details if latest else ""),
        "readiness_score": readiness_score,
        "readiness_status": readiness_status,
        "readiness_label": readiness_status,
        "material_count": len(evacuation_materials),
        "climate_change_observations": [
            value
            for value in [
                _safe_text(latest.climate_change_impact_details if latest else ""),
                _safe_text(latest.climate_change_solution_details if latest else ""),
            ]
            if value != "-"
        ],
        "summary": (
            f"Disaster readiness is {readiness_status.lower()} with {len(evacuation_materials)} materials selected."
            if latest
            else NO_DATA
        ),
    }

    titles = qs["titles"].aggregate(
        confirmed=Sum("confirmed_count"),
        unconfirmed=Sum("unconfirmed_count"),
        processing=Count("id", filter=Q(being_processed=YES)),
    )
    culture = {
        "confirmed_titles": titles["confirmed"] or 0,
        "unconfirmed_titles": titles["unconfirmed"] or 0,
        "processing_titles": titles["processing"] or 0,
        "knowledge_by_area": _group_count(qs["culture"], "knowledge_type"),
        "cultural_knowledge": [
            {
                "knowledge_type": item.knowledge_type,
                "preservation_plan": _safe_text(item.preservation_plan),
            }
            for item in qs["culture"][:8]
        ],
        "summary": (
            f"E {titles['confirmed'] or 0} na itutu sa vakadeitaki; "
            f"{titles['unconfirmed'] or 0} e se bera."
        ),
    }

    if draft_reports:
        recommendations.append(_recommend("High", "Vakacavara na draft", f"E {draft_reports} na ripote draft e se bera ni submit."))
    if not total_population:
        recommendations.append(_recommend("High", "Vola na lewe ni koro", "Na iwiliwili ni tamata e bibi ena veivuke kei na tuvatuva."))
    if committees["weak_committees"]:
        recommendations.append(_recommend("Medium", "Vaqaqacotaka na komiti", "Eso na komiti e sega na lewe se sega ni sota ena vula 3."))
    if law["not_reported"]:
        recommendations.append(_recommend("High", "Ripote na basu lawa", "Eso na cala e volai ni sega ni ripotetaki ki na tabana ni lawa."))
    if water_no:
        recommendations.append(_recommend("Medium", "Vakavinakataka na komiti ni wai", "Eso na taro ni komiti ni wai e saumi Sega."))
    if disaster_climate["readiness_status"] == "Needs attention":
        recommendations.append(_recommend("High", "Vakarautaka na leqa tubukoso", "E gadrevi me vaqaqacotaki na vale ni dro, tuvatuva, kei na iyaya."))
    if not recommendations:
        recommendations.append(_recommend("Low", "Tomana na veiqaravi vinaka", "E laurai ni sa tiko vinaka na levu ni itukutuku bibi."))

    summary_text = (
        f"E tiko e {report_count} na ripote TNK, {submitted_reports} sa submit ka {draft_reports} draft. "
        f"Sa volai e {total_population} na lewe ni koro, {total_households} na matavuvale, "
        f"{total_offences} na basu lawa, kei {ivdp['total_projects']} na tuvatuva IVDP."
        if report_count
        else "E sega ni dua na ripote TNK me vakadikevi ena gauna oqo."
    )

    return {
        "overview": overview,
        "population": population,
        "housing": housing,
        "committees": committees,
        "meetings": meetings,
        "visits": visits,
        "law": law,
        "returnees": returnees,
        "trainings": trainings,
        "water_sanitation": water_sanitation,
        "electricity": electricity,
        "health": health,
        "crops": crops,
        "ivdp": ivdp,
        "business": business,
        "assets": assets,
        "disaster_climate": disaster_climate,
        "culture": culture,
        "recommendations": recommendations,
        "summary_text": summary_text,
    }
