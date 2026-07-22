"""
Yapılandırma Modülü

Projenin tüm yapılandırma ayarlarını merkezileştirilmiş bir şekilde tutar.
"""

from pathlib import Path
from typing import Dict, List

# ============================================================================
# PROJE YAPISI
# ============================================================================

# Proje kökü
PROJECT_ROOT = Path(__file__).parent.parent

# Veri klasörleri
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Kaynak kodları
SRC_DIR = PROJECT_ROOT / "src"
MODELS_DIR = SRC_DIR / "models"
PROCESSORS_DIR = SRC_DIR / "processors"
REPORTING_DIR = SRC_DIR / "reporting"

# ============================================================================
# GÖRÜNTÜ İŞLEMECİ AYARLARI
# ============================================================================

IMAGE_PROCESSOR_CONFIG = {
    "kernel_size": 5,           # Morfolojik işlem kernel boyutu
    "blur_strength": 5,         # Gürültü engelleme gücü
    "max_image_width": 2000,    # Maksimum görüntü genişliği (px)
    "max_image_height": 2000,   # Maksimum görüntü yüksekliği (px)
}

# ============================================================================
# OCR ENGINE AYARLARI
# ============================================================================

OCR_ENGINE_CONFIG = {
    # Aktif olarak kullanılacak OCR motoru secme 
    # Seçenekler: "tesseract", "paddleocr"
    "active_engine": "paddleocr", 

    "engines": {
        "tesseract": {
            "language": "tur+eng",      
            "tesseract_cmd": None,      # (None = sistem PATH'ten)
            "config": "--oem 3 --psm 6", 
        },
        "paddleocr": {
            "lang": "tr",
            "use_angle_cls": True,
            "use_gpu": False,           
            "det_model_dir": str(MODELS_DIR / "paddleocr" / "det"),
            "rec_model_dir": str(MODELS_DIR / "paddleocr" / "rec"),
            "cls_model_dir": str(MODELS_DIR / "paddleocr" / "cls"),
        }
    }}

# Windows'ta Tesseract yolu (isteğe bağlı)
# OCR_ENGINE_CONFIG["tesseract_cmd"] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ============================================================================
# PARSER AYARLARI
# ============================================================================

PARSER_CONFIG = {
    "max_date_distance": 10,     # Tarih bulma toleransı
    "default_tax_rate": 0.18,    # Varsayılan KDV oranı (%18)
    "min_price": 0.01,           # Minimum fiyat
}

# Kategori anahtar kelimeleri
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Market": ["market", "bim", "migros", "carrefour", "tesco", "gıda", "manav", "bakkal", "super"],
    "Akaryakıt": ["petrol", "benzin", "akaryakıt", "shell", "bp", "opet", "tüpraş", "sunş", "lpg"],
    "Teknoloji": ["elektronik", "bilgisayar", "telefon", "tablet", "laptop", "yazıcı", "monitor", "tech"],
    "Sağlık": ["eczane", "eczacı", "ilaç", "tıp", "doktor", "hastane", "klinik", "diş", "pharma"],
    "Yemek": ["restoran", "kafe", "kahvehane", "pizzeria", "burger", "kebap", "lokanta", "yemek", "food"],
    "Ulaşım": ["taksi", "otobüs", "tren", "uçak", "otoparkı", "benzin", "dolmuş", "uber", "transport"],
    "Giyim": ["giyim", "ayakkabı", "moda", "butik", "tekstil", "alışveriş", "confection"],
    "Eğitim": ["okul", "üniversite", "eğitim", "kütüphane", "kitap", "kursu", "education"],
}

# ============================================================================
# WORD RAPOR AYARLARI
# ============================================================================

DOCX_GENERATOR_CONFIG = {
    "title": "Harcama Raporu",
    "author": "Smart Receipt Assistant",
    "default_font": "Calibri",
    "default_font_size": 11,
    "table_style": "Light Grid Accent 1",
}

# Renk kodları (RGB Hex)
REPORT_COLORS = {
    "heading_primary": "000080",      # Koyu mavi
    "heading_secondary": "404040",    # Koyu gri
    "table_header": "D3D3D3",         # Açık gri
    "table_row_alternate": "F0F0F0",  # Çok açık gri
}

