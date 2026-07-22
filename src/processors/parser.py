"""
Fiş/Fatura Ayrıştırıcı Modülü

Bu modül OCR'dan elde edilen ham metinden Regex kalıpları kullanarak
fiş bilgilerini (tarih, tutar, KDV vb.) çıkarır ve bir Receipt nesnesine dönüştürür.
"""

import re
import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from src.models.receipt import Receipt, ReceiptItem

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReceiptParser:
    """
    OCR metinini yapılandırılmış Receipt verisine dönüştüren sınıf.
    
    Regex kalıpları kullanarak fiş bilgilerini çıkarır:
    - İşletme adı
    - Fiş tarihi
    - Kalem bilgileri
    - Toplam tutar
    - KDV miktarı
    - Kategori tahmini
    
    Attributes:
        category_keywords (Dict[str, List[str]]): Kategori anahtar kelimeleri
    """

    def __init__(self):
        """ReceiptParser başlatıcısı."""
        # Kategori anahtar kelimeleri
        self.category_keywords = {
            "Market": ["market", "bim", "migros", "carrefour", "tesco", "gıda", "manav", "bakkal"],
            "Akaryakıt": ["petrol", "benzin", "akaryakıt", "shell", "bp", "opet", "tüpraş", "sunş"],
            "Teknoloji": ["elektronik", "bilgisayar", "telefon", "tablet", "laptop", "yazıcı", "monitor"],
            "Sağlık": ["eczane", "eczacı", "ilaç", "tıp", "doktor", "hastane", "klinik", "diş"],
            "Yemek": ["restoran", "kafe", "kahvehane", "pizzeria", "burger", "kebap", "lokanta", "yemek"],
            "Ulaşım": ["taksi", "otobüs", "tren", "uçak", "otoparkı", "benzin", "dolmuş"],
            "Diğer": []
        }

        # Regex kalıpları
        self.patterns = {
            "date": [
                r"(\d{1,2})[./](\d{1,2})[./](\d{4})",  # DD.MM.YYYY veya DD/MM/YYYY
                r"(\d{4})[./](\d{1,2})[./](\d{1,2})",  # YYYY.MM.DD veya YYYY/MM/DD
            ],
            "amount": r"Toplam[:\s]*(\d+[.,]\d{2})",  # Toplam: 123.45
            "total": r"(?:TOPLAM|Genel Toplam|Total)[:\s]*([₺\$]?[\s]*)(\d+[.,]\d{2})",
            "tax": r"(?:KDV|Vergi|Tax)[:\s]*([₺\$]?[\s]*)(\d+[.,]\d{2})",
            "price": r"(\d+[.,]\d{2})",  # Fiyat: 123.45
            "quantity": r"(\d+)\s*x",  # Miktar x
        }

        logger.info("ReceiptParser başlatıldı")

    def extract_date(self, text: str) -> str:
        """
        Metinden tarih bilgisini çıkarır.
        
        Desteklenen formatlar:
        - DD.MM.YYYY
        - DD/MM/YYYY
        - YYYY.MM.DD
        
        Args:
            text (str): Metin
            
        Returns:
            str: Tarih (DD.MM.YYYY formatında) veya "Bilinmiyor"
        """
        for pattern in self.patterns["date"]:
            matches = re.findall(pattern, text)
            if matches:
                match = matches[0]
                if len(match) == 3:
                    # Tarih parçalarını al
                    if int(match[0]) > 31:
                        # YYYY.MM.DD formatı
                        year, month, day = match
                    else:
                        # DD.MM.YYYY formatı
                        day, month, year = match

                    try:
                        # Tarih doğruluğunu kontrol et
                        date_obj = datetime(int(year), int(month), int(day))
                        formatted_date = date_obj.strftime("%d.%m.%Y")
                        logger.debug(f"Tarih bulundu: {formatted_date}")
                        return formatted_date
                    except ValueError:
                        logger.warning(f"Geçersiz tarih: {day}.{month}.{year}")
                        continue

        logger.warning("Tarih bulunamadı")
        return "Bilinmiyor"

    def extract_amount(self, text: str) -> float:
        """
        Metinden tutarları çıkarır ve en büyüğünü döndürür.
        
        Args:
            text (str): Metin
            
        Returns:
            float: Tutar (float) veya 0.0
        """
        # Tüm sayısal değerleri bul
        pattern = r"(\d+[.,]\d{2})"
        matches = re.findall(pattern, text)

        if not matches:
            logger.warning("Tutar bulunamadı")
            return 0.0

        # En büyük tutarı seç (muhtemelen toplam tutar)
        amounts = []
        for match in matches:
            # Virgül veya noktayı normalize et
            amount_str = match.replace(',', '.')
            try:
                amount = float(amount_str)
                amounts.append(amount)
            except ValueError:
                continue

        if amounts:
            max_amount = max(amounts)
            logger.debug(f"Tutar bulundu: {max_amount}")
            return max_amount

        logger.warning("Tutar dönüştürülemedi")
        return 0.0

    def extract_tax(self, text: str) -> float:
        """
        Metinden KDV bilgisini çıkarır.
        
        Args:
            text (str): Metin
            
        Returns:
            float: KDV miktarı veya toplam tutarın %18'i (varsayılan)
        """
        # KDV pattern'ı ara
        pattern = r"(?:KDV|Vergi|Tax|V\.K\.)[:\s]*[₺\$]?\s*(\d+[.,]\d{2})"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            tax_str = match.group(1).replace(',', '.')
            try:
                tax = float(tax_str)
                logger.debug(f"KDV bulundu: {tax}")
                return tax
            except ValueError:
                logger.warning(f"KDV dönüştürülemedi: {tax_str}")

        # KDV bulunamazsa, toplam tutarın %18'ini hesapla
        total = self.extract_amount(text)
        estimated_tax = total * 0.18 / 1.18  # KDV dahil tutardan KDV'yi çıkart
        logger.warning(f"KDV bulunamadı, tahmini değer kullanıldı: {estimated_tax:.2f}")
        return round(estimated_tax, 2)

    def extract_items(self, text: str) -> List[ReceiptItem]:
        """
        Metinden fiş kalemlerini çıkarır.
        
        Her satırda miktar x ürün fiyatı formatı arar.
        
        Args:
            text (str): Metin
            
        Returns:
            List[ReceiptItem]: Fiş kalemleri listesi
        """
        items = []
        
        # Satırları ayıkla
        lines = text.split('\n')

        for line in lines:
            # Satırda fiyat var mı kontrol et
            price_match = re.search(r"(\d+[.,]\d{2})\s*$", line)
            if not price_match:
                continue

            price_str = price_match.group(1).replace(',', '.')
            try:
                price = float(price_str)
            except ValueError:
                continue

            # Ürün adını çıkart (satırın başından fiyata kadarı)
            item_name = line[:price_match.start()].strip()
            
            # Miktar var mı kontrolü
            qty_match = re.search(r"(\d+)\s*x\s*(.*)", item_name)
            if qty_match:
                quantity = int(qty_match.group(1))
                product_name = qty_match.group(2).strip()
                
                # Bireysel fiyat = toplam fiyat / miktar
                unit_price = price / quantity
            else:
                product_name = item_name
                unit_price = price

            if product_name and unit_price > 0:
                items.append(ReceiptItem(name=product_name, price=unit_price))
                logger.debug(f"Kalem eklendi: {product_name} - {unit_price:.2f}")

        return items

    def detect_category(self, merchant_name: str, raw_text: str) -> str:
        """
        İşletme adı ve metin içeriğine göre kategori tahmin eder.
        
        Args:
            merchant_name (str): İşletme adı
            raw_text (str): Ham metin
            
        Returns:
            str: Tahmin edilen kategori
        """
        combined_text = (merchant_name + " " + raw_text).lower()

        # Kategori anahtar kelimeleri içinde ara
        for category, keywords in self.category_keywords.items():
            if category == "Diğer":
                continue
            
            for keyword in keywords:
                if keyword in combined_text:
                    logger.debug(f"Kategori bulundu: {category} (anahtar kelime: {keyword})")
                    return category

        logger.debug("Kategori bulunamadı, 'Diğer' atandı")
        return "Diğer"

    def extract_merchant_name(self, text: str) -> str:
        """
        Metinden işletme/mağaza adını çıkarır.
        
        Genellikle belgede ilk satır veya "Merchant" kelimesinden sonra gelir.
        
        Args:
            text (str): Metin
            
        Returns:
            str: İşletme adı veya "Bilinmiyor"
        """
        lines = text.split('\n')
        
        # Merchant pattern'ı ara
        for line in lines:
            if "merchant" in line.lower():
                merchant = line.split(":", 1)[-1].strip()
                if merchant:
                    logger.debug(f"İşletme adı bulundu: {merchant}")
                    return merchant

        # Merchant bulunamazsa, ilk boş olmayan satırı kullan
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                logger.debug(f"İşletme adı (ilk satırdan): {line}")
                return line

        logger.warning("İşletme adı bulunamadı")
        return "Bilinmiyor"

    def parse(self, raw_text: str, filename: str = "unknown") -> Receipt:
        """
        Ham OCR metnini Receipt nesnesine dönüştürür.
        
        Ana ayrıştırma metodu. Tüm bilgileri çıkararak ve düzenleyerek
        bir Receipt nesnesi oluşturur.
        
        Args:
            raw_text (str): OCR'dan elde edilen ham metin
            filename (str): Kaynak görüntü dosya adı
            
        Returns:
            Receipt: Ayrıştırılmış fiş bilgileri içeren Receipt nesnesi
        """
        try:
            # Bilgileri çıkart
            merchant_name = self.extract_merchant_name(raw_text)
            date = self.extract_date(raw_text)
            total_amount = self.extract_amount(raw_text)
            tax_amount = self.extract_tax(raw_text)
            items = self.extract_items(raw_text)
            category = self.detect_category(merchant_name, raw_text)

            # Receipt nesnesi oluştur
            receipt = Receipt(
                filename=filename,
                merchant_name=merchant_name,
                date=date,
                total_amount=total_amount,
                tax_amount=tax_amount,
                category=category,
                items=items,
                raw_text=raw_text
            )

            logger.info(f"Fiş başarıyla ayrıştırıldı: {filename} ({category})")
            return receipt

        except Exception as e:
            logger.error(f"Fiş ayrıştırma hatası ({filename}): {str(e)}")
            
            # Hata durumunda boş Receipt döndür
            return Receipt(
                filename=filename,
                merchant_name="Bilinmiyor",
                date="Bilinmiyor",
                total_amount=0.0,
                tax_amount=0.0,
                category="Diğer",
                items=[],
                raw_text=raw_text
            )

    def parse_multiple(self, texts: List[Tuple[str, str]]) -> List[Receipt]:
        """
        Birden fazla ham metni ayrıştırır.
        
        Args:
            texts (List[Tuple[str, str]]): (ham_metin, dosya_adı) çiftlerinin listesi
            
        Returns:
            List[Receipt]: Receipt nesnelerinin listesi
        """
        receipts = []
        for raw_text, filename in texts:
            receipt = self.parse(raw_text, filename)
            receipts.append(receipt)
        
        logger.info(f"{len(receipts)} fiş ayrıştırıldı")
        return receipts
