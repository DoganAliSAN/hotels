from create_browser import extension_browser
import traceback
from bs4 import BeautifulSoup
from waitelement import wait_for_element
import asyncio
import json 

async def code_scraper(search_data):
    try:
        #Browser - Url Creation - Soup
        browser = await extension_browser("temp","temp")
        temp_page = await browser.get("https://www.marriott.com") #making website recognize the ip
        await asyncio.sleep(15)
        await temp_page.evaluate("document.querySelector('.update-search-btn').click();")
        await asyncio.sleep(15)

        
        parameter_string = (
            f'propertyCode={search_data["hotel_code"]}'
            f'&fromDate={search_data["fromDate"]}&toDate={search_data["toDate"]}'
            f'&destinationAddress.destination={search_data["destination"]}'
            f'&roomCount={search_data["roomCount"]}&numAdultsPerRoom={search_data["numAdultsPerRoom"]}'
            f'&childrenCount={search_data["childrenCount"]}&childrenAges={search_data["childrenAges"]}'
            f'&useRewardsPoints=true'
        )
        hotel_link = f"https://www.marriott.com/reservation/availabilitySearch.mi?{parameter_string}"
        page = await browser.get(hotel_link)
        await wait_for_element(page,".image-container")
        search_html = await page.get_content()
        soup = BeautifulSoup(search_html,"html.parser")

        # First Simple Data
        title = soup.select_one(".hotel-name").text
        reviews = soup.select_one("[data-testid='book-PropertyRating']").text
        hotel_data = {
            "hotel_code":search_data["hotel_code"],
            "fromDate":search_data["fromDate"],
            "toDate":search_data["toDate"],
            "destination":search_data["destination"],
            "roomCount":search_data["roomCount"],
            "numAdultsPerRoom":search_data["numAdultsPerRoom"],
            "childrenCount":search_data["childrenCount"],
            "childrenAges":search_data["childrenAges"],
            "title":title,
            "reviews":reviews,
            "hotel_link":hotel_link

        }
        try:
            address = soup.select_one(".address").text
        except Exception as e:
            print("address failed\n")
            print(e)
            address=None
        hotel_data["address"] = address    
        try:
            phone_number = soup.select_one(".phone").text
        except Exception as e:
            phone_number = None
            print("phone failed\n")
            print(e)
        hotel_data["phone_number"] = phone_number

        #Determine Page Layout
        room_data_list = []
        layout_type = 0
        try:
            rooms = soup.find_all('div',{"data-testid": "RateCardV2"})
            rooms_n = await page.select_all('[data-testid="RateCardV2"]')
            for r in rooms_n:
                print(r)
                rate_button = await r.query_selector("button[data-testid='rate-button']")
                await rate_button.click()
                await asyncio.sleep(2)
                layout_type = 1
            if len(rooms_n) == 0:
                layout_type = 2
        except Exception as e:
            traceback.print_exc()
            layout_type = 2 
        print("Page layout: ",layout_type)
        
        async def room_info(page,soup):
            await asyncio.sleep(7)

            search_html = await page.get_content()
            soup = BeautifulSoup(search_html,"html.parser")
            rooms = soup.find_all("div",class_="rate-card-container")
            for i in range(len(rooms)):
                await page.scroll_down(40)
                await asyncio.sleep(2)
            print("len of rooms found: ",len(rooms))
            search_html = await page.get_content()
            soup = BeautifulSoup(search_html,"html.parser")
            rooms = soup.find_all("div",class_="rate-card-container")
            print("len of rooms found: ",len(rooms))
            for room in rooms:
                await page.select(".room-name")

                room_title = room.select_one(".room-name").text
                images_src = [x.get("src") or x.get("data-src") for x in room.find_all("img")]

                room_data = {
                    "title":room_title,
                    "images": images_src
                }

                rates = soup.find_all("div",class_="rate-details")
                rate_data_list = []

                for rate in rates:
                    rate_title = rate.select_one(".rate-name").text
                    try:
                        rate_description = rate.select_one(".rate-description").text
                    except:
                        rate_description = None
                    try:
                        prices = [x.text for x in rate.find_all("span",class_="room-rate")]

                        for i in prices:
                                
                            price_data = {
                                "tax_price":i,
                                "normal_price":i,
                            }
                    except Exception as e:
                        print("prices error: ",e)
                        price_data = {
                            "price":None,
                        }
                    
                    rate_data = {
                        "rate_title": rate_title,
                        "rate_description":rate_description,
                        "prices":price_data
                    }
                    rate_data_list.append(rate_data)
                room_data["rates"] = rate_data_list
                room_data_list.append(room_data)

        #Fetch Room info by layout
        if layout_type == 1:
            for room in rooms:
                #activate points

                await page.select(".room-name")
                room_title = room.select_one(".room-name").text
                images_src = [x.get("src") or x.get("data-src") for x in room.find_all("img")]

                room_data = {
                    "title":room_title,
                    "images": images_src
                }

                search_html = await page.get_content()
                soup = BeautifulSoup(search_html,"html.parser")

                rates = soup.find_all('div',class_='rate-card-content')
                rate_data_list=[]
                for rate in rates:
                    rate_title = rate.select_one(".title-name").text

                    try:
                        rate_description = rate.select_one(".rate-description").text
                    except:
                        rate_description = None

                    try:
                        prices = [x.text for x in rate.select_one(".price").find_all("span")]
                        price_data = {
                            "tax_price":prices[0] or None,
                            "normal_price":prices[1] or None,
                        }
                    except:
                        prices = [x.text for x in rate.select_one(".points").find_all("span")]
                        price_data = {
                            "point":prices[0] or None,
                        }

                    rate_data = {
                        "rate_title": rate_title,
                        "rate_description":rate_description,
                        "prices":price_data
                    }
                    rate_data_list.append(rate_data)
            

                room_data["rates"] = rate_data_list
                room_data_list.append(room_data)
        elif layout_type == 2:

            tablist = await page.query_selector_all("li[role='tab']")
            print("tablist: ",tablist)
            for tab in tablist:
                await tab.click()
                await asyncio.sleep(5)
                print("clicked tab")
                await room_info(page,soup)
            if len(tablist) == 0 :
                await room_info(page,soup)

        hotel_data["rooms"] = json.dumps(room_data_list)

        return hotel_data
        
    except Exception as e:
        print("hotel has an error")
        traceback.print_exc()
        browser.stop()

    finally:
        browser.stop()
        