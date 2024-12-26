import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from scraper.models.job import Job  
from ..serializers.job_serializer import JobSerializer
from scraper.services.job_service import JobService 
from rest_framework import status 
from scraper.utils.response import BaseResponse
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR


logger = logging.getLogger(__name__)


class JobDetailView(APIView):
    def get(self, request, uuid):
        """Retrieve a job's detailed information by UUID."""
        try:
            job_details = JobService.get_job_by_uuid(uuid)
            return BaseResponse(
                status=status.HTTP_200_OK,
                message="Job retrieved successfully.",
                payload=job_details,
            )
        except ValueError as e:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Job not found.",
                payload={"error": str(e)},
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An error occurred while retrieving the job.",
                payload={"error": str(e)},
            )

class JobListView(APIView):
    def get(self, request):

        filters = {
            "title": request.query_params.get("title"),
            "company": request.query_params.get("company"),
            "location": request.query_params.get("location"),
            "is_active": request.query_params.get("is_active") == "true" if request.query_params.get("is_active") else None,
        }
        sort_by = request.query_params.get("sort_by", "-posted_at")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        try:
            result = JobService.get_jobs(filters, sort_by, page, page_size)

            serialized_jobs = JobSerializer(result["data"], many=True)

            return BaseResponse(
                status=200,
                message="Jobs retrieved successfully",
                payload={
                    "jobs": serialized_jobs.data,
                    "meta": result["meta"],
                }
            )

        except Exception as e:
            return BaseResponse(
                status=500,
                message="An error occurred while fetching jobs",
                payload={"error": str(e)}
            )


class JobScrapeView(APIView):
    def post(self, request):
        try:
            website_url = request.data.get('url')

            if not website_url:
                return BaseResponse(
                    status=HTTP_400_BAD_REQUEST,
                    message="Validation error",
                    payload={"error": "The 'website_url' field is required."}
                )

            scraped_jobs = JobService.scrape_jobs(website_url)

            return BaseResponse(
                status=HTTP_201_CREATED,
                message="Jobs scraped successfully!",
                payload={"jobs": scraped_jobs}
            )

        except Exception as e:
            return BaseResponse(
                status=HTTP_500_INTERNAL_SERVER_ERROR,
                message="An error occurred while scraping jobs",
                payload={"error": str(e)}
            )
        

class UpdateJobView(APIView):
    def patch(self, request, uuid):
        update_data = request.data

        try:
            updated_job = JobService.update_job(uuid, update_data)

            job_dict = updated_job.to_mongo().to_dict()
            job_dict["_id"] = str(job_dict["_id"])

            return BaseResponse(
                status=status.HTTP_200_OK,
                message="Job updated successfully in both Django and FastAPI",
                payload={"job": job_dict}
            )

        except ValueError as e:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Job not found",
                payload={"error": str(e)}
            )

        except Exception as e:
            return BaseResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An error occurred while updating the job",
                payload={"error": str(e)}
            )

        

class DeleteJobView(APIView):

    def delete(self, request, uuid):
        try:
            result = JobService.delete_job(uuid)

            return BaseResponse(
                status=status.HTTP_200_OK,
                message="Job deleted successfully",
                payload=result
            )

        except ValueError as e:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Job not found",
                payload={"error": str(e)}
            )

        except Exception as e:
            return BaseResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred while deleting the job",
                payload={"error": str(e)}
            )