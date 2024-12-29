import requests
import uuid
import requests
import random
import requests
import re
import time
import logging
import jwt

from bs4 import BeautifulSoup
from scraper.models.job import Job
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
from scraper.utils.pagination import paginate_query
from scraper.serializers.job_serializer import JobSerializer
from datetime import datetime, timedelta
from urllib.robotparser import RobotFileParser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from pyppeteer import launch
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    def is_scraping_allowed(url):
        base_url = "/".join(url.split("/")[:3])
        robots_url = f"{base_url}/robots.txt"
        rp = RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception as e:
            print(f"[Warning] Failed to read robots.txt for {url}: {e}")
            return True


    @staticmethod
    def scrape_with_beautifulsoup(url):
        headers = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        ]
        selected_header = random.choice(headers)
        retries = 3

        for attempt in range(retries):
            try:
                time.sleep(random.uniform(1, 3))
                response = requests.get(url, headers=selected_header, timeout=10)
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                print(f"[Retry {attempt + 1}] Failed to fetch URL {url}. Status: {response.status_code}")
            except requests.RequestException as e:
                print(f"[Retry {attempt + 1}] Error fetching {url}: {e}")
        return None  


    @staticmethod
    def scrape_with_selenium(url, request):
        is_local = request.META.get('REMOTE_ADDR') == '127.0.0.1'

        try:
            if is_local:
                service = Service(ChromeDriverManager().install())
                options = webdriver.ChromeOptions()
                options.add_argument('--headless')
                driver = webdriver.Chrome(service=service, options=options)
            else:
                service = Service('/usr/bin/chromedriver')  
                options = webdriver.ChromeOptions()
                options.binary_location = '/usr/bin/chromium-browser'  
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920x1080')

                driver = webdriver.Chrome(service=service, options=options)

            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            job_details = JobService.extract_job_details(soup, url) 

            if job_details:
                return {"status": "success", "data": job_details} 
            else:
                logging.error(f"Scraping failed for {url}: No job details extracted")
                return {"status": "error", "message": "No job details extracted from the URL"}

        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            driver.quit()


    @staticmethod
    async def scrape_with_puppeteer(url):
        try:
            browser = await launch(headless=True)
            page = await browser.newPage()
            await page.goto(url, {'waitUntil': 'networkidle2'})
            content = await page.content()
            await browser.close()
            return BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"[Error] Puppeteer scraping failed for {url}: {e}")
            return None

    @staticmethod
    def extract_job_details(soup, url):
        def extract(selector, attribute=None):
            element = soup.select_one(selector)
            if element:
                return element[attribute] if attribute else element.get_text(strip=True)
            return None  

        def extract_list(selector):
            elements = soup.select(selector)
            return [el.get_text(strip=True) for el in elements] if elements else []

        try:
            if "bongthom.com" in url:  
                title = extract('.header-thumb .title') or "No title provided"
                company = extract('.header-thumb .sub-title') or "No company provided"
                logo = extract('.header-thumb .thumb img', 'src')
                facebook_url = extract('a[href*="facebook.com"]', 'href')
                location = extract('li:contains("Location") .value')
                posted_at = datetime.now()
                closing_date = extract('time[datetime]') or None
                description = extract('#announcemnt-description .ql-editor')
                category = extract('li:contains("Category") .value')
                job_type = extract('li:contains("Type") .value')
                schedule = extract('li:contains("Schedule") .value')
                salary = extract('li:contains("Salary") .value')

                requirements = extract_list('.job-detail-req-mobile li')
                responsibilities = extract_list('.job-detail-req li')
                benefits = extract_list('.job-benefit li')

                email = extract('a[href^="mailto:"]', 'href')
                email = email.split(':')[1] if email else None

                phone = [
                    a['href'].replace('tel:', '').strip()
                    for a in soup.select('a[href^="tel:"]') if a.get('href')
                ]

            elif "nea.gov.kh" in url:  
                title = extract('#vacancyTitle') or "No title provided"
                company = extract('.title_box strong') or "No company provided"
                logo_raw = extract('.img_box img', 'src')
                if logo_raw:
                    logo = urljoin(url, logo_raw)
                else:
                    logo = None

                facebook_raw = extract('a[href*="facebook.com"]', 'href')  
                facebook_url = None

                if facebook_raw and "javascript: fnNewOpen" in facebook_raw:
                    match = re.search(r"fnNewOpen\('([^']+)'\)", facebook_raw)
                    if match:
                        facebook_url = match.group(1)
                else:
                    facebook_url = facebook_raw  

                if not facebook_url:
                    facebook_url = "No Facebook URL provided"

                location_raw = extract('div.view_form:contains("ទីកន្លែងធ្វើការ") p.cont_box') or None
                if location_raw:
                    try:
                        location_cleaned = re.sub(r'\s+', ' ', location_raw.replace('\xa0', ' ').strip())
                        location_match = re.search(r'/\s*(.+)', location_cleaned)
                        location = location_match.group(1).strip() if location_match else "Unknown location"
                    except Exception as e:
                        location = "Unknown location"
                else:
                    location = "Unknown location"


                posted_at = datetime.now()
                closing_date = extract('.date') or None  
                closing_date_raw = extract('.date') or None  
                if closing_date_raw:
                    try:
                        closing_date_cleaned = closing_date_raw.replace("រយ:ពេលឈប់ទទូលពាក្យនៅសល់៖", "").strip()

                        days_match = re.search(r'(\d+)\s+ថ្ងៃ', closing_date_cleaned)
                        if days_match:
                            days_remaining = int(days_match.group(1)) 

                            closing_date = (datetime.now() + timedelta(days=days_remaining)).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            closing_date = "Unknown closing date"
                    except Exception as e:
                        closing_date = "Unknown closing date"
                else:
                    closing_date = "Unknown closing date"


                description_container = soup.select_one('div.form_wrap div.form_view div.view_box div.view_form.type6 div.cont_box')
                if description_container:
                    print("HTML Content of div.cont_box:\n", description_container.prettify())

                    spans = description_container.find_all('span', attrs={'style': True})
                    if spans:
                        description = "\n".join([span.get_text(strip=True) for span in spans if span.get_text(strip=True)])
                    else:
                        description = "No description provided"
                else:
                    description = "No description provided"


                category = extract('div:contains("ប្រភេទមុខតំណែង") .cont_box') or None
                contract_element = soup.find(string="កិច្ចសន្យាផ្ទាល់មាត់")  

                if contract_element:
                    job_type_element = contract_element.find_next("p", class_="cont_box") 
                    if job_type_element:
                        job_type = job_type_element.get_text(strip=True)  
                    else:
                        job_type = "Unknown job type"
                else:
                    job_type = "Unknown job type"

                schedule = extract('div:contains("ទម្រង់ការងារ") .cont_box') or None
                salary = extract('p.cont_box:contains("$")') or None

                requirements = extract_list('.job-detail-req-mobile li')

                education_raw = soup.select_one('strong.tit:contains("ការអប់រំ") + span.con')
                if education_raw:
                    education = education_raw.get_text(strip=True)
                    requirements.append(f"{education}")
                else:
                    requirements.append("Education: Not specified")

                responsibilities_raw = soup.select_one('div.view_form:contains("លក្ខខណ្ឌទាមទារមុខរបរ") .cont_box')
                if responsibilities_raw:
                    responsibilities = [responsibilities_raw.get_text(strip=True)]
                else:
                    responsibilities = ["No responsibilities provided"]

                benefits = extract_list('.form_wrap:contains("អត្ថប្រយោជន៍") .view_box .cont_box')

                emails = soup.select('a[href^="mailto:"]')

                blocked_emails = {'info@nea.gov.kh'}
                blocked_domains = {'@nea.gov.kh'}

                company_emails = []
                for email_tag in emails:
                    email = email_tag.get('href').split(':')[1] if email_tag.get('href') else None
                    if email and email not in blocked_emails and not any(email.endswith(domain) for domain in blocked_domains):
                        company_emails.append(email)

                phone = [
                    a['href'].replace('tel:', '').strip()
                    for a in soup.select('a[href^="tel:"]') if a.get('href')
                ]

            elif "cambojob.com" in url:  
                title = extract('.job-detail-left .part1 .jobs_name') or "No title provided"
                company = extract('.job-detail-right .part1 h3 a') or "No company provided"
                logo = extract('.job-detail-right .part1 .company-logo img', 'src')

                facebook_url = None 
                category = extract('.job-news-body a:contains("Recruitment Department:")') or "Unknown category"

                job_type_raw = soup.select('.job-news-body a')
                job_type = "Unknown job type"  
                for item in job_type_raw:
                    job_type_text = " ".join(item.get_text(strip=True).split()) 
                    if "Job Type:" in job_type_text:
                        job_type = job_type_text.split("Job Type:")[-1].strip()
                        break

                location_raw = soup.select('.job-news-body a')
                location = "Unknown location"  
                for item in location_raw:
                    location_text = " ".join(item.get_text(strip=True).split())  
                    if "Work Location:" in location_text:
                        location = location_text.split("Work Location:")[-1].strip()
                        break


                schedule = None
                salary = extract('.job-detail-left .part1 h4') or "No salary information"
                
                posted_at_raw_element = soup.select_one('.btns-left span img[src*="time_icon"]').find_next_sibling(text=True)
                posted_at_raw = posted_at_raw_element.strip() if posted_at_raw_element else None

                if posted_at_raw:
                    try:
                        posted_at = datetime.strptime(posted_at_raw, "%Y/%m/%d").strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        posted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
                else:
                    posted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 

                closing_date_raw_element = soup.select_one('img[src*="time_icon@2x"]')  
                if closing_date_raw_element:
                    closing_date_raw = closing_date_raw_element.find_next_sibling(text=True)  
                    if closing_date_raw:
                        try:
                            closing_date = closing_date_raw.strip()
                            closing_date = datetime.strptime(closing_date, "%Y/%m/%d").strftime('%Y-%m-%d')
                        except ValueError:
                            closing_date = "Unknown closing date" 
                    else:
                        closing_date = "Unknown closing date"
                else:
                    closing_date = "Unknown closing date"
                
                description = extract('.job-desc .job-news-body') or "No description provided"
            

                requirements_raw = soup.select('.job-news-body a')  
                education = None
                experience = None
                age = None

                for item in requirements_raw:
                    text = " ".join(item.get_text(strip=True).split())  
                    if "Education requirements" in text:
                        education = text
                    elif "Work experience" in text:
                        experience = text
                    elif "Age requirements" in text:
                        age = text

                requirements = []
                if education:
                    requirements.append(education)
                if experience:
                    requirements.append(experience)
                if age:
                    requirements.append(age)

                responsibilities_raw = extract('.job-desc .job-news-body')
                responsibilities = (
                    responsibilities_raw.split("\n") if responsibilities_raw else ["No responsibilities provided"]
                )
                benefits = extract_list('.job-detail-left .part1 h5 span') or ["No benefits specified"]
                
                email = extract('a[href^="mailto:"]', 'href')
                email = email.split(':')[1] if email else None

                phone = [
                    a['href'].replace('tel:', '').strip()
                    for a in soup.select('a[href^="tel:"]') if a.get('href')
                ]
            
            elif "https://jobify.works/jobs" in url:
                title = soup.select_one('h3.job-title')
                title = title.get_text(strip=True) if title else "No title provided"

                company = "Unknown Company"

                logo = soup.select_one('.job-top-part__container .v-image__image')
                if logo and 'background-image:' in logo.get('style', ''):
                    logo_url = logo['style'].split('url(')[-1].split(')')[0].strip('\"\'')
                    base_url = "https://jobify.works"
                    logo = f"{base_url}{logo_url}" if logo_url.startswith('/') else logo_url
                else:
                    logo = None
                    

                facebook_url = None 

                category = soup.select_one('span:contains("Category:")')
                category = category.get_text(strip=True).split("Category:")[-1].strip() if category else "Unknown category"

                job_type = "Job Opportunity"

                schedule = soup.select_one('span:contains("Job Type:")')
                if schedule:
                    schedule = schedule.get_text(strip=True).split("Job Type:")[-1].strip()
                    if schedule == "Full Time":
                        schedule = "Full-time"
                else:
                    schedule = "Unknown schedule"

                location = soup.select_one('span:contains("Location:")')
                if location:
                    location_text = location.get_text(strip=True).split("Location:")[-1].strip()
                    parts = [part.strip() for part in location_text.split(",") if part.strip()]
                    location = parts[1] if len(parts) > 1 else parts[0]
                else:
                    location = "Unknown location"


                salary = soup.select_one('span:contains("Salary:")')
                salary = salary.get_text(strip=True).split("Salary:")[-1].strip() if salary else "No salary information"

                posted_at = soup.select_one('span:contains("Published date:")')
                if posted_at:
                    try:
                        posted_at = datetime.strptime(posted_at.get_text(strip=True).split("Published date:")[-1].strip(), "%B %d, %Y")
                    except ValueError:
                        posted_at = datetime.now()
                else:
                    posted_at = datetime.now()

                closing_date = soup.select_one('span:contains("Closing date:")')
                if closing_date:
                    try:
                        closing_date = datetime.strptime(closing_date.get_text(strip=True).split("Closing date:")[-1].strip(), "%B %d, %Y")
                    except ValueError:
                        closing_date = None
                else:
                    closing_date = None

                requirements_section = soup.find('h5', string=lambda text: text and "Job Requirement" in text)
                requirements = []
                if requirements_section:
                    requirements_div = requirements_section.find_next('div', class_='text-dark')
                    if requirements_div:
                        ul = requirements_div.find('ul')
                        if ul:
                            requirements = [li.get_text(strip=True).replace('\xa0', ' ') for li in ul.find_all('li')]

                if not requirements:
                    requirements = ["No requirements provided"]

                responsibilities_section = soup.find('h5', string=lambda text: text and "Job Responsibility" in text)
                responsibilities = []
                if responsibilities_section:
                    responsibilities_div = responsibilities_section.find_next('div', class_='text-dark')
                    if responsibilities_div:
                        ul = responsibilities_div.find('ul')
                        if ul:
                            responsibilities = [li.get_text(strip=True).replace('\xa0', ' ') for li in ul.find_all('li')]

                if not responsibilities:
                    responsibilities = ["No responsibilities provided"]

                description_section = soup.find('h5', string=lambda text: text and "Job Description" in text)
                description = "No description provided"
                if description_section:
                    description_div = description_section.find_next('div', class_='text-dark')
                    if description_div:
                        nested_div = description_div.find('div', recursive=False)
                        if nested_div:
                            paragraph = nested_div.find('p', recursive=True)
                            if paragraph:
                                description = paragraph.get_text(strip=True)

                benefits_section = soup.find('h5', string=lambda text: text and "Employee Benefit" in text)
                benefits = []
                if benefits_section:
                    benefits_div = benefits_section.find_next('div', class_='text-dark')
                    if benefits_div:
                        ul = benefits_div.find('ul')
                        if ul:
                            benefits = [li.get_text(strip=True).replace('\xa0', ' ') for li in ul.find_all('li')]

                if not benefits:
                    benefits = ["No benefits provided"]

                email_raw = soup.select_one('a[href^="mailto:"]')
                email = email_raw.get('href').split(':')[1] if email_raw else None

                phone_raw = soup.select('a[href^="tel:"]')
                phone = [a.get('href').split(':')[1] for a in phone_raw] if phone_raw else []


            elif "camhr.com" in url:   
                title = extract('.job-name-span.text-break') or "No title provided"

                posted_at = extract('.send-date span') or "No publish date provided"
                closing_date = extract('.send-date .close-date') or "No closing date provided"

                company = extract('.compnay-name') or "No company provided"
                logo = extract('.company-head-img', 'src')

                location = extract('.location-item') or "Unknown location"
                salary = extract('.salary-fs-28') or "Negotiable"

                description = extract('.descript-list') or "No description provided"
                requirements = extract('.fs-14.descript-list') or "No requirements provided"

                email = extract('a[href^="mailto:"]', 'href')
                email = email.split(':')[1] if email else None
                phone = [a['href'].replace('tel:', '').strip() for a in soup.select('a[href^="tel:"]') if a.get('href')]

                responsibilities = extract('.fs-14.descript-list') or ["No responsibilities provided"]

                benefits = extract_list('.form-wrap .view-box .cont-box') or ["No benefits provided"]

                facebook_url = extract('a[href*="facebook.com"]', 'href') or "No Facebook URL provided"

                category_row = soup.select_one('.mailTable .column:contains("Function")')
                category = None
                if category_row:
                    category = category_row.find_next('td').get_text(strip=True) or "No category provided"

                schedule_row = soup.select_one('.mailTable .column:contains("Term")')
                schedule = None
                if schedule_row:
                    schedule = schedule_row.find_next('td').get_text(strip=True) or "No schedule provided"
                    if schedule == "Full Time":
                        schedule = "Full-time"

                job_type = "Job Opportunity"

            elif "pelprek.com" in url:
                title = extract('.title_job_detaill') or "No title provided"
                company = extract('.company-name') or "No company provided"
                logo = extract('.company-logo img', 'src') or None
                location = extract('.job-location') or "Unknown location"
                posted_at = extract('.job-schedule .i-right') or "No publish date provided"
                closing_date = extract('.closing-date .i-right') or "No closing date provided"
                salary = extract('.job-salary') or "Negotiable"
                description = extract('.job-desc') or "No description provided"
                requirements = extract_list('.requirements') or ["No requirements provided"]
                responsibilities = extract_list('.responsibilities') or ["No responsibilities provided"]
                benefits = extract_list('.benefits') or ["No benefits provided"]
                facebook_url = extract('a[href*="facebook.com"]', 'href') or "No Facebook URL provided"
                category = None
                schedule = extract('.job-schedule .i-right') or "No schedule provided"
                job_type = "Job Opportunity"

                # Extract the email from the "How to Apply" section
                email_text = extract('.sect-part__title:contains("HOW TO APPLY") + div p')
                email = None
                if email_text:
                    # Extract the email from the text, after "Email:"
                    match = re.search(r'Email:\s*([\w\.-]+@[\w\.-]+)', email_text)
                    if match:
                        email = match.group(1)
                if not email:
                    email = "No email provided"

                # Extracting phone number(s) from the page (looking for 'tel:' links)
                phone_numbers = extract_list('a[href^="tel:"]')
                phone = None
                if phone_numbers:
                    # We assume the first phone number is the main one
                    phone = phone_numbers[0]
                if not phone:
                    phone = "No phone provided"

            else:
                raise ValueError("Unsupported source URL")
                

            job_data = {
                "uuid": str(uuid.uuid4()),
                "title": title,
                "company": company,
                "logo": logo,
                "facebook_url": facebook_url,
                "location": location,
                "posted_at": posted_at,
                "description": description,
                "category": category,
                "job_type": job_type,
                "schedule": schedule,
                "salary": salary,
                "closing_date": closing_date,
                "requirements": requirements or [],
                "responsibilities": responsibilities or ["No responsibilities provided"],
                "benefits": benefits or None,
                "email": email,
                "phone": phone,
                "website": url,
                "is_active": True,
            }

            return job_data

        except Exception as e:
            print(f"[Error] Failed to extract job details from {url}: {e}")
            raise ValueError(f"An error occurred while extracting job details: {e}")

    @staticmethod
    def save_to_db(job_data):
        try:
            job = Job(**job_data)
            job.save()
            print(f"Job saved to database: {job.uuid}")
        except Exception as e:
            print(f"[Error] Failed to save job to database: {e}")

    @staticmethod
    async def scrape_jobs(url):
        try:
            if not JobService.is_scraping_allowed(url):
                logging.warning(f"Scraping not allowed for {url}")
                return None

            if "jobify.works" in url or "camhr.com" in url or "pelprek.com" in url:
                soup = JobService.scrape_with_selenium(url)
                if not soup:
                    raise ValueError(f"Failed to scrape with Selenium from {url}.")
            else:
                soup = JobService.scrape_with_beautifulsoup(url)

            job_data = JobService.extract_job_details(soup, url)
            JobService.save_to_db(job_data)
            return job_data

        except Exception as e:
            logging.error(f"Failed to scrape jobs from {url}: {e}")
            raise


    @staticmethod
    def update_job(uuid, update_data, token):
        try:
            try:
                decoded_token = jwt.decode(token.split()[1], settings.JWT_SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                raise ValueError("Token has expired.")
            except jwt.InvalidTokenError:
                raise ValueError("Invalid token.")

            job = Job.objects.get(uuid=uuid)

            for field, value in update_data.items():
                if hasattr(job, field):
                    setattr(job, field, value)

            job.is_updated = True
            job.save()

            data = {
                "uuid": str(job.uuid),
                "title": getattr(job, "title", ""),
                "company": getattr(job, "company", ""),
                "facebook_url": getattr(job, "facebook_url", ""),
                "location": getattr(job, "location", ""),
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                "description": getattr(job, "description", ""),
                "category": getattr(job, "category", ""),
                "job_type": getattr(job, "job_type", ""),
                "schedule": getattr(job, "schedule", ""),
                "salary": getattr(job, "salary", ""),
                "closing_date": job.closing_date.isoformat() if job.closing_date else None,
                "requirements": ",".join(getattr(job, "requirements", [])),
                "responsibilities": ",".join(getattr(job, "responsibilities", [])),
                "benefits": ",".join(getattr(job, "benefits", [])),
                "email": getattr(job, "email", ""),
                "phone": ",".join(getattr(job, "phone", [])),
                "website": getattr(job, "website", ""),
                "is_active": getattr(job, "is_active", True),
                "is_scraped": getattr(job, "is_scraped", True),
            }

            headers = {"Authorization": token}

            files = {}
            if job.logo:
                try:
                    logo_content = requests.get(job.logo, timeout=10).content
                    files["logo"] = ("logo.png", logo_content)
                except requests.RequestException as e:
                    raise Exception(f"Error fetching logo: {e}")

            fastapi_url = "http://136.228.158.126:3300/api/v1/jobs"
            response = requests.post(fastapi_url, data=data, files=files, headers=headers)

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

        query &= Q(is_updated=False)

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

