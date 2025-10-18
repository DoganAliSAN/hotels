#testing several browsers and requests to see what kind of captcha we are 
# dealing with


"""
multi_openers.py

Provides four functions:
 - open_with_selenium(url)
 - open_with_seleniumbase_no_uc(url)
 - open_with_seleniumbase_with_uc(url)
 - open_with_requests(url)

Each function will open the URL and return a tuple: (label, driver_or_response)
The main() runs them sequentially, waits 20 seconds, then saves screenshots (for browser drivers)
and closes all browsers.

Notes:
 - Requires Chrome/Chromium installed.
 - Install dependencies: selenium, webdriver-manager, seleniumbase, undetected-chromedriver, requests
   pip install selenium webdriver-manager seleniumbase undetected-chromedriver requests
"""

import time
import os
import sys
from datetime import datetime
from pathlib import Path

# -----------------------
# Helpers / imports safe
# -----------------------
def safe_import(module_name, package_name=None):
    try:
        module = __import__(module_name)
        return module
    except Exception:
        try:
            # If package name differs from module name
            if package_name:
                return __import__(package_name)
        except Exception:
            return None

# selenium + webdriver-manager
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    webdriver = None
    ChromeService = None
    ChromeOptions = None
    ChromeDriverManager = None

# undetected-chromedriver
try:
    import undetected_chromedriver as uc
except Exception:
    uc = None

# seleniumbase
try:
    from seleniumbase import BaseCase
    from seleniumbase import drivers as sb_drivers  # optional
except Exception:
    BaseCase = None
    sb_drivers = None

# requests
try:
    import requests
except Exception:
    requests = None

# screenshot directory
OUT_DIR = Path("screenshots")
OUT_DIR.mkdir(exist_ok=True)


# -----------------------
# 1) Plain Selenium
# -----------------------
def open_with_selenium(url: str, headless: bool = False, window_size=(1280, 800)):
    """
    Open url with plain Selenium (chromedriver fetched by webdriver-manager).
    Returns ('selenium_plain', driver)
    """
    label = "selenium_plain"
    if webdriver is None or ChromeDriverManager is None:
        raise RuntimeError("selenium or webdriver-manager is not installed. pip install selenium webdriver-manager")

    chrome_options = ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    # minor stealth-ish options (not undetected)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)
    return (label, driver)


# -----------------------
# 2) SeleniumBase (no uc)
# -----------------------
def open_with_seleniumbase_no_uc(url: str, headless: bool = False, window_size=(1280, 800)):
    """
    Example using SeleniumBase's BaseCase to open the URL.
    If SeleniumBase internals are not usable, falls back to plain Selenium.
    Returns ('seleniumbase_no_uc', driver)
    """
    label = "seleniumbase_no_uc"

    if BaseCase is None:
        # fallback
        return ("seleniumbase_no_uc_fallback_to_selenium", open_with_selenium(url, headless=headless, window_size=window_size)[1])

    # Create a BaseCase instance and attempt to get a driver.
    # NOTE: SeleniumBase expects test runner usually; this is a lightweight usage that works on many installs.
    try:
        sb = BaseCase()
        # If seleniumbase provides a method to get a new driver, prefer it.
        get_driver = getattr(sb, "get_new_driver", None)
        if callable(get_driver):
            driver = get_driver()
        else:
            # fallback: create a webdriver via selenium and assign to sb._driver
            # Use webdriver-manager to create a chrome driver
            if webdriver is None or ChromeDriverManager is None:
                raise RuntimeError("selenium + webdriver-manager required for fallback driver.")
            chrome_options = ChromeOptions()
            if headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            sb._driver = driver

        # Ask sb to open the url (if open exists) or use driver.get
        if hasattr(sb, "open"):
            sb.open(url)
        else:
            driver.get(url)

        # Return the raw selenium driver for screenshotting
        if hasattr(sb, "_driver"):
            return (label, sb._driver)
        else:
            return (label, driver)
    except Exception as e:
        # on any error, provide fallback to plain selenium
        print(f"[WARN] seleniumbase usage failed: {e}. Falling back to plain selenium.")
        return ("seleniumbase_no_uc_fallback_to_selenium", open_with_selenium(url, headless=headless, window_size=window_size)[1])


# -----------------------
# 3) SeleniumBase with undetected-chromedriver (uc)
# -----------------------
def open_with_seleniumbase_with_uc(url: str, headless: bool = False, window_size=(1280, 800)):
    """
    Start undetected-chromedriver (uc) and return a driver.
    If SeleniumBase is present, attach uc driver to a SeleniumBase BaseCase instance where possible.
    Returns ('seleniumbase_with_uc', driver)
    """
    label = "seleniumbase_with_uc"

    if uc is None:
        # fallback: try normal selenium
        print("[WARN] undetected-chromedriver not installed; falling back to plain selenium.")
        return ("seleniumbase_with_uc_fallback_to_selenium", open_with_selenium(url, headless=headless, window_size=window_size)[1])

    # uc options
    try:
        options = uc.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        # You can add more options or experimental args here.
        driver = uc.Chrome(options=options)
        driver.get(url)

        # If SeleniumBase exists and you want a BaseCase wrapper:
        if BaseCase is not None:
            try:
                sb = BaseCase()
                # attach uc driver to sb if possible
                sb._driver = driver
                return (label, sb._driver)
            except Exception:
                # fallback to returning raw driver
                return (label, driver)
        else:
            return (label, driver)
    except Exception as e:
        print(f"[WARN] uc driver creation failed: {e}. Falling back to plain selenium.")
        return ("seleniumbase_with_uc_fallback_to_selenium", open_with_selenium(url, headless=headless, window_size=window_size)[1])


