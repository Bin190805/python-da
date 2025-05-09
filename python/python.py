import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import os

def setup_driver():
    """Thiết lập driver cho Selenium"""
    chrome_options = Options()
    # Uncomment dòng dưới nếu muốn chạy ở chế độ headless
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def clean_price(price_text):
    """Làm sạch dữ liệu giá, loại bỏ ký tự đặc biệt và chuyển về số"""
    if not price_text:
        return ""
    # Loại bỏ các ký tự không phải số hoặc dấu chấm/phẩy
    cleaned = re.sub(r'[^\d.,]', '', price_text)
    return cleaned

def extract_date_from_text(text):
    """Trích xuất ngày từ chuỗi văn bản"""
    # Mẫu cho các định dạng ngày phổ biến: dd/mm/yyyy, dd-mm-yyyy, v.v.
    patterns = [
        r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})',  # dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
        r'(\d{1,2})/(\d{1,2})'  # dd/mm (năm hiện tại)
    ]
    
    for pattern in patterns:
        matches = re.search(pattern, text)
        if matches:
            groups = matches.groups()
            if len(groups) == 3:  # dd/mm/yyyy
                day, month, year = groups
                return f"{day}/{month}/{year}"
            elif len(groups) == 2:  # dd/mm
                day, month = groups
                year = datetime.now().year
                return f"{day}/{month}/{year}"
    
    # Nếu không tìm thấy định dạng nào, trả về ngày hiện tại
    return datetime.now().strftime("%d/%m/%Y")

def get_chart_data(driver):
    """Cố gắng lấy dữ liệu từ biểu đồ nếu có"""
    chart_data = []
    try:
        # Chờ biểu đồ tải
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".highcharts-root"))
        )
        
        print("Đang cố gắng lấy dữ liệu từ biểu đồ 30 ngày...")
        
        # Tìm phần tử canvas của biểu đồ
        chart_element = driver.find_element(By.CSS_SELECTOR, ".highcharts-root")
        
        # Lấy dữ liệu từ thuộc tính data của biểu đồ (nếu có)
        # Đây chỉ là một ví dụ, tùy thuộc vào cách triển khai biểu đồ
        chart_data_script = driver.execute_script("""
            // Tìm biến chứa dữ liệu biểu đồ
            if (window.Highcharts && window.Highcharts.charts) {
                for (let i = 0; i < window.Highcharts.charts.length; i++) {
                    let chart = window.Highcharts.charts[i];
                    if (chart && chart.series && chart.series.length > 0) {
                        return chart.series.map(s => ({
                            name: s.name,
                            data: s.points.map(p => ({
                                x: p.x,
                                y: p.y,
                                date: new Date(p.x).toLocaleDateString('vi-VN'),
                                value: p.y
                            }))
                        }));
                    }
                }
            }
            return null;
        """)
        
        if chart_data_script:
            print("Đã tìm thấy dữ liệu biểu đồ qua JavaScript")
            for series in chart_data_script:
                series_name = series.get('name', 'Unknown')
                for point in series.get('data', []):
                    chart_data.append({
                        'Ngày': point.get('date'),
                        'Loại vàng': 'SJC', # Giả định là SJC, có thể thay đổi tùy theo trang
                        'Chỉ số': series_name,
                        'Giá trị': point.get('value')
                    })
    except Exception as e:
        print(f"Không thể lấy dữ liệu từ biểu đồ: {e}")
    
    return chart_data

