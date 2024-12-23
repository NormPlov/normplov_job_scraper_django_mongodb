import requests
import uuid
import requests
import random
import time
import requests

from bs4 import BeautifulSoup
from scraper.models.job import Job
from scraper.utils.url import validate_url
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
from scraper.utils.pagination import paginate_query
from scraper.serializers.job_serializer import JobSerializer
from datetime import datetime

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
            headers = [
                {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
                {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            ]
            selected_header = random.choice(headers)
            
            retries = 3
            for attempt in range(retries):
                try:
                    time.sleep(random.uniform(1, 3))
                    response = requests.get(website_url, headers=selected_header, timeout=10)
                    if response.status_code == 200:
                        break
                    print(f"[Retry {attempt + 1}] Failed to fetch URL. Status: {response.status_code}")
                except requests.RequestException as e:
                    print(f"[Retry {attempt + 1}] Error: {e}")
            else:
                raise ValueError(f"Failed to fetch data from {website_url} after {retries} attempts.")

            soup = BeautifulSoup(response.text, 'html.parser')

            def extract_text(selector, key):
                element = soup.select_one(selector)
                return element.text.strip() if element else None

            title = extract_text('h1.title', 'Title')
            company = extract_text('a.sub-title', 'Company')
            logo_tag = soup.find('div', class_='thumb')
            logo = validate_url(logo_tag.find('img')['src'] if logo_tag and logo_tag.find('img') else None)

            facebook = soup.find('a', href=lambda href: href and "facebook.com" in (href or ""))
            facebook_url = validate_url(facebook['href'] if facebook else None)

            location = extract_text('li.clearfix.en:-soup-contains("Location:") span', 'Location')
            job_type = extract_text('li.clearfix.en:-soup-contains("Type :") span', 'Job Type')
            schedule = extract_text('li.clearfix.en:-soup-contains("Schedule:") span', 'Schedule')
            salary = extract_text('li.clearfix.en:-soup-contains("Salary:") span', 'Salary')
            category = extract_text('li.clearfix.en:-soup-contains("Category:") span', 'Category')
            description = extract_text('div.ql-editor', 'Description')

            requirements = [li.text.strip() for li in soup.select('.job-detail-req-mobile li')] or None
            responsibilities = [li.text.strip() for li in soup.select('.job-detail-req li')] or None
            benefits = [li.text.strip() for li in soup.select('.job-benefit li')] or None

            phone_elements = soup.select('strong:contains("Phone") + ul.no-list li a[href^="tel:"]')
            phones = [phone['href'].replace('tel:', '').strip() for phone in phone_elements if phone.get('href')]

            website_elements = soup.select('strong:contains("Website") + ul.no-list li a[href^="http"]')
            websites = [validate_url(link['href']) for link in website_elements if link.get('href')]

            email_tag = soup.find('a', href=lambda href: href and "mailto:" in (href or ""))
            email = email_tag['href'].split(':')[1] if email_tag else None

            posted_at = datetime.now() 
            closing_date = None  

            job_data = {
                "uuid": str(uuid.uuid4()),
                "title": title or "No title provided",
                "company": company or "No company provided",
                "logo": logo,
                "facebook_url": facebook_url,
                "location": location,
                "job_type": job_type,
                "schedule": schedule,
                "salary": salary,
                "description": description,
                "category": category,
                "requirements": requirements,
                "responsibilities": responsibilities,
                "benefits": benefits,
                "email": email,
                "phone": phones,
                "website": website_url,
                "posted_at": posted_at,
                "closing_date": closing_date,
                "is_active": True,
            }

            job = Job(**job_data)
            job.save()

            return JobSerializer(job).data

        except Exception as e:
            print(f"[Error] Failed to scrape job: {e}")
            raise ValueError(f"An error occurred while scraping the job: {e}")
        

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

