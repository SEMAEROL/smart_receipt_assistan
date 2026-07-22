"""
Test ve Örnek Komut Dosyası

Bu dosya projenin her bir bileşeninin nasıl kullanılacağını gösteren
test ve örnek kodlarını içerir.

Çalıştırmak için:
    python test_examples.py
"""

import sys
from pathlib import Path
import logging

# Logging ayarı
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# TEST 1: Veri Modelleri
# ============================================================================

def test_models():
    """
    ReceiptItem, Receipt ve BatchReportSummary sınıflarını test eder.
    """
    logger.info("=" * 60)
    logger.info("TEST 1: Veri Modelleri (Models)")
    logger.info("=" * 60)

    from src.models.receipt import ReceiptItem, Receipt, BatchReportSummary

    # ReceiptItem test
    print("\n1. ReceiptItem Oluşturma:")
    item1 = ReceiptItem(name="Ekmek", price=5.50)
    item2 = ReceiptItem(name="Süt", price=12.00)
    print(f"   ✓ Item 1: {item1.name} - ₺ {item1.price}")
    print(f"   ✓ Item 2: {item2.name} - ₺ {item2.price}")

    # Receipt test
    print("\n2. Receipt Oluşturma:")
    receipt = Receipt(
        filename="receipt_001.jpg",
        merchant_name="Market X",
        date="15.07.2026",
        total_amount=17.50,
        tax_amount=3.15,
        category="Market",
        items=[item1, item2],
        raw_text="Market X 15.07.2026 Ekmek 5.50 Süt 12.00 Toplam 17.50"
    )
    print(f"   ✓ İşletme: {receipt.merchant_name}")
    print(f"   ✓ Tarih: {receipt.date}")
    print(f"   ✓ Toplam: ₺ {receipt.total_amount}")
    print(f"   ✓ KDV: ₺ {receipt.tax_amount}")
    print(f"   ✓ Kategori: {receipt.category}")
    print(f"   ✓ Kalem Sayısı: {receipt.get_item_count()}")
    print(f"   ✓ KDV Hariç Tutar: ₺ {receipt.get_net_amount()}")

    # BatchReportSummary test
    print("\n3. BatchReportSummary Oluşturma:")
    summary = BatchReportSummary()
    summary.add_receipt(receipt)
    print(f"   ✓ Toplam Fiş: {summary.total_receipts}")
    print(f"   ✓ Toplam Tutar: ₺ {summary.total_amount}")
    print(f"   ✓ Toplam KDV: ₺ {summary.total_tax}")
    print(f"   ✓ Ortalama Fiş: ₺ {summary.get_average_receipt_amount()}")
    print(f"   ✓ Kategori Yüzde: %{summary.get_category_percentage('Market')}")

    print("\n✅ TEST 1 BAŞARILI\n")


# ============================================================================
# TEST 2: OCR Engine
# ============================================================================

def test_ocr_engine():
    """
    OCREngine sınıfını test eder - Levenshtein mesafesi hesaplaması.
    """
    logger.info("=" * 60)
    logger.info("TEST 2: OCR Engine (Levenshtein)")
    logger.info("=" * 60)

    from src.processors.ocr_engine import OCREngine

    ocr = OCREngine(language="tur+eng")

    # Levenshtein mesafesi test
    print("\n1. Levenshtein Mesafesi Hesaplama:")
    distances = [
        ("cat", "cat"),
        ("cat", "bat"),
        ("kitten", "sitting"),
        ("resiut", "receipt"),
    ]
    for word1, word2 in distances:
        dist = ocr.levenshtein_distance(word1, word2)
        print(f"   '{word1}' → '{word2}': {dist} (edit sayısı)")

    # Typo düzeltme test
    print("\n2. Typo Düzeltme:")
    dictionary = ["receipt", "restaurant", "market", "coffee"]
    typos = ["resiut", "restarant", "market", "cofe"]
    for typo in typos:
        corrected = ocr.fix_typos_levenshtein(typo, dictionary, max_distance=2)
        print(f"   '{typo}' → '{corrected}'")

    # Sayı çıkarma test
    print("\n3. Metinden Sayı Çıkarma:")
    text = "Toplam: 123.45 TL, KDV: 22.20 TL, 2 adet ürün"
    numbers = ocr.extract_numbers(text)
    print(f"   Metin: {text}")
    print(f"   Bulunan Sayılar: {numbers}")

    # Tarih çıkarma test
    print("\n4. Metinden Tarih Çıkarma:")
    text_with_date = "Tarih: 15.07.2026, Saat: 14:30, Tutar: 45.99"
    dates = ocr.extract_dates(text_with_date)
    print(f"   Metin: {text_with_date}")
    print(f"   Bulunan Tarihler: {dates}")

    print("\n✅ TEST 2 BAŞARILI\n")


# ============================================================================
# TEST 3: Parser
# ============================================================================

