# Bilibili Trend Analyst (B站趋势分析仪)

**中文文档** | [English](README.md)

一款强大的 B 站 UP 主、趋势及视频数据分析工具。基于 Python (FastAPI) 和现代 Web 技术构建。

## 功能特性

- 🔍 **智能搜索**：搜索趋势或关键词，获取相关的精选 UP 主列表。
- 📊 **深度分析**：分析 UP 主表现、周更频率及平均播放量。
- 🧠 **AI 洞察**：自动内容摘要及观众反馈分析。
- 📉 **市场看板**：可视化竞争格局、受众定位及市场空白点。
- 🛡️ **强力兜底**：先进的反爬虫绕过及多级兜底机制，确保数据高可用性。

## 演示截图

| 首页 | 赛道分析 | UP主详情 |
| :---: | :---: | :---: |
| ![Home](assets/demo_home.png) | ![Track](assets/demo_track.png) | ![Creator](assets/demo_creator.png) |

## 安装指南

1.  **克隆仓库**
    ```bash
    git clone https://github.com/your-repo/bilibili-trend-analyst.git
    cd bilibili-trend-analyst
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置**:
    - 将 `.env.example` 复制为 `.env`
    - 填入你的 B 站 `SESSDATA` (Cookie) 以获取完整数据访问权限。

4.  **启动服务器**:
    ```bash
    python web_app.py
    ```

5.  **访问**: 
    打开浏览器访问：`http://localhost:8000`

## 技术栈

- **后端**: FastAPI, Requests
- **前端**: HTML5, Tailwind CSS (CDN), Jinja2 Templates
- **设计**: Glassmorphism, Neon Dark Mode

## License

MIT
