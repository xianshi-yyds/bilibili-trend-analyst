<div align="center">

# Bilibili Trend Analyst
# B 站趋势分析仪

**洞察 B 站蓝海赛道 | 深度挖掘优质创作者**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**中文文档** | [English](README.md)

</div>

---

## 🚀 项目简介

**Bilibili Trend Analyst** 是一款专为内容创作者和市场营销人员打造的下一代数据分析工具。它突破了复杂的反爬虫限制，为您提供关于 B 站趋势、UP 主表现和观众互动的实时洞察。

无乱是挖掘潜力赛道，还是分析竞品策略，本工具都能为您提供决策所需的关键数据。

## ✨ 核心功能

| 功能 | 说明 |
| :--- | :--- |
| 🔍 **智能搜索** | 通过智能关键词匹配，发现热门趋势并识别高潜力赛道。 |
| 📊 **深度分析** | 全方位解析 UP 主数据：增长率、周更频率、平均播放量及互动质量。 |
| 🧠 **AI 洞察** | **(AI 驱动)** 自动提取视频内容摘要，并对观众评论进行情感倾向分析。 |
| 🛡️ **强力兜底** | 多级回退系统 (API -> 搜索 -> 视频反查)，确保在极高反爬等级下依然可用。 |
| 🎨 **极致体验** | 采用现代化的玻璃拟态 (Glassmorphism) 与霓虹暗色主题，操作体验流畅丝滑。 |

## 🖼️ 演示画廊

<div align="center">
  <img src="assets/demo_home.png" width="800" alt="Home Page">
  <br>
  <em>智能搜索与趋势发现</em>
  <br><br>
  
  <img src="assets/demo_track.png" width="800" alt="Track Analysis">
  <br>
  <em>赛道深度分析与市场看板</em>
  <br><br>

  <img src="assets/demo_creator.png" width="800" alt="Creator Detail">
  <br>
  <em>UP 主详细画像与数据透视</em>
</div>

## 🛠️ 技术栈

- **后端框架**: [FastAPI](https://fastapi.tiangolo.com/) (高性能，易扩展)
- **数据引擎**: `Requests` + 自研重试与兜底逻辑
- **前端技术**: HTML5 + [TailwindCSS](https://tailwindcss.com/) + Jinja2 模板
- **设计风格**: 自定义霓虹暗色主题 (Neon-Dark)

## ⚡ 快速开始

### 1. 克隆与安装
```bash
git clone https://github.com/your-repo/bilibili-trend-analyst.git
cd bilibili-trend-analyst
pip install -r requirements.txt
```

### 2. 环境配置
复制示例配置文件，并填入您的 B 站 SESSDATA (Cookie) 以获取完整访问权限：
```bash
cp .env.example .env
# 编辑 .env 文件并填入您的 SESSDATA
```

### 3. 启动服务
```bash
python web_app.py
```
> 服务运行地址: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

<div align="center">
  <sub>Built with ❤️ by Multi-Agent AI System</sub>
</div>
