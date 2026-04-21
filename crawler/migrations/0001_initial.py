from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain_name', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=2048)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('crawled_at', models.DateTimeField(auto_now_add=True)),
                ('domain', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pages',
                    to='crawler.domain',
                )),
            ],
            options={'ordering': ['-crawled_at']},
        ),
        migrations.AddConstraint(
            model_name='page',
            constraint=models.UniqueConstraint(fields=['domain', 'url'], name='unique_domain_url'),
        ),
        migrations.CreateModel(
            name='Insight',
            fields=[
                ('page', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='insight',
                    serialize=False,
                    to='crawler.page',
                )),
                ('title', models.CharField(blank=True, max_length=512, null=True)),
                ('meta_description', models.TextField(blank=True, null=True)),
                ('h1', models.JSONField(default=list)),
                ('h2', models.JSONField(default=list)),
                ('h3', models.JSONField(default=list)),
                ('p_count', models.IntegerField(default=0)),
                ('image_count', models.IntegerField(default=0)),
                ('internal_links', models.IntegerField(default=0)),
                ('external_links', models.IntegerField(default=0)),
                ('keywords', models.JSONField(default=list)),
            ],
        ),
    ]
