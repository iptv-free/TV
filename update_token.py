import os
import requests
import re
from datetime import datetime

SITE_LOGIN = os.environ.get('SITE_LOGIN')
SITE_PASSWORD = os.environ.get('SITE_PASSWORD')
CF_API_TOKEN = os.environ.get('CF_API_TOKEN')
CF_ACCOUNT_ID = os.environ.get('CF_ACCOUNT_ID')
WORKER_NAME = os.environ.get('WORKER_NAME')

def get_new_token():
    """Mediabay.uz dan yangi token olish"""
    print(f"[{datetime.now()}] Token olish boshlandi...")
    print(f"Login: {SITE_LOGIN}")
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://mediabay.uz/',
        'Origin': 'https://mediabay.uz'
    }
    
    try:
        # 1. Bosh sahifaga kirish (cookie olish)
        home_url = 'https://mediabay.uz/'
        response = session.get(home_url, headers=headers)
        print(f"📄 Bosh sahifa: {response.status_code}")
        
        # CSRF token olish
        csrf_match = re.search(r'name="_token" value="([^"]+)"', response.text)
        csrf_token = csrf_token.group(1) if csrf_match else None
        print(f"🔑 CSRF token: {'Topildi' if csrf_token else 'Topilmadi'}")
        
        # 2. Login sahifasi
        login_url = 'https://mediabay.uz/login'
        response = session.get(login_url, headers=headers)
        
        # 3. Login qilish
        login_data = {
            '_token': csrf_token or '',
            'email': SITE_LOGIN,
            'password': SITE_PASSWORD,
            'remember': 'on'
        }
        
        response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
        print(f"🔐 Login: {response.status_code}")
        print(f"📍 Current URL: {response.url}")
        
        # 4. Kanallar sahifasiga kirish
        channels_url = 'https://mediabay.uz/channels'
        response = session.get(channels_url, headers=headers)
        print(f"📺 Kanallar: {response.status_code}")
        
        # 5. Tokenni M3U8 URL dan topish (eng ishonchli usul)
        m3u8_pattern = r'https?://st\d+\.mediabay\.uz/[^\s"\']+\.m3u8[^\s"\']*'
        m3u8_matches = re.findall(m3u8_pattern, response.text)
        print(f" M3U8 linklar topildi: {len(m3u8_matches)}")
        
        for m3u8_url in m3u8_matches:
            print(f"🔍 Tekshirilmoqda: {m3u8_url[:80]}...")
            token_match = re.search(r'token=([a-zA-Z0-9_-]+)', m3u8_url)
            if token_match:
                new_token = token_match.group(1)
                print(f"✅ YANGI TOKEN TOPILDI: {new_token[:50]}...")
                print(f"📏 Token uzunligi: {len(new_token)}")
                return new_token
        
        # 6. Tokenni to'g'ridan-to'g'ri HTML dan topish
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
                print(f"✅ TOKEN HTML dan topildi: {new_token[:50]}...")
                return new_token
        
        # 7. Debug: Sahifa matnini saqlash (keyingi tekshirish uchun)
        print("❌ Token topilmadi!")
        print(f"📄 Response length: {len(response.text)}")
        
        # Sahifa matnini file ga saqlash (debug uchun)
        with open('debug_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("📁 Debug file saqlandi: debug_response.html")
        
        return None
        
    except Exception as e:
        print(f"❌ XATOLIK: {type(e).__name__}: {e}")
        return None

def update_worker_token(new_token):
    """Cloudflare Worker TOKEN ni yangilash"""
    print(f"\n🔄 Worker yangilanmoqda...")
    print(f"📛 Worker: {WORKER_NAME}")
    print(f"🆔 Account: {CF_ACCOUNT_ID[:20]}...")
    
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
        print(f"📡 API so'rov yuborilmoqda...")
        response = requests.put(url, json=data, headers=headers)
        result = response.json()
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response: {result}")
        
        if result.get('success'):
            print(f"✅ WORKER MUVAFFAQIYATLI YANGILANDI!")
            return True
        else:
            print(f"❌ Cloudflare API xatosi!")
            if 'errors' in result:
                for error in result['errors']:
                    print(f"   - {error.get('message', 'Noma'lum xato')}")
            return False
            
    except Exception as e:
        print(f"❌ XATOLIK: {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print(f"🔄 {WORKER_NAME} Token Auto-Updater")
    print(f"📅 Vaqt: {datetime.now()}")
    print("=" * 60)
    
    # Secrets tekshirish
    if not all([SITE_LOGIN, SITE_PASSWORD, CF_API_TOKEN, CF_ACCOUNT_ID, WORKER_NAME]):
        print("❌ XATO: Ba'zi secrets topilmadi!")
        print(f"   SITE_LOGIN: {'✅' if SITE_LOGIN else '❌'}")
        print(f"   SITE_PASSWORD: {'✅' if SITE_PASSWORD else '❌'}")
        print(f"   CF_API_TOKEN: {'✅' if CF_API_TOKEN else '❌'}")
        print(f"   CF_ACCOUNT_ID: {'✅' if CF_ACCOUNT_ID else '❌'}")
        print(f"   WORKER_NAME: {'✅' if WORKER_NAME else '❌'}")
        exit(1)
    
    new_token = get_new_token()
    
    if new_token:
        print("\n" + "=" * 60)
        success = update_worker_token(new_token)
        print("=" * 60)
        print("✅ HAMMASI BAJARILDI!" if success else "❌ WORKER YANGILANMADI!")
    else:
        print("\n" + "=" * 60)
        print("❌ TOKEN OLINMADI!")
        print("=" * 60)
    
    print("=" * 60)
