from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from prettytable import PrettyTable
import time
import csv

# Khởi tạo trình duyệt Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# URL của trang web
url = "https://sjc.com.vn/bieu-do-gia-vang"
driver.get(url)

# Đợi trang web tải xong
time.sleep(5)

# Lấy nội dung trang sau khi đã tải
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Tìm bảng giá vàng
table = soup.find('table', class_='w-full')

# Kiểm tra nếu bảng tồn tại
if table:
    # Lấy tiêu đề bảng
    headers = [header.get_text(strip=True) for header in table.find_all('th')]

    # Khởi tạo bảng PrettyTable để hiển thị đẹp
    pretty_table = PrettyTable(headers)

    # Mở file CSV để ghi
    with open('gia_vang_sjc.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Ghi tiêu đề vào file

        # Duyệt qua từng hàng trong tbody
        tbody = table.find('tbody')
        for row in tbody.find_all('tr'):
            cols = row.find_all('td')
            # Lấy dữ liệu, làm sạch và chuyển đổi số liệu
            values = []
            for col in cols:
                text = col.get_text(strip=True).replace(',', '')  # Bỏ dấu phẩy
                if '+' in text:
                    text = text.split('+')[0]  # Bỏ dấu cộng và phần sau dấu cộng
                values.append(text)
            
            # Thêm vào bảng PrettyTable và file CSV
            pretty_table.add_row(values)
            writer.writerow(values)

    # In bảng đẹp ra màn hình
    print("\n📊 BẢNG GIÁ VÀNG SJC (Dữ liệu sạch)")
    print(pretty_table)

    print("\n✅ Dữ liệu sạch đã được lưu vào file 'gia_vang_sjc.csv'")
else:
    print("❌ Không tìm thấy bảng giá vàng")

# Đóng trình duyệt
driver.quit()
