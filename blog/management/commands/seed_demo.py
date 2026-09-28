from django.core.management.base import BaseCommand

from blog.models import Post, SiteProfile, Topic

DEMO_POSTS = [
    (
        "Welcome to my blog",
        "A first post to check that everything works. Delete it whenever you like.",
        "<h2>Hello, world</h2><p>This is a demo post. Open the admin panel, click <strong>Posts</strong>, "
        "and write your own. You can drop photos anywhere in the text with the image button in the toolbar.</p>"
        "<blockquote>Every blog starts with a single post.</blockquote>",
        ["Life"],
    ),
    (
        "Why I started writing online",
        "Notes on why I finally built my own corner of the internet.",
        "<p>Social media is loud. A blog is a quiet room with your name on the door.</p>"
        "<h3>What I'll write about</h3><ul><li>Anime I loved</li><li>Things I'm learning</li><li>Small projects</li></ul>",
        ["Life", "Anime"],
    ),
    (
        "Building this site with Django",
        "A quick look at how this blog is put together.",
        "<p>The site runs on Django, with a rich text editor for writing and SQLite for storing posts.</p>",
        ["Coding"],
    ),
]


class Command(BaseCommand):
    help = "Adds a few demo posts and default About details so a fresh site isn't empty."

    def handle(self, *args, **options):
        for title, summary, body, topic_names in DEMO_POSTS:
            post, created = Post.objects.get_or_create(
                title=title,
                defaults={"summary": summary, "body": body, "status": Post.Status.PUBLISHED},
            )
            if created:
                for name in topic_names:
                    topic, _ = Topic.objects.get_or_create(name=name)
                    post.topics.add(topic)
        profile = SiteProfile.load()
        if not profile.about:
            profile.about = (
                "<p>Hi, I'm the person behind this blog. Edit this text in the admin panel under "
                "<em>About &amp; contact details</em>.</p>"
            )
            profile.save()
        self.stdout.write(self.style.SUCCESS("Demo content added."))