# -----------------------
# 4) Requests-based (no browser)
# -----------------------
def open_with_requests(url: str, timeout: int = 30):
    """
    Use requests to GET the URL. Returns ('requests', response).
    Note: can't take a browser screenshot from a requests response.
    """
    label = "requests"
    if requests is None:
        raise RuntimeError("requests is not installed. pip install requests")
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (compatible)"})
    # Save a local HTML snapshot for inspection
    snapshot = OUT_DIR / f"requests_snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
    snapshot.write_text(resp.text, encoding="utf-8")
    return (label, resp)


# -----------------------
# Screenshot & cleanup
# -----------------------
def safe_screenshot(driver, filename: Path):
    """
    Save a screenshot if the driver supports get_screenshot_as_file
    """
    try:
        if hasattr(driver, "get_screenshot_as_file"):
            driver.get_screenshot_as_file(str(filename))
            return True
        elif hasattr(driver, "save_screenshot"):
            driver.save_screenshot(str(filename))
            return True
        else:
            return False
    except Exception as e:
        print(f"[WARN] Could not save screenshot {filename}: {e}")
        return False


def close_driver(driver):
    try:
        driver.quit()
    except Exception:
        try:
            driver.close()
        except Exception:
            pass


# -----------------------
# Main runner
# -----------------------
def main(url: str):
    """
    Run all openers one-by-one, keep browsers open for 20 seconds to investigate,
    then take screenshots from each browser and close them.
    """
    
    runners = [
        open_with_selenium,
        open_with_seleniumbase_no_uc,
        open_with_seleniumbase_with_uc,
        open_with_requests
    ]

    opened = []  # list of tuples (label, obj)
    print(f"[INFO] Starting openers for: {url}")

    for fn in runners:
        try:
            print(f"[INFO] Running: {fn.__name__}")
            label, obj = fn(url)
            print(f"[INFO] -> returned: {label} / type: {type(obj)}")
            opened.append((label, obj))
            # Small pause between starts to be gentle
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Runner {fn.__name__} failed: {e}")

    print("[INFO] All openers started. Waiting 20 seconds to investigate...")
    # total investigation time
    time.sleep(20)

    print("[INFO] Saving screenshots / snapshots...")
    saved = []
    for label, obj in opened:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # For requests responses, we already saved an HTML snapshot. Also save a tiny text file.
        if label.startswith("requests") or isinstance(obj, requests.models.Response) if requests else False:
            info_file = OUT_DIR / f"{label}_response_{timestamp}.txt"
            try:
                info_file.write_text(f"Status: {obj.status_code}\nURL: {obj.url}\nLen: {len(obj.text)}\n", encoding="utf-8")
                saved.append(str(info_file))
            except Exception as e:
                print(f"[WARN] Could not save requests info: {e}")
            continue

        # For browser drivers
        driver = obj
        fname = OUT_DIR / f"{label}_screenshot_{timestamp}.png"
        ok = safe_screenshot(driver, fname)
        if ok:
            saved.append(str(fname))
            print(f"[INFO] Screenshot saved: {fname}")
        else:
            # fallback: save current page source
            try:
                pagefile = OUT_DIR / f"{label}_page_{timestamp}.html"
                with open(pagefile, "w", encoding="utf-8") as f:
                    f.write(driver.page_source if hasattr(driver, "page_source") else "no page source")
                saved.append(str(pagefile))
                print(f"[INFO] Page source saved: {pagefile}")
            except Exception as e:
                print(f"[WARN] Could not save page source for {label}: {e}")

    print("[INFO] Closing all browser drivers...")
    for label, obj in opened:
        if label.startswith("requests") or isinstance(obj, requests.models.Response) if requests else False:
            continue
        try:
            close_driver(obj)
        except Exception as e:
            print(f"[WARN] Could not close driver for {label}: {e}")

    print("[INFO] Done. Saved files:")
    for s in saved:
        print(" -", s)


# -----------------------
# If run as script
# -----------------------
if __name__ == "__main__":
    url = "https://www.marriott.com/search/findHotels.mi?fromToDate_submit=10/10/2025&fromDate=10/09/2025&toDate=10/10/2025&toDateDefaultFormat=10/10/2025&fromDateDefaultFormat=10/09/2025&flexibleDateSearch=false&t-start=2025-10-09&t-end=2025-10-10&lengthOfStay=1&childrenCountBox=0+Children+Per+Room&childrenCount=0&clusterCode=none&isAdvanceSearch=false&recordsPerPage=40&destinationAddress.type=State_Province_Region&isInternalSearch=true&vsInitialRequest=false&searchType=InCity&destinationAddress.stateProvince=CA&singleSearchAutoSuggest=Unmatched&destinationAddress.placeId=ChIJPV4oX_65j4ARVW8IJ6IJUYs&for-hotels-nearme=Near&destinationAddress.country=US&collapseAccordian=is-hidden&singleSearch=true&destinationAddress.secondaryText=CA,+US&isTransient=true&initialRequest=true&flexibleDateSearchRateDisplay=false&isSearch=true&isRateCalendar=true&destinationAddress.destination=California,+USA&isHideFlexibleDateCalendar=false&roomCountBox=1+Room&roomCount=1&guestCountBox=1+Adult+Per+Room&numAdultsPerRoom=1&deviceType=desktop-web&view=list&destinationAddress.location=California,+USA&searchRadius=50&fromToDate=10/09/2025&isFlexibleDatesOptionSelected=false&numberOfRooms=1#/2/"
    main(url)