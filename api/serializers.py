from rest_framework import serializers
from crawler.models import Domain, Page, Insight


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'domain_name', 'created_at']


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'url', 'status_code', 'crawled_at']


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = [
            'title',
            'meta_description',
            'h1',
            'h2',
            'h3',
            'p_count',
            'image_count',
            'internal_links',
            'external_links',
            'keywords',
        ]
