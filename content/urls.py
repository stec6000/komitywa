from django.urls import path

from . import views


app_name = "content"

urlpatterns = [
    path("", views.BlogListView.as_view(), name="blog_list"),
    path(
        "admin/content/weeklyresearch/<int:pk>/stories.zip",
        views.WeeklyResearchStoriesZipView.as_view(),
        name="weeklyresearch_stories_zip",
    ),
    path("<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
]
