# 拼多多自动化测试指南

## 📋 项目架构概览

这个项目通过**两种方式**控制拼多多的客服、订单和商品信息：

### 1️⃣ 官方API方式 (`pdd_client.py`)
- 通过拼多多开放平台REST API
- 需要配置 Client ID、Client Secret、Access Token
- 适用于：批量数据获取、后台定时任务

### 2️⃣ 浏览器自动化方式 (`playwright_bot.py`)  
- 使用Playwright模拟真实用户操作
- 二维码扫码登录 + Session持久化
- 适用于：需要UI交互的操作、无API支持的功能

---

## 🎯 操作能力对比

| 功能模块 | API方式 | Playwright方式 |
|---------|---------|---------------|
| **客服消息** | ✅ 获取会话、发送消息 | ✅ 自动回复、读取DOM元素 |
| **订单管理** | ✅ 查询、发货、退款 | ✅ 页面操作、批量处理 |
| **商品管理** | ✅ 查询、改价、改库存 | ✅ 复杂表单操作 |
| **登录认证** | ❌ 需要提前获取Token | ✅ 二维码自动登录 |
| **响应速度** | ⚡ 快（直接API） | 🐢 慢（需加载页面） |
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ (依赖页面结构) |

---

## 🚀 测试准备

### 1. 安装依赖

```bash
cd D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter

# 安装Python依赖
pip install playwright httpx fastapi uvicorn

# 安装Playwright浏览器（首次运行）
playwright install chromium
```

### 2. 配置环境变量

编辑 `config.py` 或创建 `.env` 文件：

```bash
# 拼多多开放平台配置（API方式需要）
PDD_CLIENT_ID=your_client_id
PDD_CLIENT_SECRET=your_client_secret
PDD_ACCESS_TOKEN=your_access_token

# 浏览器配置（Playwright方式）
PDD_WORKBENCH_URL=https://mms.pinduoduo.com
BROWSER_HEADLESS=False  # 设为False可以看到浏览器操作过程
PDD_DATA_DIR=./data  # 存放截图和Session数据
```

### 3. 获取拼多多API凭据

