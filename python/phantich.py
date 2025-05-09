import pandas as pd

# Đọc file CSV
file_path = r"d:\python\gia_vang_sjc_theo_ngay.csv"
df = pd.read_csv(file_path)

# Loại bỏ các hàng có giá trị NaN trong cột 'Ngày' và 'Thành phố'
df = df.dropna(subset=['Ngày', '#', 'Loại (nghìn đồng/ lượng)', 'Mua', 'Bán'])

# Chuyển đổi cột 'Ngày' sang kiểu datetime
df['Ngày'] = pd.to_datetime(df['Ngày'], format="%d/%m/%Y")

# Thêm cột 'Tháng' để tổng hợp theo tháng
df['Tháng'] = df['Ngày'].dt.to_period('M')

# Nhóm theo 'Tháng' và 'Thành phố', tính trung bình giá Mua và Bán
df['Mua'] = pd.to_numeric(df['Mua'], errors='coerce')
df['Bán'] = pd.to_numeric(df['Bán'], errors='coerce')

# Tính trung bình giá Mua và Bán theo Tháng và Thành phố
summary = df.groupby(['Tháng', 'Loại (nghìn đồng/ lượng)'])[['Mua', 'Bán']].mean().reset_index()
average_per_month = df.groupby('Tháng')[['Mua', 'Bán']].mean().reset_index()
print("✅ Giá trị trung bình vàng theo tháng:")
print(average_per_month)


# Xuất kết quả ra file CSV
summary.to_csv(r"d:\python\trung_binh_gia_vang_theo_thang.csv", index=False, encoding='utf-8-sig')

print("✅ Đã lưu file 'trung_binh_gia_vang_theo_thang.csv'")
print(summary)
