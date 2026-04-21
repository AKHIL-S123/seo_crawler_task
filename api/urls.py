from django.urls import path
from .views import DomainListView, DomainPageListView, PageInsightView

urlpatterns = [
    path('domains/', DomainListView.as_view(), name='domain-list'),
    path('domains/<int:domain_id>/pages/', DomainPageListView.as_view(), name='domain-pages'),
    path('pages/<int:page_id>/insights/', PageInsightView.as_view(), name='page-insights'),
]
