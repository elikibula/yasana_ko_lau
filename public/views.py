from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from events.models import Event
from news.models import NewsPost

from .forms import ContactForm
from .models import News


class HomeView(TemplateView):
    template_name = "public/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["homepage_news"] = NewsPost.objects.filter(
            status="published",
            published_at__isnull=False,
        ).select_related("category").prefetch_related("photos")[:3]
        context["homepage_events"] = Event.objects.filter(
            status__in=["upcoming", "ongoing"],
            start_date__gte=timezone.now(),
        ).select_related("category")[:3]
        return context


class AboutView(TemplateView):
    template_name = "public/about.html"


class TikinaListView(TemplateView):
    template_name = "public/tikina.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tikina_cards"] = [
            {"name": "Lakeba", "group": "Central Lau", "koro": 8, "mata": "To be assigned", "image": "images/gallery/image8.jfif"},
            {"name": "Oneata", "group": "Southern Lau", "koro": 3, "mata": "To be assigned", "image": "images/gallery/image1.jfif"},
            {"name": "Moce", "group": "Southern Lau", "koro": 2, "mata": "To be assigned", "image": "images/gallery/image5.jfif"},
            {"name": "Kabara", "group": "Southern Lau", "koro": 4, "mata": "To be assigned", "image": "images/gallery/image11.jfif"},
            {"name": "Fulaga", "group": "Southern Lau", "koro": 3, "mata": "To be assigned", "image": "images/gallery/image12.jfif"},
            {"name": "Ogea", "group": "Southern Lau", "koro": 2, "mata": "To be assigned", "image": "images/gallery/image13.jfif"},
            {"name": "Vatoa", "group": "Southern Lau", "koro": 1, "mata": "To be assigned", "image": "images/gallery/image7.jfif"},
            {"name": "Ono-i-Lau", "group": "Far Southern Lau", "koro": 4, "mata": "To be assigned", "image": "images/gallery/image2.jfif"},
            {"name": "Cicia", "group": "Northern Lau", "koro": 5, "mata": "To be assigned", "image": "images/gallery/image10.jfif"},
            {"name": "Nayau", "group": "Central Lau", "koro": 3, "mata": "To be assigned", "image": "images/gallery/image3.jfif"},
            {"name": "Vanuabalavu", "group": "Northern Lau", "koro": 17, "mata": "To be assigned", "image": "images/gallery/image16.jfif"},
            {"name": "Mago", "group": "Northern Lau", "koro": 1, "mata": "To be assigned", "image": "images/gallery/image9.jfif"},
        ]
        return context


class NewsListView(ListView):
    model = News
    template_name = "public/news_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return News.objects.filter(is_published=True)


class NewsDetailView(DetailView):
    model = News
    template_name = "public/news_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return News.objects.filter(is_published=True)


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        contact_message = form.save()
        send_mail(
            subject=f"Lau Provincial Council contact: {contact_message.subject}",
            message=f"From: {contact_message.name} <{contact_message.email}>\n\n{contact_message.message}",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=True,
        )
        messages.success(request, "Vinaka. Your message has been received by the Provincial Office.")
        return redirect("public:contact")
    return render(request, "public/contact.html", {"form": form})