def crawl_gold_price_current(driver):
    """Crawl dữ liệu giá vàng của ngày hiện tại và hôm qua"""
    gold_data = []
    
    try:
        print("Đang lấy dữ liệu giá vàng hiện tại...")
        
        # Tìm thông tin cập nhật thời gian
        update_info_elements = driver.find_elements(By.XPATH, "//div[contains(text(), 'Cập nhật lúc')]")
        update_info = update_info_elements[0].text if update_info_elements else "Không có thông tin cập nhật"
        print(f"Thông tin cập nhật: {update_info}")
        
        # Trích xuất ngày từ thông tin cập nhật
        current_date = extract_date_from_text(update_info)
        
        # Tìm tất cả các bảng giá vàng
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        for table_idx, table in enumerate(tables):
            try:
                # Lấy header của bảng để xác định loại bảng
                headers = table.find_elements(By.TAG_NAME, "th")
                header_texts = [h.text.strip() for h in headers if h.text.strip()]
                
                if not header_texts:
                    continue
                
                print(f"Đang xử lý bảng {table_idx + 1} với các cột: {header_texts}")
                
                # Xác định cấu trúc của bảng
                has_buy_sell = any("mua" in h.lower() for h in header_texts) and any("bán" in h.lower() for h in header_texts)
                is_today_yesterday = any("hôm nay" in h.lower() for h in header_texts) and any("hôm qua" in h.lower() for h in header_texts)
                
                # Lấy tất cả các dòng trong bảng (bỏ qua hàng tiêu đề)
                rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 2:
                        continue
                    
                    # Trích xuất dữ liệu từ dòng
                    row_data = [cell.text.strip() for cell in cells]
                    
                    if is_today_yesterday and has_buy_sell:
                        # Bảng có cả hôm nay/hôm qua và giá mua/bán
                        if len(row_data) >= 5:
                            gold_type = row_data[0]
                            
                            # Hôm nay
                            today_buy = clean_price(row_data[1])
                            today_sell = clean_price(row_data[2])
                            
                            # Hôm qua
                            yesterday_buy = clean_price(row_data[3])
                            yesterday_sell = clean_price(row_data[4])
                            
                            # Ngày hôm nay
                            gold_data.append({
                                "Ngày": current_date,
                                "Loại vàng": gold_type,
                                "Giá mua": today_buy,
                                "Giá bán": today_sell
                            })
                            
                            # Ngày hôm qua
                            yesterday_date = (datetime.strptime(current_date, "%d/%m/%Y") - timedelta(days=1)).strftime("%d/%m/%Y")
                            gold_data.append({
                                "Ngày": yesterday_date,
                                "Loại vàng": gold_type,
                                "Giá mua": yesterday_buy,
                                "Giá bán": yesterday_sell
                            })
                    
                    elif has_buy_sell:
                        # Bảng chỉ có giá mua/bán
                        if len(row_data) >= 3:
                            gold_type = row_data[0]
                            buy_price = clean_price(row_data[1])
                            sell_price = clean_price(row_data[2])
                            
                            gold_data.append({
                                "Ngày": current_date,
                                "Loại vàng": gold_type,
                                "Giá mua": buy_price,
                                "Giá bán": sell_price
                            })
                    else:
                        # Trường hợp khác - có thể là bảng tỷ giá hoặc cấu trúc khác
                        print(f"Bỏ qua dòng có dữ liệu không phù hợp: {row_data}")
            
            except Exception as e:
                print(f"Lỗi khi xử lý bảng {table_idx + 1}: {e}")
        
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu hiện tại: {e}")
    
    return gold_data

def crawl_historical_data(driver):
    """Cố gắng crawl dữ liệu lịch sử 30 ngày bằng cách duyệt các trang lịch sử nếu có"""
    historical_data = []
    
    try:
        # Kiểm tra xem có liên kết đến trang lịch sử không
        history_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'lịch sử') or contains(text(), 'Lịch sử')]")
        
        if history_links:
            print("Tìm thấy liên kết đến trang lịch sử giá vàng")
            
            # Click vào liên kết lịch sử
            driver.execute_script("arguments[0].click();", history_links[0])
            time.sleep(3)
            
            # Chờ trang lịch sử tải
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Lấy dữ liệu từ bảng lịch sử
            tables = driver.find_elements(By.TAG_NAME, "table")
            
            for table_idx, table in enumerate(tables):
                try:
                    # Lấy header của bảng để xác định loại bảng
                    headers = table.find_elements(By.TAG_NAME, "th")
                    header_texts = [h.text.strip() for h in headers if h.text.strip()]
                    
                    if not header_texts or len(header_texts) < 3:
                        continue
                    
                    print(f"Đang xử lý bảng lịch sử {table_idx + 1} với các cột: {header_texts}")
                    
                    # Xác định vị trí cột ngày, giá mua, giá bán
                    date_col = -1
                    buy_col = -1
                    sell_col = -1
                    
                    for i, header in enumerate(header_texts):
                        header_lower = header.lower()
                        if "ngày" in header_lower or "thời gian" in header_lower:
                            date_col = i
                        elif "mua" in header_lower:
                            buy_col = i
                        elif "bán" in header_lower:
                            sell_col = i
                    
                    if date_col == -1 or (buy_col == -1 and sell_col == -1):
                        print("Không thể xác định cấu trúc bảng lịch sử")
                        continue
                    
                    # Lấy tất cả các dòng trong bảng (bỏ qua hàng tiêu đề)
                    rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                    
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) <= max(date_col, buy_col, sell_col):
                            continue
                        
                        # Trích xuất dữ liệu từ dòng
                        row_data = [cell.text.strip() for cell in cells]
                        
                        date_value = row_data[date_col]
                        formatted_date = extract_date_from_text(date_value)
                        
                        # Xác định loại vàng từ tiêu đề bảng hoặc các cột trong bảng
                        gold_type = "SJC"  # Mặc định
                        for header in header_texts:
                            if "SJC" in header:
                                gold_type = "SJC"
                                break
                            elif "9999" in header or "24K" in header:
                                gold_type = "Vàng 9999"
                                break
                        
                        # Lấy giá mua/bán nếu có
                        buy_price = clean_price(row_data[buy_col]) if buy_col != -1 and buy_col < len(row_data) else ""
                        sell_price = clean_price(row_data[sell_col]) if sell_col != -1 and sell_col < len(row_data) else ""
                        
                        historical_data.append({
                            "Ngày": formatted_date,
                            "Loại vàng": gold_type,
                            "Giá mua": buy_price,
                            "Giá bán": sell_price
                        })
                
                except Exception as e:
                    print(f"Lỗi khi xử lý bảng lịch sử {table_idx + 1}: {e}")
        else:
            print("Không tìm thấy liên kết đến trang lịch sử giá vàng")
    
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu lịch sử: {e}")
    
    return historical_data

