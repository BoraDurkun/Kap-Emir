import time
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import json
from algolab import Backend
from config import *

# Şirket adına göre borsa kodu almak için bir fonksiyon
def get_ticker_from_context(context_value):
    with open('SIRKETLER.json', 'r', encoding='utf-8') as file:
        mapping_list = json.load(file)
    for item in mapping_list:
        for key, value in item.items():
            Ad, Ticker = value.split(';')[0:2]
            if Ad == context_value:
                return Ticker
    return None

# Bağlantının canlı olup olmadığını kontrol etmek için bir fonksiyon
def connection_control():
    try:
        if not Conn.SessionRefresh():
            print("Login Oturumu Sonlandı, Yeni Oturum Açılıyor...")
            Backend(api_key=MY_API_KEY, username=MY_USERNAME, password=MY_PASSWORD, verbose=True)
    except Exception as e:
        print(f" hata oluştu: {e}")

# WebDriver ve diğer başlangıç değişkenlerinin tanımlanması
driver = webdriver.Chrome()
previous_elements = []
symbols = []
sent_orders = []
Conn = Backend(api_key=MY_API_KEY, username=MY_USERNAME, password=MY_PASSWORD, verbose=True)
# connection_control fonksiyonunun her dakika çağrılması için zamanlayıcı
schedule.every(15).minutes.do(connection_control)

if __name__ == "__main__":
    while True:
        # Web sayfasını aç
        driver.get("https://www.kap.org.tr/tr/")
        # Yüklenmeyi beklemek için 3 saniye bekle
        time.sleep(5)
        # Ek olarak 500ms içeriklerin yüklenmesini beklemek
        driver.implicitly_wait(500)
        # Zamanlanmış görevleri çalıştır
        schedule.run_pending()

        # İlgili sütunlardan verileri almak için CSS seçiciler
        time_elements = driver.find_elements(By.CSS_SELECTOR, "div.notifications-column._2")
        Context_elements = driver.find_elements(By.CSS_SELECTOR, "div.notifications-column._4 span.vcell")
        SubContexts = driver.find_elements(By.CSS_SELECTOR, "div.notifications-column._6 span.vcell")
        Contents = driver.find_elements(By.CSS_SELECTOR, "div.notifications-column._7 span.vcell")
        current_elements = []

        # Alınan veriyi mevcut öğeler listesine eklemek
        for Context_element, SubContext, Content, time_element in zip(Context_elements, SubContexts, Contents, time_elements):
            # (Bu kısım alınan veriyi işler ve mevcut öğeler listesine ekler)
            time_text = time_element.text.strip()
            if 'Bugün' in time_text:
                today_date = datetime.today().date()
                time_text = time_text.replace('Bugün', today_date.strftime('%Y-%m-%d'))
            context_text = Context_element.text.strip()
            subcontext_text = SubContext.text.strip()
            content_text = Content.text.strip()
            if context_text and subcontext_text and content_text and time_text:
                current_elements.append({
                    'time': time_text,
                    'context': context_text,
                    'subcontext': subcontext_text,
                    'content': content_text
                })

        # Öğelerin zaman damgasına göre sıralanması
        current_elements.sort(key=lambda x: datetime.strptime(x['time'], '%Y-%m-%d %H:%M'))

        # Mevcut ve önceki öğelerin karşılaştırılması
        if current_elements != previous_elements:
            for item in current_elements:
                # Eğer içerikte "Yeni İş İlişkisi" kelimesi bulunuyorsa
                if "Yeni İş İlişkisi" in item['subcontext']:
                    # İlgili şirketin borsa kodunu al
                    symbol = get_ticker_from_context(item['context'])
                    # Eğer borsa kodu varsa ve daha önce eklenmemişse
                    if symbol and symbol not in symbols:
                        # Sembolleri tutan listeye ekleyin
                        symbols.append(symbol)
                        print(f"Sembol ekleniyor: {symbol}")
                        print(symbols)
                        # Eğer bu sembol için daha önce bir emir gönderilmemişse
                        if symbol not in sent_orders:
                            # Emri ilet
                            Conn.SendOrder(symbol=symbol, direction="BUY", pricetype="Piyasa", lot="1",price="",sms=True,email=False,subAccount="")
                            print(str(symbol) + " sembolüne emir iletildi.")
            previous_elements = current_elements.copy()