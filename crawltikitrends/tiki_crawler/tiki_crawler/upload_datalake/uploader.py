import os
from google.cloud import storage
from datetime import datetime

def upload_to_gcs(): # Google Cloud Storage
    # Đường dẫn tuyệt đối tới file key
    key_path = os.path.join(os.path.dirname(__file__),"gcp-26cb0bb02da0.json")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

    # Tạo client
    client = storage.Client()
    bucket_name = "my-datalake"
    bucket = client.bucket(bucket_name)

    # Đường dẫn local tới file
    file_path = os.path.join(os.path.dirname(__file__),  "..","data", "datatrends.json")
    if not os.path.exists(file_path):
        print(" Không tìm thấy file:", file_path)
        return

    # Đặt tên file trên cloud (có thêm timestamp để không bị ghi đè)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destination_blob_name = f"datatrends/datatrends_{now}.json"

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)

    print(f" Đã upload: {file_path} → gs://{bucket_name}/{destination_blob_name}")