# ============================================================================
# PIPELINE AYARLARI
# ============================================================================

PIPELINE_CONFIG = {
    "recursive_directory_search": False,  # Alt klasörleri de arama
    "supported_image_formats": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"],
    "continue_on_error": True,             # Hata varsa devam et
    "generate_summary": True,              # Özet oluştur
}

# ============================================================================
# LOGGING AYARLARI
# ============================================================================

LOGGING_CONFIG = {
    "level": "INFO",                       # Log seviyesi
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": PROJECT_ROOT / "receipt_processing.log",
    "max_file_size": 10 * 1024 * 1024,    # 10 MB
    "backup_count": 5,                     # Kaç backup sakla
}

# ============================================================================
# VERİ TABANI AYARLARI (İsteğe bağlı)
# ============================================================================

DATABASE_CONFIG = {
    "enabled": False,                      # Veritabanı kullan
    "type": "sqlite",                      # sqlite, mysql, postgresql
    "path": PROJECT_ROOT / "receipts.db",  # SQLite için dosya yolu
    "host": "localhost",                   # MySQL/PostgreSQL için host
    "port": 3306,                          # MySQL/PostgreSQL için port
    "username": "",                        # Veritabanı kullanıcı adı
    "password": "",                        # Veritabanı şifresi
    "database": "receipts",                # Veritabanı adı
}

# ============================================================================
# İÇERİK AYARLARI (i18n)
# ============================================================================

CONTENT_STRINGS = {
    "tr": {
        "report_title": "Harcama Raporu",
        "general_summary": "Genel Özet",
        "category_distribution": "Kategori Bazlı Harcama Dağılımı",
        "receipt_details": "Fiş Detayları",
        "total_receipts": "Toplam Fiş Sayısı",
        "total_amount": "Genel Toplam Tutar",
        "total_tax": "Toplam KDV",
        "average_receipt": "Ortalama Fiş Tutarı",
        "category": "Kategori",
        "amount": "Tutar (₺)",
        "percentage": "Yüzde (%)",
        "product": "Ürün / Kalem",
        "price": "Fiyat (₺)",
        "merchant": "İşletme / Mağaza",
        "date": "Tarih",
        "report_date": "Rapor Tarihi",
    },
    "en": {
        "report_title": "Expense Report",
        "general_summary": "General Summary",
        "category_distribution": "Category-based Spending Distribution",
        "receipt_details": "Receipt Details",
        "total_receipts": "Total Receipts",
        "total_amount": "Total Amount",
        "total_tax": "Total Tax",
        "average_receipt": "Average Receipt Amount",
        "category": "Category",
        "amount": "Amount ($)",
        "percentage": "Percentage (%)",
        "product": "Product / Item",
        "price": "Price ($)",
        "merchant": "Merchant / Store",
        "date": "Date",
        "report_date": "Report Date",
    }
}

# Varsayılan dil
DEFAULT_LANGUAGE = "tr"

# ============================================================================
# YARDIMCI FONKSIYONLAR
# ============================================================================

def get_string(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    i18n string'ini al.
    
    Args:
        key (str): String anahtarı
        language (str): Dil kodu
        
    Returns:
        str: Çevrilen string
    """
    if language not in CONTENT_STRINGS:
        language = DEFAULT_LANGUAGE
    
    return CONTENT_STRINGS[language].get(key, key)


def ensure_directories() -> None:
    """
    Tüm gerekli klasörlerin var olduğundan emin ol.
    """
    for directory in [DATA_DIR, RAW_DATA_DIR, OUTPUTS_DIR, SRC_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # Konfigürasyonu test et
    print("Yapılandırma Parametreleri:")
    print(f"Proje Kökü: {PROJECT_ROOT}")
    print(f"Veri Klasörü: {RAW_DATA_DIR}")
    print(f"Çıktı Klasörü: {OUTPUTS_DIR}")
    print(f"\nImage Processor: {IMAGE_PROCESSOR_CONFIG}")
    print(f"OCR Engine: {OCR_ENGINE_CONFIG}")
    print(f"Parser: {PARSER_CONFIG}")
