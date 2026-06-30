from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin

from .access import user_can_access_document
from .forms import DocumentForm
from .models import Document, DocumentCategory


def accessible_documents(user):
    docs = Document.objects.select_related("category", "uploaded_by")
    if not user.is_authenticated:
        return docs.filter(access_level="public")
    if user.groups.filter(name="roko_admin").exists():
        return docs
    group_names = set(user.groups.values_list("name", flat=True))
    allowed = ["public", "login"]
    if "turaga_ni_koro" in group_names:
        allowed.append("koro")
    if "mata_ni_tikina" in group_names:
        allowed.extend(["koro", "tikina"])
    if "liuliu_ni_yavusa" in group_names:
        allowed.extend(["koro", "tikina"])
    return docs.filter(access_level__in=set(allowed))


class DocumentListView(ListView):
    model = Document
    template_name = "documents/list.html"
    context_object_name = "documents"
    paginate_by = 12

    def get_queryset(self):
        qs = accessible_documents(self.request.user)
        q = self.request.GET.get("q")
        category = self.request.GET.get("category")
        year = self.request.GET.get("year")
        file_type = self.request.GET.get("file_type")
        tags = self.request.GET.get("tags")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if category:
            qs = qs.filter(category__slug=category)
        if year:
            qs = qs.filter(year=year)
        if file_type:
            qs = qs.filter(file_type=file_type)
        if tags:
            qs = qs.filter(tags__icontains=tags)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        docs = accessible_documents(self.request.user)
        context.update(
            {
                "categories": DocumentCategory.objects.all(),
                "featured_documents": docs.filter(is_featured=True)[:3],
                "years": docs.exclude(year__isnull=True).values_list("year", flat=True).distinct().order_by("-year"),
                "file_types": Document.FILE_TYPE_CHOICES,
            }
        )
        return context


class DocumentCategoryView(DocumentListView):
    template_name = "documents/category.html"

    def get_queryset(self):
        self.category = get_object_or_404(DocumentCategory, slug=self.kwargs["slug"])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class DocumentDetailView(DetailView):
    model = Document
    template_name = "documents/detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return Document.objects.select_related("category", "uploaded_by")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not user_can_access_document(request.user, self.object):
            return HttpResponseForbidden("You do not have permission to view this document.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        related = accessible_documents(self.request.user).exclude(pk=self.object.pk)
        if self.object.category:
            related = related.filter(category=self.object.category)
        context["related_documents"] = related[:3]
        return context


class DocumentDownloadView(View):
    def get(self, request, slug):
        document = get_object_or_404(Document, slug=slug)
        if not user_can_access_document(request.user, document):
            return HttpResponseForbidden("You do not have permission to download this document.")
        document.download_count += 1
        document.save(update_fields=["download_count"])
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.file.name.rsplit("/", 1)[-1])


class DocumentManageView(RoleRequiredMixin, ListView):
    required_group = "roko_admin"
    model = Document
    template_name = "documents/manage/list.html"
    context_object_name = "documents"
    paginate_by = 20

    def get_queryset(self):
        return Document.objects.select_related("category", "uploaded_by")


class DocumentUploadView(RoleRequiredMixin, CreateView):
    required_group = "roko_admin"
    model = Document
    form_class = DocumentForm
    template_name = "documents/manage/form.html"
    success_url = reverse_lazy("documents:manage")

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, "Document uploaded.")
        return super().form_valid(form)


class DocumentUpdateView(RoleRequiredMixin, UpdateView):
    required_group = "roko_admin"
    model = Document
    form_class = DocumentForm
    template_name = "documents/manage/form.html"
    success_url = reverse_lazy("documents:manage")

    def form_valid(self, form):
        messages.success(self.request, "Document updated.")
        return super().form_valid(form)


class DocumentDeleteView(RoleRequiredMixin, DeleteView):
    required_group = "roko_admin"
    model = Document
    template_name = "documents/manage/confirm_delete.html"
    success_url = reverse_lazy("documents:manage")

    def form_valid(self, form):
        messages.success(self.request, "Document deleted.")
        return super().form_valid(form)
