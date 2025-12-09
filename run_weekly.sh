#!/bin/bash

# Proje dizinine git (Cron için kritik)
cd "$(dirname "$0")"

# Log dosyası
LOG_FILE="bot_scheduler.log"

echo "==========================================" >> $LOG_FILE
echo "📅 WEEKLY RUN STARTED: $(date)" >> $LOG_FILE

# .env dosyasını güvenli yükle (export hatalarını önle)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Sanal ortamı aktif et
source .venv/bin/activate

# Botu 'stats-weekly' modunda çalıştır - Çıktıyı loga ekle
python main_v2.py stats-weekly >> $LOG_FILE 2>&1

echo "🏁 WEEKLY RUN FINISHED: $(date)" >> $LOG_FILE
echo "==========================================" >> $LOG_FILE
