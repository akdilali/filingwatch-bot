import requests
import json

url = "https://uspto-trademark.p.rapidapi.com/v1/batchTrademarkSearch"
headers = {
    "x-rapidapi-key": "561a232959msh4490808833362fap13da1ejsn9df08b6f694d",
    "x-rapidapi-host": "uspto-trademark.p.rapidapi.com",
    "Content-Type": "application/x-www-form-urlencoded"
}

# İlk istek - count ve scroll_id al
response = requests.post(url, headers=headers, data='keywords=["apple"]')
result = response.json()
scroll_id = result.get('scroll_id', '')
print(f"Toplam Apple trademark: {result.get('count')}")

# Scroll ile veri çek
scroll_data = f'keywords=["apple"]&scroll_id={scroll_id}'
scroll_response = requests.post(url, headers=headers, data=scroll_data)
data = scroll_response.json()

print(f"Data type: {type(data)}")

# Dict ise results içine bak
if isinstance(data, dict):
    data = data.get('results', [])
    
print(f"Data length: {len(data) if isinstance(data, list) else 'N/A'}")

if isinstance(data, list) and len(data) > 0:
    dates = [(item.get('filing_date', ''), item.get('keyword', '')) for item in data if item.get('filing_date')]
    dates.sort(reverse=True)
    
    print("\n📅 EN YENİ 15 APPLE TRADEMARK BAŞVURUSU:")
    print("="*50)
    for d, n in dates[:15]:
        print(f"  {d} - {n}")
    
    print("\n📅 EN ESKİ 5 BAŞVURU:")
    print("="*50)
    for d, n in dates[-5:]:
        print(f"  {d} - {n}")
        
    # 2025 başvuruları
    recent_2025 = [x for x in dates if x[0].startswith('2025')]
    print(f"\n📅 2025 BAŞVURULARI: {len(recent_2025)} adet")
    for d, n in recent_2025[:10]:
        print(f"  {d} - {n}")
else:
    print("Veri gelmedi veya boş!")
    print(f"Response: {str(data)[:500]}")
