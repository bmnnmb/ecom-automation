# 平台授权功能验证清单

## ✅ 完成情况

### 后端实现 ✅
- [x] 拼多多 `playwright_bot.py` - 浏览器自动化
- [x] 抖音 `douyin_bot.py` - 浏览器自动化
- [x] 拼多多授权API (`routes/system_routes.py`)
- [x] 抖音授权API (`routes/douyin_routes.py`)
- [x] 路由注册 (`routes/__init__.py`)
- [x] 统一API返回格式
- [x] 会话持久化
- [x] 解绑功能

### 前端实现 ✅
- [x] 拼多多授权弹窗 (`PddAuthModal.jsx`)
- [x] 抖音授权弹窗 (`DouyinAuthModal.jsx`)
- [x] 系统管理页面集成 (`System/index.jsx`)
- [x] 授权状态显示
- [x] 授权/解绑按钮
- [x] 轮询机制
- [x] 错误处理

### 文档 ✅
- [x] 平台授权指南 (`PLATFORM_AUTH_GUIDE.md`)
- [x] 系统管理说明 (`System/README.md`)
- [x] 实现总结 (`PLATFORM_AUTH_SUMMARY.md`)
- [x] 验证清单 (本文件)

### 测试工具 ✅
- [x] API测试脚本 (`test_platform_auth.py`)

## 🧪 需要验证的功能

### 基础功能
- [ ] 访问系统管理页面 http://localhost:5173/system
- [ ] 拼多多显示"未授权"状态
- [ ] 抖音显示"未授权"状态
- [ ] 点击拼多多"授权"按钮打开弹窗
- [ ] 点击抖音"授权"按钮打开弹窗

### 拼多多授权流程
- [ ] 弹窗显示三个步骤
- [ ] 点击"开始授权"生成二维码
- [ ] 二维码图片正常显示
- [ ] 用拼多多商家版APP扫码
- [ ] 在APP中确认登录
- [ ] 前端自动检测到登录成功
- [ ] 状态更新为"已授权"（绿色标签）
- [ ] 按钮文字变为"解绑"

### 抖音授权流程
- [ ] 弹窗显示三个步骤
- [ ] 点击"开始授权"生成二维码
- [ ] 二维码图片正常显示
- [ ] 用抖音APP扫码
- [ ] 在APP中确认登录
- [ ] 前端自动检测到登录成功
- [ ] 状态更新为"已授权"（绿色标签）
- [ ] 按钮文字变为"解绑"

### 解绑功能
- [ ] 点击拼多多"解绑"弹出确认框
- [ ] 确认解绑后状态变为"未授权"
- [ ] 会话文件被删除
- [ ] 点击抖音"解绑"弹出确认框
- [ ] 确认解绑后状态变为"未授权"
- [ ] 会话文件被删除

### 会话持久化
- [ ] 授权成功后刷新页面仍显示"已授权"
- [ ] 会话文件存在于 `data/` 目录
- [ ] 重启后端服务，前端仍显示"已授权"

### 错误处理
- [ ] 扫码超时（2分钟）后显示超时提示
- [ ] 点击"重新授权"可以重新生成二维码
- [ ] 点击"取消授权"关闭弹窗并清理资源
- [ ] 网络错误时显示友好提示

### API测试
- [ ] 运行 `python test_platform_auth.py` 无错误
- [ ] 访问 http://localhost:8003/docs 可以查看API文档
- [ ] Swagger中可以看到拼多多和抖音的接口

## 🔍 检查项

### 文件存在性
```bash
# 后端文件
ls services/pdd-cs-adapter/douyin_bot.py
ls services/pdd-cs-adapter/routes/douyin_routes.py
ls services/pdd-cs-adapter/test_platform_auth.py
ls services/pdd-cs-adapter/PLATFORM_AUTH_GUIDE.md

# 前端文件
ls admin/src/pages/System/DouyinAuthModal.jsx
ls admin/src/pages/System/PddAuthModal.jsx
ls admin/src/pages/System/README.md

# 数据目录
ls services/pdd-cs-adapter/data/
```

