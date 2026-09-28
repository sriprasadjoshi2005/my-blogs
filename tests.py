from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ContactMessage, Post, SiteProfile, Topic


class BlogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anime = Topic.objects.create(name="Anime")
        cls.coding = Topic.objects.create(name="Coding")
        cls.p1 = Post.objects.create(
            title="Frieren review", body="<p>Slow, warm and beautiful.</p>", status="published"
        )
        cls.p1.topics.add(cls.anime)
        cls.p2 = Post.objects.create(
            title="Learning Django", body="<p>Models and views.</p>", status="published"
        )
        cls.p2.topics.add(cls.coding)
        cls.draft = Post.objects.create(title="Secret draft", body="<p>Nope</p>", status="draft")
        cls.future = Post.objects.create(
            title="Scheduled", body="<p>Later</p>", status="published",
            published_at=timezone.now() + timedelta(days=3),
        )

    def test_pages_load(self):
        for name in ["blog:home", "blog:post_list", "blog:about", "blog:contact"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_only_published_posts_are_listed(self):
        html = self.client.get(reverse("blog:post_list")).content.decode()
        self.assertIn("Frieren review", html)
        self.assertNotIn("Secret draft", html)
        self.assertNotIn("Scheduled", html)

    def test_slug_is_unique(self):
        dup = Post.objects.create(title="Frieren review", body="x")
        self.assertNotEqual(dup.slug, self.p1.slug)

    def test_search_by_title_body_and_topic(self):
        url = reverse("blog:post_list")
        self.assertContains(self.client.get(url, {"q": "django"}), "Learning Django")
        self.assertContains(self.client.get(url, {"q": "warm"}), "Frieren review")
        by_topic = self.client.get(url, {"q": "anime"})
        self.assertContains(by_topic, "Frieren review")
        self.assertNotContains(by_topic, "Learning Django")
        self.assertContains(self.client.get(url, {"q": "zzzz"}), "Nothing matched")

    def test_topic_filter(self):
        res = self.client.get(reverse("blog:post_list"), {"topic": "coding"})
        self.assertContains(res, "Learning Django")
        self.assertNotContains(res, "Frieren review")

    def test_draft_hidden_from_visitors_but_visible_to_staff(self):
        url = self.draft.get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 404)
        staff = get_user_model().objects.create_user("me", password="pw", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_post_detail_renders_body_html(self):
        res = self.client.get(self.p1.get_absolute_url())
        self.assertContains(res, "<p>Slow, warm and beautiful.</p>", html=True)

    def test_contact_form_saves_message(self):
        res = self.client.post(
            reverse("blog:contact"),
            {"name": "Sam", "email": "sam@example.com", "subject": "Hi", "message": "Great blog!"},
        )
        self.assertRedirects(res, reverse("blog:contact"))
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_contact_honeypot_blocks_bots(self):
        self.client.post(
            reverse("blog:contact"),
            {"name": "Bot", "email": "b@example.com", "message": "buy now", "website": "http://spam"},
        )
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_profile_is_a_singleton(self):
        SiteProfile.objects.create(display_name="A")
        SiteProfile.objects.create(display_name="B")
        self.assertEqual(SiteProfile.objects.count(), 1)
