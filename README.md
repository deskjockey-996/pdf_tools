# PDF工具大全

[![Version](https://img.shields.io/badge/version-1.1.1-blue.svg)](https://github.com/deskjockey-996/pdf_tools/releases/tag/v1.1.1)

一个功能强大的在线PDF处理工具集合，提供多种实用的PDF处理功能。

## 🌟 功能特点

### 已实现功能
- **PDF旋转工具**
  - 支持90度、180度、270度旋转
  - 多页面批量旋转
  - 实时预览
  - 页面拖拽排序
  - 选择性删除页面

### 即将推出功能
- PDF合并工具
- PDF压缩工具
- PDF拆分工具
- PDF转图片工具
- PDF水印工具

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
http://localhost:5000
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
pdf_tools/
├── app.py              # 主应用文件
├── requirements.txt    # 项目依赖
├── templates/         # HTML模板
│   ├── index.html    # 首页
│   └── rotate.html   # 旋转工具页面
└── uploads/          # 上传文件存储目录
```

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