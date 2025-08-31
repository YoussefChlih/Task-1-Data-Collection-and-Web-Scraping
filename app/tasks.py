from celery import Celery
import os

celery_app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@celery_app.task
def scrape_task(job_id, url, selector, format):
    from .utils import scrape_data, generate_file
    data = scrape_data(url, selector)
    file_content = generate_file(data, format)
    # Store file_content in Redis or file system
    # Simplified: save to temp
    with open(f"temp/{job_id}.{format}", 'wb') as f:
        f.write(file_content)
    return job_id
