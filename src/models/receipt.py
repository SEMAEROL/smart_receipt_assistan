"""
Fiş/Fatura Veri Modelleri Modülü

Bu modül, fiş ve fatura verilerini tutucu dataclass'ları içerir.
OOP ilkelerine uygun şekilde tasarlanmıştır.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class ReceiptItem:
    """
    Fiş kalemini temsil eden dataclass.
    
    Attributes:
        name (str): Kalem adı/açıklaması
        price (float): Kalemin fiyatı
    """
    name: str
    price: float

    def __post_init__(self):
        """
        Dataclass başlatma sonrasında doğrulama yapar.
        Fiyatın pozitif olduğunu kontrol eder.
        """
        if self.price < 0:
            raise ValueError(f"Fiyat negatif olamaz: {self.price}")

    def to_dict(self) -> Dict:
        """
        ReceiptItem'ı dictionary'e dönüştürür.
        
        Returns:
            Dict: Kalem bilgilerini içeren dictionary
        """
        return asdict(self)


@dataclass
class Receipt:
    """
    Fiş/Fatura bilgilerini tutucu ana dataclass.
    
    Attributes:
        filename (str): Dosya adı
        merchant_name (str): İşletme/Mağaza adı
        date (str): Fiş tarihi
        total_amount (float): Toplam tutar
        tax_amount (float): KDV miktarı
        category (str): Harcama kategorisi
        items (List[ReceiptItem]): Fiş kalemlerinin listesi
        raw_text (str): OCR'dan elde edilen ham metin
    """
    filename: str
    merchant_name: str
    date: str
    total_amount: float
    tax_amount: float
    category: str
    items: List[ReceiptItem] = field(default_factory=list)
    raw_text: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """
        Dataclass başlatma sonrasında doğrulama yapar.
        Tutarların pozitif olduğunu ve tarih formatının geçerli olduğunu kontrol eder.
        """
        if self.total_amount < 0:
            raise ValueError(f"Toplam tutar negatif olamaz: {self.total_amount}")
        if self.tax_amount < 0:
            raise ValueError(f"KDV negatif olamaz: {self.tax_amount}")
        if not self.filename:
            raise ValueError("Dosya adı boş olamaz")

    def to_dict(self) -> Dict:
        """
        Receipt'i dictionary'e dönüştürür.
        ReceiptItem'lar da dictionary listesine dönüştürülür.
        
        Returns:
            Dict: Fiş bilgilerini içeren dictionary
        """
        data = asdict(self)
        # ReceiptItem listesini dictionary listesine dönüştür
        data['items'] = [item.to_dict() for item in self.items]
        # datetime nesnesini string'e dönüştür
        data['created_at'] = self.created_at.isoformat()
        return data

    def get_net_amount(self) -> float:
        """
        KDV hariç tutar hesaplar (toplam - KDV).
        
        Returns:
            float: KDV hariç tutar
        """
        return self.total_amount - self.tax_amount

    def get_item_count(self) -> int:
        """
        Fişteki kalem sayısını döndürür.
        
        Returns:
            int: Kalem sayısı
        """
        return len(self.items)


@dataclass
class BatchReportSummary:
    """
    Toplu fişler için rapor özeti dataclass.
    Birden fazla fişin genel bilgilerini tutar.
    
    Attributes:
        total_receipts (int): Toplam fiş sayısı
        total_amount (float): Genel toplam tutar
        total_tax (float): Genel toplam KDV
        category_totals (Dict[str, float]): Kategori bazlı harcama toplamları
        processed_files (List[str]): İşlenen dosya adları
    """
    total_receipts: int = 0
    total_amount: float = 0.0
    total_tax: float = 0.0
    category_totals: Dict[str, float] = field(default_factory=dict)
    processed_files: List[str] = field(default_factory=list)
    generation_date: datetime = field(default_factory=datetime.now)

    def add_receipt(self, receipt: Receipt) -> None:
        """
        Özete yeni bir fiş ekler ve toplamları günceller.
        
        Args:
            receipt (Receipt): Eklenecek fiş nesnesi
        """
        self.total_receipts += 1
        self.total_amount += receipt.total_amount
        self.total_tax += receipt.tax_amount
        self.processed_files.append(receipt.filename)

        # Kategori toplamlarını güncelle
        if receipt.category not in self.category_totals:
            self.category_totals[receipt.category] = 0.0
        self.category_totals[receipt.category] += receipt.total_amount

    def get_average_receipt_amount(self) -> float:
        """
        Ortalama fiş tutarını hesaplar.
        
        Returns:
            float: Ortalama tutar (fiş yoksa 0)
        """
        if self.total_receipts == 0:
            return 0.0
        return self.total_amount / self.total_receipts

    def get_category_percentage(self, category: str) -> float:
        """
        Belirtilen kategorinin toplam içindeki yüzdesini hesaplar.
        
        Args:
            category (str): Kategori adı
            
        Returns:
            float: Yüzde (0-100)
        """
        if self.total_amount == 0:
            return 0.0
        return (self.category_totals.get(category, 0) / self.total_amount) * 100

    def to_dict(self) -> Dict:
        """
        BatchReportSummary'yi dictionary'e dönüştürür.
        
        Returns:
            Dict: Özet bilgilerini içeren dictionary
        """
        data = asdict(self)
        data['generation_date'] = self.generation_date.isoformat()
        return data
