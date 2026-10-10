from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Comment, ContactMessage, Post, SiteProfile, Topic


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

    def test_post_has_share_tags(self):
        response = self.client.get(self.p1.get_absolute_url())
        self.assertContains(response, 'property="og:title" content="Frieren review"')
        self.assertContains(response, 'name="twitter:card"')


class CommentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.post = Post.objects.create(title="Open post", body="<p>Hello</p>", status="published")
        cls.draft = Post.objects.create(title="Hidden draft", body="<p>Nope</p>", status="draft")
        cls.user = get_user_model().objects.create_user("sakura", password="correct-horse-42")
        cls.url = cls.post.get_absolute_url()

    def test_guest_cannot_comment_and_is_sent_to_login(self):
        res = self.client.post(self.url, {"body": "Hi"})
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("blog:login"), res["Location"])
        self.assertEqual(Comment.objects.count(), 0)

    def test_logged_in_user_can_comment_and_it_shows(self):
        self.client.force_login(self.user)
        res = self.client.post(self.url, {"body": "Great review!"})
        self.assertRedirects(res, f"{self.url}#comments", fetch_redirect_response=False)
        self.assertContains(self.client.get(self.url), "Great review!")
        self.assertEqual(Comment.objects.get().author, self.user)

    def test_hidden_comment_is_not_shown(self):
        Comment.objects.create(post=self.post, author=self.user, body="Secret words", is_approved=False)
        self.assertNotContains(self.client.get(self.url), "Secret words")

    @override_settings(COMMENTS_AUTO_APPROVE=False)
    def test_comment_waits_for_approval_when_moderation_is_on(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"body": "Pending thought"})
        self.assertFalse(Comment.objects.get().is_approved)
        self.assertNotContains(self.client.get(self.url), "Pending thought")

    def test_cooldown_blocks_rapid_second_comment(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"body": "First"})
        self.client.post(self.url, {"body": "Second"})
        self.assertEqual(Comment.objects.count(), 1)

    def test_html_in_comments_is_escaped(self):
        Comment.objects.create(post=self.post, author=self.user, body="<script>alert(1)</script>")
        res = self.client.get(self.url)
        self.assertNotContains(res, "<script>alert(1)</script>")
        self.assertContains(res, "&lt;script&gt;")

    def test_cannot_comment_on_draft(self):
        staff = get_user_model().objects.create_user("boss", password="pw-for-tests-1", is_staff=True)
        self.client.force_login(staff)
        self.client.post(self.draft.get_absolute_url(), {"body": "Sneaky"})
        self.assertEqual(Comment.objects.count(), 0)

    def test_signup_creates_normal_user_and_logs_in(self):
        res = self.client.post(
            reverse("blog:signup"),
            {"username": "newfan", "password1": "Zq7!mellow-tree", "password2": "Zq7!mellow-tree", "website": ""},
        )
        self.assertRedirects(res, reverse("blog:home"))
        user = get_user_model().objects.get(username="newfan")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_honeypot_blocks_bots(self):
        self.client.post(
            reverse("blog:signup"),
            {"username": "bot", "password1": "Zq7!mellow-tree", "password2": "Zq7!mellow-tree", "website": "http://spam"},
        )
        self.assertFalse(get_user_model().objects.filter(username="bot").exists())

    def test_login_and_logout(self):
        res = self.client.post(reverse("blog:login"), {"username": "sakura", "password": "correct-horse-42"})
        self.assertEqual(res.status_code, 302)
        self.assertContains(self.client.get(reverse("blog:home")), "Log out")
        self.client.post(reverse("blog:logout"))
        self.assertContains(self.client.get(reverse("blog:home")), "Sign up")

    def test_signup_ignores_external_next_url(self):
        res = self.client.post(
            reverse("blog:signup"),
            {"username": "safe", "password1": "Zq7!mellow-tree", "password2": "Zq7!mellow-tree", "next": "https://evil.example/"},
        )
        self.assertRedirects(res, reverse("blog:home"))
