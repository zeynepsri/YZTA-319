"""
TÜİK VERİ BORU HATTI (pipeline)
================================
Tek komutla, TÜİK'ten indirdiğin Excel'i alıp HEM temiz JSON HEM de
veritabanına yazılacak migration (.sql) dosyasını üretir.

KULLANIM:
    python tuik_to_json.py <excel_dosyasi>

ÖRNEK:
    python tuik_to_json.py "Ana harcama gruplarina gore agirliklar.xls"

ÇIKTILAR:
    - tuik_<yil>_<ay>.json                          (temiz veri)
    - migrations/V<n>__real_tuik_data_<yil>_<ay>.sql (veritabanı için)
      (migrations klasörü yoksa dosya bulunduğun klasöre yazılır)

HER AY NE YAPACAKSIN:
    1. TÜİK'ten yeni ayın Excel'ini indir
    2. Bu komutu çalıştır
    3. Oluşan .sql dosyasını GitHub Desktop'tan commit + push et
"""

import sys
import os
import re
import glob
import json
import pandas as pd


# ============================================================
#  KATEGORİ EŞLEŞTİRME  (gerekirse burayı değiştir)
#  Sol: projenin kategorisi (id, ad)  ->  Sağ: hangi TÜİK grubundan oran alınacağı
#  NOT: İçecek ve Bebek TÜİK'te ayrı grup değil; ekiple netleştirilecek.
# ============================================================
KATEGORI_ESLESTIRME = [
    (1, "Gıda",     "Gıda ve alkolsüz içecekler"),
    (2, "Temizlik", "Mobilya, mefruşat ve evde kullanılan ekipmanlar ile rutin ev bakım ve onarımı"),
    (3, "Kozmetik", "Kişisel bakım, sosyal koruma ve çeşitli mal ve hizmetler"),
    (4, "İçecek",   "Gıda ve alkolsüz içecekler"),
    (5, "Sağlık",   "Sağlık"),
    (6, "Ev",       "Konut, su, elektrik, gaz ve diğer yakıtlar"),
    (7, "Bebek",    "Kişisel bakım, sosyal koruma ve çeşitli mal ve hizmetler"),
]

# Excel'deki sütun sırası
COLS = ["weight", "monthly_change", "change_to_dec",
        "yearly_change", "twelve_month_avg_change", "index"]

AYLAR = {
    "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04",
    "mayıs": "05", "haziran": "06", "temmuz": "07", "ağustos": "08",
    "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12",
}


