import requests
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.get('https://groww.in/stocks/bharat-heavy-electricals-ltd', headers=headers)

# Find all script src in HTML
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', r.text)
print('Total scripts:', len(scripts))

target_words = ['input-shares', 'shares', 'Qty', 'Stoploss', 'Add Stoploss']

for s in scripts:
    url = s if s.startswith('http') else f"https://groww.in{s}"
    try:
        content = requests.get(url, headers=headers, timeout=5).text
        for word in target_words:
            if word in content:
                print(f"Found '{word}' in {url[-35:]}")
                idx = content.find(word)
                print("Snippet:", content[max(0, idx-100):min(len(content), idx+200)])
                print("="*60)
                break
    except Exception as e:
        pass
