Dự án này sử dụng `Scrapy` để crawl thông tin sản phẩm điện thoại trên [Tiki.vn](https://tiki.vn/dien-thoai-may-tinh-bang/c1789), bao gồm:  
- Id,Tên sản phẩm, thương hiệu,thông số sản phẩm, url ảnh, giá, số lượng bán,số lượng đánh giá, đánh giá trung bình, và tất cả comment.  
- Sau đó kết hợp với Google Trends để đo lường độ phổ biến từ khóa tương ứng trong vòng 1 tháng gần nhất.
-Upload lên GCP
- Chạy tự động 1 tuần 1 lần , tự động upload lên GCP
- 
- Công nghệ sử dụng
- Python 3.10+
- Scrapy
- PyTrends
- Proxy (Webshare)
- JSON

Cách chạy

### 1. Cài đặt môi trường
```bash
pip install -r requirements.txt
#Chạy
scrapy crawl tiki_trends



3. Hướng dẫn truy cập dữ liệu
Sau khi đã cấp quyền:

✳️ Nếu team dùng Python:

from google.cloud import storage

client = storage.Client()
bucket = client.get_bucket("my-datalake")
blobs = bucket.list_blobs(prefix="datatrends/")
for blob in blobs:
    print(blob.name)
 Lưu ý: Team cần:

Cài google-cloud-storage

Dùng Google login hoặc key service account (nếu script chạy tự động)