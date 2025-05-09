from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import csv

# Khởi tạo trình duyệt Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Hàm tạo danh sách ngày từ 6 tháng trước đến hiện tại
def get_date_list(days_back=180):
    today = datetime.now()
    start_date = today - timedelta(days=days_back)
    date_list = [(start_date + timedelta(days=i)).strftime("%d/%m/%Y") 
                 for i in range((today - start_date).days + 1)]
    return date_list

# Hàm lấy giá trị mua hoặc bán từ cột, bỏ qua thẻ có class "up" hoặc "down"
def extract_price(cell):
    spans = cell.find_all('span')
    for span in spans:
        # Nếu thẻ không có class hoặc class không phải là "up" hoặc "down"
        if not span.has_attr('class') or (span['class'][0] not in ['up', 'down']):
            return span.get_text(strip=True).replace(',', '')
    return ""  # Nếu không tìm thấy, trả về chuỗi rỗng

# URL của trang web
url = "https://sjc.com.vn/bieu-do-gia-vang"
driver.get(url)

# Tạo danh sách ngày trong 6 tháng qua
date_list = get_date_list()

# Mở file CSV để ghi dữ liệu
with open('gia_vang_sjc_theo_ngay.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Ghi tiêu đề vào file CSV
    writer.writerow(["Ngày", "#", "Loại (nghìn đồng/ lượng)", "Mua", "Bán"])

    # Duyệt qua danh sách ngày và thu thập dữ liệu
    for date in date_list:
        try:
            # Tìm và điền vào ô ngày
            date_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "datesearch"))
            )
            date_input.clear()
            date_input.send_keys(date)

            # Nhấn nút Tra cứu bằng JavaScript để đảm bảo sự kiện được kích hoạt
            search_button = driver.find_element(By.CLASS_NAME, "button-datesearch")
            driver.execute_script("arguments[0].click();", search_button)

            # Chờ đợi trang cập nhật với dữ liệu mới
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "w-full"))
            )
            time.sleep(2)  # Đợi thêm một chút để dữ liệu ổn định

            # Lấy nội dung trang sau khi đã tải
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Tìm bảng giá vàng
            table = soup.find('table', class_='w-full')

            if table:
                tbody = table.find('tbody')
                # Ghi ngày làm tiêu đề cho nhóm
                writer.writerow([date, "", "", ""])

                # Duyệt qua các dòng trong bảng
                for row in tbody.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        num = cols[0].get_text(strip=True)
                        city_type = cols[1].get_text(strip=True)
                        buy = extract_price(cols[2])  # Lấy giá mua
                        sell = extract_price(cols[3])  # Lấy giá bán

                        # Ghi dữ liệu vào file CSV
                        writer.writerow([date, num, city_type, buy, sell])

                print(f"✅ Dữ liệu ngày {date} thu thập thành công.")
            else:
                print(f"❌ Không tìm thấy bảng giá vàng cho ngày {date}")
        except Exception as e:
            print(f"⚠️ Lỗi khi xử lý ngày {date}: {e}")

# Đóng trình duyệt
driver.quit()
