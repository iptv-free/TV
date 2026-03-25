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
    print(f"   SITE_LOGIN: {'✅' if SITE_LOGIN else '❌'}")
    print(f"   SITE_PASSWORD: {'✅' if SITE_PASSWORD else '❌'}")
    print(f"   CF_API_TOKEN: {'✅' if CF_API_TOKEN else '❌'}")
    print(f"   CF_ACCOUNT_ID: {'✅' if CF_ACCOUNT_ID else '❌'}")
    print(f"   WORKER_NAME: {'✅' if WORKER_NAME else '❌'}")
    exit(1)
print("✅ Barcha secrets topildi!")

def get_new_token():
    """Mediabay.uz dan yangi token olish"""
    print("\n🌐 Mediabay.uz ga ulanish...")
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://mediabay.uz/',
        'Origin': 'https://mediabay.uz'
    }
    
    try:
        # 1. Bosh sahifa
        print("📄 Bosh sahifaga kirish...")
        home_url = 'https://mediabay.uz/'
        response = session.get(home_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        # CSRF token
        csrf_match = re.search(r'name="_token" value="([^"]+)"', response.text)
        csrf_token = csrf_match.group(1) if csrf_match else None
        print(f"   CSRF token: {'✅ Topildi' if csrf_token else '❌ Topilmadi'}")
        
        # 2. Login
        print("\n🔐 Login jarayoni...")
        login_url = 'https://mediabay.uz/login'
        login_data = {
            '_token': csrf_token or '',
            'email': SITE_LOGIN,
            'password': SITE_PASSWORD,
            'remember': 'on'
        }
        
        response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True, timeout=30)
        print(f"   Login status: {response.status_code}")
        print(f"   Current URL: {response.url}")
        
        # Login muvaffaqiyatli bo'lganini tekshirish
        if 'login' in response.url.lower() or 'auth' in response.url.lower():
            print("❌ Login muvaffaqiyatsiz! URL hali login sahifasida.")
            return None
        
        # 3. Kanallar sahifasi
        print("\n📺 Kanallar sahifasiga kirish...")
        channels_url = 'https://mediabay.uz/channels'
        response = session.get(channels_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Response length: {len(response.text)} bytes")
        
        # 4. Tokenni M3U8 dan topish
        print("\n🔍 Token qidirilmoqda...")
        m3u8_pattern = r'https?://st\d+\.mediabay\.uz/[^\s"\']+\.m3u8[^\s"\']*'
        m3u8_matches = re.findall(m3u8_pattern, response.text)
        print(f"   M3U8 linklar: {len(m3u8_matches)} ta topildi")
        
        for i, m3u8_url in enumerate(m3u8_matches[:5], 1):
            print(f"   [{i}] {m3u8_url[:80]}...")
            token_match = re.search(r'token=([a-zA-Z0-9_-]+)', m3u8_url)
            if token_match:
                new_token = token_match.group(1)
                print(f"\n✅ TOKEN TOPILDI!")
                print(f"   Token: {new_token[:50]}...")
                print(f"   Uzunligi: {len(new_token)} belgi")
                return new_token
        
        # 5. HTML dan to'g'ridan-to'g'ri topish
        print("\n🔎 HTML dan token qidirilmoqda...")
        token_patterns = [
            r'"token"\s*:\s*"([^"]+)"',
            r"'token'\s*:\s*'([^']+)'",
            r'token=([a-zA-Z0-9_-]{50,})',
            r'data-token="([^"]+)"'
        ]
        
        for pattern in token_patterns:
            token_match = re.search(pattern, response.text)
            if token_match:
                new_token = token_match.group(1)
                print(f"✅ TOKEN HTML DAN TOPILDI!")
                print(f"   Token: {new_token[:50]}...")
                return new_token
        
        print("\n❌ TOKEN TOPILMADI!")
        print("💡 Maslahat: Mediabay.uz saytida login jarayoni o'zgargan bo'lishi mumkin.")
        
        # Debug file
        with open('debug_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text[:10000])
        print("📁 debug_response.html fayl saqlandi")
        
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
        print(f"   URL: {url[:80]}...")
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
                    # ✅ Tuzatildi: "Noma'lum" o'rniga double quote
                    print(f"   - {error.get('message', 'Noma\'lum')}")
            if 'messages' in result:
                for msg in result['messages']:
                    print(f"   - {msg}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: Cloudflare javob bermadi!")
        return None
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