def turkce_kucuk(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def sayi(x):
    try:
        deger = float(x)
    except (ValueError, TypeError):
        return None
    if pd.isna(deger):
        return None
    return round(deger, 2)


def donemi_bul(df):
    """Başlıktaki 'Haziran 2026' -> '2026-06'."""
    metin = " ".join(str(x) for x in df.iloc[0].tolist() if str(x) != "nan")
    metin_kucuk = turkce_kucuk(metin)
    yil = re.search(r"(20\d{2})", metin)
    yil = yil.group(1) if yil else "0000"
    for ay_adi, ay_no in AYLAR.items():
        if ay_adi in metin_kucuk:
            return f"{yil}-{ay_no}"
    return f"{yil}-00"


def temiz_isim(hucre):
    return str(hucre).split("\n")[0].strip()


def excel_oku(girdi_yolu):
    """Excel'i okuyup {donem, general, categories} sözlüğü döndürür."""
    df = pd.read_excel(girdi_yolu, header=None)
    donem = donemi_bul(df)
    genel = None
    kategoriler = []

    for i in range(len(df)):
        isim = temiz_isim(df.iloc[i, 0])
        degerler = df.iloc[i, 1:7].tolist()
        if sum(1 for v in degerler if sayi(v) is not None) < 4:
            continue
        kayit = {"name": isim}
        for kolon, deger in zip(COLS, degerler):
            kayit[kolon] = sayi(deger)
        if isim.upper().startswith("TÜFE") or isim.upper().startswith("CPI"):
            genel = kayit
        else:
            kategoriler.append(kayit)

    return {
        "period": donem,
        "source": "TUIK",
        "dataset": "Ana harcama gruplarına göre ağırlıklar, TÜFE ve değişim oranları",
        "base_year": "2025=100",
        "general": genel,
        "categories": kategoriler,
    }


def json_yaz(veri, klasor):
    yol = os.path.join(klasor, f"tuik_{veri['period'].replace('-', '_')}.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    return yol


def sonraki_versiyon(migrations_klasor):
    """migrations klasöründeki en büyük V numarasını bulup +1 verir."""
    en_buyuk = 0
    for dosya in glob.glob(os.path.join(migrations_klasor, "V*__*.sql")):
        m = re.search(r"V(\d+)__", os.path.basename(dosya))
        if m:
            en_buyuk = max(en_buyuk, int(m.group(1)))
    return en_buyuk + 1


def sql_yaz(veri, migrations_klasor, versiyon):
    """official_inflation tablosu için migration üretir."""
    oran = {c["name"]: c["yearly_change"] for c in veri["categories"]}
    ay = veri["period"] + "-01"

    satirlar = []
    eksik = []
    for cid, proj_ad, tuik_ad in KATEGORI_ESLESTIRME:
        if tuik_ad not in oran or oran[tuik_ad] is None:
            eksik.append(f"{proj_ad} (TÜİK: {tuik_ad})")
            continue
        satirlar.append((cid, proj_ad, tuik_ad, oran[tuik_ad]))

    if eksik:
        print("  UYARI - eşleştirilemeyen kategori(ler):", ", ".join(eksik))

    # VALUES satırları (sonuncusunda virgül yok)
    values = []
    for idx, (cid, proj_ad, tuik_ad, r) in enumerate(satirlar):
        virgul = "," if idx < len(satirlar) - 1 else ""
        values.append(f"    ('{ay}', {cid}, {r:.3f}, 'TUIK'){virgul}  -- {proj_ad}  <- TÜİK: {tuik_ad}")

    sql = f"""-- V{versiyon}__real_tuik_data_{veri['period'].replace('-', '_')}.sql
-- Gerçek TÜİK enflasyon verisi ({veri['period']})
-- Kaynak: TÜİK, Tüketici Fiyat Endeksi
--         "Ana harcama gruplarına göre ağırlıklar, TÜFE ve değişim oranları"
-- Oranlar: bir önceki yılın aynı ayına göre (yıllık) değişim (%)
--
-- category_id 1-7 = projenin kendi kategorileri (TÜİK'in 13 grubu değil).
-- İçecek ve Bebek eşleştirmesi TASLAK; ekiple netleştirilecek.
-- Bu dosya otomatik üretildi: tuik_to_json.py

INSERT INTO official_inflation (month, category_id, rate, source) VALUES
{chr(10).join(values)}
ON CONFLICT (month, category_id) DO UPDATE
    SET rate = EXCLUDED.rate,
        source = EXCLUDED.source;
"""

    ad = f"V{versiyon}__real_tuik_data_{veri['period'].replace('-', '_')}.sql"
    yol = os.path.join(migrations_klasor, ad)
    with open(yol, "w", encoding="utf-8") as f:
        f.write(sql)
    return yol


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python tuik_to_json.py <excel_dosyasi>")
        sys.exit(1)

    girdi = sys.argv[1]
    if not os.path.exists(girdi):
        print(f"HATA: dosya bulunamadı -> {girdi}")
        sys.exit(1)

    # migrations klasörü varsa oraya, yoksa bulunduğumuz klasöre yaz
    migrations_klasor = "migrations" if os.path.isdir("migrations") else "."

    print("Excel okunuyor...")
    veri = excel_oku(girdi)
    print(f"  Dönem: {veri['period']}")
    print(f"  Genel TÜFE yıllık: %{veri['general']['yearly_change']}")
    print(f"  Bulunan TÜİK grubu: {len(veri['categories'])}")

    json_yolu = json_yaz(veri, ".")
    print(f"JSON yazıldı  -> {json_yolu}")

    versiyon = sonraki_versiyon(migrations_klasor)
    sql_yolu = sql_yaz(veri, migrations_klasor, versiyon)
    print(f"SQL yazıldı   -> {sql_yolu}  (migration V{versiyon})")

    print("\nBitti! Simdi olusan .sql dosyasini GitHub Desktop'tan commit + push et.")


if __name__ == "__main__":
    main()
