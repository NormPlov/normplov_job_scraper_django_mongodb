from rest_framework import serializers

class JobSerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', required=False) 
    uuid = serializers.UUIDField(required=False) 
    title = serializers.CharField()  
    company = serializers.CharField()
    location = serializers.CharField(required=False)
    posted_at = serializers.DateTimeField(required=False)
    description = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    salary = serializers.CharField(required=False)
    closing_date = serializers.DateTimeField(required=False)
    requirements = serializers.ListField(child=serializers.CharField(), required=False)
    responsibilities = serializers.ListField(child=serializers.CharField(), required=False)
    benefits = serializers.ListField(child=serializers.CharField(), required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    website = serializers.URLField(required=False)
    is_active = serializers.BooleanField(default=True)
    is_scraped = serializers.BooleanField(default=True)
    is_updated = serializers.BooleanField(default=False)
    logo = serializers.URLField(required=False)  
    facebook_url = serializers.URLField(required=False)  
    schedule = serializers.CharField(required=False) 
    job_type = serializers.CharField(required=False)  