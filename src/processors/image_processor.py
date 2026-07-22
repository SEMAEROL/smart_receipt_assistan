"""
Görüntü İşleme Modülü

Bu modül OpenCV kullanarak fatura/fiş görsellerini ön işlemden geçirir.
Gri tona çevirme, gürültü engelleme ve eşikleme işlemlerini gerçekleştirir.
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Optional

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Görüntü ön işleme için gerekli tüm işlemleri gerçekleştiren sınıf.
    
    OpenCV kütüphanesi kullanarak:
    - Gri tona çevirme
    - Gürültü engelleme
    - Adaptif eşikleme
    işlemlerini sırayla uygular.
    
    Attributes:
        kernel_size (int): Morfolojik işlemler için kernel boyutu
        blur_strength (int): Gürültü engelleme gücü
    """

    def __init__(self, kernel_size: int = 5, blur_strength: int = 5):
        """
        ImageProcessor başlatıcısı.
        
        Args:
            kernel_size (int): Morfolojik işlemler için kernel boyutu (tek sayı olmalı)
            blur_strength (int): Gürültü engelleme gücü (tek sayı olmalı)
        """
        # Kernel ve blur değerlerinin tek sayı olduğunu doğrula
        if kernel_size % 2 == 0:
            kernel_size += 1
        if blur_strength % 2 == 0:
            blur_strength += 1

        self.kernel_size = kernel_size
        self.blur_strength = blur_strength
        self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        
        logger.info(f"ImageProcessor başlatıldı - Kernel: {kernel_size}x{kernel_size}, Blur: {blur_strength}")

    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Renkli görüntüyü gri tona çevirir.
        
        Args:
            image (np.ndarray): Renkli görüntü (BGR formatında)
            
        Returns:
            np.ndarray: Gri tone çevrilmiş görüntü
        """
        if len(image.shape) == 2:
            logger.warning("Görüntü zaten gri tonlu, dönüştürmeye gerek yok")
            return image

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        logger.debug("Görüntü gri tona çevrildi")
        return gray

    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Görüntüdeki gürültüyü engeller.
        Bilateral filtering kullanarak kenarları koruyarak gürültü engeller.
        
        Args:
            image (np.ndarray): Gri ton görüntü
            
        Returns:
            np.ndarray: Gürültü engelleme uygulanmış görüntü
        """
        # Bilateral filtering - kenarları korur, gürültüyü engeller
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        # Ek gürültü engelleme: morphological opening (erosion → dilation)
        # Küçük gürültü parçacıklarını kaldırır
        opened = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, self.kernel, iterations=1)
        
        logger.debug("Gürültü engelleme işlemi tamamlandı")
        return opened

    def apply_threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Adaptif eşikleme (thresholding) uygular.
        Görüntüyü siyah ve beyaza çevirir.
        Adaptif eşikleme, ışık değişkenliğine karşı daha dirençli olduğu için kullanılır.
        
        Args:
            image (np.ndarray): Gri ton görüntü
            
        Returns:
            np.ndarray: Eşikleme uygulanmış ikili (binary) görüntü
        """
        # Adaptif eşikleme: Gaussian ortalama kullanır
        # maxValue=255, neighborhood=11x11, constant=2
        thresholded = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        logger.debug("Adaptif eşikleme uygulandı")
        return thresholded

    def apply_dilation(self, image: np.ndarray, iterations: int = 1) -> np.ndarray:
        """
        Dilation işlemi uygular - metin bölgelerini genişletir.
        
        Args:
            image (np.ndarray): İkili görüntü
            iterations (int): Dilation iterasyon sayısı
            
        Returns:
            np.ndarray: Dilation uygulanmış görüntü
        """
        dilated = cv2.dilate(image, self.kernel, iterations=iterations)
        logger.debug(f"Dilation işlemi uygulandı ({iterations} iterasyon)")
        return dilated

    def apply_erosion(self, image: np.ndarray, iterations: int = 1) -> np.ndarray:
        """
        Erosion işlemi uygular - metin bölgelerini ince leştirir.
        
        Args:
            image (np.ndarray): İkili görüntü
            iterations (int): Erosion iterasyon sayısı
            
        Returns:
            np.ndarray: Erosion uygulanmış görüntü
        """
        eroded = cv2.erode(image, self.kernel, iterations=iterations)
        logger.debug(f"Erosion işlemi uygulandı ({iterations} iterasyon)")
        return eroded

    def resize_image(self, image: np.ndarray, max_width: int = 2000, max_height: int = 2000) -> np.ndarray:
        """
        Görüntüyü maksimum boyutlara göre yeniden boyutlandırır.
        Oranları koruyan yeniden boyutlandırma yapar.
        
        Args:
            image (np.ndarray): Görüntü
            max_width (int): Maksimum genişlik
            max_height (int): Maksimum yükseklik
            
        Returns:
            np.ndarray: Yeniden boyutlandırılmış görüntü
        """
        height, width = image.shape[:2]

        # Boyut kontrolü
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.debug(f"Görüntü yeniden boyutlandırıldı: {width}x{height} → {new_width}x{new_height}")
            return resized

        return image

    def process(self, image_path: str) -> Optional[np.ndarray]:
        """
        Tüm ön işleme adımlarını sırayla uygular.
        Ana metod - çağrı noktası olarak kullanılır.
        
        İşleme adımları:
        1. Görüntüyü dosyadan yükleme
        2. Boyutlandırma
        3. Gri tona çevirme
        4. Gürültü engelleme
        5. Eşikleme
        6. Dilation ve Erosion
        
        Args:
            image_path (str): İşlenecek görüntü dosyasının yolu
            
        Returns:
            np.ndarray: Ön işlemden geçmiş görüntü (numpy array)
            None: Dosya bulunamadı veya hata oluştu durumunda
        """
        # Dosya varlığı kontrolü
        if not Path(image_path).exists():
            logger.error(f"Görüntü dosyası bulunamadı: {image_path}")
            return None

        try:
            # Adım 1: Görüntüyü yükle
            original_image = cv2.imread(image_path)
            if original_image is None:
                logger.error(f"Görüntü yüklenemedi: {image_path}")
                return None
            logger.info(f"Görüntü yüklendi: {image_path}")

            # Adım 2: Boyutlandırma
            resized = self.resize_image(original_image)

            # Adım 3: Gri tona çevirme
            gray = self.convert_to_grayscale(resized)

            # Adım 4: Gürültü engelleme
            denoised = self.remove_noise(gray)

            # Adım 5: Eşikleme
            thresholded = self.apply_threshold(denoised)

            # Adım 6: Morfolojik işlemler
            dilated = self.apply_dilation(thresholded, iterations=1)
            processed = self.apply_erosion(dilated, iterations=1)

            logger.info(f"Görüntü ön işleme başarıyla tamamlandı: {image_path}")
            return processed

        except Exception as e:
            logger.error(f"Görüntü işlemede hata oluştu ({image_path}): {str(e)}")
            return None

    def get_image_info(self, image: np.ndarray) -> dict:
        """
        Görüntü hakkında bilgi döndürür.
        
        Args:
            image (np.ndarray): Görüntü
            
        Returns:
            dict: Görüntü bilgileri
        """
        if image is None:
            return {}
        
        height, width = image.shape[:2]
        return {
            "width": width,
            "height": height,
            "channels": len(image.shape) if len(image.shape) > 2 else 1,
            "dtype": str(image.dtype)
        }
