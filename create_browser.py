import asyncio
import nodriver as uc
from nodriver import cdp
import os
import json
import random


def create_extension():
    """Create proxy extension"""
    ext_dir = "./proxy_extension"
    os.makedirs(ext_dir, exist_ok=True)
    
    manifest = {
        "manifest_version": 2,
        "name": "Proxy",
        "version": "1.0",
        "permissions": [
            "alarms",
            "contextMenus",
            "storage",
            "notifications",
            "webRequest",
            "webRequestBlocking",
            "<all_urls>"
        ],
        "background": {
            "scripts": ["background.js"],
            "persistent": True
        },
    }
    
    content_script = '''
var calls = {};
var DEFAULT_RETRY_ATTEMPTS = 5;
chrome.webRequest.onAuthRequired.addListener(
  function (details) {
    if (!details.isProxy) return {};
    var id = details.requestId;
    calls[id] = (calls[id] || 0) + 1;
    var retry = parseInt(5) || DEFAULT_RETRY_ATTEMPTS;
    if (calls[id] >= retry) {
      return { cancel: true };
    }

    var login = "brd-customer-hl_d3197ffb-zone-mobile_proxy1";
    var password = "due4rtnm5jyo";
    if (login && password) {
      return {
        authCredentials: {
          username: login,
          password: password
        }
      };
    }
    return {};
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);
    '''
    
    with open(f"{ext_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    with open(f"{ext_dir}/background.js", "w") as f:
        f.write(content_script)
    
    return os.path.abspath(ext_dir)

async def create_browser(profile, headless=False):
    
    ext_path = create_extension()
    
    # ✅ Define custom Windows User-Agent
    custom_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49  Safari/537.36"
     
    cfg = uc.Config()
    cfg.user_data_dir = profile
    cfg.add_argument("--proxy-server=brd.superproxy.io:33335")
    cfg.add_argument("--load-extension=" + ext_path)
    cfg.add_argument("--no-default-browser-check")
    cfg.add_argument("--no-first-run")
    cfg.add_argument("--disable-popup-blocking")
    cfg.add_argument("--disable-blink-features=AutomationControlled")
    cfg.add_argument("--disable-background-networking")
    cfg.add_argument("--disable-default-apps")
    cfg.add_argument("--disable-component-update")
    cfg.add_argument("--disable-sync")
    cfg.add_argument("--disable-dev-shm-usage")
    cfg.add_argument("--disable-gpu")
    cfg.add_argument("--disable-setuid-sandbox")
    cfg.add_argument("--ignore-certificate-errors")
    cfg.add_argument("--window-size=1920,1080")
    
    # ✅ Set User-Agent via Chrome flag (most reliable)
    cfg.add_argument(f"--user-agent={custom_ua}")
    
    browser = await uc.start(config=cfg, headless=headless)
    
    # ✅ Also set via CDP for all tabs (extra protection)
    for tab in browser.tabs:
        await tab.send(cdp.network.set_user_agent_override(
            user_agent=custom_ua,
            accept_language="en-US,en;q=0.9",
            platform="Win32"
        ))
    
    print(f"[+] Browser created with UA: {custom_ua}")
    return browser

async def extension_browser(email, password):
    rndstr = "".join([chr(random.randint(97, 122)) for _ in range(10)])
    profile = f"{os.getcwd()}/stockx-{rndstr}"
    browser = await create_browser(profile)
    
    user_data_dir = browser.config.user_data_dir
    browser.stop()
    await asyncio.sleep(3)
    
    # Enable developer mode
    with open(user_data_dir + "/Default/Preferences", "r") as f:
        data = json.load(f)
        extensions = data.get("extensions", {})
        extensions["ui"] = {"developer_mode": True}
        data["extensions"] = extensions
    
    with open(user_data_dir + "/Default/Preferences", "w") as f:
        json.dump(data, f, indent=2)
    
    browser = await create_browser(profile)
    browser.email = email
    browser.password = password

    
    return browser

# Test function
async def test_user_agent():
    rndstr = "".join([chr(random.randint(97, 122)) for _ in range(10)])
    profile = f"{os.getcwd()}/test-{rndstr}"
    
    browser = await create_browser(profile)
    page = browser.main_tab
    
    await page.get("https://www.whatismybrowser.com/detect/what-is-my-user-agent")
    await asyncio.sleep(2)
    
    # Check User-Agent
    current_ua = await page.evaluate("navigator.userAgent")
    platform = await page.evaluate("navigator.platform")
    
    print(f"[+] User-Agent: {current_ua}")
    print(f"[+] Platform: {platform}")
    
    # Should show Windows, not Linux
    assert "Windows" in current_ua, f"UA still shows Linux: {current_ua}"
    assert "Win32" in platform, f"Platform still shows Linux: {platform}"
    
    print("[✓] User-Agent successfully spoofed!")
    
    await asyncio.sleep(5)
    browser.stop()

if __name__ == "__main__":
    asyncio.run(test_user_agent())