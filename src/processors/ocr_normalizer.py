from typing import Any, Dict, List
from config import OCR_ENGINE_CONFIG


def normalize_ocr_output(raw_ocr_output: Any) -> List[Dict[str, Any]]:
    """
    Farklı OCR motorlarından gelen ham çıktıları standart bir formata dönüştürür.
    JSON parser'ın her zaman aynı veri yapısıyla çalışmasını sağlar.
    """
    active_engine = OCR_ENGINE_CONFIG.get("active_engine")
    
    if active_engine == "paddleocr":
        return _normalize_paddleocr(raw_ocr_output)
    
    elif active_engine == "tesseract":
        return _normalize_tesseract(raw_ocr_output)
    
    else:
        raise ValueError(f"Normalizasyon desteklenmiyor: {active_engine}")

def _normalize_paddleocr(raw_output: Any) -> List[Dict[str, Any]]:
    """
    PaddleOCR Çıktı Formatı:
    [ [ [[x1,y1], [x2,y2], [x3,y3], [x4,y4]], ('Metin', 0.98) ], ... ]
    """
    standardized_data = []
    
    if not raw_output:
        return []
    # PaddleOCR bazen liste içinde liste dönebilir, yapıyı kontrol ediyoruz
    if not raw_output or not isinstance(raw_output, list):
        return standardized_data
    
    
    # İlk sayfanın verisi
    page_data = raw_output[0] if isinstance(raw_output[0], list) else raw_output
    
    for line in page_data:
        if len(line) != 2:
            continue
            
        box, (text, confidence) = line
        
        # Bounding box koordinatlarını ayıkla (sol üst ve sağ alt köşeler)
        x_coords = [point[0] for point in box]
        y_coords = [point[1] for point in box]
        
        standardized_data.append({
            "text": text.strip(),
            "confidence": float(confidence),
            "bbox": {
                "x_min": int(min(x_coords)),
                "y_min": int(min(y_coords)),
                "x_max": int(max(x_coords)),
                "y_max": int(max(y_coords))
            }
        })
        
    return standardized_data

def _normalize_tesseract(raw_output: Dict[str, list]) -> List[Dict[str, Any]]:
    """
    Tesseract Çıktı Formatı (pytesseract.image_to_data(output_type=Output.DICT) kullanıldığında):
    {'text': ['Metin', ''], 'conf': [95, -1], 'left': [10, 0], 'top': [20, 0], 'width': [90, 0], 'height': [20, 0], ...}
    """
    standardized_data = []
    
    # Tesseract çıktısı boş veya hatalıysa
    if not raw_output or 'text' not in raw_output:
        return standardized_data
        
    n_boxes = len(raw_output['text'])
    for i in range(n_boxes):
        text = str(raw_output['text'][i]).strip()
        conf = float(raw_output['conf'][i])
        
        # Boş metinleri ve çok düşük güvenilirlikli (veya -1 olan boşluk) verileri atla
        if not text or conf < 0:
            continue
            
        x_min = int(raw_output['left'][i])
        y_min = int(raw_output['top'][i])
        width = int(raw_output['width'][i])
        height = int(raw_output['height'][i])
        
        standardized_data.append({
            "text": text,
            "confidence": conf / 100.0, # 0-1 aralığına normalize et (Tesseract 0-100 arası döner)
            "bbox": {
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_min + width,
                "y_max": y_min + height
            }
        })
        
    return standardized_data