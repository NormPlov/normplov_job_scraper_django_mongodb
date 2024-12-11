from rest_framework.views import APIView
from rest_framework.response import Response
from scraper.models.job import Job  
from .serializers.job_serializer import JobSerializer
from scraper.service.job_service import JobService  
import logging

logger = logging.getLogger(__name__)


class JobListView(APIView):
    def get(self, request):
        try:
            logger.debug("Fetching jobs from MongoDB...")
            jobs = Job.objects.all()  
            logger.debug(f"Fetched {len(jobs)} jobs.")

            serializer = JobSerializer(jobs, many=True)
            logger.debug(f"Serialized data: {serializer.data}")

            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error: {e}")
            return Response({"error": str(e)}, status=500)


class JobScrapeView(APIView):
    def post(self, request):
        """Scrape job data from the website provided in the request."""
        try:
            website_url = request.data.get('website_url')  
            if not website_url:
                return Response({"error": "website_url is required."}, status=400)

            scraped_jobs = JobService.scrape_jobs(website_url)
            return Response({"message": "Jobs scraped successfully!", "data": scraped_jobs}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=500)