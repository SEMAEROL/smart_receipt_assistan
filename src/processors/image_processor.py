import cv2
import numpy as np
from typing import Optional
from src.config import IMAGE_PROCESSOR_CONFIG

class ImageProcessor:
    """
    Masraf yönetimi ve OCR pipeline'ı için ön işleme modülü.
    Görsellerdeki gölgeleri ve gürültüleri temizleyerek metin tabanlı
    okuma (Tesseract/PaddleOCR) doğruluk oranını maksimize eder.
    """
    
    def __init__(self):
        self.kernel_size = IMAGE_PROCESSOR_CONFIG.get("kernel_size", 5)
        self.block_size = IMAGE_PROCESSOR_CONFIG.get("block_size", 11) 
        
        # Fiş üzerindeki gölgeleri tolere etmek ve arka planı temizlemek için optimum threshold değeri.
        self.c_value = IMAGE_PROCESSOR_CONFIG.get("c_value", 7)        

    def process(self, image_path: str) -> Optional[np.ndarray]:
        """
        Görüntü işleme adımlarını sırasıyla yöneten ana orkestratör.
        """
        image = cv2.imread(str(image_path))
        
        if image is None:
            return None

        gray_image = self._convert_to_grayscale(image)
        clean_image = self._remove_shadows_and_binarize(gray_image)
        
        return clean_image

    def _convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Optimum thresholding için renk uzayını daraltır."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _remove_shadows_and_binarize(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Adaptive Thresholding kullanarak aydınlatma farklılıklarını giderir 
        ve metni arka plandan izole eder.
        """
        blurred = cv2.GaussianBlur(gray_image, (self.kernel_size, self.kernel_size), 0)
        
        binary_image = cv2.adaptiveThreshold(
            blurred, 
            255,                                  
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,       
            cv2.THRESH_BINARY,                    
            self.block_size,                      
            self.c_value                          
        )
        
        # Tuz-karabiber (salt-and-pepper) gürültülerini filtreler.
        clean_binary = cv2.medianBlur(binary_image, 3)
        return clean_binary



