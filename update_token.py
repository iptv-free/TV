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
    print(f"[{datetime.now()}] Token olish boshlandi...")
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        # Login sahifasi
        login_url = 'https://mediabay.uz/login'
        response = session.get(login_url, headers=headers)
        
        # CSRF token
        csrf_match = re.search(r'name="_token" value="([^"]+)"', response.text)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # Login qilish
        login_data = {
            'email': SITE_LOGIN,
            'password': SITE_PASSWORD,
        }
        if csrf_token:
            login_data['_token'] = csrf_token
        
        response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
        
        # Playlist sahifasi
        playlist_url = 'https://mediabay.uz/channels'
        response = session.get(playlist_url, headers=headers)
        
        # Tokenni URL dan topish
        token_match = re.search(r'token=([a-zA-Z0-9_-]+)', response.url)
        if token_match:
            new_token = token_match.group(1)
            print(f"✅ Yangi token: {new_token[:30]}...")
            return new_token
        
        # Tokenni HTML dan topish
        token_match = re.search(r'"token":"([^"]+)"', response.text)
        if token_match:
            new_token = token_match.group(1)
            print(f"✅ Yangi token: {new_token[:30]}...")
            return new_token
        
        # M3U8 linkdan topish
        m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', response.text)
        if m3u8_match:
            m3u8_url = m3u8_match.group(0)
            token_match = re.search(r'token=([a-zA-Z0-9_-]+)', m3u8_url)
            if token_match:
                new_token = token_match.group(1)
                print(f"✅ Yangi token (M3U8): {new_token[:30]}...")
                return new_token
        
        print("❌ Token topilmadi!")
        return None
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return None

def update_worker_token(new_token):
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
            print(f"✅ Worker yangilandi!")
            return True
        else:
            print(f"❌ API xatosi: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("🔄 Mediabay Token Auto-Updater")
    print("=" * 50)
    
    new_token = get_new_token()
    
    if new_token:
        success = update_worker_token(new_token)
        print("✅ Tayyor!" if success else "❌ Xato!")
    else:
        print("❌ Token olinmadi!")
    
    print("=" * 50)
