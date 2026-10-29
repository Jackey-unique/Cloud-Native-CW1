# Travel Journal Share：运行与范围

## 启动

在本目录执行 `python server.py`，浏览器打开 http://127.0.0.1:8000。Python 3.9 或更高版本，无需额外依赖。数据保存在 `data/`，停止服务可按 Ctrl+C。

## 功能与接口

- `POST /api/assets`：JSON 中传入 title、description、fileName、mediaType、content（Base64 文件内容），创建记录。
- `GET /api/assets`：列出记录；`GET /api/assets/{id}`：获取单条。
- `PUT /api/assets/{id}`：更新 title 和 description；`DELETE /api/assets/{id}`：删除记录和文件。
- `GET /media/{id}`：读取关联文件。

本地演示限制 JPEG、PNG、WebP 和 MP4，单文件最多 10 MB。这些是原型限制，并非课程实验或 Azure 的已核实限制。当前通过 Base64 将文件传给本地服务器，文件保存在本机，元数据保存在 SQLite。浏览器提供单条编辑和删除，详情接口可单独调用。

## 与云设计的关系

本程序是本地功能原型，不是 Azure 部署：没有 Logic Apps、Blob Storage 或 Cosmos DB，也没有真实身份验证、授权、私有共享、恶意文件检查或视频流式播放。切勿公开部署或存储敏感内容。下一步需取得 Lab 1–6，核实 Lab 6 IUPS/RAI 的请求格式、文件流向、认证、CORS、大小限制及连接方式，再实现云端工作流并修改前端的 API 地址和数据格式。云方案中的失败补偿和清理也必须实际实现和测试。