### 服务运行状态
```bash
# 检查后端服务
curl http://localhost:8003/

# 检查系统状态
curl http://localhost:8003/api/v1/system/status

# 检查前端服务
curl http://localhost:5173/
```

## 📋 测试步骤

### 1. 准备工作
```bash
# 确保后端服务运行
cd services/pdd-cs-adapter
uvicorn main:app --reload --port 8003

# 确保前端服务运行
cd admin
npm run dev
```

### 2. 测试拼多多授权
1. 访问 http://localhost:5173/system
2. 找到"拼多多"（购物车图标 🛒）
3. 确认状态为"未授权"（红色标签）
4. 点击"授权"按钮
5. 在弹窗中点击"开始授权"
6. 等待二维码加载（约2秒）
7. 打开拼多多商家版APP
8. 扫描二维码
9. 在APP中点击"确认登录"
10. 观察前端自动更新为"已授权"
11. 弹窗自动关闭

### 3. 测试抖音授权
1. 在同一页面找到"抖音"（音符图标 🎵）
2. 确认状态为"未授权"（红色标签）
3. 点击"授权"按钮
4. 在弹窗中点击"开始授权"
5. 等待二维码加载（约2秒）
6. 打开抖音APP
7. 扫描二维码
8. 在APP中点击"确认登录"
9. 观察前端自动更新为"已授权"
10. 弹窗自动关闭

### 4. 测试会话持久化
1. 确保拼多多和抖音都已授权
2. 刷新浏览器页面（F5）
3. 确认两个平台仍显示"已授权"
4. 检查会话文件存在：
   ```bash
   ls services/pdd-cs-adapter/data/pdd_storage_state.json
   ls services/pdd-cs-adapter/data/douyin_storage_state.json
   ```

### 5. 测试解绑功能
1. 点击拼多多的"解绑"按钮
2. 在确认对话框中点击"确认解绑"
3. 观察状态变为"未授权"
4. 点击抖音的"解绑"按钮
5. 在确认对话框中点击"确认解绑"
6. 观察状态变为"未授权"

## 🐛 常见问题排查

### 问题1: 二维码不显示
**检查**:
```bash
# 检查后端服务
curl http://localhost:8003/api/v1/system/pdd-login/start -X POST

# 检查浏览器控制台是否有CORS错误
# 打开开发者工具 -> Console
```

### 问题2: 扫码后一直"等待确认"
**检查**:
- 确认在APP中点击了"确认登录"
- 查看后端日志是否有错误
- 检查网络连接

### 问题3: 会话文件不生成
**检查**:
```bash
# 确保data目录存在且可写
ls -la services/pdd-cs-adapter/data/

# 查看后端日志
```

### 问题4: 前端编译错误
**检查**:
```bash
# 查看npm运行日志
# 确保所有组件导入正确
```

## 📊 测试结果记录

### 环境信息
- 操作系统: Windows 10
- Node版本: ___________
- Python版本: 3.11
- 浏览器: ___________
- 后端服务状态: ✅ 运行中
- 前端服务状态: ___________

### 测试结果
| 功能 | 状态 | 备注 |
|------|------|------|
| 拼多多授权 | [ ] | |
| 抖音授权 | [ ] | |
| 拼多多解绑 | [ ] | |
| 抖音解绑 | [ ] | |
| 会话持久化 | [ ] | |
| 错误处理 | [ ] | |

### 问题记录
1. ___________
2. ___________
3. ___________

## ✅ 验证完成标准

满足以下所有条件即可认为验证完成：

- [ ] 拼多多和抖音都能成功授权
- [ ] 授权状态正确显示
- [ ] 解绑功能正常工作
- [ ] 会话持久化有效
- [ ] 刷新页面后状态保持
- [ ] 错误提示清晰友好
- [ ] 无控制台错误
- [ ] API测试脚本通过

## 📝 反馈

如果在测试过程中遇到问题，请记录：
1. 问题描述
2. 复现步骤
3. 错误信息（截图或日志）
4. 浏览器控制台信息

---

**验证时间**: __________  
**验证人**: __________  
**验证结果**: [ ] 通过 [ ] 部分通过 [ ] 未通过
