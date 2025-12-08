#!/usr/bin/env python3
"""
İlginç trademark'ları bul - AI, Crypto, Tech, Büyük Şirketler
"""
import json
import re
from typing import List, Dict

# İLGİNÇ PATTERNLER
AI_PATTERNS = [
    r'\bAI\b', r'\bA\.I\.', r'ARTIFICIAL', r'INTELLIGEN', r'NEURAL', r'GPT', 
    r'MACHINE\s*LEARN', r'DEEP\s*LEARN', r'COGNITIVE', r'\bML\b', r'GENAI',
    r'COPILOT', r'CHATBOT', r'LLM', r'LANGUAGE\s*MODEL', r'OPENAI',
    r'ANTHROPIC', r'GEMINI', r'CLAUDE', r'MISTRAL'
]

CRYPTO_PATTERNS = [
    r'\bCRYPTO', r'\bCOIN\b', r'\bTOKEN', r'BLOCKCHAIN', r'\bNFT\b',
    r'WEB3', r'WEB\s*3', r'DEFI', r'DECENTRALIZ', r'\bDAO\b', r'METAVERSE',
    r'ETHEREUM', r'BITCOIN', r'SOLANA', r'WALLET'
]

TECH_PATTERNS = [
    r'QUANTUM', r'CYBER', r'\bCLOUD\b', r'SMART\s', r'NEURAL', r'ROBOT',
    r'AUTOMAT', r'AUTONOMOUS', r'DRONE', r'SPATIAL', r'\bXR\b', r'\bVR\b',
    r'\bAR\b', r'VIRTUAL\s*REALITY', r'AUGMENTED', r'HOLOGRAPH'
]

STARTUP_PATTERNS = [
    r'LABS?\b', r'\.IO\b', r'\.AI\b', r'\.XYZ', r'TECH\b', r'VERSE\b',
    r'FINTECH', r'HEALTHTECH', r'PROPTECH', r'EDTECH', r'INSURTECH'
]

# BÜYÜK ŞİRKETLER (owner'da aranacak)
BIG_COMPANIES = [
    'APPLE', 'GOOGLE', 'ALPHABET', 'META', 'FACEBOOK', 'MICROSOFT', 
    'AMAZON', 'TESLA', 'NVIDIA', 'OPENAI', 'ANTHROPIC', 'SPACEX',
    'NETFLIX', 'DISNEY', 'WARNER', 'SONY', 'SAMSUNG', 'INTEL',
    'AMD', 'QUALCOMM', 'ORACLE', 'SALESFORCE', 'ADOBE', 'PAYPAL',
    'STRIPE', 'COINBASE', 'ROBINHOOD', 'UBER', 'LYFT', 'AIRBNB',
    'DOORDASH', 'INSTACART', 'SNAP', 'TWITTER', 'X CORP', 'TIKTOK',
    'BYTEDANCE', 'ALIBABA', 'TENCENT', 'BAIDU', 'HUAWEI', 'XIAOMI'
]


def matches_patterns(text: str, patterns: List[str]) -> str:
    """Pattern'a uyan ilk match'i döndür"""
    if not text:
        return None
    text_upper = text.upper()
    for pattern in patterns:
        if re.search(pattern, text_upper):
            match = re.search(pattern, text_upper)
            return match.group(0) if match else pattern
    return None


def analyze_trademark(tm: Dict) -> Dict:
    """Trademark'ı analiz et ve kategorize et"""
    mark_name = tm.get('mark_name', '') or ''
    owner = tm.get('owner', '') or ''
    goods = tm.get('goods_services', '') or ''
    
    combined = f"{mark_name} {owner} {goods}"
    
    result = {
        'trademark': tm,
        'categories': [],
        'matches': []
    }
    
    # AI check
    match = matches_patterns(mark_name, AI_PATTERNS)
    if match:
        result['categories'].append('🤖 AI')
        result['matches'].append(f"AI: {match}")
    
    # Crypto check
    match = matches_patterns(mark_name, CRYPTO_PATTERNS)
    if match:
        result['categories'].append('🪙 CRYPTO')
        result['matches'].append(f"Crypto: {match}")
    
    # Tech check
    match = matches_patterns(mark_name, TECH_PATTERNS)
    if match:
        result['categories'].append('⚡ TECH')
        result['matches'].append(f"Tech: {match}")
    
    # Startup name patterns
    match = matches_patterns(mark_name, STARTUP_PATTERNS)
    if match:
        result['categories'].append('🚀 STARTUP')
        result['matches'].append(f"Startup: {match}")
    
    # Big company check
    owner_upper = owner.upper()
    for company in BIG_COMPANIES:
        if company in owner_upper:
            result['categories'].append('🏢 BIG CORP')
            result['matches'].append(f"Company: {company}")
            break
    
    return result


def find_interesting(trademarks: List[Dict]) -> List[Dict]:
    """İlginç trademark'ları bul ve sırala"""
    interesting = []
    
    for tm in trademarks:
        analysis = analyze_trademark(tm)
        if analysis['categories']:
            interesting.append(analysis)
    
    # Kategori sayısına göre sırala (çok kategorili = çok ilginç)
    interesting.sort(key=lambda x: len(x['categories']), reverse=True)
    
    return interesting


def main():
    # Dosyadan yükle
    try:
        with open('wide_scan.json', 'r') as f:
            trademarks = json.load(f)
    except FileNotFoundError:
        print("❌ wide_scan.json bulunamadı!")
        print("   Önce geniş tarama yapın.")
        return
    
    print(f"📊 Toplam {len(trademarks)} trademark analiz ediliyor...\n")
    
    interesting = find_interesting(trademarks)
    
    print(f"🎯 {len(interesting)} ilginç trademark bulundu!\n")
    print("=" * 70)
    
    # Kategorilere göre grupla
    by_category = {}
    for item in interesting:
        for cat in item['categories']:
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)
    
    # Her kategoriden örnekler göster
    for category, items in sorted(by_category.items()):
        print(f"\n{category} ({len(items)} adet)")
        print("-" * 50)
        
        for item in items[:10]:  # Her kategoriden max 10
            tm = item['trademark']
            print(f"  📌 {tm['mark_name']}")
            print(f"     Serial: {tm['serial_number']} | Owner: {tm['owner'][:40]}...")
            print(f"     Matches: {', '.join(item['matches'])}")
            print()
    
    # En ilginçleri kaydet
    with open('interesting_trademarks.json', 'w') as f:
        json.dump(interesting, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 {len(interesting)} ilginç trademark 'interesting_trademarks.json' dosyasına kaydedildi")


if __name__ == "__main__":
    main()
