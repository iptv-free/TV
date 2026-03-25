import os
import requests
import re
from datetime import datetime

# Secrets
SITE_LOGIN = os.environ.get('SITE_LOGIN')
SITE_PASSWORD = os.environ.get('SITE_PASSWORD')
CF_API_TOKEN = os.environ.get('CF_API_TOKEN')
CF_ACCOUNT_ID = os.environ.get('CF_ACCOUNT_ID')
WORKER_NAME = os.environ.get('WORKER_NAME')

print("=" * 60)
print(f"🔄 {WORKER_NAME} Token Auto-Updater")
print(f"📅 Vaqt: {datetime.now()}")
print("=" * 60)

# Secrets tekshirish
print("🔐 Secrets tekshirilmoqda...")
if not all([SITE_LOGIN, SITE_PASSWORD, CF_API_TOKEN, CF_ACCOUNT_ID, WORKER_NAME]):
    print("❌ XATO: Ba'zi secrets topilmadi!")
    exit(1)
print("✅ Barcha secrets topildi!")

def get_new_token():
    """Mediabay.uz dan yangi token olish"""
    print("\n🌐 Mediabay.uz ga ulanish...")
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # 1. Bosh sahifa (cookies olish)
        print("📄 Bosh sahifaga kirish...")
        home_url = 'https://mediabay.uz/'
        response = session.get(home_url, headers=headers, timeout=30, allow_redirects=True)
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        
        # CSRF token - bir nechta variantlarni tekshiramiz
        csrf_patterns = [
            r'name="_token" value="([^"]+)"',
            r'name="csrf-token" content="([^"]+)"',
            r'_token["\']\s*:\s*["\']([^"\']+)["\']',
            r'csrf["\']\s*:\s*["\']([^"\']+)["\']'
        ]
        
        csrf_token = None
        for pattern in csrf_patterns:
            match = re.search(pattern, response.text)
            if match:
                csrf_token = match.group(1)
                print(f"   ✅ CSRF token topildi: {csrf_token[:30]}...")
                break
        
        if not csrf_token:
            print("   ❌ CSRF token topilmadi!")
            # Debug: Sahifa matnini saqlash
            with open('debug_login_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:20000])
            print("   📁 debug_login_page.html saqlandi")
            # CSRF siz ham urinib ko'ramiz
            csrf_token = ''
        
        # 2. Login sahifasiga kirish
        print("\n🔐 Login sahifasiga kirish...")
        login_url = 'https://mediabay.uz/login'
        response = session.get(login_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        # Yangi CSRF token olish (login sahifasidan)
        for pattern in csrf_patterns:
            match = re.search(pattern, response.text)
            if match:
                csrf_token = match.group(1)
                print(f"   ✅ Login sahifasidan CSRF: {csrf_token[:30]}...")
                break
        
        # 3. Login qilish
        print("\n🔑 Login jarayoni...")
        
        # Turli login form formatlarini sinab ko'ramiz
        login_data_options = [
            # Variant 1: Standart Laravel
            {
                '_token': csrf_token,
                'email': SITE_LOGIN,
                'password': SITE_PASSWORD,
                'remember': 'on'
            },
            # Variant 2: Login maydoni
            {
                '_token': csrf_token,
                'login': SITE_LOGIN,
                'password': SITE_PASSWORD,
                'remember': '1'
            },
            # Variant 3: Username
            {
                '_token': csrf_token,
                'username': SITE_LOGIN,
                'password': SITE_PASSWORD
            },
            # Variant 4: CSRF siz
            {
                'email': SITE_LOGIN,
                'password': SITE_PASSWORD,
                'remember': 'on'
            }
        ]
        
        for i, login_data in enumerate(login_data_options, 1):
            print(f"   Variant {i} sinab ko'rilmoqda...")
            
            response = session.post(
                login_url, 
                data=login_data, 
                headers=headers, 
                timeout=30, 
                allow_redirects=True
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Current URL: {response.url}")
            
            # Login muvaffaqiyatli bo'lganini tekshirish
            if 'login' not in response.url.lower() and 'auth' not in response.url.lower():
                print(f"   ✅ Variant {i} muvaffaqiyatli!")
                break
        else:
            print("   ❌ Barcha login variantlari muvaffaqiyatsiz!")
            with open('debug_after_login.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:20000])
            print("   📁 debug_after_login.html saqlandi")
            return None
        
        # 4. Kanallar sahifasiga kirish
        print("\n📺 Kanallar sahifasiga kirish...")
        channels_url = 'https://mediabay.uz/channels'
        response = session.get(channels_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Response length: {len(response.text)} bytes")
        
        # 5. Tokenni M3U8 dan topish
        print("\n🔍 Token qidirilmoqda...")
        m3u8_pattern = r'https?://st\d+\.mediabay\.uz/[^\s"\']+\.m3u8[^\s"\']*'
        m3u8_matches = re.findall(m3u8_pattern, response.text)
        print(f"   M3U8 linklar: {len(m3u8_matches)} ta topildi")
        
        for i, m3u8_url in enumerate(m3u8_matches[:5], 1):
            print(f"   [{i}] {m3u8_url[:100]}...")
            token_match = re.search(r'token=([a-zA-Z0-9_-]+)', m3u8_url)
            if token_match:
                new_token = token_match.group(1)
                print(f"\n✅ TOKEN TOPILDI!")
                print(f"   Token: {new_token[:50]}...")
                print(f"   Uzunligi: {len(new_token)} belgi")
                return new_token
        
        # 6. HTML dan to'g'ridan-to'g'ri topish
        print("\n🔎 HTML dan token qidirilmoqda...")
        token_patterns = [
            r'"token"\s*:\s*"([^"]+)"',
            r"'token'\s*:\s*'([^']+)'",
            r'token=([a-zA-Z0-9_-]{50,})',
            r'data-token="([^"]+)"',
            r'"jwt"\s*:\s*"([^"]+)"'
        ]
        
        for pattern in token_patterns:
            token_match = re.search(pattern, response.text)
            if token_match:
                new_token = token_match.group(1)
                print(f"✅ TOKEN HTML DAN TOPILDI!")
                print(f"   Token: {new_token[:50]}...")
                return new_token
        
        print("\n❌ TOKEN TOPILMADI!")
        with open('debug_channels.html', 'w', encoding='utf-8') as f:
            f.write(response.text[:20000])
        print("📁 debug_channels.html saqlandi")
        
        return None
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: Sayt javob bermadi!")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Network xatosi: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        print(f"❌ Noma'lum xatolik: {type(e).__name__}: {e}")
        return None

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
        print(f"   Worker: {WORKER_NAME}")
        
        response = requests.put(url, json=data, headers=headers, timeout=30)
        result = response.json()
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200 and result.get('success'):
            print("\n✅ WORKER MUVAFFAQIYATLI YANGILANDI!")
            return True
        else:
            print("\n❌ CLOUDFLARE API XATOSI!")
            print(f"   Status: {response.status_code}")
            if 'errors' in result:
                for error in result['errors']:
                    error_message = error.get('message', 'Noma lum')
                    print(f"   - {error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Xatolik: {type(e).__name__}: {e}")
        return None

# Asosiy jarayon
if __name__ == '__main__':
    new_token = get_new_token()
    
    if new_token:
        print("\n" + "=" * 60)
        success = update_worker_token(new_token)
        print("=" * 60)
        if success:
            print("🎉 HAMMASI MUVAFFAQIYATLI!")
            exit(0)
        else:
            print("⚠️ TOKEN TOPILDI, LEKIN WORKER YANGILANMADI!")
            exit(1)
    else:
        print("\n" + "=" * 60)
        print("❌ TOKEN OLINMADI! JARAYON TO'XTATILDI!")
        print("=" * 60)
        exit(1)
