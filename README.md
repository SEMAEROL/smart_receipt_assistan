# Akıllı Fatura/Fiş Okuma ve Mini Muhasebe Asistanı

**Smart Receipt Assistant** - Tesseract OCR ve Python tabanlı profesyonel fiş/fatura işleme sistemi.

## 📋 Proje Özeti

Bu proje, fiş ve fatura görsellerini otomatik olarak okur, bilgilerini çıkarır ve kategorize ederek profesyonel bir Word raporuna dönüştüren Python uygulamasıdır.

### Özellikler

✅ **OCR Teknolojisi** - Tesseract kullanarak türkçe/ingilizce metin okuma
✅ **Görüntü İşleme** - OpenCV ile ön işleme (gri tona çevirme, gürültü engelleme, eşikleme)
✅ **Typo Düzeltme** - Levenshtein mesafesi ile yazım hatası düzeltme
✅ **Akıllı Kategorizasyon** - İşletme adı ve içeriğe göre kategori tahmini
✅ **Professional Raporlama** - python-docx ile şık Word raporları
✅ **Modüler Mimari** - SOLID ve OOP prensipleriyle tasarlanmış
✅ **Logging & Error Handling** - Detaylı loglama ve hata yönetimi

---

## 📂 Proje Yapısı

```
smart_receipt_assistant/
│
├── src/
│   ├── __init__.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── receipt.py              # ReceiptItem, Receipt, BatchReportSummary dataclass'ları
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── image_processor.py      # ImageProcessor - Görüntü ön işleme
│   │   ├── ocr_engine.py           # OCREngine - Metin çıkarma & typo düzeltme
│   │   └── parser.py               # ReceiptParser - Veri ayrıştırma
│   │
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── docx_generator.py       # DocxReportGenerator - Word rapor oluşturma
│   │
│   └── pipeline.py                 # ReceiptPipeline - Orkestra sınıfı
│
├── data/
│   └── raw/                        # Giriş: Fiş görüntüleri (JPG, PNG)
│
├── outputs/
│   └── Harcama_Raporu.docx        # Çıktı: Oluşturulan Word raporu
│
├── main.py                         # Uygulamanın ana giriş noktası
├── requirements.txt                # Python bağımlılıkları
└── README.md                       # Bu dosya
```

---

## 🛠️ Kurulum

### 1. Gereksinimler

- **Python 3.8+**
- **Tesseract OCR** (Sistem paketi olarak kurulu olmalı)
  
  **Windows:**
  ```bash
  # https://github.com/UB-Mannheim/tesseract/wiki adresinden indir ve kur
  # veya Scoop/Chocolatey ile:
  choco install tesseract
  ```
  
  **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt-get install tesseract-ocr
  sudo apt-get install libtesseract-dev
  ```
  
  **macOS:**
  ```bash
  brew install tesseract
  ```

### 2. Python Ortamı Oluşturma

```bash
# Virtual environment oluştur
python -m venv venv

# Windows'ta aktif et
venv\Scripts\activate

# Linux/macOS'ta aktif et
source venv/bin/activate
```

### 3. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 4. Tesseract Yolunu Ayarla (Windows için)

Eğer Tesseract standart yolda kurulu değilse, `main.py` içinde:

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 🚀 Kullanım

### Temel Kullanım

```bash
# data/raw klasörüne fiş görüntülerini koy
# (örn: receipt1.jpg, receipt2.png, ...)

# Uygulamayı çalıştır
python main.py

# Sonuç: outputs/Harcama_Raporu.docx oluşturulacak
```

### Python Kodunda Kullanım

```python
from src.pipeline import ReceiptPipeline

# Pipeline'ı başlat
pipeline = ReceiptPipeline()

# Klasörü işle
success = pipeline.process_directory(
    input_dir="data/raw",
    output_docx_path="outputs/Harcama_Raporu.docx",
    recursive=False
)

if success:
    print("✓ Başarılı!")
else:
    print("✗ Hata oluştu")
```

### Birden Fazla Klasörü İşleme

```python
# Birden fazla klasördeki görüntüleri işle
pipeline.process_multiple_directories(
    input_dirs=["data/raw", "data/backups"],
    output_docx_path="outputs/Harcama_Raporu.docx"
)
```

---

## 📊 Sınıf Mimarisi

### 1. **Receipt.py** - Veri Modelleri

```python
# ReceiptItem - Fiş kalemini temsil eder
@dataclass
class ReceiptItem:
    name: str          # Ürün adı
    price: float       # Fiyat

# Receipt - Tüm fiş bilgilerini tutar
@dataclass
class Receipt:
    filename: str
    merchant_name: str
    date: str
    total_amount: float
    tax_amount: float
    category: str
    items: List[ReceiptItem]
    raw_text: str

# BatchReportSummary - Toplu özet
@dataclass
class BatchReportSummary:
    total_receipts: int
    total_amount: float
    total_tax: float
    category_totals: Dict[str, float]
    processed_files: List[str]
```

### 2. **ImageProcessor** - Görüntü İşleme

```python
processor = ImageProcessor(kernel_size=5, blur_strength=5)

# Tüm adımları sırayla uygula
processed_image = processor.process("receipt.jpg")

# Veya adım adım:
gray = processor.convert_to_grayscale(image)
denoised = processor.remove_noise(gray)
thresholded = processor.apply_threshold(denoised)
```

### 3. **OCREngine** - Metin Çıkarma

```python
ocr = OCREngine(language="tur+eng")

# Metni çıkart
text = ocr.extract_text(processed_image)

# Typo düzelt
corrected = ocr.fix_typos_levenshtein("resiut", ["receipt"])
# Sonuç: "receipt"

