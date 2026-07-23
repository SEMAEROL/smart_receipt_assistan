from typing import Any, Dict, List

try:
    from src.config import OCR_ENGINE_CONFIG
except ModuleNotFoundError:  # pragma: no cover
    from config import OCR_ENGINE_CONFIG


def normalize_ocr_output(raw_ocr_output: Any) -> List[Dict[str, Any]]:
    """
    Farklı OCR motorlarından gelen ham çıktıları standart bir formata dönüştürür.
    JSON parser'ın her zaman aynı veri yapısıyla çalışmasını sağlar.
    """
    if not raw_ocr_output:
        return []

    if isinstance(raw_ocr_output, dict) and "text" in raw_ocr_output:
        return _normalize_tesseract(raw_ocr_output)

    if isinstance(raw_ocr_output, list):
        if raw_ocr_output and isinstance(raw_ocr_output[0], dict):
            return _normalize_rapidocr(raw_ocr_output)

        if raw_ocr_output and isinstance(raw_ocr_output[0], (list, tuple)):
            if len(raw_ocr_output[0]) == 3 and isinstance(raw_ocr_output[0][0], (list, tuple)):
                return _normalize_rapidocr_list(raw_ocr_output)
            return _normalize_paddleocr(raw_ocr_output)

    raise ValueError(f"Normalizasyon desteklenmiyor: {type(raw_ocr_output).__name__}")

def _normalize_paddleocr(raw_output: Any) -> List[Dict[str, Any]]:
    """
    PaddleOCR Çıktı Formatı:
    [ [ [[x1,y1], [x2,y2], [x3,y3], [x4,y4]], ('Metin', 0.98) ], ... ]
    """
    standardized_data = []
    
    if not raw_output:
        return []
    if not isinstance(raw_output, list):
        return standardized_data
    
    page_data = raw_output[0] if isinstance(raw_output[0], list) else raw_output
    
    for line in page_data:
        if len(line) != 2:
            continue
            
        box, (text, confidence) = line
        
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


def _normalize_rapidocr(raw_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    RapidOCR benzeri fallback çıktı formatı:
    [ {"text": "...", "conf": 95.0, "left": 10, "top": 20, "width": 100, "height": 30}, ... ]
    """
    standardized_data = []
    for item in raw_output:
        text = str(item.get("text", "")).strip()
        conf = float(item.get("conf", 0.0))
        if not text:
            continue

        standardized_data.append({
            "text": text,
            "confidence": conf / 100.0,
            "bbox": {
                "x_min": int(item.get("left", 0)),
                "y_min": int(item.get("top", 0)),
                "x_max": int(item.get("left", 0)) + int(item.get("width", 0)),
                "y_max": int(item.get("top", 0)) + int(item.get("height", 0)),
            }
        })

    return standardized_data


def _normalize_rapidocr_list(raw_output: List[Any]) -> List[Dict[str, Any]]:
    """
    RapidOCR gerçek çıktı formatı:
    [ [ [[x1, y1], [x2, y2], [x3, y3], [x4, y4]], 'metin', 0.883 ], ... ]
    """
    standardized_data = []
    for item in raw_output:
        if len(item) < 3:
            continue

        box, text, conf = item[0], item[1], item[2]
        text = str(text).strip()
        if not text:
            continue

        x_coords = [point[0] for point in box]
        y_coords = [point[1] for point in box]
        standardized_data.append({
            "text": text,
            "confidence": float(conf),
            "bbox": {
                "x_min": int(min(x_coords)),
                "y_min": int(min(y_coords)),
                "x_max": int(max(x_coords)),
                "y_max": int(max(y_coords)),
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