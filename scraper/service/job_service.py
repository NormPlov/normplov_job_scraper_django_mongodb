import requests
from bs4 import BeautifulSoup
from scraper.models.job import Job

class JobService:
    @staticmethod
    def scrape_jobs(website_url):
        """Scrape job data from the provided URL and save it to the database."""

        response = requests.get(website_url)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data from {website_url}. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the job details
        title = soup.find('h1', class_='title').text.strip()
        company = soup.find('a', class_='sub-title').text.strip()
        location = soup.find('span', text='Location:').find_next_sibling('span').text.strip() if soup.find('span', text='Location:') else None
        posted_at = soup.find('time').text.strip() if soup.find('time') else None
        closing_date = soup.find('strong', text='Closing Date:').find_next_sibling('time').text.strip() if soup.find('strong', text='Closing Date:') else None
        category = soup.find('span', text='Category:').find_next_sibling('span').text.strip() if soup.find('span', text='Category:') else None
        job_type = soup.find('span', text='Type :').find_next_sibling('span').text.strip() if soup.find('span', text='Type :') else None
        salary = soup.find('span', text='Salary:').find_next_sibling('span').text.strip() if soup.find('span', text='Salary:') else None
        description = soup.find('div', class_='ql-editor').text.strip() if soup.find('div', class_='ql-editor') else None

        # Extract requirements and responsibilities
        requirements = [
            li.text.strip()
            for li in soup.select('.job-detail-req-mobile li')
        ]
        responsibilities = [
            li.text.strip()
            for li in soup.select('.job-detail-req li')
        ]

        # Extract email and phone
        email = soup.find('a', href=lambda href: href and "mailto:" in href)
        email = email.text.strip() if email else None
        phone = None  # Add logic to extract phone if available

        job_data = {
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
        job = Job(**data)
        job.save()
        return job
