"""
OCR (Optik Karakter Tanıma) Motoru Modülü

Bu modül Tesseract OCR aracı kullanarak görüntülerden metin çıkarır
ve Levenshtein mesafesini kullanarak yazım hatalarını düzeltir.
"""

import pytesseract
import logging
import re
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import numpy as np

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCREngine:
    """
    OCR işlemlerini gerçekleştiren sınıf.
    
    Tesseract OCR aracı kullanarak görüntülerden metin çıkarır ve
    Levenshtein mesafesini kullanarak yazım hatalarını düzeltir.
    
    Attributes:
        language (str): OCR için kullanılan dil (Türkçe için 'tur')
        config (str): Tesseract konfigürasyonu
    """

    def __init__(self, language: str = "tur+eng"):
        """
        OCREngine başlatıcısı.
        
        Args:
            language (str): OCR dili (varsayılan: Türkçe + İngilizce)
        """
        self.language = language
        # Tesseract konfigürasyonu: PDF ve Üst Kalite modu
        self.config = "--oem 3 --psm 6"
        
        logger.info(f"OCREngine başlatıldı - Dil: {language}")

    def extract_text(self, processed_image: np.ndarray) -> str:
        """
        İşlenmiş görüntüden metin çıkarır.
        
        Args:
            processed_image (np.ndarray): Ön işlemden geçmiş görüntü
            
        Returns:
            str: Çıkarılan metin
        """
        if processed_image is None:
            logger.warning("İşlenmiş görüntü None, boş string döndürülüyor")
            return ""

        try:
            # Tesseract ile metin çıkarma
            raw_text = pytesseract.image_to_string(
                processed_image,
                lang=self.language,
                config=self.config
            )
            
            # Ham metni temizle
            cleaned_text = self._clean_text(raw_text)
            
            logger.info(f"Metin başarıyla çıkarıldı ({len(cleaned_text)} karakter)")
            return cleaned_text

        except Exception as e:
            logger.error(f"OCR işleminde hata oluştu: {str(e)}")
            return ""

    def _clean_text(self, text: str) -> str:
        """
        Çıkarılan metni temizler ve standardize eder.
        
        Args:
            text (str): Ham metin
            
        Returns:
            str: Temizlenmiş metin
        """
        # Fazla boşlukları kaldır
        text = re.sub(r'\s+', ' ', text)
        # Başı ve sonundaki boşlukları kaldır
        text = text.strip()
        # Kontrol karakterlerini kaldır
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        return text

    def levenshtein_distance(self, word1: str, word2: str) -> int:
        """
        İki kelime arasındaki Levenshtein mesafesini hesaplar.
        
        Levenshtein mesafesi, bir stringi diğer stringe dönüştürmek için
        gerekli olan minimum edit (ekleme, silme, değiştirme) sayısıdır.
        
        Args:
            word1 (str): Birinci kelime
            word2 (str): İkinci kelime
            
        Returns:
            int: Levenshtein mesafesi
        """
        # Lowercase'e çevir (case-insensitive)
        word1 = word1.lower()
        word2 = word2.lower()

        # DP tablosu oluştur
        rows = len(word1) + 1
        cols = len(word2) + 1
        dp = [[0 for _ in range(cols)] for _ in range(rows)]

        # İlk satırı ve sütunu doldur (boş stringten dönüşüm maliyeti)
        for i in range(rows):
            dp[i][0] = i
        for j in range(cols):
            dp[0][j] = j

        # DP tablosunu doldur
        for i in range(1, rows):
            for j in range(1, cols):
                if word1[i - 1] == word2[j - 1]:
                    # Karakterler aynı, maliyet eklenmez
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    # Karakterler farklı, minimum maliyetli operasyonu seç
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # Silme
                        dp[i][j - 1],      # Ekleme
                        dp[i - 1][j - 1]   # Değiştirme
                    )

        return dp[rows - 1][cols - 1]

    def fix_typos_levenshtein(
        self,
        word: str,
        dictionary: List[str],
        max_distance: int = 2
    ) -> str:
        """
        Levenshtein mesafesini kullanarak yazım hatalarını düzeltir.
        Verilen sözlükten en yakın eşleşmeyi bulur.
        
        Args:
            word (str): Düzeltilecek kelime
            dictionary (List[str]): Doğru kelimelerin listesi (sözlük)
            max_distance (int): Maksimum Levenshtein mesafesi
            
        Returns:
            str: Düzeltilmiş kelime veya orijinal kelime (eşleşme yoksa)
        """
        if not word or not dictionary:
            return word

        # Kelimeyi küçük harfe çevir
        word_lower = word.lower()
        
        # Aynı kelimeyi bul
        for dict_word in dictionary:
            if dict_word.lower() == word_lower:
                return dict_word

        # En yakın eşleşmeyi bul
        best_match = word
        min_distance = float('inf')

        for dict_word in dictionary:
            distance = self.levenshtein_distance(word, dict_word)
            
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                best_match = dict_word

        if min_distance <= max_distance:
            logger.debug(f"Typo düzeltildi: '{word}' → '{best_match}' (mesafe: {min_distance})")
            return best_match

        logger.debug(f"Typo düzeltme başarısız: '{word}' (en yakın mesafe: {min_distance})")
        return word

    def fix_typos_in_text(
        self,
        text: str,
        dictionary: List[str],
        max_distance: int = 2
    ) -> str:
        """
        Metnin tüm kelimelerinde yazım hatalarını düzeltir.
        
        Args:
            text (str): Düzeltilecek metin
            dictionary (List[str]): Doğru kelimelerin listesi
            max_distance (int): Maksimum Levenshtein mesafesi
            
        Returns:
            str: Düzeltilmiş metin
        """
        # Kelimeleri ayıkla
        words = text.split()
        corrected_words = []

        for word in words:
            # Noktalama işaretlerini ayıkla
            punctuation = ''
            clean_word = word
            
            while clean_word and not clean_word[-1].isalnum():
                punctuation = clean_word[-1] + punctuation
                clean_word = clean_word[:-1]

            # Typo düzelt
            corrected = self.fix_typos_levenshtein(clean_word, dictionary, max_distance)
            corrected_words.append(corrected + punctuation)

        return ' '.join(corrected_words)

    def extract_numbers(self, text: str) -> List[str]:
        """
        Metinden tüm sayıları çıkarır.
        Para miktarları (virgül ve nokta içeren) da dahil.
        
        Args:
            text (str): Metin
            
        Returns:
            List[str]: Bulunan sayılar
        """
        # Sayıları (ondalık destekli) bulma regex'i
        pattern = r'\d+(?:[.,]\d+)?'
        numbers = re.findall(pattern, text)
        return numbers

    def extract_dates(self, text: str) -> List[str]:
        """
        Metinden tarihleri çıkarır (DD.MM.YYYY, DD/MM/YYYY formatlarında).
        
        Args:
            text (str): Metin
            
        Returns:
            List[str]: Bulunan tarihler
        """
        # Tarih regex'leri (DD.MM.YYYY veya DD/MM/YYYY)
        patterns = [
            r'\d{2}[./]\d{2}[./]\d{4}',  # DD.MM.YYYY veya DD/MM/YYYY
            r'\d{4}[./]\d{2}[./]\d{2}',  # YYYY.MM.DD veya YYYY/MM/DD
        ]
        
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text))
        
        return dates

    def get_text_statistics(self, text: str) -> Dict[str, int]:
        """
        Metin hakkında istatistik bilgisi döndürür.
        
        Args:
            text (str): Metin
            
        Returns:
            Dict[str, int]: Metin istatistikleri
        """
        words = text.split()
        lines = text.split('\n')
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "line_count": len(lines),
            "average_word_length": len(text) // max(len(words), 1)
        }
