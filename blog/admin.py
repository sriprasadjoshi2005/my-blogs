from django.contrib import admin

from .models import Comment, ContactMessage, Post, SiteProfile, Topic

admin.site.site_header = "Blog admin"
admin.site.site_title = "Blog admin"
admin.site.index_title = "Write and manage your blog"


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_at", "updated_at")
    list_filter = ("status", "topics")
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("topics",)
    date_hierarchy = "published_at"
    fieldsets = (
        (None, {"fields": ("title", "slug", "summary", "cover_image")}),
        ("Write your post", {"fields": ("body",)}),
        ("Publishing", {"fields": ("topics", "status", "published_at")}),
    )
    actions = ["publish_selected", "unpublish_selected"]

    @admin.action(description="Publish selected posts")
    def publish_selected(self, request, queryset):
        for post in queryset:
            post.status = Post.Status.PUBLISHED
            post.save()

    @admin.action(description="Move selected posts back to draft")
    def unpublish_selected(self, request, queryset):
        queryset.update(status=Post.Status.DRAFT)


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ("About me", {"fields": ("display_name", "tagline", "photo", "about")}),
        ("Contact page", {"fields": ("contact_intro", "contact_email")}),
        ("Links", {"fields": ("github_url", "instagram_url", "x_url", "youtube_url", "linkedin_url")}),
    )

    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at")
    list_editable = ("is_read",)

    def has_add_permission(self, request):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "short_body", "created_at", "is_approved")
    list_filter = ("is_approved", "created_at")
    list_editable = ("is_approved",)
    search_fields = ("body", "author__username", "post__title")
    readonly_fields = ("post", "author", "created_at")
    actions = ["approve_selected", "hide_selected"]

    def has_add_permission(self, request):
        return False

    @admin.display(description="Comment")
    def short_body(self, obj):
        return obj.body[:60]

    @admin.action(description="Approve selected comments")
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Hide selected comments")
    def hide_selected(self, request, queryset):
        queryset.update(is_approved=False)