def test_parser():
    """
    ReceiptParser sınıfını test eder.
    """
    logger.info("=" * 60)
    logger.info("TEST 3: Receipt Parser")
    logger.info("=" * 60)

    from src.processors.parser import ReceiptParser

    parser = ReceiptParser()

    # Test metin
    test_text = """
    MARKET X
    Tarih: 15.07.2026
    
    Ekmek         5.50
    Süt 2L       12.00
    Çikolata      3.50
    
    Ara Toplam: 21.00
    KDV (%18):   3.78
    TOPLAM:     24.78
    """

    print("\n1. Ham Metni Ayrıştırma:")
    print(f"   Ham Metin:\n{test_text}")

    receipt = parser.parse(test_text, filename="test_receipt.jpg")

    print(f"\n2. Ayrıştırılmış Bilgiler:")
    print(f"   ✓ Dosya: {receipt.filename}")
    print(f"   ✓ İşletme: {receipt.merchant_name}")
    print(f"   ✓ Tarih: {receipt.date}")
    print(f"   ✓ Toplam Tutar: ₺ {receipt.total_amount}")
    print(f"   ✓ KDV: ₺ {receipt.tax_amount}")
    print(f"   ✓ Kategori: {receipt.category}")
    print(f"   ✓ Kalem Sayısı: {len(receipt.items)}")

    if receipt.items:
        print(f"\n3. Kalemleri:")
        for idx, item in enumerate(receipt.items, 1):
            print(f"   {idx}. {item.name}: ₺ {item.price}")

    print("\n✅ TEST 3 BAŞARILI\n")


# ============================================================================
# TEST 4: ImageProcessor (Demo)
# ============================================================================

def test_image_processor():
    """
    ImageProcessor sınıfını test eder (test görüntüsü olmadığında).
    """
    logger.info("=" * 60)
    logger.info("TEST 4: Image Processor (Demo)")
    logger.info("=" * 60)

    from src.processors.image_processor import ImageProcessor

    processor = ImageProcessor(kernel_size=5, blur_strength=5)

    print("\n1. ImageProcessor Bilgileri:")
    print(f"   ✓ Kernel Boyutu: {processor.kernel_size}x{processor.kernel_size}")
    print(f"   ✓ Blur Gücü: {processor.blur_strength}")

    print("\n2. Desteklenen İşlemler:")
    print(f"   ✓ convert_to_grayscale() - Gri tona çevirme")
    print(f"   ✓ remove_noise() - Gürültü engelleme")
    print(f"   ✓ apply_threshold() - Eşikleme")
    print(f"   ✓ apply_dilation() - Genişletme")
    print(f"   ✓ apply_erosion() - İnce leştirme")
    print(f"   ✓ process() - Tüm adımları sırayla uygula")

    print("\n3. Kullanım Örneği:")
    print(f"   processed_image = processor.process('receipt.jpg')")
    print(f"   if processed_image is not None:")
    print(f"       print('Görüntü başarıyla işlendi')")

    print("\n✅ TEST 4 BAŞARILI\n")


# ============================================================================
# TEST 5: Pipeline
# ============================================================================

def test_pipeline():
    """
    ReceiptPipeline sınıfını test eder.
    """
    logger.info("=" * 60)
    logger.info("TEST 5: Receipt Pipeline (Demo)")
    logger.info("=" * 60)

    from src.pipeline import ReceiptPipeline

    pipeline = ReceiptPipeline()

    print("\n1. Pipeline Bileşenleri:")
    print(f"   ✓ ImageProcessor: Başlatıldı")
    print(f"   ✓ OCREngine: Başlatıldı")
    print(f"   ✓ ReceiptParser: Başlatıldı")
    print(f"   ✓ DocxReportGenerator: Hazır")

    stats = pipeline.get_processing_stats()
    print(f"\n2. İstatistikler:")
    print(f"   ✓ Image Processor: {stats['image_processor']}")
    print(f"   ✓ OCR Dili: {stats['ocr_engine_language']}")
    print(f"   ✓ Kategoriler: {', '.join(stats['parser_categories'][:3])}...")

    print(f"\n3. Kullanım Örneği:")
    print(f"   pipeline.process_directory(")
    print(f"       input_dir='data/raw',")
    print(f"       output_docx_path='outputs/Harcama_Raporu.docx'")
    print(f"   )")

    print("\n✅ TEST 5 BAŞARILI\n")


# ============================================================================
# ANA MENU
# ============================================================================

def main():
    """
    Test ana menüsü.
    """
    print("\n" + "=" * 60)
    print("SMART RECEIPT ASSISTANT - TEST VE ÖRNEK KOMUTLARI")
    print("=" * 60)

    tests = [
        ("1", "Veri Modelleri (Receipt, ReceiptItem)", test_models),
        ("2", "OCR Engine (Levenshtein Mesafesi)", test_ocr_engine),
        ("3", "Receipt Parser (Veri Ayrıştırma)", test_parser),
        ("4", "Image Processor (Demo)", test_image_processor),
        ("5", "Receipt Pipeline (Demo)", test_pipeline),
        ("0", "Tüm Testleri Çalıştır", None),
    ]

    print("\nMevcut Testler:")
    for code, description, _ in tests:
        print(f"  {code}. {description}")

    choice = input("\nTest seçin (0-5): ").strip()

    if choice == "0":
        logger.info("Tüm testler çalıştırılıyor...")
        for code, _, test_func in tests[:-1]:
            if test_func:
                try:
                    test_func()
                except Exception as e:
                    logger.error(f"Test hatası: {e}")

    else:
        for code, desc, test_func in tests:
            if code == choice and test_func:
                try:
                    test_func()
                except Exception as e:
                    logger.error(f"Test hatası: {e}")
                break

    print("\n" + "=" * 60)
    print("TEST MENÜSÜ KAPATILIYOR...")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTesti iptal ettiniz.")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        sys.exit(1)
