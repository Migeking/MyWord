"""Download Wuxia2_Guzheng_Pipa BGM."""
import requests

url = 'https://www.chosic.com/download-audio/27259/?download=1'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.chosic.com/download-audio/27259/'
}
r = requests.get(url, headers=headers, allow_redirects=True)
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("Content-Type", "")}')
print(f'Content-Length: {r.headers.get("Content-Length", "0")}')
print(f'Final URL: {r.url}')

ct = r.headers.get("Content-Type", "")
if len(r.content) > 5000 and 'audio' in ct:
    out_path = 'D:/code/MyWord/scripts/assets/bgm/Wuxia2_Guzheng_Pipa.mp3'
    with open(out_path, 'wb') as f:
        f.write(r.content)
    print(f'Saved! Size: {len(r.content)} bytes')
else:
    print(f'Got non-audio content ({len(r.content)} bytes, type={ct})')
    print(r.text[:300])
