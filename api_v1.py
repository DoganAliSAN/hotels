#Testing website bot protection with nodriver browser
#Using my own browser creation without proxy 
#email and password is not necessary for this project might have to change 
#browser creation

#this api_v1 is so slow it uses nodriver to scrape
#it needs scrolldown to load every hotel information
from create_browser import extension_browser
import asyncio 
import time
import traceback
import json

async def wait_for_element(page,selector):
    start_time = time.time()
    try:
        await page.select(selector)
        await asyncio.sleep(10)
    except:
        await asyncio.sleep(25)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Execution time: {elapsed:.2f} seconds")
async def main(search_data: dict):
    browser = await extension_browser("ertepberke@gmail.com","11024076742Da")
    try:

        parameter_string = (
            f'fromDate={search_data["fromDate"]}&toDate={search_data["toDate"]}'
            f'&destinationAddress.destination={search_data["destination"]}'
            f'&roomCount={search_data["roomCount"]}&numAdultsPerRoom={search_data["numAdultsPerRoom"]}'
            f'&childrenCount={search_data["childrenCount"]}&childrenAges={search_data["childrenAges"]}'
            f'&deviceType=desktop-web&view=list'
        )
        url = f"https://www.marriott.com/search/findHotels.mi?{parameter_string}"
        page = await browser.get(url)
        await wait_for_element(page,".property-card")
        await page.save_screenshot("screenshots/nodriver.png")
        await asyncio.sleep(3)
    except Exception as e:
        print(e)
        print("Opening search url failed")
        browser.stop()
        await main()
    
    try:
        all_hotels = await page.select_all(".property-card")
        hotels_data_list = []
        for hotel in all_hotels:
            try:
                async def banner_get():
                    try:
                        await asyncio.sleep(10)
                        banner = await hotel.query_selector("img")
                        banner_attr = banner.attributes
                        img_src = banner_attr[banner_attr.index("src") + 1]
                        return img_src
                    except AttributeError:
                        return False
                img_src = False
                while not img_src:
                    await asyncio.sleep(5)
                    img_src = await banner_get()

                    
                title = await hotel.query_selector("div.t-subtitle-xl")
                title = title.text

                reviews = await hotel.query_selector("a[data-testid=reviews]")
                try:
                    reviews = reviews.text
                except Exception as e:
                    reviews = None
                    print("reviews has error reviews: ",reviews)

                description = await hotel.query_selector(".description-container>span")
                description = description.text
                hotel_link = None
                try:
                    max_guests= await hotel.query_selector(".max-quests")
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
                    print("No max guests error")
                    traceback.print_exc()
                    hotel_link = await hotel.query_selector(".view-rates-button-container")
                print(hotel_link)

                hotel_link = f"https://www.marriott.com/{hotel_link.attributes[hotel_link.attributes.index('href')+1]}"
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
        for hotel_data in hotels_data_list:
            try:
                print("number of hotels fetched: ",len(updated_hotels_data_list))
                hotel_link = hotel_data["hotel_link"]
                page = await browser.get(hotel_link)
                await wait_for_element(page,".image-container")
                try:
                    address = await page.query_selector(".address")
                    print(address)
                    address= str(address).replace('<p class="ml-1 d-none d-lg-inline-block mb-0 address">','').replace("</p>","")
                    print(address)
                    hotel_data["address"] = address
                except Exception as e:
                    print("address failed\n")
                    print(e)
                    address=None
                try:
                    phone_number = await page.query_selector('.phone')
                    phone_number= str(phone_number).replace('<span dir="ltr" class="mr-3 ml-1 phone">','').replace("</span>","")
                    hotel_data["phone_number"] = phone_number
                except Exception as e:
                    print("phone failed\n")
                    print(e)
                try:
                    await page.evaluate("""document.querySelector("input[name='useRewardsPoints']").click();document.querySelector('.search-page-btn').click();""")
                    await asyncio.sleep(30)
                except Exception as e:
                    print("points activation failed")
                    print(e)
                rooms = await page.select_all('[data-testid="RateCardV2"]')
                room_data_list = []
                for room in rooms:
                    #activate points

                    await page.select(".room-name")
                    room_title = await room.query_selector(".room-name")
                    room_title = room_title.text
                    images = await room.query_selector_all("img")

                    images_src = []
                    for x in images:
                        try:
                            images_src.append(x.attributes[x.attributes.index("src") + 1])
                        except:
                            pass
                        try:
                            images_src.append(x.attributes[x.attributes.index("data-src") + 1])
                        except Exception as e:
                            print(e)

                    room_data = {
                        "title":room_title,
                        "images": images_src
                    }
                    rate_button = await room.query_selector("button[data-testid='rate-button']")
                    await rate_button.click()


                    rates = await room.query_selector_all(".rate-card-content")
                    rate_data_list=[]
                    for rate in rates:

                        rate_title = await rate.query_selector(".title-name")
                        rate_title = rate_title.text

                        try:
                            rate_description = await rate.query_selector(".rate-description")
                            rate_description = rate_description.text
                        except:
                            rate_description = None
                        
                        async def get_prices():
                            rate_prices = await rate.query_selector_all(".price>span")
                            rate_prices = [x.text for x in rate_prices]
                            if len(rate_prices) ==0:

                                rate_prices = await rate.query_selector(".points>span")
                                rate_prices = [str(rate_prices).replace('<span class="">','').replace("</span>","")]

                            return rate_prices
                        
                        prices = False
                        while not prices:
                            prices =  await get_prices()
                            await asyncio.sleep(5)
                        price_data = {
                            "tax_price":prices[0] or None,
                            "normal_price":prices[1] or None,
                        }
                        rate_data = {
                            "rate_title": rate_title,
                            "rate_description":rate_description,
                            "prices":price_data
                        }
                        rate_data_list.append(rate_data)

                    room_data["rates"] = rate_data_list
                    room_data_list.append(room_data)
                hotel_data["rooms"] = room_data_list
                updated_hotels_data_list.append(hotel_data)
                break
            except Exception as e:
                print("hotel has an error")
                traceback.print_exc()

        with open("hotels.json", "w", encoding="utf-8") as f:
            json.dump(hotels_data_list, f, indent=4, ensure_ascii=False)
    except Exception as e:
        with open("hotels-failsafe.json", "w", encoding="utf-8") as f:
            json.dump(hotels_data_list, f, indent=4, ensure_ascii=False)
        print("fetching all hotels failed")
        print(e)


search_data = {
    "fromDate":"10/10/2025",
    "toDate":"10/11/2025",
    "destination":"California,+USA",
    "roomCount":"1",
    "numAdultsPerRoom":"5",
    "childrenCount":"2",
    "childrenAges":"7,3"
}

asyncio.run(main(search_data))