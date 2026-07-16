from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .forms import NewsPostForm
from .models import NewsPhoto, NewsPost, youtube_video_id


def image_upload(name="photo.jpg"):
    stream = BytesIO()
    Image.new("RGB", (20, 20), "#d4af37").save(stream, "JPEG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/jpeg")


class NewsTypeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("editor", password="StrongPass123!")
        group, _ = Group.objects.get_or_create(name="roko_admin")
        self.user.groups.add(group)

    def article(self, **overrides):
        values = {"title": "Existing article", "summary": "Summary", "body": "Article body", "status": "published", "published_at": timezone.now(), "author": self.user}
        values.update(overrides)
        return NewsPost.objects.create(**values)

    def test_existing_posts_default_to_article_and_render(self):
        post = self.article()
        self.assertEqual(post.news_type, NewsPost.NEWS_TYPE_ARTICLE)
        response = self.client.get(reverse("news:detail", args=[post.slug]))
        self.assertContains(response, "Article body")
        self.assertContains(response, "Article")

    def test_article_form_still_requires_body(self):
        form = NewsPostForm(data={"title": "No body", "news_type": "article", "summary": "Summary", "status": "draft"})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_supported_youtube_urls(self):
        video_id = "dQw4w9WgXcQ"
        for url in (
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://youtu.be/{video_id}",
            f"https://www.youtube.com/embed/{video_id}",
            f"https://www.youtube.com/shorts/{video_id}",
        ):
            with self.subTest(url=url):
                self.assertEqual(youtube_video_id(url), video_id)

    def test_video_requires_source_and_rejects_bad_youtube_url(self):
        base = {"title": "Video", "news_type": "video", "summary": "Summary", "body": "", "status": "draft"}
        self.assertFalse(NewsPostForm(data=base).is_valid())
        bad = NewsPostForm(data={**base, "video_url": "https://youtube.com/watch?v=bad"})
        self.assertFalse(bad.is_valid())
        self.assertIn("video_url", bad.errors)

    def test_youtube_video_detail_uses_generated_embed(self):
        post = self.article(title="Video story", body="", news_type="video", video_url="https://youtu.be/dQw4w9WgXcQ")
        response = self.client.get(reverse("news:detail", args=[post.slug]))
        self.assertContains(response, "https://www.youtube.com/embed/dQw4w9WgXcQ")
        self.assertNotContains(response, "youtu.be/dQw4w9WgXcQ")
        self.assertContains(response, 'referrerpolicy="strict-origin-when-cross-origin"')

    def test_youtube_url_with_tracking_query_keeps_only_video_id(self):
        url = "https://www.youtube.com/watch?v=ailoN7f5jRI&source_ve_path=MTc4NDI0"
        self.assertEqual(youtube_video_id(url), "ailoN7f5jRI")

    def test_editor_can_create_photo_news_with_ordered_photos(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("news:create"), data={
            "title": "Island gallery", "news_type": "photo", "summary": "Scenes from Lau", "body": "", "status": "draft",
            "photos-TOTAL_FORMS": "2", "photos-INITIAL_FORMS": "0", "photos-MIN_NUM_FORMS": "0", "photos-MAX_NUM_FORMS": "1000",
            "photos-0-image": image_upload("second.jpg"), "photos-0-caption": "Second", "photos-0-display_order": "2",
            "photos-1-image": image_upload("first.jpg"), "photos-1-caption": "First", "photos-1-display_order": "1",
        })
        self.assertRedirects(response, reverse("news:manage"))
        post = NewsPost.objects.get(title="Island gallery")
        self.assertEqual(list(post.photos.values_list("caption", flat=True)), ["First", "Second"])

    def test_photo_news_requires_photo(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("news:create"), data={
            "title": "Empty gallery", "news_type": "photo", "summary": "Summary", "body": "", "status": "draft",
            "photos-TOTAL_FORMS": "1", "photos-INITIAL_FORMS": "0", "photos-MIN_NUM_FORMS": "0", "photos-MAX_NUM_FORMS": "1000",
            "photos-0-caption": "", "photos-0-display_order": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Photo News requires at least one gallery photo")
        self.assertFalse(NewsPost.objects.filter(title="Empty gallery").exists())

    def test_unpublished_news_is_hidden_and_permissions_are_preserved(self):
        draft = self.article(title="Private draft", status="draft", published_at=None)
        self.assertEqual(self.client.get(reverse("news:detail", args=[draft.slug])).status_code, 404)
        self.assertNotEqual(self.client.get(reverse("news:create")).status_code, 200)

    def test_gallery_delete_and_ordering(self):
        post = self.article(title="Gallery", news_type="photo")
        later = NewsPhoto.objects.create(news=post, image=image_upload("later.jpg"), caption="Later", display_order=9)
        NewsPhoto.objects.create(news=post, image=image_upload("earlier.jpg"), caption="Earlier", display_order=1)
        self.assertEqual(post.photos.first().caption, "Earlier")
        later.delete()
        self.assertEqual(post.photos.count(), 1)


class PublishedNewsDetailTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("publisher")

    def post(self, **overrides):
        values = {
            "title": "Published story",
            "summary": "News from Lau",
            "body": "Story body",
            "status": "published",
            "published_at": timezone.now(),
            "author": self.user,
        }
        values.update(overrides)
        return NewsPost.objects.create(**values)

    def test_published_detail_has_absolute_share_url_and_draft_is_hidden(self):
        published = self.post()
        response = self.client.get(reverse("news:detail", args=[published.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post_share_url"], f"http://testserver{published.get_absolute_url()}")
        self.assertContains(response, 'rel="canonical"')
        draft = self.post(title="Draft", status="draft", published_at=None)
        self.assertEqual(self.client.get(reverse("news:detail", args=[draft.slug])).status_code, 404)

    def test_social_image_prefers_cover_then_first_photo_then_default(self):
        covered = self.post(title="Covered", cover_image=image_upload("cover.jpg"))
        response = self.client.get(covered.get_absolute_url())
        self.assertIn(covered.cover_image.url, response.context["post_share_image_url"])

        gallery = self.post(title="Gallery fallback", news_type="photo", body="")
        first = NewsPhoto.objects.create(news=gallery, image=image_upload("first-social.jpg"), display_order=1)
        response = self.client.get(gallery.get_absolute_url())
        self.assertIn(first.image.url, response.context["post_share_image_url"])

        plain = self.post(title="Default fallback")
        response = self.client.get(plain.get_absolute_url())
        self.assertEqual(response.context["post_share_image_url"], "http://testserver/static/images/logo_lau.png")

    def test_gallery_is_ordered_scoped_and_progressively_enhanced(self):
        post = self.post(title="Main gallery", news_type="photo", body="")
        other = self.post(title="Other gallery", news_type="photo", body="")
        later = NewsPhoto.objects.create(news=post, image=image_upload("later-detail.jpg"), caption='Later "quote"', display_order=8)
        earlier = NewsPhoto.objects.create(news=post, image=image_upload("earlier-detail.jpg"), caption="Earlier", display_order=2)
        unrelated = NewsPhoto.objects.create(news=other, image=image_upload("unrelated.jpg"), caption="Unrelated", display_order=1)

        response = self.client.get(post.get_absolute_url())
        content = response.content.decode()
        self.assertLess(content.index(earlier.image.url), content.index(later.image.url))
        self.assertNotIn(unrelated.image.url, content)
        self.assertContains(response, f'href="{earlier.image.url}"')
        self.assertContains(response, 'data-caption="Later &quot;quote&quot;"')
        self.assertContains(response, 'data-gallery-index="0"')
        self.assertContains(response, 'data-gallery-index="1"')

    def test_single_photo_gallery_has_valid_shared_modal(self):
        post = self.post(title="Single gallery", news_type="photo", body="")
        photo = NewsPhoto.objects.create(news=post, image=image_upload("single.jpg"))
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, f'href="{photo.image.url}"')
        self.assertContains(response, "data-news-lightbox")
        self.assertContains(response, 'aria-label="Previous photo"')
