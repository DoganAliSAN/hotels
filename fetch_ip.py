from create_browser import extension_browser

async def fetch_ip():
    browser = await extension_browser("pass","pass")
    page = await browser.get("https://ipv4.icanhazip.com")
    ip  = await page.evaluate("document.querySelector('pre').textContent;")
    ip = str(ip.value).strip()
    user_agent = await page.evaluate("navigator.userAgent;")
    user_agent = user_agent.value
    browser.stop()
    return (ip,user_agent)