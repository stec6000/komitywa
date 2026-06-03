import zipfile
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, ListView

from .models import BlogPost, WeeklyResearch


class BlogListView(ListView):
    model = BlogPost
    template_name = "content/blog_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return BlogPost.objects.published().select_related("source_research")


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = "content/blog_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        # Tylko opublikowane są dostępne publicznie
        return BlogPost.objects.published()


class WeeklyResearchStoriesZipView(View):
    """Staff-only download endpoint: ZIP all generated story PNGs for a WR."""

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        wr = get_object_or_404(WeeklyResearch, pk=pk)
        stories_dir = (
            Path(settings.MEDIA_ROOT)
            / "weekly_research"
            / wr.week_label
            / "stories"
        )
        if not stories_dir.exists():
            return HttpResponseNotFound("Brak wygenerowanych grafik")
        pngs = sorted(stories_dir.glob("*.png"))
        if not pngs:
            return HttpResponseNotFound("Brak wygenerowanych grafik")
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for png in pngs:
                zf.write(png, arcname=png.name)
        buf.seek(0)
        resp = HttpResponse(buf.getvalue(), content_type="application/zip")
        resp["Content-Disposition"] = (
            f'attachment; filename="stories_{wr.week_label}.zip"'
        )
        return resp
