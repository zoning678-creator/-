# 团建活动管理 App（Python + HTML）

这是一个示例应用，满足以下模块：

- 商家入驻管理
- 用户社群管理（创建社群、加入社群、发布帖子）
- 管理者后台数据分析

## 技术栈

- 后端：Python（标准库 HTTP Server）
- 前端：HTML + CSS + 原生 JavaScript

## 快速启动

```bash
python3 app.py
```

启动后访问：

- 首页：`http://127.0.0.1:8000/`
- 管理后台：`http://127.0.0.1:8000/admin`

## 主要接口

- `POST /api/merchants`：商家入驻
- `GET /api/merchants`：商家列表
- `POST /api/communities`：创建社群
- `GET /api/communities`：社群列表
- `POST /api/communities/<id>/join`：加入社群
- `POST /api/posts`：发布帖子
- `GET /api/posts`：帖子列表
- `GET /api/admin/analytics`：管理后台分析数据
