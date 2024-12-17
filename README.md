# 🚀 NormPlov API Routes

## 📌 Project Overview
The **NormPlov API** is a critical sub-project designed to support the NormPlov platform. NormPlov integrates advanced data analytics, machine learning algorithms, and personalized recommendation systems to revolutionize career and academic planning. This API is built using **Django** and connects to **MongoDB**, complementing another **FastAPI** service connected to **PostgreSQL**.

---

## 🛠️ Technologies Used
- **Backend Framework**: Django (Python)
- **Database**: MongoDB
- **API Development**: Django REST Framework
- **Web Scraping**: BeautifulSoup, Requests
- **Deployment**: Gunicorn, Nginx

---

## 🔧 Installation Requirements
Ensure you have the following installed before running the project:
1. **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
2. **MongoDB**: [Install MongoDB](https://www.mongodb.com/try/download/community)

### Install Dependencies
Run the following commands in your terminal:
```bash
# Clone the repository
git clone <repository-url>
cd <repository-folder>

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

---

### 1. 📄 Job Detail
- **Method**: `GET`
- **URL**: `/jobs/<uuid>`
- **Description**: Retrieves detailed information for a specific job by its **UUID**.

---

### 2. 📃 Job List
- **Method**: `GET`
- **URL**: `/jobs`
- **Description**: Fetches a list of jobs with optional filters. Results are paginated and can be sorted.

#### Query Parameters:
| Parameter        | Type    | Description                                  | Default         |
|------------------|---------|----------------------------------------------|-----------------|
| `title`         | string  | Filter by job title                          | Optional        |
| `company`       | string  | Filter by company name                       | Optional        |
| `location`      | string  | Filter by job location                       | Optional        |
| `is_active`     | boolean | Filter by active status (`true` or `false`)  | Optional        |
| `sort_by`       | string  | Sort field (e.g., `-posted_at` for descending)| `-posted_at`    |
| `page`          | integer | Page number                                  | `1`             |
| `page_size`     | integer | Number of results per page                   | `10`            |

---

### 3. 🔄 Job Scraping
- **Method**: `POST`
- **URL**: `/jobs/scrape`
- **Description**: Initiates job scraping from a specified website URL.

#### Request Body:
```json
{
  "website_url": "<URL>"
}
```

#### Responses:
- **201**: Jobs scraped successfully.
- **400**: Validation error (e.g., missing `website_url`).
- **500**: Internal server error during scraping.

---

### 4. ✏️ Update Job
- **Method**: `PATCH`
- **URL**: `/jobs/<uuid>`
- **Description**: Updates specific fields of a job by its **UUID**.

#### Request Body:
```json
{
  "field_to_update": "value"
}
```

---

### 5. 🗑️ Delete Job
- **Method**: `DELETE`
- **URL**: `/jobs/<uuid>`
- **Description**: Deletes a job from the database using its **UUID**.

#### Responses:
- **200**: Job deleted successfully.
- **404**: Job not found.
- **500**: Unexpected error during deletion.

---

## ⚙️ Running the Project
To run the server locally, execute the following commands:
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Django server
python manage.py runserver
```

---

## 🎉 Acknowledgements
We extend our deepest gratitude to:

- **Mr. Chen Phirum**: Director of the Institute of Science and Technology Advanced Development, for his invaluable guidance, mentorship, and leadership.
- **Ms. Mom Reksmey** & **Mr. Ing Muyleang**: Exceptional mentors whose inspiring suggestions and coordination helped shape and refine this project.

✨ Thank you for making this project possible! ✨

---

## 🙌 Developers
👩‍💻 Phy Lymann

---

## 📬 Contact
- **Email**: [support@normplov.com](mailto:support@normplov.com)
- **Website**: [NormPlov](https://www.normplov.com)

---

🎉 **NormPlov API** — Empowering Education Through Technology! 🎉
