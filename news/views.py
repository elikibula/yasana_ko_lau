from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin

from .forms import NewsPhotoFormSet, NewsPostForm
from .models import NewsCategory, NewsPost


class PublishedNewsMixin:
    def get_queryset(self):
        return (
            NewsPost.objects.filter(status="published", published_at__isnull=False)
            .select_related("category", "author")
            .prefetch_related("photos")
            .order_by("-published_at", "-created_at")
        )


class NewsListView(PublishedNewsMixin, ListView):
    model = NewsPost
    template_name = "news/list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context.update(
            {
                "featured_posts": qs.filter(is_featured=True)[:3],
                "categories": NewsCategory.objects.all(),
                "recent_posts": qs[:5],
            }
        )
        return context


class NewsCategoryView(PublishedNewsMixin, ListView):
    model = NewsPost
    template_name = "news/category.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        self.category = NewsCategory.objects.get(slug=self.kwargs["slug"])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["categories"] = NewsCategory.objects.all()
        return context


class NewsDetailView(PublishedNewsMixin, DetailView):
    model = NewsPost
    template_name = "news/detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        related = self.get_queryset().exclude(pk=self.object.pk)
        if self.object.category:
            related = related.filter(category=self.object.category)
        share_url = self.request.build_absolute_uri(self.object.get_absolute_url())
        first_photo = self.object.photos.first()
        share_image = self.object.cover_image or (first_photo.image if first_photo else None)
        if share_image:
            share_image_url = self.request.build_absolute_uri(share_image.url)
        else:
            share_image_url = self.request.build_absolute_uri(static("images/logo_lau.png"))
        context.update(
            {
                "related_posts": related[:3],
                "post_share_url": share_url,
                "post_share_title": self.object.title,
                "post_share_image_url": share_image_url,
            }
        )
        return context


class NewsManageView(RoleRequiredMixin, ListView):
    required_group = "roko_admin"
    model = NewsPost
    template_name = "news/manage/list.html"
    context_object_name = "posts"
    paginate_by = 20

    def get_queryset(self):
        qs = NewsPost.objects.select_related("category", "author")
        status = self.request.GET.get("status")
        sort = self.request.GET.get("sort", "-created_at")
        allowed_sorts = {"created_at", "-created_at", "published_at", "-published_at", "status", "-status"}
        if status:
            qs = qs.filter(status=status)
        return qs.order_by(sort if sort in allowed_sorts else "-created_at")


class NewsCreateView(RoleRequiredMixin, CreateView):
    required_group = "roko_admin"
    model = NewsPost
    form_class = NewsPostForm
    template_name = "news/manage/form.html"
    success_url = reverse_lazy("news:manage")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photo_formset"] = kwargs.get("photo_formset") or NewsPhotoFormSet(self.request.POST or None, self.request.FILES or None)
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = NewsPhotoFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            if form.cleaned_data["news_type"] == NewsPost.NEWS_TYPE_PHOTO and not any(
                item.cleaned_data and not item.cleaned_data.get("DELETE") and (item.cleaned_data.get("image") or item.instance.image)
                for item in formset.forms
            ):
                formset._non_form_errors = formset.error_class(["Photo News requires at least one gallery photo."])
            else:
                return self.forms_valid(form, formset)
        return self.render_to_response(self.get_context_data(form=form, photo_formset=formset))

    def forms_valid(self, form, formset):
        form.instance.author = self.request.user
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        messages.success(self.request, "News post saved.")
        return HttpResponseRedirect(self.get_success_url())


class NewsUpdateView(RoleRequiredMixin, UpdateView):
    required_group = "roko_admin"
    model = NewsPost
    form_class = NewsPostForm
    template_name = "news/manage/form.html"
    success_url = reverse_lazy("news:manage")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photo_formset"] = kwargs.get("photo_formset") or NewsPhotoFormSet(
            self.request.POST or None, self.request.FILES or None, instance=self.object
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = NewsPhotoFormSet(request.POST, request.FILES, instance=self.object)
        if form.is_valid() and formset.is_valid():
            if form.cleaned_data["news_type"] == NewsPost.NEWS_TYPE_PHOTO and not any(
                item.cleaned_data and not item.cleaned_data.get("DELETE") and (item.cleaned_data.get("image") or item.instance.image)
                for item in formset.forms
            ):
                formset._non_form_errors = formset.error_class(["Photo News requires at least one gallery photo."])
            else:
                with transaction.atomic():
                    self.object = form.save()
                    formset.save()
                messages.success(request, "News post updated.")
                return HttpResponseRedirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form, photo_formset=formset))

    def form_valid(self, form):
        messages.success(self.request, "News post updated.")
        return super().form_valid(form)


class NewsDeleteView(RoleRequiredMixin, DeleteView):
    required_group = "roko_admin"
    model = NewsPost
    template_name = "news/manage/confirm_delete.html"
    success_url = reverse_lazy("news:manage")

    def form_valid(self, form):
        messages.success(self.request, "News post deleted.")
        return super().form_valid(form)