# Metindeki tüm sayıları bul
numbers = ocr.extract_numbers(text)
```

### 4. **ReceiptParser** - Veri Ayrıştırma

```python
parser = ReceiptParser()

# Ham metni ayrıştır
receipt = parser.parse(raw_text, filename="receipt.jpg")

# Receipt bilgileri:
print(receipt.merchant_name)    # İşletme adı
print(receipt.date)              # Tarih
print(receipt.total_amount)      # Toplam tutar
print(receipt.category)          # Kategori
```

### 5. **DocxReportGenerator** - Rapor Üretimi

```python
generator = DocxReportGenerator(title="Harcama Raporu")

# Rapor oluştur ve kaydet
generator.generate_report(
    receipts=receipts,
    summary=summary,
    output_path="Harcama_Raporu.docx"
)
```

### 6. **ReceiptPipeline** - Orkestra

```python
pipeline = ReceiptPipeline()

# Klasörü işle
pipeline.process_directory(
    input_dir="data/raw",
    output_docx_path="outputs/Harcama_Raporu.docx"
)

# İstatistikleri al
stats = pipeline.get_processing_stats()
```

---

## 📋 Desteklenen Kategoriler

| Kategori | Anahtar Kelimeler |
|----------|-------------------|
| Market | market, bim, migros, carrefour, gıda |
| Akaryakıt | petrol, benzin, akaryakıt, shell, bp |
| Teknoloji | elektronik, bilgisayar, telefon, tablet |
| Sağlık | eczane, ilaç, doktor, hastane |
| Yemek | restoran, kafe, pizzeria, kebap |
| Ulaşım | taksi, otobüs, tren, uçak |
| Diğer | (varsayılan) |

---

## 🔍 Logging

Uygulamada detaylı logging yapılır:

- **Console Çıktı** - Gerçek zamanlı bilgi
- **Dosya Loglama** - `receipt_processing.log` dosyasına kaydedilir

### Log Seviyeleri

```
INFO   - Genel bilgiler
DEBUG  - Detaylı hata ayıklama bilgileri
WARNING - Uyarılar
ERROR  - Hatalar
```

---

## 🧪 Test & Hata Ayıklama

### Debug Modu

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

pipeline = ReceiptPipeline()
pipeline.process_directory(...)
```

### Tek Fiş İşlemesi (Debug)

```python
from src.pipeline import ReceiptPipeline

pipeline = ReceiptPipeline()
receipt = pipeline.process_single_receipt("test_receipt.jpg")

if receipt:
    print(f"Merchant: {receipt.merchant_name}")
    print(f"Total: ₺ {receipt.total_amount}")
    print(f"Category: {receipt.category}")
    print(f"Items: {len(receipt.items)}")
```

---

## 📝 Örnek Rapor Çıktısı

Oluşturulan Word raporunda:

1. **Başlık Sayfası**
   - Rapor adı ve tarihi

2. **Genel Özet**
   - Toplam fiş sayısı
   - Genel toplam tutar
   - Toplam KDV
   - Ortalama fiş tutarı

3. **Kategori Dağılımı (Tablo)**
   - Kategori adı
   - Her kategorideki toplam tutar
   - Yüzdesel dağılım

4. **Fiş Detayları (Sayfalar)**
   - Her fiş için:
     - İşletme adı ve tarihi
     - Kalem listesi (ürün × fiyat)
     - Toplam tutar ve KDV

---

## ⚙️ Yapılandırma

### ImageProcessor Parametreleri

```python
processor = ImageProcessor(
    kernel_size=5,      # Morfolojik işlem kernel boyutu
    blur_strength=5     # Gürültü engelleme gücü
)
```

### OCREngine Parametreleri

```python
ocr = OCREngine(
    language="tur+eng"  # Tesseract dil kodu
)
```

### Levenshtein Typo Düzeltme

```python
# Maksimum mesafe: 2 (kaç harf farklı olabilir)
fixed = ocr.fix_typos_levenshtein(
    word="resiut",
    dictionary=["receipt", "recent"],
    max_distance=2
)
```

---

## 🐛 Sık Karşılaşılan Sorunlar

### 1. "Tesseract not found" Hatası

**Çözüm:**
```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 2. "No images found" Uyarısı

**Çözüm:** data/raw klasörüne görüntü dosyaları ekleyin

### 3. Düşük OCR Kalitesi

**Çözüm:** İmage Processor parametrelerini ayarlayın veya daha yüksek kaliteli görüntü kullanın

### 4. Word dosyası açılmıyor

**Çözüm:** Çıkış klasörünün yazılabilir olduğundan emin olun

---

## 📊 Performans İpuçları

- Görüntüleri önceden optimize edin (1-3 MB ideal)
- Batch işlemesi için `process_directory()` kullanın
- Büyük miktarda fiş işlemek için logging seviyesini WARNING'e ayarlayın
- GPU hızlandırması için OpenCV-contrib sürümü kullanın

---

## 🤝 Katkılar

Bu proje tamamen fonksiyonel olup, gereksinimlerinize göre özelleştirilebilir.

### Özelleştirme Önerileri

- Farklı kategoriler eklemek: `parser.py` içinde `category_keywords` güncelleyin
- PDF desteği: `DocxReportGenerator`'i genişletin
- Veritabanı entegrasyonu: `Receipt` nesnelerini depolayın

---

## 📄 Lisans

Proje şahsi kullanıma açıktır. Ticari kullanım için lütfen taraf olun.

---

## 📞 İletişim & Destek

Herhangi bir sorun veya öneriniz varsa bildiriniz.

---

**Version:** 1.0.0  
**Güncelleme Tarihi:** 2026-07-22  
**Durum:** ✅ Tam Fonksiyonel

