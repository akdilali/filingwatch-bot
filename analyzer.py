
import logging
from collections import Counter
from typing import List, Dict, Tuple
from datetime import datetime
from history_manager import HistoryManager

class Analyzer:
    def __init__(self):
        self.history = HistoryManager()

    def generate_weekly_report(self) -> str:
        """Son 7 günün trendlerini analiz et ve rapor oluştur"""
        recent_data = self.history.get_recent_data(days=7)
        
        if not recent_data:
            return "❌ Yeterli veri yok (Son 7 gün boş)."

        total_count = len(recent_data)
        
        # 1. Kelime Analizi (AI, Crypto, vs)
        keywords = ['AI', 'GPT', 'Crypto', 'Blockchain', 'Metaverse', 'Quantum', 'Robot', 'Drone', 'Gaming', 'Food']
        keyword_counts = Counter()
        
        for tm in recent_data:
            text = ((tm.get('mark_name') or '') + " " + (tm.get('goods_services') or '')).upper()
            for kw in keywords:
                if kw.upper() in text:
                    keyword_counts[kw] += 1
        
        # En popüler 3 kelime
        top_keywords = keyword_counts.most_common(3)
        
        # 2. Şirket Analizi
        exclude_owners = ['UNKNOWN', 'N/A', '']
        owners = [tm.get('owner') for tm in recent_data if tm.get('owner') not in exclude_owners]
        top_owners = Counter(owners).most_common(3)
        
        # 3. Rapor Oluştur
        report = f"📊 HAFTALIK PATENT RAPORU ({datetime.now().strftime('%d %b')})\n\n"
        
        if top_keywords:
            report += "🔥 Yükselen Trendler:\n"
            for kw, count in top_keywords:
                report += f"• #{kw}: {count} başvuru\n"
            report += "\n"
            
        if top_owners:
            report += "🏆 Lider Şirketler:\n"
            for owner, count in top_owners:
                # Kısalt
                short_owner = owner[:25] + "..." if len(owner) > 25 else owner
                report += f"• {short_owner}: {count}\n"
        
        return report.strip()

if __name__ == "__main__":
    # Test
    analyzer = Analyzer()
    print(analyzer.generate_weekly_report())
