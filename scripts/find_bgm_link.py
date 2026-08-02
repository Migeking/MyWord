import requests, re

url = 'https://peritune.com/blog/2018/10/13/wuxia2/'
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)

# Find all links
pattern = r'href=["\'](https?://[^"\']*mp3[^"\']*)["\']'
mp3s = re.findall(pattern, r.text, re.I)
for m in mp3s:
    print(f"MP3 link: {m}")

# Find download links
pattern2 = r'href=["\']([^"\']*download[^"\']*)["\']'
dls = re.findall(pattern2, r.text, re.I)
for d in dls:
    print(f"Download link: {d}")

# Find audio source tags
pattern3 = r'src=["\'](https?://[^"\']*wuxia[^"\']*mp3[^"\']*)["\']'
srcs = re.findall(pattern3, r.text, re.I)
for s in srcs:
    print(f"Audio src: {s}")

# Find any .mp3 in the entire page
all_mp3 = re.findall(r'(https?://[^"\'<> ]+\.mp3)', r.text)
for a in all_mp3:
    print(f"Any MP3: {a}")

# Find audio/mp3 in mediaelement
pattern4 = r'(https?://[^"\']*peritune[^"\']*/[^"\']*\.mp3[^"\']*)'
p4 = re.findall(pattern4, r.text)
for p in p4:
    print(f"PeriTune MP3: {p}")
