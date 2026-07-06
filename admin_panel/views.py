from itertools import chain

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import ProtectedError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from common.reporting_periods import count_overdue_reports
from documents.models import Document
from events.models import Event
from koro.models import KoroReport
from mata_ni_tikina.models import MNTReport
from news.models import NewsPost
from tikina.models import Tikina, TikinaReport
from turaga_ni_yavusa.models import TNYReport
from turani.models import TNKReport
from yavusa.models import YavusaReport

from .forms import ManagedUserForm, PasswordResetForm


def is_roko_admin(user):
    return user.groups.filter(name="roko_admin").exists()


@login_required
@user_passes_test(is_roko_admin)
def dashboard(request):
    koro_reports = KoroReport.objects.select_related("tikina")
    tikina_reports = TikinaReport.objects.select_related("tikina")
    yavusa_reports = YavusaReport.objects.all()
    tnk_pdf_reports = TNKReport.objects.all()
    mata_pdf_reports = MNTReport.objects.all()
    yavusa_pdf_reports = TNYReport.objects.all()
    pdf_reports = sorted(
        chain(
            ((r.created_at, "Turaga ni Koro", r.village, r.quarter, r.year, "turani:report_detail", "turani:report_pdf", r.pk) for r in tnk_pdf_reports[:8]),
            ((r.created_at, "Mata ni Tikina", r.tikina, r.quarter, r.year, "mata_ni_tikina:report_detail", "mata_ni_tikina:report_pdf", r.pk) for r in mata_pdf_reports[:8]),
            ((r.created_at, "Turaga ni Yavusa", r.yavusa, r.quarter, r.year, "turaga_ni_yavusa:report_detail", "turaga_ni_yavusa:report_pdf", r.pk) for r in yavusa_pdf_reports[:8]),
        ),
        key=lambda item: item[0],
        reverse=True,
    )[:12]
    tikina_summary = []
    for tikina in Tikina.objects.prefetch_related("koro").annotate(
        reports_submitted=Count("koro_reports"),
        pending_reports=Count("koro_reports", filter=Q(koro_reports__status="pending")),
    ):
        tikina_summary.append(
            {
                "tikina": tikina,
                "reports_submitted": tikina.reports_submitted,
                "pending": tikina.pending_reports,
            }
        )
    context = {
        "total_submissions": koro_reports.count() + tikina_reports.count() + yavusa_reports.count(),
        "pending_count": (
            koro_reports.filter(status="pending").count()
            + tikina_reports.filter(status="pending").count()
            + yavusa_reports.filter(status="pending").count()
        ),
        "approved_count": (
            koro_reports.filter(status="approved").count()
            + tikina_reports.filter(status="approved").count()
            + yavusa_reports.filter(status="approved").count()
        ),
        "overdue_count": count_overdue_reports(tnk_pdf_reports, mata_pdf_reports, yavusa_pdf_reports),
        "koro_reports": koro_reports[:12],
        "tikina_reports": tikina_reports[:8],
        "yavusa_reports": yavusa_reports[:8],
        "news_published_count": NewsPost.objects.filter(status="published").count(),
        "news_draft_count": NewsPost.objects.filter(status="draft").count(),
        "upcoming_events_count": Event.objects.filter(status="upcoming").count(),
        "documents_total_count": Document.objects.count(),
        "documents_public_count": Document.objects.filter(access_level="public").count(),
        "documents_restricted_count": Document.objects.exclude(access_level="public").count(),
        "pdf_reports": pdf_reports,
        "tikina_summary": tikina_summary,
    }
    return render(request, "dashboard/admin/index.html", context)


@login_required
@user_passes_test(is_roko_admin)
def user_list(request):
    users = (
        get_user_model()
        .objects.select_related("turaga_profile", "user_profile")
        .order_by("first_name", "last_name", "username")
    )
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")
    if role:
        users = users.filter(user_profile__role=role)
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)
    return render(
        request,
        "dashboard/admin/users/list.html",
        {"users": users, "active_role": role, "active_status": status},
    )


@login_required
@user_passes_test(is_roko_admin)
def user_create(request):
    form = ManagedUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"{user.get_full_name() or user.username} has been created.")
        return redirect("admin_panel:user_list")
    return render(request, "dashboard/admin/users/form.html", {"form": form, "mode": "create"})


@login_required
@user_passes_test(is_roko_admin)
def user_edit(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk)
    form = ManagedUserForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"{user.get_full_name() or user.username} has been updated.")
        return redirect("admin_panel:user_list")
    return render(request, "dashboard/admin/users/form.html", {"form": form, "mode": "edit", "managed_user": user})


@login_required
@user_passes_test(is_roko_admin)
def user_reset_password(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk)
    form = PasswordResetForm(request.POST or None, user=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"The password for {user.get_full_name() or user.username} has been reset.")
        return redirect("admin_panel:user_list")
    return render(request, "dashboard/admin/users/reset_password.html", {"form": form, "managed_user": user})


@login_required
@user_passes_test(is_roko_admin)
def user_delete(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk)
    if request.method == "POST":
        if user.pk == request.user.pk:
            messages.error(request, "You cannot delete your own account while signed in.")
            return redirect("admin_panel:user_list")
        label = user.get_full_name() or user.username
        try:
            user.delete()
            messages.success(request, f"{label} has been deleted.")
        except ProtectedError:
            user.is_active = False
            user.save(update_fields=["is_active"])
            messages.warning(request, f"{label} owns reports, so the account was deactivated instead.")
        return redirect("admin_panel:user_list")
    return render(request, "dashboard/admin/users/confirm_delete.html", {"managed_user": user})
