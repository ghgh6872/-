import html
import json
import os
import re
import sys
import time
from urllib.parse import urljoin

import requests

URL = "https://boardlife.co.kr/game/15778/board/used/product?product_num=278474"
SEEN_FILE = "seen.json"
LOOPS = 5       # 한 번 실행에서 확인하는 횟수
INTERVAL = 60   # 확인 사이 간격(초)
TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"


def notify(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT, "text": text},
        timeout=20,
    )
    r.raise_for_status()


def fetch():
    resp = requests.get(URL, timeout=30, headers={"User-Agent": UA})
    resp.raise_for_status()
    found = {}
    for href, num in re.findall(r'href="([^"]*bbs_num=(\d+)[^"]*)"', resp.text):
        found.setdefault(num, urljoin(URL, html.unescape(href)))
    return found


first_run = not os.path.exists(SEEN_FILE)
seen = set() if first_run else set(json.load(open(SEEN_FILE)))
ok = False

for i in range(LOOPS):
    if i:
        time.sleep(INTERVAL)
    try:
        found = fetch()
    except Exception as e:
        print(f"[{i}] fetch error: {e}")
        continue
    if not found:
        print(f"[{i}] no listings found")
        continue

    ok = True
    print(f"[{i}] found {len(found)} listings")

    if first_run:
        seen = set(found)
        first_run = False
        try:
            notify(f"모니터링 시작: 현재 글 {len(found)}개를 확인했어요. 이후 새 글만 알려드릴게요.")
        except Exception as e:
            print("notify error:", e)
        continue

    for n in found:
        if n in seen:
            continue
        try:
            notify("새 매물: " + found[n])
            seen.add(n)  # 알림이 성공했을 때만 기록
        except Exception as e:
            print("notify error:", e)

if ok:
    json.dump(sorted(seen), open(SEEN_FILE, "w"))
else:
    sys.exit("no successful check")
