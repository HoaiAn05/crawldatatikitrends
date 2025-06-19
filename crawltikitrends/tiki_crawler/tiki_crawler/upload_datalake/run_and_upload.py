import subprocess
from uploader import upload_to_gcs

if __name__ == "__main__":
    print("=== BẮT ĐẦU CRAWL ===")
    subprocess.run([
        "scrapy", "crawl", "tiki_trends",
        "-o", "tiki_crawler/data/datatrends.json",
        "-t", "json"
    ])
    print("=== CRAWL XONG. BẮT ĐẦU UPLOAD ===")
    upload_to_gcs()
    print("=== HOÀN TẤT ===")
