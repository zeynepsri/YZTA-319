"""
TÜİK "Ana harcama gruplarına göre ağırlıklar, TÜFE ve değişim oranları"
Excel (.xls) dosyasını, backend'in kullanabileceği standart JSON'a çevirir.

Kullanım:
    python tuik_to_json.py girdi.xls cikti.json

Not: Bu script satırları isimden bulur, satır numarasına göre DEĞİL.
Bu yüzden gelecek ayların dosyalarında da çalışır.
"""

import sys
import json
import re
import pandas as pd


# TÜİK'in 13 ana harcama grubunu, projedeki 7 ürün kategorisine bağlayan
# Bir TÜİK grubu birden fazla proje kategorisine bağlanabilir.
TUIK_TO_PROJECT = {
    "Gıda ve alkolsüz içecekler": ["Gıda", "İçecek"],
    "Alkollü içecekler, tütün ve tütün ürünleri": ["İçecek"],
    "Konut, su, elektrik, gaz ve diğer yakıtlar": ["Ev"],
    "Mobilya, mefruşat ve evde kullanılan ekipmanlar ile rutin ev bakım ve onarımı": ["Ev", "Temizlik"],
    "Sağlık": ["Sağlık"],
    "Kişisel bakım, sosyal koruma ve çeşitli mal ve hizmetler": ["Kozmetik", "Bebek"],
}

# Sütun sırası (dosyadaki sırayla):
# 0: grup adı | 1: ağırlık | 2: aylık | 3: yıl başından beri
# 4: yıllık | 5: 12 aylık ort. | 6: endeks
COLS = ["weight", "monthly_change", "change_to_dec",
        "yearly_change", "twelve_month_avg_change", "index"]

# Türkçe ay adı -> ay numarası
AYLAR = {
    "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04",
    "mayıs": "05", "haziran": "06", "temmuz": "07", "ağustos": "08",
    "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12",
}


def turkce_kucuk(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def donemi_bul(df):
    """Başlıktaki 'Haziran 2026' gibi ifadeden '2026-06' üretir."""
    metin = " ".join(str(x) for x in df.iloc[0].tolist() if str(x) != "nan")
    metin_kucuk = turkce_kucuk(metin)
    yil = re.search(r"(20\d{2})", metin)
    yil = yil.group(1) if yil else "0000"
    for ay_adi, ay_no in AYLAR.items():
        if ay_adi in metin_kucuk:
            return f"{yil}-{ay_no}"
    return f"{yil}-00"


def temiz_isim(hucre):
    """Hücredeki Türkçe+İngilizce isimden sadece Türkçe ilk satırı alır."""
    return str(hucre).split("\n")[0].strip()


def sayi(x):
    try:
        deger = float(x)
    except (ValueError, TypeError):
        return None
    if pd.isna(deger):  # boş hücreler NaN olarak gelir, onları eleriz
        return None
    return round(deger, 2)


def donustur(girdi_yolu):
    df = pd.read_excel(girdi_yolu, header=None)
    donem = donemi_bul(df)

    genel = None
    kategoriler = []

    for i in range(len(df)):
        isim = temiz_isim(df.iloc[i, 0])
        degerler = df.iloc[i, 1:7].tolist()

        # Sadece rakam içeren (veri) satırlarını al
        if sum(1 for v in degerler if sayi(v) is not None) < 4:
            continue

        kayit = {"name": isim}
        for kolon, deger in zip(COLS, degerler):
            kayit[kolon] = sayi(deger)

        if isim.upper().startswith("TÜFE") or isim.upper().startswith("CPI"):
            genel = kayit
        else:
            kayit["project_categories"] = TUIK_TO_PROJECT.get(isim, [])
            kategoriler.append(kayit)

    return {
        "period": donem,
        "source": "TUIK",
        "dataset": "Ana harcama gruplarına göre ağırlıklar, TÜFE ve değişim oranları",
        "base_year": "2025=100",
        "general": genel,
        "categories": kategoriler,
    }


if __name__ == "__main__":
    girdi = sys.argv[1] if len(sys.argv) > 1 else "tuik.xls"
    cikti = sys.argv[2] if len(sys.argv) > 2 else "tuik_haziran_2026.json"

    sonuc = donustur(girdi)
    with open(cikti, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)

    print(f"Bitti -> {cikti}")
    print(f"Dönem: {sonuc['period']}")
    print(f"Genel TÜFE yıllık: %{sonuc['general']['yearly_change']}")
    print(f"Kategori sayısı: {len(sonuc['categories'])}")
