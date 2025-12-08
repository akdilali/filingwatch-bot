from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import random

# TEMA RENKLERİ
THEME_BG = (20, 23, 26)       # Dark Slate / Twitter Dark
THEME_TEXT = (255, 255, 255)  # White
THEME_ACCENT = (29, 161, 242) # Twitter Blue
THEME_SUBTEXT = (136, 153, 166) # Grey

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

def generate_trademark_card(
    mark_name: str, 
    owner: str, 
    date_str: str, 
    serial: str,
    output_path: str = "temp_card.png"
) -> str:
    """
    Şık bir trademark kartviziti oluşturur.
    Returns: Kaydedilen dosyanın path'i
    """
    
    # 1. Canvas Oluştur (1200x675 - Twitter Card Size)
    W, H = 1200, 675
    img = Image.new('RGB', (W, H), color=THEME_BG)
    d = ImageDraw.Draw(img)
    
    # 2. Üst Bar (New Filing)
    d.rectangle([0, 0, W, 20], fill=THEME_ACCENT)
    
    # 3. Marka İsmi (Ortala ve Büyüt)
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
    line_spacing = 10
    
    # Bounding box calculation fix due to pillow version differences
    try:
        # Modern Pillow
        ascent, descent = font_mark.getmetrics()
        line_height = ascent + descent + line_spacing
    except:
        # Ancient Pillow fallback
        line_height = font_size * 1.2
        
    total_text_h = len(lines) * line_height
    
    current_y = (H - total_text_h) / 2 - 40 # Biraz yukarı taşı
    
    for line in lines:
        # Metni ortala
        try:
            bbox = d.textbbox((0, 0), line, font=font_mark)
            w = bbox[2] - bbox[0]
        except:
             w = d.textlength(line, font=font_mark) # Fallback
             
        d.text(((W - w) / 2, current_y), line, font=font_mark, fill=THEME_TEXT)
        current_y += line_height

    # 4. Alt Bilgiler (Owner & Date)
    font_sub = get_font(30, bold=False)
    
    # Çizgi çek
    d.line([(100, H - 150), (W - 100, H - 150)], fill=THEME_SUBTEXT, width=2)
    
    # Owner
    d.text((100, H - 120), "APPLICANT", font=get_font(20, bold=True), fill=THEME_ACCENT)
    d.text((100, H - 90), owner[:50], font=font_sub, fill=THEME_TEXT)
    
    # Date
    d.text((W - 300, H - 120), "FILED DATE", font=get_font(20, bold=True), fill=THEME_ACCENT)
    d.text((W - 300, H - 90), date_str, font=font_sub, fill=THEME_TEXT)
    
    # Branding - Sağ alt
    d.text((W - 200, 40), "FilingWatch", font=get_font(20, bold=True), fill=THEME_SUBTEXT)
    
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
