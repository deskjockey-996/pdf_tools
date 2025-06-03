import os
import requests

def download_file(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}")

# 创建 webfonts 目录
os.makedirs('static/webfonts', exist_ok=True)

# Font Awesome 字体文件
font_files = {
    'fa-solid-900.woff2': 'https://use.fontawesome.com/releases/v5.15.4/webfonts/fa-solid-900.woff2',
    'fa-regular-400.woff2': 'https://use.fontawesome.com/releases/v5.15.4/webfonts/fa-regular-400.woff2',
    'fa-brands-400.woff2': 'https://use.fontawesome.com/releases/v5.15.4/webfonts/fa-brands-400.woff2'
}

# 下载字体文件
for filename, url in font_files.items():
    filepath = os.path.join('static/webfonts', filename)
    download_file(url, filepath) 