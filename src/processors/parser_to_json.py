import re
from typing import List, Dict, Any

try:
    from src.config import RECEIPT_KEYWORDS
except ModuleNotFoundError:  # pragma: no cover
    from config import RECEIPT_KEYWORDS

from src.models.receipt import Receipt, ReceiptItem

def group_items_by_line(ocr_data: List[Dict], y_tolerance: int = 15) -> List[List[Dict]]:
    """
    OCR verilerini y-koordinatlarındaki yakınlığa göre satırlara (line) gruplar.
    y_tolerance: Aynı satırda sayılmak için y_min değerleri arasındaki maksimum piksel farkı.
    """
    if not ocr_data:
        return []

    # Verileri yukarıdan aşağıya (y_min'e göre) sırala
    sorted_data = sorted(ocr_data, key=lambda item: item["bbox"]["y_min"])
    
    lines = []
    current_line = [sorted_data[0]]
    
    for item in sorted_data[1:]:
        # Eğer mevcut eleman, aktif satırın ilk elemanı ile aynı hizada ise
        if abs(item["bbox"]["y_min"] - current_line[0]["bbox"]["y_min"]) <= y_tolerance:
            current_line.append(item)
        else:
            # Hiza bozulduysa yeni satıra geç
            lines.append(current_line)
            current_line = [item]
            
    if current_line:
        lines.append(current_line)
        
    # Her satırı kendi içinde soldan sağa (x_min'e göre) sırala
    for line in lines:
        line.sort(key=lambda item: item["bbox"]["x_min"])
        
    return lines

def extract_prices(text: str) -> List[float]:
    """
    Metin içerisindeki para birimi formatındaki sayıları (örn: 14.50, 1,200.00, 15,40) çıkarır.
    """
    # Rakamla başlayıp nokta veya virgül ile kuruş/sent ayırımı yapılan formata uygun Regex
    pattern = r'\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})\b'
    matches = re.findall(pattern, text)
    
    prices = []
    for match in matches:
        # 1,200.50 veya 1.200,50 durumlarını float'a çevirmek için temizlik
        clean_match = match.replace(',', '.')
        # Birden fazla nokta varsa (ör: 1.200.50 -> 1200.50 yapmak için) son nokta hariç sil
        if clean_match.count('.') > 1:
            parts = clean_match.rsplit('.', 1)
            clean_match = parts[0].replace('.', '') + '.' + parts[1]
        try:
            prices.append(float(clean_match))
        except ValueError:
            continue
    return prices

def extract_dates(text: str) -> List[str]:
    """
    Metin içerisinden tarih formatlarını (DD.MM.YYYY, DD/MM/YY vb.) çıkarır.
    """
    pattern = r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b'
    return re.findall(pattern, text)

def select_final_values(candidates: Dict[str, List[Any]]) -> Dict[str, Any]:
 
    final_result = {
        "date": None,
        "tax": None,
        "total": None
    }
    
    # Tarih için: Bulunan ilk tarihi al
    if candidates["date"]:
        final_result["date"] = candidates["date"][0]
        
    # Tax için: Bulunan ilk vergiyi al
    if candidates["tax"]:
        final_result["tax"] = candidates["tax"][0]
        
    # Total için: Fişteki toplamlar genelde en yüksek rakamdır, bu yüzden maksimumu al.
    
    if candidates["total"]:
        final_result["total"] = max(candidates["total"])
        
    return final_result

def parse_to_json(ocr_data: List[Dict]) -> Dict[str, Any]:
   
    # 1. Config'deki tüm dillerin keyword'lerini tek bir listede düzleştir ve küçük harfe çevir
    target_keywords = {"date": [], "total": [], "tax": []}
    for lang_dict in RECEIPT_KEYWORDS.values():
        target_keywords["date"].extend([kw.lower() for kw in lang_dict.get("date", [])])
        target_keywords["total"].extend([kw.lower() for kw in lang_dict.get("total", [])])
        target_keywords["tax"].extend([kw.lower() for kw in lang_dict.get("tax", [])])

    # Adayları tutacağımız sözlük
    candidates = {"date": [], "tax": [], "total": []}
    
    # 2. Verileri satırlara grupla
    lines = group_items_by_line(ocr_data)
    
    # 3. Her satırı analiz et
    for line_items in lines:
        # Satırdaki metinleri boşlukla birleştir ve küçük harfe çevir
        full_line_text = " ".join([item["text"] for item in line_items]).lower()
        
        # --- TOTAL KONTROLÜ ---
        if any(kw in full_line_text for kw in target_keywords["total"]):
            prices = extract_prices(full_line_text)
            candidates["total"].extend(prices)
            
        # --- TAX KONTROLÜ ---
        if any(kw in full_line_text for kw in target_keywords["tax"]):
            prices = extract_prices(full_line_text)
            candidates["tax"].extend(prices)
            
        # --- DATE KONTROLÜ ---
        if any(kw in full_line_text for kw in target_keywords["date"]):
            dates = extract_dates(full_line_text)
            candidates["date"].extend(dates)
            
    if not candidates["date"]:
        all_text = " ".join([item["text"] for item in ocr_data])
        dates = extract_dates(all_text)
        if dates:
            candidates["date"].extend(dates)

    return select_final_values(candidates)


class ReceiptParser:
    """
    OCR çıktısını Receipt modeline dönüştürür.
    """

    def __init__(self):
        self.category_keywords = {
            "Market": ["market", "bim", "migros", "carrefour", "tesco", "gıda", "manav", "bakkal"],
            "Akaryakıt": ["petrol", "benzin", "akaryakıt", "shell", "bp", "opet", "tüpraş", "sunş"],
            "Teknoloji": ["elektronik", "bilgisayar", "telefon", "tablet", "laptop", "yazıcı", "monitor"],
            "Diğer": []
        }

    def _detect_category(self, merchant_name: str, raw_text: str) -> str:
        combined_text = f"{merchant_name} {raw_text}".lower()
        for category, keywords in self.category_keywords.items():
            if category == "Diğer":
                continue
            for keyword in keywords:
                if keyword in combined_text:
                    return category
        return "Diğer"

    def _extract_merchant_name(self, raw_text: str) -> str:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            return "Bilinmiyor"
        return lines[0]

    def parse(self, ocr_data: List[Dict], filename: str = "unknown") -> Receipt:
        """
        Normalized OCR çıktısını Receipt nesnesine çevirir.
        """
        raw_text = " ".join(item.get("text", "") for item in ocr_data if item.get("text"))
        parsed = parse_to_json(ocr_data)

        merchant_name = self._extract_merchant_name(raw_text)
        category = self._detect_category(merchant_name, raw_text)
        total_amount = float(parsed.get("total") or 0.0)
        tax_amount = float(parsed.get("tax") or 0.0)
        date = parsed.get("date") or "Bilinmiyor"

        return Receipt(
            filename=filename,
            merchant_name=merchant_name,
            date=date,
            total_amount=total_amount,
            tax_amount=tax_amount,
            category=category,
            items=[],
            raw_text=raw_text,
        )