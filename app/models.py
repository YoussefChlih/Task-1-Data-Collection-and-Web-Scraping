from pydantic import BaseModel, HttpUrl, validator
from typing import Optional

class ScrapeRequest(BaseModel):
    url: HttpUrl
    selector: Optional[str] = None
    format: str

    @validator('format')
    def validate_format(cls, v):
        if v not in ['csv', 'xlsx', 'json', 'txt']:
            raise ValueError('Invalid format')
        return v

    @validator('url')
    def validate_url(cls, v):
        if str(v).startswith(('http://', 'https://')):
            return v
        raise ValueError('URL must be HTTP or HTTPS')
