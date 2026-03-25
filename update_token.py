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
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://mediabay.uz/'
    }
    
    try:
        # 1. Login sahifasi
        login_url = 'https://mediabay.uz/login'
        response = session.get(login_url, headers=headers)
        
        # CSRF token olish
        csrf_match = re.search(r'name="_token" value="([^"]+)"', response.text)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # 2. Login qilish
        login_data = {
            'email': SITE_LOGIN,
            'password': SITE_PASSWORD,
        }
        if csrf_token:
            login_data['_token'] = csrf_token
        
        response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
        
        # 3. Kanal sahifasiga kirish
        channel_url = 'https://mediabay.uz/channels'
        response = session.get(channel_url, headers=headers)
        
        # 4. Tokenni M3U8 URL dan topish
        m3u8_pattern = r'https?://st\d+\.mediabay\.uz/[^\s"\']+\.m3u8[^\s"\']*'
        m3u8_matches = re.findall(m3u8_pattern, response.text)
        
        for m3u8_url in m3u8_matches:
            token_match = re.search(r'token=([a-zA-Z0-9_-]+)', m3u8_url)
            if token_match:
                new_token = token_match.group(1)
                print(f"✅ Yangi token: {new_token[:50]}...")
                return new_token
        
        # 5. Tokenni HTML dan to'g'ridan-to'g'ri topish
        token_patterns = [
            r'"token":"([^"]+)"',
            r"token:'([^']+)'",
            r'token=([a-zA-Z0-9_-]{50,})'
        ]
        
        for pattern in token_patterns:
            token_match = re.search(pattern, response.text)
            if token_match:
                new_token = token_match.group(1)
                print(f"✅ Yangi token: {new_token[:50]}...")
                return new_token
        
        print("❌ Token topilmadi!")
        print(f"Response URL: {response.url}")
        print(f"Response length: {len(response.text)}")
        return None
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return None

def update_worker_token(new_token):
    """Cloudflare Worker TOKEN ni yangilash"""
    print(f"🔄 Worker yangilanmoqda...")
    
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
        response = requests.put(url, json=data, headers=headers)
        result = response.json()
        
        if result.get('success'):
            print(f"✅ Worker muvaffaqiyatli yangilandi!")
            return True
        else:
            print(f"❌ Cloudflare API xatosi: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print(f"🔄 {WORKER_NAME} Token Auto-Updater")
    print("=" * 50)
    
    new_token = get_new_token()
    
    if new_token:
        success = update_worker_token(new_token)
        print("✅ Hammasi bajarildi!" if success else "❌ Worker yangilanmadi!")
    else:
        print("❌ Token olinmadi!")
    
    print("=" * 50)
