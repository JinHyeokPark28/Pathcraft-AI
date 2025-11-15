# -*- coding: utf-8 -*-
"""
Path of Exile OAuth 2.1 Authentication
사용자 계정 연동 및 캐릭터 정보 가져오기
"""

import json
import os
import sys
import webbrowser
import requests
from typing import Optional, Dict
from urllib.parse import urlencode, parse_qs
import http.server
import socketserver
import threading
import hashlib
import secrets
import base64

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# POE OAuth 설정
POE_OAUTH_BASE = "https://www.pathofexile.com/oauth"
POE_API_BASE = "https://www.pathofexile.com/api"

# 로컬 리다이렉트 서버 (OAuth 콜백 수신용)
REDIRECT_URI = "http://localhost:12345/oauth_callback"
REDIRECT_PORT = 12345


def generate_pkce_pair():
    """
    PKCE (Proof Key for Code Exchange) 생성
    OAuth 2.1 public client에서 필수

    Returns:
        (code_verifier, code_challenge)
    """
    # Code verifier: 43-128자의 랜덤 문자열
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

    # Code challenge: code_verifier의 SHA256 해시 (Base64 URL-safe 인코딩)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """OAuth 콜백을 처리하는 로컬 HTTP 서버"""

    auth_code = None

    def do_GET(self):
        # URL 파싱
        if self.path.startswith('/oauth_callback'):
            # 쿼리 파라미터 추출
            query_string = self.path.split('?', 1)[1] if '?' in self.path else ''
            params = parse_qs(query_string)

            if 'code' in params:
                OAuthCallbackHandler.auth_code = params['code'][0]

                # 성공 메시지
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                html = """
                <html>
                <head><title>PathcraftAI - Authentication Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px; background: #1a1a1a; color: #fff;">
                    <h1 style="color: #C47533;">✓ Authentication Successful!</h1>
                    <p>You can close this window and return to PathcraftAI.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode('utf-8'))
            else:
                # 에러
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                error = params.get('error', ['Unknown error'])[0]
                html = f"""
                <html>
                <head><title>PathcraftAI - Authentication Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px; background: #1a1a1a; color: #fff;">
                    <h1 style="color: #ff0000;">✗ Authentication Failed</h1>
                    <p>Error: {error}</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        # 로그 출력 억제
        pass


def start_oauth_server() -> threading.Thread:
    """OAuth 콜백 수신용 로컬 서버 시작"""

    httpd = socketserver.TCPServer(("", REDIRECT_PORT), OAuthCallbackHandler)

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    return server_thread


def get_authorization_url(client_id: str, scopes: list[str], code_challenge: str) -> str:
    """
    OAuth 인증 URL 생성 (PKCE 포함)

    Args:
        client_id: POE OAuth 클라이언트 ID
        scopes: 요청할 권한 목록 (예: ['account:profile', 'account:characters'])
        code_challenge: PKCE code challenge

    Returns:
        인증 URL
    """

    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': ' '.join(scopes),
        'redirect_uri': REDIRECT_URI,
        'state': 'random_state_string',  # CSRF 방지용 (실제 앱에서는 랜덤 값 사용)
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'  # SHA256 사용
    }

    return f"{POE_OAUTH_BASE}/authorize?{urlencode(params)}"


def exchange_code_for_token(client_id: str, client_secret: str, auth_code: str, code_verifier: str) -> Dict:
    """
    Authorization Code를 Access Token으로 교환 (PKCE 포함)

    Args:
        client_id: POE OAuth 클라이언트 ID
        client_secret: POE OAuth 클라이언트 시크릿 (public client의 경우 None)
        auth_code: 인증 코드
        code_verifier: PKCE code verifier

    Returns:
        {
            'access_token': '...',
            'token_type': 'Bearer',
            'expires_in': 2592000,
            'refresh_token': '...',
            'scope': 'account:profile account:characters',
            'username': '...',
            'sub': '...'
        }
    """

    data = {
        'client_id': client_id,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier  # PKCE verifier
    }

    # Public client가 아닌 경우에만 client_secret 추가
    if client_secret and client_secret.lower() != 'none':
        data['client_secret'] = client_secret

    # 브라우저처럼 보이도록 헤더 추가 (Cloudflare 우회)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://localhost:12345',
        'Referer': 'https://www.pathofexile.com/',
        'Connection': 'keep-alive'
    }

    print(f"[DEBUG] Token exchange request:")
    print(f"  URL: {POE_OAUTH_BASE}/token")
    print(f"  Data: {data}")
    print(f"  Headers: User-Agent={headers['User-Agent'][:50]}...")

    response = requests.post(f"{POE_OAUTH_BASE}/token", data=data, headers=headers)

    print(f"[DEBUG] Response status: {response.status_code}")
    print(f"[DEBUG] Response headers: {dict(response.headers)}")

    if response.status_code != 200:
        print(f"[DEBUG] Response text (first 500 chars): {response.text[:500]}")
    else:
        print(f"[DEBUG] Response text: {response.text}")

    response.raise_for_status()

    return response.json()


def get_user_profile(access_token: str) -> Dict:
    """
    사용자 프로필 정보 가져오기 (account:profile 스코프 필요)

    Returns:
        {
            'uuid': '...',
            'name': '사용자명',
            'realm': 'pc'
        }
    """

    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8'
    }

    response = requests.get(f"{POE_API_BASE}/profile", headers=headers)
    response.raise_for_status()

    return response.json()


