import requests
import uuid

from bs4 import BeautifulSoup
from scraper.models.job import Job
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
from scraper.utils.pagination import paginate_query

class JobService:
    @staticmethod
    def scrape_jobs(website_url):
        """Scrape job data from the provided URL and save it to the database."""

        response = requests.get(website_url)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data from {website_url}. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1', class_='title').text.strip()
        company = soup.find('a', class_='sub-title').text.strip()
        location = soup.find('span', text='Location:').find_next_sibling('span').text.strip() if soup.find('span', text='Location:') else None
        posted_at = soup.find('time').text.strip() if soup.find('time') else None
        closing_date = soup.find('strong', text='Closing Date:').find_next_sibling('time').text.strip() if soup.find('strong', text='Closing Date:') else None
        category = soup.find('span', text='Category:').find_next_sibling('span').text.strip() if soup.find('span', text='Category:') else None
        job_type = soup.find('span', text='Type :').find_next_sibling('span').text.strip() if soup.find('span', text='Type :') else None
        salary = soup.find('span', text='Salary:').find_next_sibling('span').text.strip() if soup.find('span', text='Salary:') else None
        description = soup.find('div', class_='ql-editor').text.strip() if soup.find('div', class_='ql-editor') else None

        requirements = [
            li.text.strip()
            for li in soup.select('.job-detail-req-mobile li')
        ]
        responsibilities = [
            li.text.strip()
            for li in soup.select('.job-detail-req li')
        ]

        email = soup.find('a', href=lambda href: href and "mailto:" in href)
        email = email.text.strip() if email else None
        phone = None  

        job_data = {
            "uuid": str(uuid.uuid4()),
            "title": title,
            "company": company,
            "location": location,
            "posted_at": posted_at,
            "closing_date": closing_date,
            "category": category,
            "type": job_type,
            "salary": salary,
            "description": description,
            "requirements": requirements,
            "responsibilities": responsibilities,
            "email": email,
            "phone": phone,
            "is_active": True,  
        }

        JobService.create_job(job_data)

        print(f"Scraped and saved job: {title}")
        return job_data

    @staticmethod
    def create_job(data):
        """Create a new job."""
        # Check if a job with the same UUID already exists
        existing_job = Job.objects(uuid=data["uuid"]).first()
        if existing_job:
            print(f"Job with UUID {data['uuid']} already exists. Skipping creation.")
            return existing_job

        # Create and save the new job
        job = Job(**data)
        job.save()
        return job
    

    @staticmethod
    def update_job(uuid, update_data):
    
        try:
            job = Job.objects.get(uuid=uuid)
            
            for field, value in update_data.items():
                if hasattr(job, field): 
                    setattr(job, field, value)
            
            # Save changes
            job.save()
            return job
        except DoesNotExist:
            raise ValueError(f"Job with UUID {uuid} does not exist.")
        


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

