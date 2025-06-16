# PDF工具大全

本项目为一站式PDF处理工具，支持多种常用PDF操作，界面简洁，操作便捷。

## 主要功能

1. **PDF旋转工具**
   - 支持对PDF文件的单页或多页进行任意角度旋转。
   - 可批量旋转，支持预览和保存。

2. **图片转PDF工具**
   - 支持多张图片（JPG/PNG等）一键合成为PDF文件。
   - 可自定义图片顺序，支持预览和下载。

3. **PDF转图片工具**
   - 将PDF文件的每一页导出为高质量图片（JPG/PNG）。
   - 支持批量下载所有图片。

4. **PDF水印工具**
   - 可为PDF文件添加文字水印。
   - 支持自定义水印内容、字体、颜色、透明度、位置和旋转角度。

5. **PDF合并工具**
   - 支持多PDF文件合并，页面可自定义顺序。
   - 支持页面删除、旋转、拖拽排序，合并后可直接预览和下载。

---

## 使用方法

1. 克隆本项目到本地：
   ```bash
   git clone <your-repo-url>
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动服务：
   ```bash
   python app.py
   ```
4. 浏览器访问 `http://localhost:8000`，即可使用全部功能。

---

## 反馈与建议

如有问题或建议，欢迎提issue或联系作者。

## 🌟 功能特点

### 已实现功能

1. **PDF旋转工具**
2. **图片转PDF工具**
3. **PDF转图片工具**
4. **PDF水印工具**
5. **PDF合并工具**

### 即将推出功能
- PDF压缩工具
- PDF拆分工具


## 🚀 快速开始

### 环境要求
- Python 3.7+
- Flask
- PyPDF2
- 现代浏览器（Chrome、Firefox、Edge等）

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/deskjockey-996/pdf_tools.git
cd pdf_tools
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行应用
```bash
python app.py
```

4. 在浏览器中访问
```
http://localhost:8000
```

## 💻 使用说明

### PDF旋转工具
1. 点击首页的"PDF旋转工具"卡片
2. 上传PDF文件
3. 在左侧面板选择需要旋转的页面
4. 在右侧面板选择旋转角度
5. 点击"旋转选中页面"按钮
6. 操作完成后点击"保存更改"下载处理后的文件

## 🛠️ 技术栈

- **后端**
  - Flask：Web框架
  - PyPDF2：PDF处理
  - Python 3.7+

- **前端**
  - Bootstrap 5：UI框架
  - PDF.js：PDF预览
  - SortableJS：拖拽排序
  - Font Awesome：图标

## 📁 项目结构

```
.
├── app.py                  # 主程序入口
├── requirements.txt        # Python依赖
├── README.md               # 项目说明文档
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
├── download_fonts.py       # 字体下载脚本
├── static/                 # 静态资源（CSS/JS/字体/图片等）
│   ├── css/
│   ├── js/
│   ├── fonts/
│   ├── webfonts/
│   └── ico.jpeg
├── templates/              # 前端页面模板
│   ├── index.html
│   ├── pdf_merge.html
│   ├── pdf_watermark.html
│   ├── pdf2image.html
│   ├── image2pdf.html
│   ├── rotate.html
│   └── footer.html
├── routes/                 # 各功能模块后端路由
│   ├── __init__.py
│   ├── pdf_merge.py
│   ├── pdf_watermark.py
│   ├── pdf2image.py
│   ├── image2pdf.py
│   ├── rotate.py
│   └── pdf_rotate.py
├── uploads/                # 上传及临时文件目录
└── .gitignore
```

- `app.py`：主入口，注册各功能路由。
- `routes/`：每个PDF工具的后端逻辑。
- `templates/`：每个工具对应的前端页面。
- `static/`：静态资源（样式、脚本、字体等）。
- `uploads/`：用户上传和处理过程中的临时文件。
- 其它为依赖、配置及说明文件。

## 🔒 安全说明

- 所有上传的文件都使用UUID重命名
- 处理完成后自动删除原文件
- 支持的文件类型限制为PDF
- 建议文件大小不超过100MB

## 🤝 参与贡献

欢迎提交Issue和Pull Request！在提交PR之前，请确保：

1. 代码符合项目规范
2. 添加了必要的测试
3. 更新了相关文档

## 📝 开发计划

- [ ] PDF合并功能
- [ ] PDF压缩功能
- [ ] PDF拆分功能
- [ ] PDF转图片功能
- [ ] PDF水印功能
- [ ] 批量处理功能


## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系我们：
- 提交 Issue
- 发送邮件至：[您的邮箱]
- 微信：[您的微信号]

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

---

*注：本项目仍在积极开发中，欢迎提供建议和反馈。* 



# PDF 工具应用

## 系统要求
- Docker 20.10+
- Docker Compose 1.29+

## 快速启动
```bash
# 下载 docker-compose 配置文件
curl -O https://raw.githubusercontent.com/deskjockey-996/pdf_tools/main/docker-compose.yml

# 启动应用
docker-compose up -d

# 停止应用
docker-compose down
```

## 访问应用
打开浏览器访问：http://localhost:8000

## 配置选项
创建 `.env` 文件自定义配置：
```ini
# Flask 配置
FLASK_DEBUG=0
PORT=8000


```

## 高级用法
### 使用特定版本
```yaml
# 修改 docker-compose.yml
image: ghcr.io/你的GitHub用户名/pdf_tools:v1.2
```

### 查看日志
```bash
docker logs pdf-tool -f
```

### 进入容器
```bash
docker exec -it pdf-tool /bin/bash
```

## 技术支持
遇到问题请提交 issue：  
https://github.com/你的GitHub用户名/pdf_tools/issues