import asyncio
from datetime import datetime
from database import * 
from bs4 import BeautifulSoup
from create_browser import extension_browser
from waitelement import wait_for_element
import traceback
import json
async def address_scraper(search_data):
    print(f"main started at: {datetime.now()}")
    browser = await extension_browser("temp","temp")
    try:


        parameter_string = (
            f'fromDate={search_data["fromDate"]}&toDate={search_data["toDate"]}'
            f'&destinationAddress.destination={search_data["destination"]}'
            f'&roomCount={search_data["roomCount"]}&numAdultsPerRoom={search_data["numAdultsPerRoom"]}'
            f'&childrenCount={search_data["childrenCount"]}&childrenAges={search_data["childrenAges"]}'
            f'&useRewardsPoints=true&deviceType=desktop-web&view=list'
        )
        url = f"https://www.marriott.com/search/findHotels.mi?{parameter_string}"
        page = await browser.get(url)
        pageNumber = search_data["pageNumber"]
        if pageNumber == "":
            pageNumber = 1
        for i in range(int(pageNumber)):
            if int(pageNumber) != 1:
                    
                await page.evaluate('document.querySelector(".shop-pagination-next").click();')
                await asyncio.sleep(20)

        await wait_for_element(page,".property-card")
        await page.save_screenshot("screenshots/nodriver.png")
        await asyncio.sleep(3)
        try:
            await page.scroll_down(25)
            await asyncio.sleep(3)

        except Exception as e:
            print("scrooldown error")
            traceback.print_exc()

        await asyncio.sleep(3)
        await page.save_screenshot("screenshots/nodriver-scrolldown.png")

    except Exception as e:
        print(e)
        print("Opening search url failed")
        browser.stop()
        await address_scraper()
    
    try:
        search_html = await page.get_content()

        soup = BeautifulSoup(search_html,"html.parser")

        all_hotels = soup.find_all("div", class_="property-card")

        hotels_data_list = []
        for hotel in all_hotels:
            try:

                img_src = hotel.find("img").get("src")
                    
                title =  hotel.select_one("div.t-subtitle-xl").text
                all_hotels = await read_rows_async("hotels",columns="hotel_dict")
                for i in all_hotels:
                    if title == i["title"]:
                        continue
                

                try:
                    reviews = hotel.select_one("a[data-testid=reviews]").text
                except Exception as e:
                    reviews = None
                    print("reviews has error, reviews: ",reviews)

                description = hotel.select_one(".description-container>span").text

                hotel_link = None
                try:
                    max_guests= hotel.select_one("span.maximum-guest-label").text
                    print("Too many guests")
                    hotel_data = {
                        "fromDate":search_data["fromDate"],
                        "toDate":search_data["toDate"],
                        "destination":search_data["destination"],
                        "roomCount":search_data["roomCount"],
                        "numAdultsPerRoom":search_data["numAdultsPerRoom"],
                        "childrenCount":search_data["childrenCount"],
                        "childrenAges":search_data["childrenAges"],
                        "deviceType":"desktop-web",
                        "view":"list",
                        "error_message":"This property won’t allow that many guests in one room. Edit guests or rooms from your search."

                    }
                    continue
                except Exception as e:
                    #! come back here for hotel_link

                    hotel_link = hotel.select_one(".view-rates-button-container").get("href")

                hotel_link = f"https://www.marriott.com{hotel_link}"
                hotel_data = {
                    "fromDate":search_data["fromDate"],
                    "toDate":search_data["toDate"],
                    "destination":search_data["destination"],
                    "roomCount":search_data["roomCount"],
                    "numAdultsPerRoom":search_data["numAdultsPerRoom"],
                    "childrenCount":search_data["childrenCount"],
                    "childrenAges":search_data["childrenAges"],
                    "deviceType":"desktop-web",
                    "view":"list",
                    "banner_img":img_src,
                    "title":title,
                    "reviews":reviews,
                    "description":description,
                    "hotel_link":hotel_link

                }

                hotels_data_list.append(hotel_data)
            except Exception as e:
                print("fetching hotels has an error")
                traceback.print_exc()

        updated_hotels_data_list = []
        points_activated = False

        for hotel_data in hotels_data_list:
            try:

                print("number of hotels fetched: ",len(hotels_data_list))
                hotel_link = hotel_data["hotel_link"]
                page = await browser.get(hotel_link)
                await wait_for_element(page,".image-container")
                search_html = await page.get_content()
                soup = BeautifulSoup(search_html,"html.parser")

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
                # if not points_activated:
                #     try:
                #         await page.evaluate("""document.querySelector("input[name='useRewardsPoints']").click();document.querySelector('.search-page-btn').click();""")
                #         await asyncio.sleep(30)
                #         search_html = await page.get_content()
                #         soup = BeautifulSoup(search_html,"html.parser")
                #         points_activated = True
                #         print("points activated")
                        
                #     except Exception as e:
                #         print("points activation failed")
                #         print(e)
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

                hotel_data["rooms"] = room_data_list
                await insert_row_async("hotels",{"hotel_dict":json.dumps(hotel_data)})

                updated_hotels_data_list.append(hotel_data)
                
            except Exception as e:
                print("hotel has an error")
                traceback.print_exc()
        
        with open("hotels.json", "w", encoding="utf-8") as f:
            json.dump(updated_hotels_data_list, f, indent=4, ensure_ascii=False)
        print(f"main ended at: {datetime.now()}")

        return updated_hotels_data_list
    except Exception as e:
        with open("hotels-failsafe.json", "w", encoding="utf-8") as f:
            json.dump(hotels_data_list, f, indent=4, ensure_ascii=False)
        print("fetching all hotels failed")
        print(e)
    finally:
        browser.stop()

async def code_fetcher(search_data):
    print(f"main started at: {datetime.now()}")
    browser = await extension_browser("temp","temp")
    try:


        parameter_string = (
            f'fromDate={search_data["fromDate"]}&toDate={search_data["toDate"]}'
            f'&destinationAddress.destination={search_data["destination"]}'
            f'&roomCount={search_data["roomCount"]}&numAdultsPerRoom={search_data["numAdultsPerRoom"]}'
            f'&childrenCount={search_data["childrenCount"]}&childrenAges={search_data["childrenAges"]}'
            f'&useRewardsPoints=true&deviceType=desktop-web&view=list'
        )
        url = f"https://www.marriott.com/search/findHotels.mi?{parameter_string}"
        page = await browser.get(url)
        pageNumber = search_data["pageNumber"]
        if pageNumber == "":
            pageNumber = 1
        for i in range(int(pageNumber)):
            if int(pageNumber) != 1:
                    
                await page.evaluate('document.querySelector(".shop-pagination-next").click();')
                await asyncio.sleep(20)

        await wait_for_element(page,".property-card")

        try:
            await page.scroll_down(25)
            await asyncio.sleep(3)

        except Exception as e:
            print("scrooldown error")
            traceback.print_exc()


    except Exception as e:
        print(e)
        print("Opening search url failed")
        browser.stop()
        await code_fetcher()
    
    try:
        search_html = await page.get_content()

        soup = BeautifulSoup(search_html,"html.parser")

        all_hotels = soup.find_all("a", class_="view-rates-button-container")
        hotel_codes = [x.get("href").split("propertyCode=")[1].split("&")[0] for x in all_hotels]
        return hotel_codes
    except:
        traceback.print_exc()
    finally:
        browser.stop()