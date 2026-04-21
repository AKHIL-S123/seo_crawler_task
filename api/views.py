from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from crawler.models import Domain, Insight, Page
from .serializers import DomainSerializer, InsightSerializer, PageSerializer
from .pagination import StandardResultsSetPagination


class DomainListView(generics.ListAPIView):
    """
    GET /domains/
    List all crawled domains with pagination support.
    Query params: ?page=1&page_size=10
    """
    queryset = Domain.objects.all().order_by('-created_at')
    serializer_class = DomainSerializer
    pagination_class = StandardResultsSetPagination


class DomainPageListView(generics.ListAPIView):
    """
    GET /domains/{id}/pages/
    List all pages for a specific domain.
    Query params: ?page=1&page_size=10
    """
    serializer_class = PageSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        domain_id = self.kwargs['domain_id']
        try:
            domain = Domain.objects.get(pk=domain_id)
        except Domain.DoesNotExist:
            raise NotFound(detail=f'Domain with id={domain_id} not found.')
        return Page.objects.filter(domain=domain).order_by('-crawled_at')


class PageInsightView(generics.RetrieveAPIView):
    """
    GET /pages/{id}/insights/
    Retrieve the SEO insights for a specific page.
    """
    serializer_class = InsightSerializer

    def get_object(self):
        page_id = self.kwargs['page_id']
        try:
            page = Page.objects.get(pk=page_id)
        except Page.DoesNotExist:
            raise NotFound(detail=f'Page with id={page_id} not found.')
        try:
            return page.insight
        except Insight.DoesNotExist:
            raise NotFound(detail=f'No insights found for page id={page_id}. The page may not have been crawled yet.')
