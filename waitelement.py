import asyncio
import time
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