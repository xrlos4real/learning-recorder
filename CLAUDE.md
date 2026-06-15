# CLAUDE.md — 每日学习记录网站

## 项目概述

个人每日学习记录网站，单用户本地使用，轻量化优先。
核心需求：每天记录学了什么、学了多久，支持 Markdown 写作，能看到打卡统计和历史回顾。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Python 3.11 + Flask | 轻量 API 服务 |
| ORM | SQLAlchemy | 操作 SQLite |
| 数据库 | SQLite | 单文件，零运维 |
| 前端 | Vue 3 + Vite | 组件化页面 |
| HTTP 客户端 | Axios | 前端请求封装 |
| Markdown 编辑器 | EasyMDE | 开箱即用 |
| 图表 | Chart.js | 统计页折线 / 柱状图 |
| 样式 | 原生 CSS + CSS Variables | 不引入 UI 框架，保持轻量 |

---

## 目录结构

```
learning-log/
├── CLAUDE.md                  # 本文件，项目说明
├── backend/
│   ├── app.py                 # Flask 入口，注册蓝图、CORS、错误处理
│   ├── models.py              # SQLAlchemy 数据库模型
│   ├── config.py              # 配置（DB 路径、SECRET_KEY 等）
│   ├── data/
│   │   └── log.db             # SQLite 数据库文件（自动生成）
│   └── routes/
│       ├── logs.py            # 日志 CRUD 接口
│       ├── tags.py            # 标签接口
│       └── stats.py           # 统计接口
├── frontend/
│   ├── index.html
│   ├── vite.config.js         # 代理 /api -> http://localhost:5000
│   ├── package.json
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/
│       │   └── index.js       # Vue Router 路由配置
│       ├── api/
│       │   └── index.js       # Axios 封装，统一请求前缀 /api
│       ├── views/
│       │   ├── HomeView.vue   # 首页：日历热力图 + 最近日志列表
│       │   ├── EditorView.vue # 写 / 编辑日志页
│       │   ├── DetailView.vue # 日志详情页（渲染 Markdown）
│       │   ├── StatsView.vue  # 统计页：streak、时长图表
│       │   └── SearchView.vue # 搜索 / 归档页
│       └── components/
│           ├── NavBar.vue     # 顶部导航
│           ├── HeatMap.vue    # 热力图组件
│           ├── LogCard.vue    # 日志卡片组件
│           └── TagBadge.vue   # 标签徽章组件
└── requirements.txt           # Python 依赖
```

---

## 数据库模型

### Log（学习日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| title | VARCHAR(200) | 标题 |
| content | TEXT | Markdown 正文 |
| duration | INTEGER | 学习时长（分钟） |
| date | DATE | 学习日期（YYYY-MM-DD） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### Tag（标签）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | VARCHAR(50) | 标签名，唯一 |

### LogTag（日志-标签关联，多对多）

| 字段 | 类型 | 说明 |
|------|------|------|
| log_id | INTEGER FK | 关联 Log.id |
| tag_id | INTEGER FK | 关联 Tag.id |

---

## API 接口约定

**Base URL：** `http://localhost:5000/api`

**统一响应格式：**
```json
{
  "code": 0,
  "data": {},
  "msg": "ok"
}
```
错误时 `code` 非 0，`msg` 描述错误原因。

### 日志接口 `/api/logs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/logs | 获取日志列表，支持 `?tag=&date=&q=&page=&limit=` |
| POST | /api/logs | 新建日志 |
| GET | /api/logs/:id | 获取单条日志 |
| PUT | /api/logs/:id | 更新日志 |
| DELETE | /api/logs/:id | 删除日志 |

### 标签接口 `/api/tags`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/tags | 获取所有标签（含日志数量） |
| POST | /api/tags | 新建标签 |
| DELETE | /api/tags/:id | 删除标签 |

### 统计接口 `/api/stats`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/stats/heatmap | 返回过去一年每天的日志数，用于热力图 |
| GET | /api/stats/summary | 返回总日志数、总时长、当前 streak |
| GET | /api/stats/daily | 返回最近 30 天每日学习时长，用于图表 |

---

## 页面功能说明

### 首页 HomeView
- 顶部显示 summary 卡片：总记录天数、总学习时长、当前连续打卡天数
- GitHub 风格热力图，展示过去一年每天的打卡情况
- 下方列出最近 10 条日志（LogCard 组件），点击进入详情页

### 写日志页 EditorView
- EasyMDE Markdown 编辑器
- 顶部输入：标题、学习日期（默认今天）、学习时长（分钟）
- 标签多选/新建输入
- 保存 / 取消按钮
- 路由 `/editor`（新建）和 `/editor/:id`（编辑）复用同一组件

### 日志详情页 DetailView
- 渲染 Markdown 为 HTML（使用 marked.js）
- 显示标签、日期、时长
- 编辑 / 删除按钮

### 统计页 StatsView
- Summary 卡片（同首页顶部）
- 最近 30 天学习时长柱状图（Chart.js）
- 标签分布饼图

### 搜索页 SearchView
- 顶部搜索框（全文搜索标题 + 内容）
- 标签筛选按钮列表
- 日期区间选择
- 结果列表分页展示

---

## 开发规范

- 后端所有接口加 `flask-cors` 允许跨域（开发环境）
- 前端 `vite.config.js` 配置 proxy，`/api` 代理到 `http://localhost:5000`
- 日期统一使用 `YYYY-MM-DD` 字符串格式
- 时长单位统一为**分钟**（整数）
- 标签名去除首尾空格，不允许重复
- 删除日志时同步删除 LogTag 关联记录

---

## 开发顺序建议

1. **后端骨架**：`app.py` + `models.py` + `config.py`，初始化数据库
2. **日志 CRUD**：`routes/logs.py`，完成增删改查接口
3. **标签接口**：`routes/tags.py`
4. **统计接口**：`routes/stats.py`
5. **前端骨架**：Vite 初始化、路由配置、Axios 封装、NavBar
6. **首页**：热力图 + 日志列表
7. **编辑页**：EasyMDE 集成
8. **详情页**：Markdown 渲染
9. **统计页**：Chart.js 图表
10. **搜索页**：筛选 + 分页

---

## 启动方式

```bash
# 后端
cd backend
pip install -r requirements.txt
python app.py

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

后端运行在 `http://localhost:5000`，前端运行在 `http://localhost:5173`。
