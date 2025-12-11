from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import random

# TEMA RENKLERİ (LIGHT MODE - FRESH)
THEME_BG = (255, 255, 255)      # Pure White
THEME_TEXT = (15, 20, 25)       # Almost Black
THEME_ACCENT = (29, 161, 242)   # Twitter Blue
THEME_SUBTEXT = (83, 100, 113)  # Dark Grey
THEME_PATTERN = (240, 242, 245) # Very Light Grey (for dots)

def get_font(size, bold=False):
    """Sistem fontlarını bulmaya çalışır"""
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                index = 1 if bold else 0 # Genelde index 1 bold olur ttc'de
                return ImageFont.truetype(path, size, index=index)
            except:
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue
                    
    return ImageFont.load_default()

def draw_pattern(d, w, h):
    """Arka plana ince bir nokta deseni çizer"""
    step = 40 # Nokta aralığı
    for x in range(0, w, step):
        for y in range(0, h, step):
            d.ellipse([x, y, x+3, y+3], fill=THEME_PATTERN)

def generate_trademark_card(
    mark_name: str, 
    owner: str, 
    date_str: str, 
    serial: str,
    description: str = "",  # Yeni parametre
    output_path: str = "temp_card.png"
) -> str:
    """
    Şık bir trademark kartviziti oluşturur (Light Theme).
    Using simple layout:
    [ Blue Header Bar ]
    [                 ]
    [   TRADEMARK     ]
    [     NAME        ]
    [                 ]
    [-----------------]
    [ Owner    Date   ]
    """
    
    # 1. Canvas Oluştur (1200x675 - Twitter Card Size)
    W, H = 1200, 675
    img = Image.new('RGB', (W, H), color=THEME_BG)
    d = ImageDraw.Draw(img)
    
    # 2. Desen Ekle
    draw_pattern(d, W, H)
    
    # 3. Üst Bar (Modern Touch)
    d.rectangle([0, 0, W, 12], fill=THEME_ACCENT)
    
    # 4. Marka İsmi (Ortala ve Büyüt)
    # Font boyutu ismin uzunluğuna göre dinamik olsun
    font_size = 120
    if len(mark_name) > 10: font_size = 100
    if len(mark_name) > 20: font_size = 80
    if len(mark_name) > 30: font_size = 60
    
    font_mark = get_font(font_size, bold=True)
    
    # Metni sar (Wrap)
    wrapper = textwrap.TextWrapper(width=15 if font_size > 80 else 25)
    lines = wrapper.wrap(mark_name.upper())
    
    # Toplam metin yüksekliğini hesapla
    total_text_h = 0
    line_spacing = 15
    
    try:
        ascent, descent = font_mark.getmetrics()
        line_height = ascent + descent + line_spacing
    except:
        line_height = font_size * 1.2
        
    total_text_h = len(lines) * line_height
    
    # Dikey ortalama (İsim + Açıklama için alan hesabı)
    # İsim yukarı kaydırılsın (Marka ismi çok uzunsa font küçültülmüştü zaten)
    
    # 4.1 İsim Çizimi
    name_y_offset = (H / 2) - total_text_h - 40 # Biraz yukarı taşı
    
    current_y = name_y_offset
    for line in lines:
        try:
            bbox = d.textbbox((0, 0), line, font=font_mark)
            w = bbox[2] - bbox[0]
        except:
             w = d.textlength(line, font=font_mark)
             
        d.text(((W - w) / 2, current_y), line, font=font_mark, fill=THEME_TEXT)
        current_y += line_height

    # 4.2 Açıklama (Description) Çizimi - YENİ (Dynamic Sizing)
    if description and len(description) > 5:
        # Metni temizle
        clean_desc = description.replace('\n', ' ').strip()
        
        # Dinamik Font Ayarı
        char_count = len(clean_desc)
        if char_count < 150:
            desc_font_size = 40
            wrap_width = 50
            max_lines = 4
        elif char_count < 300:
            desc_font_size = 32
            wrap_width = 65
            max_lines = 6
        else:
            desc_font_size = 26
            wrap_width = 80
            max_lines = 10
            
        # Hard Limit & Smart Truncate (Cümle ortasında kesmemeye çalış)
        max_limit = 800
        if char_count > max_limit: 
            # Limite kadar olan kısmı al
            candidate = clean_desc[:max_limit]
            # Son noktayı bul
            last_dot = candidate.rfind('.')
            
            # Eğer son nokta makul bir yerdeyse (örneğin metnin %10'undan ilerideyse) oradan kes
            if last_dot > (max_limit * 0.1): 
                clean_desc = candidate[:last_dot+1]
            else:
                # Nokta bulamazsa veya çok baştaysa mecburen kesip ... koy
                clean_desc = candidate[:max_limit-3] + "..."
            
        font_desc = get_font(desc_font_size, bold=False)
        
        wrapper_desc = textwrap.TextWrapper(width=wrap_width)
        desc_lines = wrapper_desc.wrap(clean_desc)
        
        # Max satır sayısı kontrolü
        desc_lines = desc_lines[:max_lines]
        
        desc_y = current_y + 30 
        desc_line_height = desc_font_size * 1.3
        
        for line in desc_lines:
            try:
                bbox = d.textbbox((0, 0), line, font=font_desc)
                w = bbox[2] - bbox[0]
            except:
                 w = d.textlength(line, font=font_desc)
            
            d.text(((W - w) / 2, desc_y), line, font=font_desc, fill=THEME_SUBTEXT)
            desc_y += desc_line_height

    # 5. Alt Bilgiler (Footer)
    # Divider Line
    line_y = H - 140
    d.line([(100, line_y), (W - 100, line_y)], fill=(230, 236, 240), width=3)
    
    # Fontlar
    font_label = get_font(18, bold=True)
    font_val = get_font(28, bold=False)
    
    # Sol: Owner
    d.text((100, line_y + 25), "APPLICANT", font=font_label, fill=THEME_ACCENT)
    d.text((100, line_y + 55), owner[:45], font=font_val, fill=THEME_SUBTEXT)
    
    # Sağ: Date
    d.text((W - 350, line_y + 25), "FILED DATE", font=font_label, fill=THEME_ACCENT)
    d.text((W - 350, line_y + 55), date_str, font=font_val, fill=THEME_SUBTEXT)
    
    # Logo / Branding (Sağ Üst Köşe - Minimal)
    d.text((W - 160, 40), "FilingWatch", font=get_font(18, bold=True), fill=THEME_SUBTEXT)
    
    # Save
    img.save(output_path)
    return output_path

if __name__ == "__main__":
    # Test
    print("Generating test card...")
    path = generate_trademark_card(
        "KAHUNA AI", 
        "Kahuna Labs Inc.", 
        "Dec 08, 2025", 
        "99999999"
    )
    print(f"Card generated: {path}")
