# 新加坡活动联系人管理系统

🎯 专业的联系人管理工具，支持数据库持久化、联系状态跟踪、备注管理等功能。

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 功能特点

- 📊 **完整信息展示**
  - 姓名、职位、公司信息
  - 邮箱、官网、LinkedIn个人主页
  - 行业分类、公司规模
  - 详细背景说明和邀约切入点
  - 微软产品和营销技术栈

- 📞 **联系状态管理**
  - 四种联系方式：LinkedIn / WhatsApp / Email / 电话
  - 一键切换"未联系"/"已联系"状态
  - 所有状态自动保存到数据库

- 📝 **备注系统**
  - 每个联系人独立的备注框
  - 实时保存到数据库
  - 支持长文本记录

- 🗑️ **软删除与回收站**
  - 安全删除联系人
  - 回收站查看已删除记录
  - 一键恢复功能

- 🔍 **搜索与排序**
  - 实时搜索（姓名/公司/职位/行业）
  - 按公司规模排序
  - 统计面板（总数/已联系/未联系）

- 💾 **数据管理**
  - SQLite数据库持久化存储
  - 导入CSV批量数据
  - 导出完整联系记录

## 🚀 快速开始

### 本地运行

1. **克隆或下载项目**
```bash
cd C:\Users\86185
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动系统**

Windows用户：
```bash
双击 启动系统.bat
```

或手动启动：
```bash
python contact_manager_app.py
```

4. **访问系统**

打开浏览器访问：http://127.0.0.1:5000

### 在线部署

系统支持多种免费部署方案：

#### 方案1：PythonAnywhere（推荐）
- ✅ 完全免费
- ✅ 数据持久化
- ✅ 适合长期使用
- 📖 [部署教程](部署到PythonAnywhere.txt)

#### 方案2：Render
- ✅ GitHub自动部署
- ✅ 现代化配置
- ⚠️ 免费版会休眠
- 📖 [部署教程](部署到Render.txt)

详细对比请查看：[部署平台选择指南.txt](部署平台选择指南.txt)

## 📁 项目结构

```
.
├── contact_manager_app.py      # Flask后端主程序
├── templates/
│   └── index.html              # 前端页面
├── uploads/                    # CSV上传目录
├── contacts.db                 # SQLite数据库（自动创建）
├── requirements.txt            # Python依赖
├── Procfile                    # 部署配置（Render/Heroku）
├── .gitignore                  # Git忽略配置
└── README.md                   # 本文件
```

## 🛠️ 技术栈

- **后端**: Python 3.7+ / Flask 2.0+
- **数据库**: SQLite 3
- **前端**: HTML5 / CSS3 / JavaScript (Vanilla)
- **部署**: PythonAnywhere / Render / Railway

## 📊 数据库结构

### contacts表（联系人信息）
- id, name, title, company, email
- website, linkedin, industry, employees
- priority, background, approach
- ms_products, marketing_tech
- is_global, global_reason
- is_deleted, created_at

### contact_status表（联系状态）
- id, email
- linkedin_contacted, whatsapp_contacted
- email_contacted, phone_contacted
- notes, last_updated

## 🔐 安全说明

- ✅ 数据库本地存储，不上传到云端
- ✅ 支持软删除，防止误删
- ✅ .gitignore 排除敏感文件
- ⚠️ 生产环境建议添加身份验证

## 📝 使用说明

### 导入数据
1. 点击"📁 导入CSV文件"
2. 选择CSV文件（必须包含指定列）
3. 等待导入完成

### 管理联系人
- 点击联系状态按钮切换状态
- 在备注框输入信息（自动保存）
- 点击删除按钮移至回收站
- 使用搜索框快速查找

### 导出数据
- 点击"💾 导出联系记录"
- 下载包含所有状态和备注的完整CSV

### 回收站
- 点击"🗑️ 回收站"查看已删除联系人
- 点击"恢复"按钮还原联系人

## 🔄 数据备份

**重要**：定期备份 `contacts.db` 文件！

```bash
# Windows
copy contacts.db contacts_backup_2026-03-05.db

# Linux/Mac
cp contacts.db contacts_backup_2026-03-05.db
```

## 🐛 故障排除

### 启动失败
- 检查Python版本（需要3.7+）
- 确认Flask已安装：`pip show flask`
- 查看错误日志

### 数据不保存
- 确认 contacts.db 有写入权限
- 检查数据库文件是否存在
- 查看浏览器控制台错误

### 导入失败
- 确认CSV格式正确（UTF-8编码）
- 检查 uploads 文件夹权限
- 查看后台错误日志

## 📞 支持

- 查看 [使用说明.txt](使用说明.txt)
- 查看 [部署前检查清单.txt](部署前检查清单.txt)
- 检查相关教程文档

## 📄 许可证

MIT License

## 🎉 更新日志

### v2.1 (最新)
- ✨ 新增删除联系人功能（软删除）
- ✨ 新增回收站功能
- ✨ 支持恢复已删除联系人
- 🐛 优化数据库兼容性

### v2.0
- ✨ SQLite数据库支持
- ✨ 联系状态和备注永久保存
- ✨ 导出功能
- ✨ 搜索和排序功能

### v1.0
- 🎉 初始版本

---

Made with ❤️ for 新加坡活动联系人管理
