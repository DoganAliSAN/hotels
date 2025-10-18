from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from scraper import handler 
app = FastAPI()

# Define input schema
class ScrapeRequest(BaseModel):
    params: dict

@app.post("/scrape")
async def scrape_endpoint(req: ScrapeRequest):
    result = await handler(req.params)
    return result
