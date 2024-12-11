import uuid
from mongoengine import Document, StringField, DateTimeField, ListField, BooleanField, URLField

class Job(Document):
    meta = {'collection': 'jobs'}  

    uuid = StringField(default=lambda: str(uuid.uuid4()), unique=True, required=True)
    title = StringField(required=True) 
    company = StringField(required=True) 
    location = StringField(required=False)  
    posted_at = DateTimeField(required=False) 
    description = StringField(required=False) 
    category = StringField(required=False) 
    type = StringField(required=False)  
    salary = StringField(required=False)  
    closing_date = DateTimeField(required=False)  
    requirements = ListField(StringField(), required=False)  
    responsibilities = ListField(StringField(), required=False)  
    benefits = ListField(StringField(), required=False)  
    email = StringField(required=False)  
    phone = StringField(required=False) 
    website = URLField(required=False)  
    is_active = BooleanField(default=True)  

