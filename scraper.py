#Testing website bot protection with nodriver browser
#Using my own browser creation without proxy 
#email and password is not necessary for this project might have to change 
#browser creation

#api_v2 will be used to fetch hotels faster it will use nodriver for js 
#and bs4 for scraping

import asyncio 
from database import * 
from address_scraper import address_scraper
from address_scraper import code_fetcher
from code_scraper import code_scraper

async def address(search_data):
    #first make another function that takes hotel titles from a page or hotel codes
    #search the database to see if those hotels are in the database or not 
    #if not run the hotel code search to fetch and return 
    #if so then just return the data
    hotel_codes = await code_fetcher(search_data)
    print(hotel_codes)
    for code in hotel_codes:
        try:
            #Search for the hotel inside database with hotel_code 
            hotels = await read_rows_async("hotels",condition="hotel_code=%s",params=[code])
            if len(hotels) > 0:
                return hotels
            hotel_data = await code_scraper(code)
            await insert_row_async("hotels",hotel_data)
            return hotel_data
        except Exception as e:
            print(e)
    pass
async def code(search_data):
    try:
        #Search for the hotel inside database with hotel_code 
        hotels = await read_rows_async("hotels",condition="hotel_code=%s",params=[search_data["hotel_code"]])
        if len(hotels) > 0:
            return hotels
        hotel_data = await code_scraper(search_data)
        await insert_row_async("hotels",hotel_data)
        return hotel_data
    except Exception as e:
        print(e)
async def handler(search_data):
    api_type = search_data["type"]
    if api_type == "address":
        return await address(search_data)
    elif api_type == "code":
        return await code(search_data)
if __name__ == "__main__":

    search_data = {
        "type":"address",
        "fromDate":"10/18/2025",
        "toDate":"10/19/2025",
        "destination":"California,+USA",
        "roomCount":"1",
        "numAdultsPerRoom":"2",
        "childrenCount":"0",
        "childrenAges":"",
        "pageNumber":"1"
    }
    data = asyncio.run(handler(search_data))
    if len(data) == 0 :
        print("failed data trying again..")
        data = asyncio.run(handler(search_data))