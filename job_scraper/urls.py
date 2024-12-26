from django.urls import path
from django.http import JsonResponse  
from scraper.views.job_views import JobListView, JobScrapeView, UpdateJobView, DeleteJobView, JobDetailView


def root_view(request):
    return JsonResponse({"message": "Welcome to the Job Scraper API!"})  

urlpatterns = [
    path('', root_view, name='root'), 
    path('api/v1/jobs', JobListView.as_view(), name='job-list'),
    path('api/v1/job-scraper', JobScrapeView.as_view(), name='job-scraper'),
    path('api/v1/jobs/update/<str:uuid>', UpdateJobView.as_view(), name='update-job'),
    path('api/v1/jobs/delete/<str:uuid>', DeleteJobView.as_view(), name='delete-job'),
    path("api/v1/jobs/<str:uuid>", JobDetailView.as_view(), name="job-detail"),
]


