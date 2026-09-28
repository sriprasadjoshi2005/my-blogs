from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm
from .models import Post, Topic


def home(request):
    latest = Post.published.prefetch_related("topics")[:3]
    return render(request, "blog/home.html", {"latest_posts": latest})


def post_list(request):
    """All blogs. Also handles the search box (?q=) and topic filter (?topic=)."""
    posts = Post.published.prefetch_related("topics")
    query = request.GET.get("q", "").strip()
    topic_slug = request.GET.get("topic", "").strip()
    active_topic = None

    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(body__icontains=query)
            | Q(topics__name__icontains=query)
        ).distinct()

    if topic_slug:
        active_topic = Topic.objects.filter(slug=topic_slug).first()
        posts = posts.filter(topics__slug=topic_slug)

    page = Paginator(posts, settings.POSTS_PER_PAGE).get_page(request.GET.get("page"))

    # Keep ?q= and ?topic= when moving between pages
    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "blog/post_list.html",
        {
            "page": page,
            "query": query,
            "active_topic": active_topic,
            "topics": Topic.objects.filter(posts__in=Post.published.all()).distinct(),
            "querystring": params.urlencode(),
        },
    )


def post_detail(request, slug):
    qs = Post.objects.prefetch_related("topics")
    # You (when logged in to the admin) can preview drafts. Visitors only see published posts.
    if not request.user.is_staff:
        qs = qs.filter(pk__in=Post.published.values("pk"))
    post = get_object_or_404(qs, slug=slug)
    newer = Post.published.filter(published_at__gt=post.published_at).order_by("published_at").first() if post.published_at else None
    older = Post.published.filter(published_at__lt=post.published_at).first() if post.published_at else None
    return render(request, "blog/post_detail.html", {"post": post, "newer": newer, "older": older})


def about(request):
    return render(request, "blog/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save()
            if settings.CONTACT_NOTIFY_EMAIL:
                send_mail(
                    subject=f"[{settings.SITE_NAME}] {msg.subject or 'New message'} from {msg.name}",
                    message=f"From: {msg.name} <{msg.email}>\n\n{msg.message}",
                    from_email=None,
                    recipient_list=[settings.CONTACT_NOTIFY_EMAIL],
                    fail_silently=True,
                )
            messages.success(request, "Thanks! Your message has been sent.")
            return redirect("blog:contact")
    else:
        form = ContactForm()
    return render(request, "blog/contact.html", {"form": form})
