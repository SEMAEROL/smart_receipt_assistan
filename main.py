"""
Akıllı Fatura/Fiş Okuma ve Mini Muhasebe Asistanı - Ana Giriş Noktası

Bu script ReceiptPipeline'ı kullanarak data/raw klasöründeki tüm görüntüleri
işler ve sonuçları bir Word raporuna kaydeder.
"""

import logging
import sys
from pathlib import Path

# Proje kütüphaneleri
from src.pipeline import ReceiptPipeline

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('receipt_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """
    Ana uygulama fonksiyonu.
    
    İşleme adımları:
    1. Giriş ve çıkış klasörlerini tanımla
    2. ReceiptPipeline'ı başlat
    3. Klasördeki tüm görselleri işle
    4. Word raporunu oluştur ve kaydet
    """
    
    logger.info("="*60)
    logger.info("Akıllı Fatura/Fiş Okuma ve Mini Muhasebe Asistanı Başlatıldı")
    logger.info("="*60)

    # Klasör yollarını tanımla
    project_root = Path(__file__).parent
    input_directory = project_root / "data" / "raw"
    output_directory = project_root / "outputs"
    output_file = output_directory / "Harcama_Raporu.docx"

    # Giriş klasörü varlığı kontrolü
    if not input_directory.exists():
        logger.error(f"Giriş klasörü bulunamadı: {input_directory}")
        logger.info("Lütfen 'data/raw' klasörüne görüntü dosyaları ekleyiniz.")
        return False

    # Çıkış klasörünü oluştur
    output_directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Giriş klasörü: {input_directory}")
    logger.info(f"Çıkış dosyası: {output_file}")

    try:
        # Pipeline'ı başlat
        pipeline = ReceiptPipeline()
        
        # Klasördeki tüm görselleri işle
        logger.info(f"İşleme başlanıyor...")
        success = pipeline.process_directory(
            input_dir=str(input_directory),
            output_docx_path=str(output_file),
            recursive=False
        )

        if success:
            logger.info("="*60)
            logger.info("✓ İşleme başarıyla tamamlandı!")
            logger.info(f"✓ Rapor kaydedildi: {output_file}")
            logger.info("="*60)
            
            # Rapor bilgilerini göster
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB cinsinden
                logger.info(f"Dosya boyutu: {file_size:.2f} KB")
            
            return True
        else:
            logger.error("="*60)
            logger.error("✗ İşleme başarısız oldu!")
            logger.error("Lütfen logs'u kontrol ediniz.")
            logger.error("="*60)
            return False

    except KeyboardInterrupt:
        logger.warning("\nİşleme kullanıcı tarafından durduruldu.")
        return False
    except Exception as e:
        logger.error(f"Beklenmeyen hata oluştu: {str(e)}")
        logger.exception("Detaylı hata bilgisi:")
        return False


def run_demo_with_sample():
    """
    Örnek veriler ile demo çalıştırması yapar.
    (Test amaçlı)
    
    Not: Gerçek görüntü dosyaları data/raw klasörüne eklenmelidir.
    """
    logger.info("Demo modunda çalışıyor...")
    
    # Örnek bilgiler
    logger.info("Beklenen klasör yapısı:")
    logger.info("  smart_receipt_assistan/")
    logger.info("  ├── data/")
    logger.info("  │   └── raw/")
    logger.info("  │       ├── receipt1.jpg")
    logger.info("  │       ├── receipt2.png")
    logger.info("  │       └── ...")
    logger.info("  └── outputs/")
    logger.info("      └── Harcama_Raporu.docx (oluşturulacak)")
    
    return True


if __name__ == "__main__":
    """
    Uygulamanın giriş noktası.
    
    Kullanım:
        python main.py
    
    data/raw klasörüne görüntü dosyaları eklendikten sonra çalıştırın.
    Sonuç outputs/Harcama_Raporu.docx dosyasına kaydedilecektir.
    """
    
    success = main()
    sys.exit(0 if success else 1)
