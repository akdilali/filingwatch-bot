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
    
    # Dikey ortalama
    current_y = (H - total_text_h) / 2 - 20
    
    for line in lines:
        try:
            bbox = d.textbbox((0, 0), line, font=font_mark)
            w = bbox[2] - bbox[0]
        except:
             w = d.textlength(line, font=font_mark)
             
        d.text(((W - w) / 2, current_y), line, font=font_mark, fill=THEME_TEXT)
        current_y += line_height

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