1. 访问 [拼多多开放平台](https://open.pinduoduo.com/)
2. 注册开发者账号，创建应用
3. 获取 `Client ID` 和 `Client Secret`
4. 完成店铺授权，获取 `Access Token`

---

## 🧪 运行测试

### 测试1: API客户端测试

```bash
python test_pdd_api.py
```

**测试内容：**
- ✅ 客户端初始化
- ✅ 获取店铺信息
- ✅ 获取商品列表
- ✅ 获取订单列表
- ✅ 获取客服会话列表
- ✅ 获取退款列表
- ✅ 客户端清理

**预期输出：**
```
============================================================
开始拼多多 API 客户端测试
============================================================

✅ PASS | 客户端初始化 | 凭据配置: ✓ | Access Token: ✓
✅ PASS | 获取店铺信息 | 店铺名: XX旗舰店
✅ PASS | 获取商品列表 | 商品总数: 125, 本页: 10
  前3个商品:
    1. iPhone 15 Pro Max 256GB
    2. 苹果AirPods Pro 2代
    3. MacBook Air M2 13寸
...
```

---

### 测试2: Playwright浏览器自动化测试

```bash
python test_playwright_bot.py
```

**测试流程：**

1. **浏览器启动** → 打开Chromium浏览器
2. **二维码登录** → 生成截图 `data/pdd_login.png`
   - ⏳ **等待30秒** - 请用手机拼多多APP扫码登录
3. **登录状态检查** → 验证是否成功登录
4. **导航测试**：
   - 客服页面 → 截图 `data/pdd_customer_service.png`
   - 订单页面 → 截图 `data/pdd_orders.png`
   - 商品页面 → 截图 `data/pdd_products.png`
5. **功能测试**：
   - 获取未读消息
   - 页面元素检查
   - Session持久化
6. **浏览器清理** → 关闭浏览器

**预期输出：**
```
============================================================
开始拼多多 Playwright Bot 测试
============================================================

✅ PASS | 浏览器启动
✅ PASS | 二维码登录初始化 | 截图路径: data/pdd_login.png
📸 请查看二维码截图: data/pdd_login.png
请在30秒内扫码登录...

✅ PASS | 登录状态检查 | 登录状态: True
✅ 已登录，继续测试...

✅ PASS | 导航到客服页面 | 当前URL: https://mms.pinduoduo.com/chat
📸 客服页面截图: data/pdd_customer_service.png
✅ PASS | 获取未读消息 | 找到 3 条未读消息
...
```

---

## 📸 查看测试截图

测试过程中会生成以下截图：

```bash
data/
├── pdd_login.png              # 登录二维码页面
├── pdd_storage_state.json     # Session持久化数据
├── pdd_customer_service.png   # 客服页面
├── pdd_orders.png             # 订单页面
└── pdd_products.png           # 商品页面
```

---

## 🔍 核心代码解析

### Playwright自动化关键方法

```python
# 1. 二维码登录
screenshot_path = await bot.start_qr_login()
# → 打开工作台URL，保存二维码截图

# 2. 检查登录状态
is_logged_in = await bot.check_login_status()
# → 检测DOM元素（用户头像、菜单项等）判断是否已登录

# 3. 持久化Session
await bot.save_storage_state()
# → 保存Cookies/LocalStorage到JSON文件

# 4. 导航到客服页面
await bot.navigate_to_customer_service()
# → 点击客服菜单或直接访问 /chat 路径

# 5. 获取未读消息
messages = await bot.get_unread_messages()
# → 解析 .conversation-item 元素，提取用户名、消息内容

# 6. 发送回复
await bot.send_reply(conversation_index, "您好！")
# → 定位输入框，填写内容，点击发送按钮
```

### API调用关键方法

```python
# 1. 初始化客户端
client = PDDClient()

# 2. 获取商品列表
result = await client.get_product_list(page=1, page_size=20)

# 3. 更新商品价格
await client.update_product_price(
    goods_id=12345,
    sku_prices=[{"sku_id": 67890, "price": 9999}]  # 单位：分
)

# 4. 订单发货
await client.ship_order(
    order_sn="PDD2024...",
    logistics_id=10001,  # 顺丰
    tracking_number="SF1234567890"
)

# 5. 获取客服消息
conversations = await client.get_conversation_list()
messages = await client.get_chat_messages(conversation_id="xxx")

# 6. 发送客服消息
await client.send_message(
    conversation_id="xxx",
    content="亲，您好！",
    msg_type=1  # 1-文本, 2-图片, 3-商品卡片
)
```

---

## ⚠️ 常见问题

### 1. Playwright测试卡在"等待扫码"
**原因：** 未在30秒内扫码登录  
**解决：** 
- 查看 `data/pdd_login.png` 是否有二维码
- 如果二维码过期，重新运行测试
- 可以修改 `test_playwright_bot.py` 中的等待时间

### 2. API测试全部失败
**原因：** 未配置正确的API凭据  
**解决：**
- 检查 `config.py` 中的配置
- 确认Access Token未过期
- 登录开放平台查看API权限

### 3. 浏览器无法启动
**原因：** Playwright浏览器未安装  
**解决：**
```bash
playwright install chromium
```

### 4. 页面元素找不到
**原因：** 拼多多页面结构变化  
**解决：**
- 手动访问工作台，检查元素选择器
- 修改 `playwright_bot.py` 中的选择器（`.conversation-item` 等）

---

## 🎓 进阶使用

### 1. 自动回复机器人

```python
from playwright_bot import PlaywrightBot
from message_handler import MessageHandler

bot = PlaywrightBot()
handler = MessageHandler()

await bot.start()
await bot.login()
await bot.auto_reply_loop(handler)  # 开始自动回复循环
```

### 2. 批量操作商品

```python
from pdd_client import PDDClient

client = PDDClient()

# 批量改价
products = await client.get_product_list(page=1, page_size=100)
for product in products['goods_list_get_response']['goods_list']:
    goods_id = product['goods_id']
    # 价格上涨10%
    new_price = int(product['min_group_price'] * 1.1)
    await client.update_product_price(
        goods_id=goods_id,
        sku_prices=[{"sku_id": sku['sku_id'], "price": new_price} 
                    for sku in product['sku_list']]
    )
```

### 3. 订单自动发货

```python
# 获取待发货订单
orders = await client.get_order_list(order_status=1)  # 1-待发货

for order in orders['order_list_get_response']['order_list']:
    order_sn = order['order_sn']
    
    # 调用物流接口获取单号（这里简化处理）
    tracking_number = get_tracking_number_from_logistics_system()
    
    # 发货
    await client.ship_order(
        order_sn=order_sn,
        logistics_id=10001,
        tracking_number=tracking_number
    )
```

---

## 📚 相关文档

- [拼多多开放平台文档](https://open.pinduoduo.com/application/document/browse)
- [Playwright中文文档](https://playwright.dev/python/)
- [FastAPI文档](https://fastapi.tiangolo.com/)

---

## 📞 技术支持

如有问题，请查看：
- `playwright_bot.py` - 浏览器自动化实现
- `pdd_client.py` - API客户端实现
- `message_handler.py` - 消息处理逻辑
- `main.py` - FastAPI服务入口

**测试完成后，你可以：**
1. 根据测试结果调整配置
2. 集成到实际业务流程
3. 部署为后台服务（`uvicorn main:app`）
