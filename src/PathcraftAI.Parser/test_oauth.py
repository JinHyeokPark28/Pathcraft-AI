# -*- coding: utf-8 -*-
"""
POE OAuth Manual Test
브라우저를 수동으로 열고 인증 진행
"""

import sys
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from poe_oauth import start_oauth_server, get_authorization_url, exchange_code_for_token, save_token, get_user_profile, get_user_characters, generate_pkce_pair
import webbrowser
import time

print("=" * 80)
print("POE OAuth Manual Authentication Test (with PKCE)")
print("=" * 80)
print()

CLIENT_ID = "pathcrafterai"
CLIENT_SECRET = "none"  # Public client
SCOPES = ['account:profile', 'account:characters', 'account:stashes', 'account:leagues']

# Step 0: Generate PKCE
print("[0/6] Generating PKCE challenge...")
code_verifier, code_challenge = generate_pkce_pair()
print(f"[OK] Code verifier: {code_verifier[:20]}...")
print(f"[OK] Code challenge: {code_challenge[:20]}...")
print()

# Step 1: Start local server
print("[1/6] Starting local server on port 12345...")
from poe_oauth import OAuthCallbackHandler
server_thread = start_oauth_server()
print("[OK] Server started")
print()

# Step 2: Generate auth URL
print("[2/6] Generating authorization URL...")
auth_url = get_authorization_url(CLIENT_ID, SCOPES, code_challenge)
print("[OK] Authorization URL:")
print(auth_url)
print()

# Step 3: Open browser
print("[3/6] Opening browser...")
try:
    webbrowser.open(auth_url)
    print("[OK] Browser opened")
except Exception as e:
    print(f"[WARN] Could not open browser automatically: {e}")
    print(f"[INFO] Please manually open this URL in your browser:")
    print(auth_url)
print()
print("Please log in to POE and authorize PathcraftAI...")
print()

# Step 4: Wait for callback
print("[4/6] Waiting for authorization callback...")
timeout = 120  # 2 minutes
start_time = time.time()

while OAuthCallbackHandler.auth_code is None:
    if time.time() - start_time > timeout:
        print("[ERROR] Timeout waiting for authorization")
        sys.exit(1)

    time.sleep(0.5)

auth_code = OAuthCallbackHandler.auth_code
print(f"[OK] Received authorization code: {auth_code[:20]}...")
print()

# Step 5: Exchange code for token
print("[5/6] Exchanging authorization code for access token...")
try:
    token_data = exchange_code_for_token(CLIENT_ID, CLIENT_SECRET, auth_code, code_verifier)
    print("[OK] Access token received!")
    print(f"     Username: {token_data.get('username')}")
    print(f"     Scopes: {token_data.get('scope')}")
    print(f"     Expires in: {token_data.get('expires_in')} seconds ({token_data.get('expires_in') // 86400} days)")
    print()

    # Save token
    save_token(token_data)
    print()

    # Test API calls
    print("=" * 80)
    print("Testing API Calls")
    print("=" * 80)
    print()

    access_token = token_data['access_token']

    # Get profile
    print("[TEST 1] Fetching profile...")
    profile = get_user_profile(access_token)
    print(f"[OK] Profile UUID: {profile.get('uuid')}")
    print(f"     Username: {profile.get('name')}")
    print(f"     Realm: {profile.get('realm')}")
    print()

    # Get characters
    print("[TEST 2] Fetching characters...")
    characters = get_user_characters(access_token)
    print(f"[OK] Total characters: {len(characters)}")

    if characters:
        print()
        print("Top 5 characters:")
        for i, char in enumerate(characters[:5], 1):
            print(f"  {i}. {char.get('name')} - Lv{char.get('level')} {char.get('class')} ({char.get('league')})")

    print()
    print("=" * 80)
    print("SUCCESS! OAuth authentication completed!")
    print("=" * 80)

except Exception as e:
    print(f"[ERROR] Failed to exchange token: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