def get_user_characters(access_token: str, realm: str = 'pc') -> list[Dict]:
    """
    사용자 캐릭터 목록 가져오기 (account:characters 스코프 필요)

    Args:
        access_token: 액세스 토큰
        realm: 'pc' 또는 'poe2'

    Returns:
        [
            {
                'name': '캐릭터명',
                'league': '리그명',
                'class': '클래스',
                'level': 95,
                'experience': 123456789
            },
            ...
        ]
    """

    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8'
    }

    params = {'realm': realm}

    response = requests.get(f"{POE_API_BASE}/character", headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def get_character_items(access_token: str, character_name: str, realm: str = 'pc') -> Dict:
    """
    특정 캐릭터의 아이템 정보 가져오기 (account:characters 스코프 필요)

    Args:
        access_token: 액세스 토큰
        character_name: 캐릭터 이름
        realm: 'pc' 또는 'poe2'

    Returns:
        {
            'character': {...},
            'items': [
                {
                    'inventoryId': 'BodyArmour',
                    'typeLine': "Death's Oath",
                    'name': '',
                    'frameType': 3,  # 0=normal, 1=magic, 2=rare, 3=unique
                    'socketedItems': [
                        {
                            'typeLine': 'Vaal Righteous Fire',
                            'support': False,
                            ...
                        }
                    ],
                    ...
                }
            ]
        }
    """

    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8'
    }

    params = {'realm': realm}

    # POE API: /character/{character_name}
    response = requests.get(f"{POE_API_BASE}/character/{character_name}",
                           headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def authenticate_user(client_id: str, client_secret: str, scopes: list[str]) -> Dict:
    """
    전체 OAuth 플로우 실행

    1. 로컬 서버 시작
    2. 브라우저에서 인증 URL 열기
    3. 사용자가 승인하면 콜백 수신
    4. Authorization Code를 Token으로 교환
    5. 토큰 반환

    Args:
        client_id: POE OAuth 클라이언트 ID
        client_secret: POE OAuth 클라이언트 시크릿
        scopes: 요청할 권한 목록

    Returns:
        토큰 정보 딕셔너리
    """

    print("=" * 80)
    print("POE OAUTH AUTHENTICATION (with PKCE)")
    print("=" * 80)
    print()

    # 0. PKCE 생성
    print("[0/5] Generating PKCE challenge...")
    code_verifier, code_challenge = generate_pkce_pair()
    print(f"[OK] PKCE challenge created")
    print()

    # 1. 로컬 서버 시작
    print("[1/5] Starting local callback server...")
    server_thread = start_oauth_server()
    print(f"[OK] Listening on {REDIRECT_URI}")
    print()

    # 2. 브라우저에서 인증 URL 열기
    print("[2/5] Opening browser for authentication...")
    auth_url = get_authorization_url(client_id, scopes, code_challenge)
    print(f"[INFO] Auth URL: {auth_url}")
    webbrowser.open(auth_url)
    print("[OK] Browser opened. Please log in and authorize PathcraftAI.")
    print()

    # 3. 콜백 대기
    print("[3/5] Waiting for authorization callback...")
    while OAuthCallbackHandler.auth_code is None:
        import time
        time.sleep(0.5)

    auth_code = OAuthCallbackHandler.auth_code
    print(f"[OK] Received authorization code: {auth_code[:20]}...")
    print()

    # 4. Token 교환
    print("[4/5] Exchanging code for access token...")
    token_data = exchange_code_for_token(client_id, client_secret, auth_code, code_verifier)
    print(f"[OK] Access token obtained!")
    print(f"     Username: {token_data.get('username')}")
    print(f"     Scopes: {token_data.get('scope')}")
    print(f"     Expires in: {token_data.get('expires_in')} seconds ({token_data.get('expires_in') // 86400} days)")
    print()

    return token_data


def save_token(token_data: Dict, filename: str = "poe_token.json"):
    """토큰을 파일에 저장"""

    filepath = os.path.join(os.path.dirname(__file__), filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(token_data, f, indent=2)

    print(f"[OK] Token saved to: {filepath}")


def load_token(filename: str = "poe_token.json") -> Optional[Dict]:
    """저장된 토큰 로드"""

    filepath = os.path.join(os.path.dirname(__file__), filename)

    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='POE OAuth Authentication')
    parser.add_argument('--client-id', type=str, required=True, help='OAuth Client ID')
    parser.add_argument('--client-secret', type=str, default='none', help='OAuth Client Secret (optional for public clients)')
    parser.add_argument('--scopes', type=str, default='account:profile account:characters account:stashes account:leagues',
                        help='Space-separated scopes')
    parser.add_argument('--save', action='store_true', help='Save token to file')

    args = parser.parse_args()

    scopes = args.scopes.split()

    try:
        # 인증 실행
        token_data = authenticate_user(args.client_id, args.client_secret, scopes)

        # 토큰 저장
        if args.save:
            save_token(token_data)

        print()
        print("=" * 80)
        print("AUTHENTICATION SUCCESSFUL")
        print("=" * 80)
        print()

        # 프로필 정보 가져오기
        if 'account:profile' in scopes:
            print("Fetching profile information...")
            profile = get_user_profile(token_data['access_token'])
            print(f"  Profile UUID: {profile.get('uuid')}")
            print(f"  Username: {profile.get('name')}")
            print(f"  Realm: {profile.get('realm')}")
            print()

        # 캐릭터 정보 가져오기
        if 'account:characters' in scopes:
            print("Fetching character list...")
            characters = get_user_characters(token_data['access_token'])
            print(f"  Total characters: {len(characters)}")

            if characters:
                print()
                print("  Top 5 characters:")
                for i, char in enumerate(characters[:5], 1):
                    print(f"    {i}. {char.get('name')} - Lv{char.get('level')} {char.get('class')} ({char.get('league')})")

            print()

    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        sys.exit(1)
