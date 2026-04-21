from django.db import models


class Domain(models.Model):
    domain_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.domain_name

    class Meta:
        ordering = ['-created_at']


class Page(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='pages')
    url = models.URLField(max_length=2048)
    status_code = models.IntegerField(null=True, blank=True)
    crawled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url

    class Meta:
        ordering = ['-crawled_at']
        unique_together = ('domain', 'url')


class Insight(models.Model):
    page = models.OneToOneField(Page, on_delete=models.CASCADE, primary_key=True, related_name='insight')
    title = models.CharField(max_length=512, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    h1 = models.JSONField(default=list)
    h2 = models.JSONField(default=list)
    h3 = models.JSONField(default=list)
    p_count = models.IntegerField(default=0)
    image_count = models.IntegerField(default=0)
    internal_links = models.IntegerField(default=0)
    external_links = models.IntegerField(default=0)
    keywords = models.JSONField(default=list)  # List of {"keyword": str, "density": float}

    def __str__(self):
        return f"Insights for {self.page.url}"
