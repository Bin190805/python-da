import pandas as pd
import matplotlib.pyplot as plt

# Đọc file CSV
file_path = r"d:\python\gia_vang_sjc_theo_ngay.csv"
df = pd.read_csv(file_path)

# Loại bỏ các hàng có giá trị NaN trong cột 'Ngày', 'Loại (nghìn đồng/ lượng)', 'Mua', 'Bán'
df = df.dropna(subset=['Ngày', '#', 'Loại (nghìn đồng/ lượng)', 'Mua', 'Bán'])

# Chuyển đổi cột 'Ngày' sang kiểu datetime
df['Ngày'] = pd.to_datetime(df['Ngày'], format="%d/%m/%Y")

# Thêm cột 'Tháng' để tổng hợp theo tháng
df['Tháng'] = df['Ngày'].dt.to_period('M')

# Chuyển đổi cột 'Mua' và 'Bán' thành kiểu số
df['Mua'] = pd.to_numeric(df['Mua'], errors='coerce')
df['Bán'] = pd.to_numeric(df['Bán'], errors='coerce')

# Tính trung bình giá Mua và Bán theo từng tháng (làm tròn 2 chữ số thập phân)
average_per_month = df.groupby('Tháng')[['Mua', 'Bán']].mean().round(2).reset_index()

# Tính độ lệch chuẩn (biến động) của giá Mua và Bán theo từng tháng (làm tròn 2 chữ số thập phân)
std_per_month = df.groupby('Tháng')[['Mua', 'Bán']].std().round(2).reset_index()

# Tính tỷ lệ chênh lệch giữa giá Mua và Bán theo tháng (làm tròn 2 chữ số thập phân)
df['Chênh lệch'] = df['Bán'] - df['Mua']
avg_diff_per_month = df.groupby('Tháng')['Chênh lệch'].mean().round(2).reset_index()

# Tính các tháng có sự biến động cao nhất và thấp nhất
max_variation_month = std_per_month.loc[std_per_month['Mua'].idxmax()]
min_variation_month = std_per_month.loc[std_per_month['Mua'].idxmin()]

# In kết quả trung bình giá vàng theo tháng
print("✅ Giá trị trung bình vàng theo tháng:")
print(average_per_month)

# In kết quả sự biến động giá vàng theo tháng (Độ lệch chuẩn)
print("✅ Sự biến động giá vàng theo tháng:")
print(std_per_month)

# In kết quả tỷ lệ chênh lệch giữa Mua và Bán theo tháng
print("✅ Tỷ lệ chênh lệch giữa giá Mua và Bán theo tháng:")
print(avg_diff_per_month)

# In kết quả tháng có sự biến động cao nhất và thấp nhất
print(f"✅ Tháng biến động cao nhất: {max_variation_month['Tháng']} - Mua: {max_variation_month['Mua']} Bán: {max_variation_month['Bán']}")
print(f"✅ Tháng biến động thấp nhất: {min_variation_month['Tháng']} - Mua: {min_variation_month['Mua']} Bán: {min_variation_month['Bán']}")

# Lưu các kết quả vào các file CSV riêng biệt
average_per_month.to_csv(r"d:\python\trung_binh_gia_vang_theo_thang.csv", index=False, encoding='utf-8-sig')
std_per_month.to_csv(r"d:\python\bien_dong_gia_vang_theo_thang.csv", index=False, encoding='utf-8-sig')
avg_diff_per_month.to_csv(r"d:\python\chenh_lech_gia_vang_theo_thang.csv", index=False, encoding='utf-8-sig')

# Vẽ đồ thị xu hướng giá vàng (Mua và Bán) và sự biến động (Độ lệch chuẩn)
plt.figure(figsize=(10, 8))

# Đồ thị xu hướng giá vàng theo tháng
plt.subplot(3, 1, 1)
plt.plot(average_per_month['Tháng'].astype(str), average_per_month['Mua'], label='Mua', color='blue')
plt.plot(average_per_month['Tháng'].astype(str), average_per_month['Bán'], label='Bán', color='orange')
plt.title('Xu hướng giá vàng theo tháng')
plt.xlabel('Tháng')
plt.ylabel('Giá (nghìn đồng/lượng)')
plt.legend()

# Đồ thị sự biến động giá vàng (Độ lệch chuẩn)
plt.subplot(3, 1, 2)
plt.plot(std_per_month['Tháng'].astype(str), std_per_month['Mua'], label='Biến động Mua', color='blue', linestyle='--')
plt.plot(std_per_month['Tháng'].astype(str), std_per_month['Bán'], label='Biến động Bán', color='orange', linestyle='--')
plt.title('Sự biến động giá vàng theo tháng')
plt.xlabel('Tháng')
plt.ylabel('Độ lệch chuẩn')
plt.legend()

# Đồ thị tỷ lệ chênh lệch giữa giá Mua và Bán
plt.subplot(3, 1, 3)
plt.plot(avg_diff_per_month['Tháng'].astype(str), avg_diff_per_month['Chênh lệch'], label='Chênh lệch', color='green')
plt.title('Tỷ lệ chênh lệch giữa giá Mua và Bán theo tháng')
plt.xlabel('Tháng')
plt.ylabel('Chênh lệch (nghìn đồng/lượng)')
plt.legend()
plt.tight_layout()
plt.show()

# Lưu tháng biến động cao nhất và thấp nhất
with open(r"d:\python\thang_bien_dong.txt", "w", encoding='utf-8-sig') as f:
    f.write(f"Tháng biến động cao nhất: {max_variation_month['Tháng']} - Mua: {max_variation_month['Mua']} Bán: {max_variation_month['Bán']}\n")
    f.write(f"Tháng biến động thấp nhất: {min_variation_month['Tháng']} - Mua: {min_variation_month['Mua']} Bán: {min_variation_month['Bán']}\n")

print("✅ Đã lưu tất cả các file phân tích vào thư mục 'd:\\python'")
