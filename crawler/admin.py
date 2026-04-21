from django.contrib import admin
from .models import Domain, Page, Insight


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('id', 'domain_name', 'created_at')
    search_fields = ('domain_name',)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'status_code', 'domain', 'crawled_at')
    list_filter = ('status_code', 'domain')
    search_fields = ('url',)


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ('page', 'title', 'p_count', 'image_count', 'internal_links', 'external_links')
    search_fields = ('title', 'page__url')
