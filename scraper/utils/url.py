from urllib.parse import urlparse

def validate_url(url):
    if url and urlparse(url).scheme in ['http', 'https']:
        return url
    return None  

