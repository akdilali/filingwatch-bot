
import re

class WeirdFilter:
    def __init__(self):
        # 1. Komik / İlginç Kelimeler (Temiz Liste)
        self.funny_keywords = [
            "ZOMBIE", "ALIEN", "NINJA", "UNICORN", "MAGIC", "WIZARD",
            "MEME", "DOGE", "CRYPTO", "HODL", "MOON", "LAMBO",
            "BEER", "VODKA", "WHISKEY", "Tequila", "WINE",  # İçki isimleri genelde komik oluyor
            "TOILET", "POOP", "FART", # Çocuksu mizah
            "WTF", "OMG", "LOL", "LMAO", "YOLO", 
            "DUDE", "BRO", "GUY", "CHICK",
            "HATE", "LOVE", "KISS", "MARRY", "DIVORCE",
            "DEAD", "ALIVE", "GHOST", "MONSTER",
            "LAZY", "CRAZY", "STUPID", "IDIOT", "GENIUS",
            "CAT", "DOG", "MONKEY", "APE" # Hayvanlar (Bored Ape vb.)
        ]
        
        # 2. Yasaklı Kelimeler (Politik / NSFW / Nefret)
        self.block_keywords = [
            "FUCK", "SHIT", "BITCH", "ASSHOLE", "CUNT", "DICK", "PUSSY", "SEX", "PORN",
            "TRUMP", "BIDEN", "OBAMA", "HARRIS", "REPUBLICAN", "DEMOCRAT", "MAGA",
            "NAZI", "HITLER", "KKK", "TERROR", "JIHAD", "KILL", "MURDER", "RAPE"
        ]

    def check_weirdness(self, mark_name: str, goods: str) -> dict:
        """
        Markayı analiz et ve bir 'ariyet skoru' döndür.
        Return: {is_weird: bool, score: int, reason: str}
        """
        score = 0
        reason = []
        mark_upper = mark_name.upper()
        
        # 0. Güvenlik Kontrolü (Block List)
        for bad_word in self.block_keywords:
            if re.search(r'\b' + re.escape(bad_word) + r'\b', mark_upper):
                return {"is_weird": False, "score": -100, "reason": "Blocked Content"}

        # 1. Kelime Eşleşmesi
        for word in self.funny_keywords:
            if re.search(r'\b' + re.escape(word) + r'\b', mark_upper):
                score += 30
                reason.append(f"Keyword: {word}")

        # 2. Uzun Slogan Kontrolü (Genelde komik cümleler uzundur)
        # Örn: "I CAME HERE TO DRINK MILK AND KICK ASS" -> 10 kelime
        word_count = len(mark_upper.split())
        if word_count > 6:
            score += 20
            reason.append("Long Slogan")
            
        # 3. Noktalama İşaretleri (! veya ?)
        if "!" in mark_upper or "?" in mark_upper:
            score += 15
            reason.append("Punctuation")

        # 4. Tekrar Eden Harfler (örn: WOOOOOW)
        if re.search(r'(.)\1{2,}', mark_upper): # 3 kere aynı harf
            score += 15
            reason.append("Repeated Chars")

        # Karar
        is_weird = score >= 40 # Limit puan (En az 1 kelime + 1 özellik lazım)
        
        return {
            "is_weird": is_weird,
            "score": score,
            "reason": ", ".join(reason)
        }
