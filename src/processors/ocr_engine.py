import logging
import re
import shutil
from typing import List, Dict, Any, Optional
import numpy as np
import pytesseract
from pytesseract import Output

try:
    from src.config import OCR_ENGINE_CONFIG
except ModuleNotFoundError:  # pragma: no cover
    from config import OCR_ENGINE_CONFIG

from src.processors.ocr_normalizer import normalize_ocr_output

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception:  # pragma: no cover
    RapidOCR = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCREngine:
    """
    Config dosyasına bağlı olarak Tesseract veya PaddleOCR kullanarak 
    görüntüden metin çıkaran ve Levenshtein ile düzelten ana sınıf.
    """

    def __init__(self, language: str = "tur+eng"):
        self.active_engine = OCR_ENGINE_CONFIG.get("active_engine", "tesseract")
        self.config_params = OCR_ENGINE_CONFIG.get("engines", {}).get(self.active_engine, {})
        self.language = language
        self.rapid_ocr = None
        
        if self.active_engine == "paddleocr":
            try:
                from paddleocr import PaddleOCR
                self.paddle_ocr = PaddleOCR(
                    lang=self.config_params.get("lang", "tr"),
                    use_angle_cls=self.config_params.get("use_angle_cls", True),
                    use_gpu=self.config_params.get("use_gpu", False),
                    show_log=False
                )
            except Exception as exc:
                logger.warning(f"PaddleOCR yüklenemedi, Tesseract kullanacak: {exc}")
                self.active_engine = "tesseract"
                self.config_params = OCR_ENGINE_CONFIG.get("engines", {}).get("tesseract", {})

        if self.active_engine == "tesseract":
            if self.config_params.get("tesseract_cmd"):
                pytesseract.pytesseract.tesseract_cmd = self.config_params["tesseract_cmd"]

            if shutil.which("tesseract") is None:
                logger.warning("Tesseract PATH erişimi yok, RapidOCR fallback devreye girecek.")
                if RapidOCR is not None:
                    self.rapid_ocr = RapidOCR()
                    self.active_engine = "rapidocr"
                    self.config_params = {}
                else:
                    self.active_engine = "rapidocr"
                    self.config_params = {}

        logger.info(f"OCREngine başlatıldı - Aktif Motor: {self.active_engine}")

    def process_image(self, processed_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Görseli alır, aktif OCR motorunda çalıştırır ve 
        NORMALİZE EDİLMİŞ standart liste formatında döndürür.
        """
        if processed_image is None:
            logger.warning("Görüntü None, boş liste dönüyor.")
            return []

        try:
            if self.active_engine == "paddleocr":
                raw_output = self.paddle_ocr.ocr(processed_image, cls=True)

            elif self.active_engine == "rapidocr":
                if self.rapid_ocr is None:
                    raise RuntimeError("RapidOCR motoru kurulu değil")
                result, _ = self.rapid_ocr(np.array(processed_image))
                raw_output = result
            
            elif self.active_engine == "tesseract":
                lang = self.language or self.config_params.get("language", "tur+eng")
                custom_config = self.config_params.get("config", "--oem 3 --psm 6")
                raw_output = pytesseract.image_to_data(
                    processed_image,
                    lang=lang,
                    config=custom_config,
                    output_type=Output.DICT
                )
            
            standardized_data = normalize_ocr_output(raw_output)
            return standardized_data

        except Exception as e:
            logger.error(f"OCR işleminde hata oluştu: {str(e)}")
            return []

    def extract_text(self, processed_image: np.ndarray) -> str:
        """
        Görüntüden OCR ile metin çıktısı döndürür.
        """
        standardized = self.process_image(processed_image)
        if not standardized:
            return ""

        return " ".join(item.get("text", "") for item in standardized if item.get("text"))

    # =========================================================================
    # LEVENSHTEIN VE YAZIM DÜZELTME METOTLARI (Aynen Korundu)
    # =========================================================================

    def levenshtein_distance(self, word1: str, word2: str) -> int:
        word1, word2 = word1.lower(), word2.lower()
        rows, cols = len(word1) + 1, len(word2) + 1
        dp = [[0 for _ in range(cols)] for _ in range(rows)]

        for i in range(rows): dp[i][0] = i
        for j in range(cols): dp[0][j] = j

        for i in range(1, rows):
            for j in range(1, cols):
                if word1[i - 1] == word2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

        return dp[rows - 1][cols - 1]

    def fix_typos_levenshtein(self, word: str, dictionary: List[str], max_distance: int = 2) -> str:
        if not word or not dictionary: return word
        word_lower = word.lower()
        
        for dict_word in dictionary:
            if dict_word.lower() == word_lower:
                return dict_word

        best_match = word
        min_distance = float('inf')

        for dict_word in dictionary:
            distance = self.levenshtein_distance(word, dict_word)
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                best_match = dict_word

        return best_match if min_distance <= max_distance else word