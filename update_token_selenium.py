from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import requests
import re
import time
from datetime import datetime
import os
import json

# Secrets
MEDIABAY_LOGIN = os.environ.get('MEDIABAY_LOGIN')
MEDIABAY_PASSWORD = os.environ.get('MEDIABAY_PASSWORD')
CF_API_TOKEN = os.environ.get('CF_API_TOKEN')
CF_ACCOUNT_ID = os.environ.get('CF_ACCOUNT_ID')
WORKER_NAME = os.environ.get('WORKER_NAME')

print("=" * 60)
print("🔄 Mediabay Token Updater (GitHub Actions)")
print(f"📅 Vaqt: {datetime.now()}")
print("=" * 60)

def get_token_with_selenium():
    """Brauzer orqali login qilish va token olish"""
    print("\n🌐 Brauzer orqali login...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = None
    found_token = None
    
    try:
        print("🚗 ChromeDriver yuklanmoqda...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        driver.maximize_window()
        
        # Login
        print("📄 Login sahifasiga kirish...")
        driver.get('https://mediabay.uz/auth')
        time.sleep(3)
        
        email_input = driver.find_element(By.CSS_SELECTOR, 'input[type="text"]')
        email_input.clear()
        email_input.send_keys(MEDIABAY_LOGIN)
        
        password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        password_input.clear()
        password_input.send_keys(MEDIABAY_PASSWORD)
        
        print("   ✅ Inputlar topildi")
        
        print("🔐 Login (Enter)...")
        password_input.send_keys(Keys.ENTER)
        time.sleep(5)
        
        # TV sahifasi
        print("\n📺 TV sahifasiga o'tish...")
        driver.get('https://mediabay.uz/tv')
        time.sleep(5)
        
        # Kanal topish
        print("\n🎬 Kanal qidirilmoqda...")
        channel_names = ["UzReportTV", "Sport", "O'zbekistan 24"]
        channel_element = None
        
        for channel_name in channel_names:
            try:
                xpath = f"//*[contains(text(), '{channel_name}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    channel_element = elements[0]
                    print(f"   ✅ Kanal topildi: {channel_name}")
                    break
            except:
                continue
        
        if not channel_element:
            selectors = ['.channel-card', '.tv-card', '.card']
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        channel_element = elements[0]
                        print(f"   ✅ Birinchi kanal topildi")
                        break
                except:
                    continue
        
        if channel_element:
            print("   🖱️ Kanal ochilmoqda...")
            driver.execute_script("arguments[0].scrollIntoView(true);", channel_element)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", channel_element)
            
            # Network kuzatish
            print("\n🔍 Network requestlar kuzatilmoqda...")
            start_time = time.time()
            timeout = 15
            
            while time.time() - start_time < timeout:
                logs = driver.get_log('performance')
                
                for entry in logs:
                    try:
                        message = json.loads(entry['message'])['message']
                        
                        if message['method'] == 'Network.responseReceived':
                            response = message['params']['response']
                            url = response['url']
                            
                            if '.m3u8' in url and 'token=' in url:
                                print(f"\n✅ M3U8 URL topildi!")
                                token_match = re.search(r'token=([a-zA-Z0-9_-]+)', url)
                                if token_match:
                                    found_token = token_match.group(1)
                                    print(f"\n✅ TOKEN TOPILDI!")
                                    print(f"   Token: {found_token[:60]}...")
                                    print(f"   Uzunligi: {len(found_token)} belgi")
                                    return found_token
                    except:
                        continue
                
                time.sleep(0.5)
        
        print("\n❌ TOKEN TOPILMADI!")
        return None
        
    except Exception as e:
        print(f"❌ Xatolik: {type(e).__name__}: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def update_worker_token(new_token):
    """Cloudflare Worker TOKEN ni yangilash"""
    print("\n☁️ Cloudflare API ga ulanish...")
    
    url = f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/workers/scripts/{WORKER_NAME}/secrets'
    
    headers = {
        'Authorization': f'Bearer {CF_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'name': 'TOKEN',
        'text': new_token,
        'type': 'secret_text'
    }
    
    try:
        print(f"📡 So'rov yuborilmoqda...")
        response = requests.put(url, json=data, headers=headers, timeout=30)
        result = response.json()
        
        print(f"   Response status: {response.status_code}")
        print(f"   Success: {result.get('success', False)}")
        
        if response.status_code in [200, 201] and result.get('success'):
            print("\n✅ WORKER MUVAFFAQIYATLI YANGILANDI!")
            return True
        else:
            print("\n❌ CLOUDFLARE API XATOSI!")
            return False
            
    except Exception as e:
        print(f"❌ Xatolik: {type(e).__name__}: {e}")
        return False

# Asosiy jarayon
if __name__ == '__main__':
    new_token = get_token_with_selenium()
    
    if new_token:
        print("\n" + "=" * 60)
        success = update_worker_token(new_token)
        print("=" * 60)
        if success:
            print("🎉 HAMMASI MUVAFFAQIYATLI!")
        else:
            print("⚠️ TOKEN TOPILDI, LEKIN WORKER YANGILANMADI!")
    else:
        print("\n" + "=" * 60)
        print("❌ TOKEN OLINMADI!")
        print("=" * 60)
