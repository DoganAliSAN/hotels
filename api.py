from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from scraper import handler 
from fetch_ip import fetch_ip
app = FastAPI()

# Define input schema
class ScrapeRequest(BaseModel):
    params: dict

@app.post("/scrape")
async def scrape_endpoint(req: ScrapeRequest):
    result = await handler(req.params)
    return result
@app.get("/ip")
async def ip():
    ip = await fetch_ip()
    return ip
@app.get("/test")
async def test_endpoint():
    return 200