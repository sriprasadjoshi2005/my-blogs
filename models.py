from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class Topic(models.Model):
    """A subject you write about, e.g. "Anime", "Coding", "Travel"."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or "topic"
        super().save(*args, **kwargs)


class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())
        )


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft (only you can see it)"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text="Part of the post's web address. Leave blank to create it from the title.",
    )
    summary = models.CharField(
        max_length=300,
        blank=True,
        help_text="One or two sentences shown on the blog list and in search results.",
    )
    cover_image = models.ImageField(
        upload_to="covers/%Y/%m/",
        blank=True,
        help_text="Optional. Shown on the post card and at the top of the post.",
    )
    body = CKEditor5Field("Body", config_name="blog")
    topics = models.ManyToManyField(Topic, blank=True, related_name="posts")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set automatically when you publish. Choose a future time to schedule a post.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    def _make_unique_slug(self):
        base = slugify(self.title)[:200] or "post"
        slug, n = base, 2
        while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._make_unique_slug()
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class SiteProfile(models.Model):
    """Your About Me and Contact page details. There is only ever one of these."""

    display_name = models.CharField(max_length=100, default="Your Name")
    tagline = models.CharField(
        max_length=200,
        blank=True,
        default="Thoughts, stories and things I'm learning.",
        help_text="Shown on the homepage under the site name.",
    )
    photo = models.ImageField(upload_to="profile/", blank=True)
    about = CKEditor5Field("About me", config_name="blog", blank=True)

    contact_intro = models.TextField(
        blank=True,
        default="Have a question or just want to say hi? Send me a message.",
    )
    contact_email = models.EmailField(blank=True, help_text="Shown on the Contact page.")
    github_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    x_url = models.URLField("X / Twitter URL", blank=True)
    youtube_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "About & contact details"
        verbose_name_plural = "About & contact details"

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce a single row
        kwargs.pop("force_insert", None)  # update the existing row instead of failing
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def social_links(self):
        pairs = [
            ("GitHub", self.github_url),
            ("Instagram", self.instagram_url),
            ("X", self.x_url),
            ("YouTube", self.youtube_url),
            ("LinkedIn", self.linkedin_url),
        ]
        return [(label, url) for label, url in pairs if url]


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.subject or self.message[:40]}"
