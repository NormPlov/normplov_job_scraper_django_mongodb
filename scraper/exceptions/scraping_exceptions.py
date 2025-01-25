class ScrapingNotAllowedError(Exception):
    """Raised when scraping is not permitted by the website's robots.txt."""
    pass
