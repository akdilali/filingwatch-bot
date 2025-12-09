
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

HISTORY_FILE = "history.json"

class HistoryManager:
    def __init__(self, filename: str = HISTORY_FILE):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump({"trademarks": [], "last_updated": None}, f)

    def load_history(self) -> List[Dict]:
        """Tüm geçmişi yükle"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("trademarks", [])
        except Exception as e:
            logging.error(f"Geçmiş yüklenemedi: {e}")
            return []

    def append_to_history(self, new_trademarks: List[Dict]):
        """Yeni trademarkları geçmişe ekle (Duplicate kontrolü ile)"""
        if not new_trademarks:
            return

        current_data = []
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
                current_data = full_data.get("trademarks", [])
        except Exception:
            current_data = []

        # Mevcut Serial numaralarını bir set'e al (Hızlı kontrol için)
        existing_serials = {tm.get('serial_number') for tm in current_data if tm.get('serial_number')}
        
        added_count = 0
        for tm in new_trademarks:
            serial = tm.get('serial_number')
            if serial and serial not in existing_serials:
                # Sadece gerekli alanları sakla (Disk tasarrufu)
                clean_tm = {
                    'serial_number': serial,
                    'mark_name': tm.get('mark_name'),
                    'owner': tm.get('owner'),
                    'goods_services': tm.get('goods_services'),
                    'filing_date': tm.get('filing_date_raw') or datetime.now().strftime("%Y-%m-%d"),
                    'international_class': tm.get('international_class'),
                    'scanned_at': datetime.now().isoformat()
                }
                current_data.append(clean_tm)
                existing_serials.add(serial)
                added_count += 1
        
        # Dosyayı güncelle
        if added_count > 0:
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        "trademarks": current_data,
                        "last_updated": datetime.now().isoformat(),
                        "total_count": len(current_data)
                    }, f, ensure_ascii=False, indent=2)
                logging.info(f"📚 History güncellendi: +{added_count} yeni kayıt (Toplam: {len(current_data)})")
            except Exception as e:
                logging.error(f"History kaydedilemedi: {e}")
        else:
            logging.info("📚 History: Eklenecek yeni kayıt yok (Hepsi mevcut).")

    def get_recent_data(self, days: int = 7) -> List[Dict]:
        """Son X günün verisini getir"""
        all_data = self.load_history()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent = []
        for tm in all_data:
            # scanned_at'e göre filtrele (daha güvenilir)
            scanned_str = tm.get('scanned_at')
            if scanned_str:
                try:
                    scanned_date = datetime.fromisoformat(scanned_str)
                    if scanned_date >= cutoff_date:
                        recent.append(tm)
                except:
                    pass
        return recent
