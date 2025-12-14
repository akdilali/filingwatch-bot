#!/bin/bash

# Proje klasörüne git (Bu yolun doğru olduğundan emin olun)
cd "$(dirname "$0")"

# Log dosyasına tarih at
echo "Starting bot run at $(date)" >> bot_scheduler.log

# Virtual Environment aktif et
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    # Eğer venv yoksa global python kullanmayı dene veya hata ver
    echo "Virtual environment not found!" >> bot_scheduler.log
fi

# Botu çalıştır (Tweet atma modunda)
# Eğer sadece preview istiyorsanız 'run' yerine 'preview' yazın
python3 -u main_v2.py run | tee -a bot_scheduler.log

echo "Bot run finished at $(date)" >> bot_scheduler.log
echo "----------------------------------------" >> bot_scheduler.log
