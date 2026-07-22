"""
Fiş İşleme Boru Hattı Modülü

Bu modül tüm işlemleri (görüntü işleme, OCR, ayrıştırma, raporlama)
birbiriyle entegre ederek bir boru hattı (pipeline) oluşturur.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple
import os

from src.processors.image_processor import ImageProcessor
from src.processors.ocr_engine import OCREngine
from src.processors.parser_to_json import ReceiptParser
from src.reporting.docx_generator import DocxReportGenerator
from src.models.receipt import Receipt, BatchReportSummary
from src.processors.ocr_normalizer import normalize_ocr_output

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReceiptPipeline:
    """
    Fiş/Fatura işleme boru hattını yöneten orkestra sınıfı.
    
    Tüm bileşenleri (ImageProcessor, OCREngine, ReceiptParser, DocxReportGenerator)
    entegre ederek bir görüntüdeki fişi okumaktan Word raporuna kadar
    tüm süreci yönetir.
    
    İş akışı:
    1. Görüntü dosyasını yükle
    2. Görüntü ön işlemesi yap
    3. OCR ile metin çıkar
    4. Metni ayrıştır ve Receipt oluştur
    5. Tüm fişleri bir Word raporuna dönüştür
    
    Attributes:
        image_processor (ImageProcessor): Görüntü işlemci
        ocr_engine (OCREngine): OCR motoru
        parser (ReceiptParser): Fiş ayrıştırıcı
        report_generator (DocxReportGenerator): Rapor üretici
    """

    def __init__(self):
        """ReceiptPipeline başlatıcısı - Tüm bileşenleri başlatır."""
        self.image_processor = ImageProcessor(kernel_size=5, blur_strength=5)
        self.ocr_engine = OCREngine(language="tur+eng")
        self.parser = ReceiptParser()
        self.report_generator = None  # Raporlama sırasında oluşturulacak
        
        logger.info("ReceiptPipeline başlatıldı")

    def _is_image_file(self, file_path: str) -> bool:
        """
        Dosyanın görüntü formatında olduğunu kontrol eder.
        
        Args:
            file_path (str): Dosya yolu
            
        Returns:
            bool: Görüntü dosyası ise True
        """
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        file_extension = Path(file_path).suffix.lower()
        return file_extension in supported_formats

    def process_single_receipt(self, image_path: str) -> Optional[Receipt]:
        logger.info(f"Fiş işleniyor: {image_path}")

        try:
            # Adım 1: Görüntü ön işlemesi
            processed_image = self.image_processor.process(image_path)
            if processed_image is None:
                logger.error(f"Görüntü ön işlemesi başarısız: {image_path}")
                return None

            # Adım 2: OCR ile metin çıkarma (Farklı modeller farklı veri tipleri dönebilir)
            raw_ocr_data = self.ocr_engine.extract_text(processed_image)
            
            # Eğer OCR hiçbir şey bulamadıysa işlemi kes
            if not raw_ocr_data:
                logger.warning(f"OCR metni boş, fiş atlanıyor: {image_path}")
                return None 

            # Adım 3: OCR Çıktısını Normalize Et (Her modelden gelen veriyi tek tipe çevir)
            standard_data = normalize_ocr_output(raw_ocr_data)
            
            # Eğer normalizasyon sonrası liste boşsa yine devam etmenin anlamı yok
            if not standard_data:
                logger.warning(f"Normalizasyon sonrası metin kalmadı: {image_path}")
                return None

            # Adım 4: Metni ayrıştırma
            filename = Path(image_path).name
            final_json = self.parser.parse(standard_data, filename=filename)

            logger.info(f"Fiş başarıyla işlendi: {filename} - {final_json.merchant_name}")
            return final_json

        except Exception as e:
            logger.error(f"Fiş işlemede kritik hata ({image_path}): {str(e)}")
            return None

    def process_directory(
        self,
        input_dir: str,
        output_docx_path: str,
        recursive: bool = False
    ) -> bool:
        """
        Bir klasördeki tüm görüntüleri işler ve Word raporuna kaydeder.
        
        Ana orchestration metodu. Klasördeki tüm görüntüleri birer birer işler,
        yapılandırılmış Receipt nesneleri oluşturur ve nihai bir Word raporunda
        birleştirir.
        
        Args:
            input_dir (str): Görüntülerin bulunduğu giriş klasörü
            output_docx_path (str): Çıktı Word dosyasının yolu
            recursive (bool): Alt klasörleri de işleme dahil et
            
        Returns:
            bool: Başarı durumu
        """
        logger.info(f"Klasör işleniyor: {input_dir}")

        # Giriş klasörü varlığı kontrolü
        input_path = Path(input_dir)
        if not input_path.exists() or not input_path.is_dir():
            logger.error(f"Giriş klasörü bulunamadı: {input_dir}")
            return False

        try:
            # Görüntü dosyalarını topla
            image_files = []
            if recursive:
                image_files = list(input_path.rglob("*"))
            else:
                image_files = list(input_path.glob("*"))

            # Desteklenen formatları filtrele
            image_files = [f for f in image_files if f.is_file() and self._is_image_file(str(f))]

            if not image_files:
                logger.warning(f"Klasörde görüntü dosyası bulunamadı: {input_dir}")
                return False

            logger.info(f"Bulunan görüntü dosyaları: {len(image_files)}")

            # Her görüntüyü işle
            receipts = []
            for image_file in image_files:
                receipt = self.process_single_receipt(str(image_file))
                if receipt:
                    receipts.append(receipt)
                else:
                    logger.warning(f"Fiş işleme başarısız, atlanıyor: {image_file.name}")

            if not receipts:
                logger.error("Hiçbir fiş başarıyla işlenmedi")
                return False

            # Özet bilgilerini oluştur
            summary = self._create_summary(receipts)

            # Rapor üret ve kaydet
            return self._generate_and_save_report(receipts, summary, output_docx_path)

        except Exception as e:
            logger.error(f"Klasör işlemede kritik hata: {str(e)}")
            return False

    def _create_summary(self, receipts: List[Receipt]) -> BatchReportSummary:
        """
        Fişlerin özetini oluşturur.
        
        Args:
            receipts (List[Receipt]): Receipt nesnelerinin listesi
            
        Returns:
            BatchReportSummary: Hazırlanmış özet nesnesi
        """
        logger.info(f"Özet oluşturuluyor ({len(receipts)} fiş)...")

        summary = BatchReportSummary()
        for receipt in receipts:
            summary.add_receipt(receipt)

        logger.info(
            f"Özet tamamlandı - "
            f"Toplam: ₺ {summary.total_amount:,.2f}, "
            f"KDV: ₺ {summary.total_tax:,.2f}, "
            f"Kategoriler: {len(summary.category_totals)}"
        )

        return summary

    def _generate_and_save_report(
        self,
        receipts: List[Receipt],
        summary: BatchReportSummary,
        output_docx_path: str
    ) -> bool:
        """
        Raporu oluşturur ve kaydeder.
        
        Args:
            receipts (List[Receipt]): Receipt nesnelerinin listesi
            summary (BatchReportSummary): Rapor özeti
            output_docx_path (str): Çıktı dosyası yolu
            
        Returns:
            bool: Başarı durumu
        """
        try:
            logger.info("Word raporu oluşturuluyor...")

            # Rapor üreticiyi başlat
            self.report_generator = DocxReportGenerator(
                title="Harcama Raporu",
                author="Smart Receipt Assistant"
            )

            # Raporu oluştur ve kaydet
            success = self.report_generator.generate_report(
                receipts,
                summary,
                output_docx_path
            )

            if success:
                logger.info(f"Rapor başarıyla kaydedildi: {output_docx_path}")
            else:
                logger.error("Rapor oluşturma başarısız")

            return success

        except Exception as e:
            logger.error(f"Rapor oluşturmada hata: {str(e)}")
            return False

    def process_multiple_directories(
        self,
        input_dirs: List[str],
        output_docx_path: str
    ) -> bool:
        """
        Birden fazla klasördeki görüntüleri işler ve tek bir rapor haline getirir.
        
        Args:
            input_dirs (List[str]): Giriş klasörleri listesi
            output_docx_path (str): Çıktı Word dosyasının yolu
            
        Returns:
            bool: Başarı durumu
        """
        logger.info(f"Çoklu klasör işleniyor ({len(input_dirs)} klasör)...")

        all_receipts = []

        for input_dir in input_dirs:
            logger.info(f"Klasör işleniyor: {input_dir}")
            
            input_path = Path(input_dir)
            if not input_path.exists():
                logger.warning(f"Klasör bulunamadı, atlanıyor: {input_dir}")
                continue

            image_files = [f for f in input_path.glob("*") if self._is_image_file(str(f))]

            for image_file in image_files:
                receipt = self.process_single_receipt(str(image_file))
                if receipt:
                    all_receipts.append(receipt)

        if not all_receipts:
            logger.error("Hiçbir fiş işlenmedi")
            return False

        summary = self._create_summary(all_receipts)
        return self._generate_and_save_report(all_receipts, summary, output_docx_path)

    def get_processing_stats(self) -> dict:
        """
        İşleme hakkında istatistik bilgisi döndürür.
        
        Returns:
            dict: İstatistik bilgileri
        """
        stats = {
            "image_processor": str(type(self.image_processor).__name__),
            "ocr_engine_language": self.ocr_engine.language,
            "parser_categories": list(self.parser.category_keywords.keys()),
        }
        return stats
