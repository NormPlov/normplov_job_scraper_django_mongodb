import requests
import uuid
import requests

from bs4 import BeautifulSoup
from scraper.models.job import Job
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
from scraper.utils.pagination import paginate_query
from rest_framework.renderers import JSONRenderer
from scraper.serializers.job_serializer import JobSerializer
import requests
from bs4 import BeautifulSoup
import uuid

class JobService:

    @staticmethod
    def get_job_by_uuid(uuid: str) -> dict:

        try:
            job = Job.objects.get(uuid=uuid)
            return JobSerializer(job).data
        except DoesNotExist:
            raise ValueError(f"Job with UUID {uuid} does not exist.")
        except Exception as e:
            raise Exception(f"Error retrieving job by UUID: {str(e)}")
        

    @staticmethod
    def scrape_jobs(website_url):
        """Scrape job data from the provided URL and save it to the database."""
        try:
            response = requests.get(website_url)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch data from {website_url}. Status code: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract fields with default fallback to None if not found
            title = soup.find('h1', class_='title').text.strip() if soup.find('h1', class_='title') else None
            company = soup.find('a', class_='sub-title').text.strip() if soup.find('a', class_='sub-title') else None
            logo = soup.find('div', class_='thumb').find('img')['src'] if soup.find('div', class_='thumb') else None
            facebook = soup.find('a', href=lambda href: href and "facebook.com" in (href or ""))
            facebook_url = facebook['href'] if facebook else None
            location = soup.find('li', class_='clearfix en', text=lambda t: "Location:" in (t or "")).find_next('span').text.strip() \
                if soup.find('li', class_='clearfix en', text=lambda t: "Location:" in (t or "")) else None
            job_type = soup.find('li', class_='clearfix en', text=lambda t: "Type :" in (t or "")).find_next('span').text.strip() \
                if soup.find('li', class_='clearfix en', text=lambda t: "Type :" in (t or "")) else None
            schedule = soup.find('li', class_='clearfix en', text=lambda t: "Schedule:" in (t or "")).find_next('span').text.strip() \
                if soup.find('li', class_='clearfix en', text=lambda t: "Schedule:" in (t or "")) else None
            salary = soup.find('li', class_='clearfix en', text=lambda t: "Salary:" in (t or "")).find_next('span').text.strip() \
                if soup.find('li', class_='clearfix en', text=lambda t: "Salary:" in (t or "")) else None

            description = soup.find('div', class_='ql-editor').text.strip() if soup.find('div', class_='ql-editor') else None
            requirements = [li.text.strip() for li in soup.select('.job-detail-req-mobile li')]
            responsibilities = [li.text.strip() for li in soup.select('.job-detail-req li')]

            email = soup.find('a', href=lambda href: href and "mailto:" in (href or ""))
            email = email['href'].split(':')[1] if email else None
            phone = None

            # Create job data dictionary
            job_data = {
                "uuid": str(uuid.uuid4()),
                "title": title,
                "company": company,
                "logo": logo,
                "facebook_url": facebook_url,
                "location": location,
                "job_type": job_type,
                "schedule": schedule,
                "salary": salary,
                "description": description,
                "requirements": requirements,
                "responsibilities": responsibilities,
                "email": email,
                "phone": phone,
                "is_active": True,
            }

            # Save the job to the database
            job = Job(**job_data)
            job.save()

            # Serialize the saved job
            return JobSerializer(job).data
        except Exception as e:
            print(f"Error occurred while scraping jobs: {e}")
            raise ValueError("An error occurred while scraping jobs")

    @staticmethod
    def create_job(data):

        existing_job = Job.objects(uuid=data["uuid"]).first()
        if existing_job:
            print(f"Job with UUID {data['uuid']} already exists. Skipping creation.")
            return existing_job 

        job = Job(**data)
        job.save()
        return job  


    @staticmethod
    def update_job(uuid, update_data):
        try:
            # Update in Django
            job = Job.objects.get(uuid=uuid)
            
            for field, value in update_data.items():
                if hasattr(job, field):
                    setattr(job, field, value)

            job.save()

            fastapi_url = f"http://136.228.158.126:3300/api/v1/jobs"
            update_data_with_uuid = {"uuid": str(uuid), **update_data}
            response = requests.post(fastapi_url, json=update_data_with_uuid)

            if response.status_code != 201:  
                raise Exception(f"Failed to update job in FastAPI. Response: {response.text}")

            return job

        except Job.DoesNotExist:
            raise ValueError(f"Job with UUID {uuid} does not exist.")

        except Exception as e:
            raise Exception(f"Error updating job: {e}")



    @staticmethod
    def get_jobs(filters, sort_by="-posted_at", page=1, page_size=10):

        query = Q()

        if "title" in filters and filters["title"]:
            query &= Q(title__icontains=filters["title"])
        if "company" in filters and filters["company"]:
            query &= Q(company__icontains=filters["company"])
        if "location" in filters and filters["location"]:
            query &= Q(location__icontains=filters["location"])
        if "is_active" in filters and filters["is_active"] is not None:
            query &= Q(is_active=filters["is_active"])

        queryset = Job.objects.filter(query)

        if sort_by:
            queryset = queryset.order_by(sort_by)

        result = paginate_query(queryset, page, page_size)

        return result
    

    @staticmethod
    def delete_job(uuid):
        
        job = Job.objects(uuid=uuid).first()
        if not job:
            raise ValueError(f"No job found with UUID: {uuid}")
        
        job.delete()
        return {"uuid": uuid, "message": "Job deleted successfully"}

