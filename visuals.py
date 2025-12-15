from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import random

# TEMA RENKLERİ (PREMIUM DARK MODE)
THEME_BG = (15, 23, 42)         # Slate 900 (Deep Navy)
THEME_TEXT = (248, 250, 252)    # Slate 50 (White)
THEME_ACCENT = (59, 130, 246)   # Blue 500 (Electric Blue)
THEME_SUBTEXT = (148, 163, 184) # Slate 400 (Light Grey)
THEME_DIVIDER = (30, 41, 59)    # Slate 800

def get_font(size, bold=False):
    """Sistem fontlarını bul veya varsayılanı kullan"""
    font_paths = [
        # macOS Fonts
        "/System/Library/Fonts/SFNSMono.ttf", # Terminal Font looks cool
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        # Linux/Docker
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                index = 0
                if path.endswith(".ttc"):
                    index = 1 if bold else 0
                return ImageFont.truetype(path, size, index=index)
            except:
                continue
                    
    return ImageFont.load_default()

def draw_tech_grid(d, w, h):
    """Arka plana siber/teknolojik ince çizgiler"""
    step = 50
    # Dikey çizgiler (Çok silik)
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(30, 41, 59), width=1)
    
    # Yatay çizgiler
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(30, 41, 59), width=1)

def generate_trademark_card(
    mark_name: str, 
    owner: str, 
    date_str: str, 
    serial: str,
    description: str = "",
    output_path: str = "temp_card.png"
) -> str:
    """
    Premium Dark Mode Trademark Card
    """
    
    # 1. Canvas (1200x675)
    W, H = 1200, 675
    img = Image.new('RGB', (W, H), color=THEME_BG)
    d = ImageDraw.Draw(img)
    
    # 2. Tech Grid Pattern
    draw_tech_grid(d, W, H)
    
    # 3. Accent Bar (Top Neon Line)
    d.rectangle([0, 0, W, 8], fill=THEME_ACCENT)
    
    # 4. Sol Kenar Çubuğu (Terminal Style)
    # d.rectangle([0, 0, 20, H], fill=THEME_ACCENT) 
    
    # --- LAYOUT HESAPLAMALARI ---
    padding_x = 80
    current_y = 100
    
    # 5. Üst Başlık: "NEW TRADEMARK APPLICATION"
    # User Request: Remove header
    # font_small = get_font(24, bold=True)
    # d.text((padding_x, 60), "> NEW_FILING_DETECTED", font=font_small, fill=THEME_ACCENT)
    
    # 6. Marka İsmi (BÜYÜK)
    # Font boyutu dinamik
    font_size = 110
    if len(mark_name) > 12: font_size = 90
    if len(mark_name) > 20: font_size = 70
    
    font_mark = get_font(font_size, bold=True)
    
    # Wrap
    wrapper = textwrap.TextWrapper(width=16 if font_size > 90 else 25)
    lines = wrapper.wrap(mark_name.upper())
    
    for line in lines:
        d.text((padding_x, current_y), line, font=font_mark, fill=THEME_TEXT)
        current_y += (font_size * 1.2)
        
    current_y += 30 # Spacer
    
    # 7. Açıklama (Description) - Code Block Görünümü
    if description:
        clean_desc = description.replace('\n', ' ').strip()
        
        # Truncate
        if len(clean_desc) > 300: clean_desc = clean_desc[:297] + "..."
        
        desc_font_size = 32
        font_desc = get_font(desc_font_size, bold=False)
        wrapper_desc = textwrap.TextWrapper(width=60)
        desc_lines = wrapper_desc.wrap(clean_desc)
        
        # Max 5 satır
        desc_lines = desc_lines[:5]
        
        # Soluna dikey çizgi çek (Alıntı gibi)
        start_desc_y = current_y
        
        for line in desc_lines:
            d.text((padding_x + 30, current_y), line, font=font_desc, fill=THEME_SUBTEXT)
            current_y += (desc_font_size * 1.4)
            
        # Dikey gri çizgi
        d.line([(padding_x, start_desc_y + 5), (padding_x, current_y - 10)], fill=THEME_DIVIDER, width=4)

    # 8. Footer (Metadata)
    # En alta sabitle
    footer_y = H - 100
    
    # Owner
    font_label = get_font(20, bold=True)
    font_val = get_font(24, bold=False)
    
    # İkon yerine basit metin
    d.text((padding_x, footer_y), "OWNER", font=font_label, fill=THEME_ACCENT)
    d.text((padding_x, footer_y + 30), owner[:40], font=font_val, fill=THEME_TEXT)
    
    # Date (Moved to Right, Renamed to PATENT DATE per request)
    # Eski Serial ID pozisyonuna taşındı (W - 250)
    d.text((W - 250, footer_y), "PATENT DATE", font=font_label, fill=THEME_ACCENT)
    d.text((W - 250, footer_y + 30), date_str, font=font_val, fill=THEME_TEXT)
    
    # Serial ID (Removed)
    # d.text((W - 250, footer_y), "SERIAL ID", font=font_label, fill=THEME_ACCENT)
    # d.text((W - 250, footer_y + 30), f"#{serial}", font=font_val, fill=THEME_SUBTEXT)

    img.save(output_path)
    return output_path

if __name__ == "__main__":
    # Test
    generate_trademark_card(
        "CYBERTRUCK AI", 
        "Tesla, Inc.", 
        "Dec 14, 2025", 
        "98765432",
        "Downloadable software for autonomous driving simulation using neural networks and reinforcement learning."
    )