def crawl_gold_price(url):
    """Crawl dữ liệu giá vàng trong 30 ngày từ trang 24h.com.vn"""
    driver = setup_driver()
    all_data = []
    
    try:
        driver.get(url)
        print(f"Đã mở trang: {url}")
        
        # Chờ cho trang web load hoàn tất
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        print("Trang web đã load xong, bắt đầu thu thập dữ liệu...")
        
        # 1. Lấy dữ liệu hiện tại (hôm nay và hôm qua)
        current_data = crawl_gold_price_current(driver)
        all_data.extend(current_data)
        
        # 2. Thử lấy dữ liệu từ biểu đồ
        chart_data = get_chart_data(driver)
        if chart_data:
            all_data.extend(chart_data)
        
        # 3. Thử lấy dữ liệu lịch sử 30 ngày
        historical_data = crawl_historical_data(driver)
        all_data.extend(historical_data)
        
        print(f"Tổng số dữ liệu thu thập được: {len(all_data)}")
        
    except Exception as e:
        print(f"Lỗi khi crawl dữ liệu: {e}")
    finally:
        driver.quit()
    
    # Lọc dữ liệu trùng lặp
    df = pd.DataFrame(all_data)
    if not df.empty:
        # Loại bỏ các dòng trùng lặp
        df = df.drop_duplicates()
        
        # Sắp xếp theo ngày
        try:
            df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y')
            df = df.sort_values('Ngày', ascending=False)
            # Chuyển lại định dạng ngày
            df['Ngày'] = df['Ngày'].dt.strftime('%d/%m/%Y')
        except:
            print("Không thể sắp xếp theo ngày, có thể có lỗi định dạng")
        
        # Lọc chỉ giữ lại dữ liệu trong 30 ngày gần nhất
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        try:
            df['NgàyDT'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y')
            df = df[df['NgàyDT'] >= thirty_days_ago]
            df = df.drop('NgàyDT', axis=1)
        except:
            print("Không thể lọc theo 30 ngày gần nhất, có thể có lỗi định dạng")
    
    return df

def main():
    # URL của trang web giá vàng 24h
    url = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"
    
    print("Bắt đầu crawl dữ liệu giá vàng...")
    df = crawl_gold_price(url)
    
    if df is not None and not df.empty:
        # Tạo thư mục để lưu kết quả nếu chưa tồn tại
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Lưu dữ liệu vào file CSV
        csv_filename = f"data/gia_vang_30_ngay_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"Đã lưu dữ liệu vào file {csv_filename}")
        
        # Hiển thị thống kê
        print("\nThống kê dữ liệu:")
        print(f"Tổng số bản ghi: {len(df)}")
        print(f"Số ngày thu thập được: {df['Ngày'].nunique()}")
        print(f"Các loại vàng thu thập được: {df['Loại vàng'].unique()}")
        
        # Hiển thị mẫu dữ liệu
        print("\nMẫu dữ liệu:")
        print(df.head())
    else:
        print("Không có dữ liệu nào được thu thập")
    
    print("Hoàn thành crawl dữ liệu giá vàng!")

if __name__ == "__main__":
    main()