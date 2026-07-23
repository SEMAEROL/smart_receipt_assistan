import logging
import shutil
from typing import List, Dict, Any
import numpy as np
import pytesseract
from pytesseract import Output
from src.processors.ocr_normalizer import normalize_ocr_output

try:
    from src.config import OCR_ENGINE_CONFIG
except ModuleNotFoundError:  # pragma: no cover
    from config import OCR_ENGINE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCREngine:
    def __init__(self, language: str = "tur+eng"):
        self.active_engine = OCR_ENGINE_CONFIG.get("active_engine", "tesseract")
        self.config_params = OCR_ENGINE_CONFIG.get("engines", {}).get(self.active_engine, {})
        self.language = language
        
        if self.active_engine == "tesseract":
            t_cmd = self.config_params.get("tesseract_cmd")
            if t_cmd:
                pytesseract.pytesseract.tesseract_cmd = t_cmd

        logger.info(f"OCREngine başlatıldı - Aktif Motor: {self.active_engine}")

    def process_image(self, processed_image: np.ndarray) -> List[Dict[str, Any]]:
        if processed_image is None:
            logger.warning("Görüntü None, boş liste dönüyor.")
            return []

        try:
            lang = self.language or self.config_params.get("language", "tur+eng")
            custom_config = self.config_params.get("config", "--oem 3 --psm 6")
            raw_output = pytesseract.image_to_data(
                processed_image,
                lang=lang,
                config=custom_config,
                output_type=Output.DICT
            )
            
            # Doğrudan ana normalizer fonksiyonunu çağırıyoruz
            standardized_data = normalize_ocr_output(raw_output)
            return standardized_data

        except Exception as e:
            logger.error(f"OCR işleminde hata oluştu: {str(e)}")
            return []

    def extract_text(self, processed_image: np.ndarray) -> str:
        standardized = self.process_image(processed_image)
        if not standardized:
            return ""

        return " ".join(item.get("text", "") for item in standardized if item.get("text"))