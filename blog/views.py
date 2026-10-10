from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import redirect_to_login
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import CommentForm, ContactForm, SignUpForm
from .models import Comment, Post, Topic


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

    # Comments are only open on posts that are really published (not draft previews).
    comments_open = Post.published.filter(pk=post.pk).exists()
    comment_form = CommentForm()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not comments_open:
            messages.error(request, "Comments are closed on this post.")
            return redirect(post.get_absolute_url())

        comment_form = CommentForm(request.POST)
        cooldown = timezone.now() - timedelta(seconds=settings.COMMENT_COOLDOWN_SECONDS)
        if Comment.objects.filter(author=request.user, created_at__gte=cooldown).exists():
            messages.error(request, "Easy there! Please wait a few seconds before commenting again.")
        elif comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.is_approved = settings.COMMENTS_AUTO_APPROVE
            comment.save()
            if comment.is_approved:
                messages.success(request, "Thanks! Your comment has been posted.")
            else:
                messages.success(request, "Thanks! Your comment will appear once it has been approved.")
            return redirect(f"{post.get_absolute_url()}#comments")

    comments = post.comments.filter(is_approved=True).select_related("author") if comments_open else []
    share_image = request.build_absolute_uri(post.cover_image.url) if post.cover_image else ""
    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "newer": newer,
            "older": older,
            "share_image": share_image,
            "comments": comments,
            "comments_open": comments_open,
            "comment_form": comment_form,
        },
    )


def signup(request):
    """Anyone can make an account so they can comment. These accounts can't enter the admin."""
    if request.user.is_authenticated:
        return redirect("blog:home")

    next_url = request.POST.get("next") or request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = ""

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.get_username()}! You can now comment on posts.")
            return redirect(next_url or "blog:home")
    else:
        form = SignUpForm()
    return render(request, "blog/signup.html", {"form": form, "next": next_url})


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
