from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin

from .forms import NewsPostForm
from .models import NewsCategory, NewsPost


class PublishedNewsMixin:
    def get_queryset(self):
        return (
            NewsPost.objects.filter(status="published", published_at__isnull=False)
            .select_related("category", "author")
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
        context["related_posts"] = related[:3]
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

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "News post saved.")
        return super().form_valid(form)


class NewsUpdateView(RoleRequiredMixin, UpdateView):
    required_group = "roko_admin"
    model = NewsPost
    form_class = NewsPostForm
    template_name = "news/manage/form.html"
    success_url = reverse_lazy("news:manage")

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
