import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Tag,
  Input,
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  Dropdown,
  Modal,
  Drawer,
  Descriptions,
  Timeline,
  Steps,
  Tabs,
  Typography,
  Divider,
  Badge,
  Avatar,
  Tooltip,
  Spin,
  Empty,
  message,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  PrinterOutlined,
  MoreOutlined,
  ShoppingCartOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  TruckOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  CopyOutlined,
  MessageOutlined,
} from '@ant-design/icons';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;
const { TabPane } = Tabs;

// ============================================================
// 平台 & 状态映射表（后端 → 前端展示）
// ============================================================
const PLATFORM_MAP = {
  douyin:    { name: '抖音', color: '#165DFF' },
  kuaishou:  { name: '快手', color: '#722ED1' },
  pinduoduo: { name: '拼多多', color: '#F53F3F' },
  xianyu:    { name: '闲鱼', color: '#FF7D00' },
  // 兼容 api-gateway 的简写
  pdd:       { name: '拼多多', color: '#F53F3F' },
};

const STATUS_MAP = {
  pending:    { label: '待付款', color: 'default',   step: 0 },
  processing: { label: '待发货', color: 'processing', step: 1 },
  paid:       { label: '待发货', color: 'processing', step: 1 },
  shipped:    { label: '已发货', color: 'warning',    step: 2 },
  delivered:  { label: '已送达', color: 'warning',    step: 2 },
  completed:  { label: '已完成', color: 'success',    step: 3 },
  cancelled:  { label: '已取消', color: 'default',    step: -1 },
  refunding:  { label: '退款中', color: 'error',      step: -1 },
  refunded:   { label: '已退款', color: 'default',    step: -1 },
};

// ============================================================
// 后端 Order → 前端展示格式 适配器
// ============================================================
function adaptOrder(raw) {
  const platform = PLATFORM_MAP[raw.platform] || { name: raw.platform, color: '#8c8c8c' };
  const statusInfo = STATUS_MAP[raw.status] || { label: raw.status, color: 'default', step: -1 };
  const item = Array.isArray(raw.items) && raw.items.length > 0 ? raw.items[0] : {};
  const customer = raw.customer || {};

  // 金额：优先 actual_amount，其次 total_amount
  const amount = raw.actual_amount ?? raw.total_amount ?? 0;
  const price = item.unit_price ?? 0;
  const quantity = item.quantity ?? 1;
  // 利润估算：如果没有 profit 字段，用 total - actual 的差值，否则用 discount_amount 做粗略参考
  const profit = raw.profit ?? Math.max(0, (raw.total_amount ?? 0) - amount);

  return {
    id: raw.order_id || raw.id,
    orderNo: raw.platform_order_id || raw.order_id || raw.orderNo || '',
    platform: raw.platform,
    platformName: platform.name,
    platformColor: platform.color,
    status: raw.status === 'processing' ? 'paid' : raw.status, // 前端用 'paid' 代表待发货
    statusLabel: statusInfo.label,
    statusColor: statusInfo.color,
    statusStep: statusInfo.step,
    product: item.product_name || item.product || '-',
    quantity,
    price,
    amount,
    profit,
    customer: customer.name || customer.customer_name || '-',
    phone: customer.phone || customer.customer_phone || '-',
    address: customer.address || customer.customer_address || '-',
    logisticsNo: raw.shipping?.tracking_number || raw.logisticsNo || null,
    logisticsCompany: raw.shipping?.carrier || raw.logisticsCompany || null,
    createdAt: raw.created_at || raw.createdAt || new Date().toISOString(),
    paidAt: raw.paid_at || raw.paidAt || null,
    shippedAt: raw.shipped_at || raw.shippedAt || null,
    completedAt: raw.completed_at || raw.completedAt || null,
    remark: raw.remarks || raw.remark || '',
  };
}

// ============================================================
// API 调用封装
// ============================================================
const API_BASE = '/api/orders';

async function fetchOrders() {
  const resp = await fetch(`${API_BASE}/?page_size=100`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const data = await resp.json();
  // oms-service 返回数组; api-gateway 返回 { success, data: { items } }
  if (Array.isArray(data)) return data.map(adaptOrder);
  if (data.data?.items) return data.data.items.map(adaptOrder);
  if (Array.isArray(data.data)) return data.data.map(adaptOrder);
  return [];
}

async function updateOrderStatus(orderId, newStatus, extra = {}) {
  const url = `${API_BASE}/${orderId}/status?status=${newStatus}`;
  const resp = await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' } });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || err.message || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// ============================================================
// Orders 页面组件
// ============================================================
const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [activeTab, setActiveTab] = useState('all');

  // ============================================================
  // 页面加载时从后端拉取订单
  // ============================================================
  const loadOrders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchOrders();
      setOrders(data);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
      message.error('加载订单失败，请确认后端服务是否运行');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  // 统计数据
  const stats = {
    total: orders.length,
    pendingShip: orders.filter(o => o.status === 'paid' || o.status === 'processing').length,
    pendingRefund: orders.filter(o => o.status === 'refunding').length,
    todayOrders: orders.filter(o => {
      const today = new Date().toDateString();
      return new Date(o.createdAt).toDateString() === today;
    }).length,
    todayRevenue: orders.filter(o => {
      const today = new Date().toDateString();
      return new Date(o.createdAt).toDateString() === today;
    }).reduce((sum, o) => sum + o.amount, 0),
  };

  // 筛选
  const [filters, setFilters] = useState({
    keyword: '',
    platform: 'all',
    status: 'all',
    dateRange: null,
  });

  // 处理筛选
  const handleFilter = (changedValues) => {
    setFilters({ ...filters, ...changedValues });
  };

  // 重置筛选
  const handleReset = () => {
    setFilters({
      keyword: '',
      platform: 'all',
      status: 'all',
      dateRange: null,
    });
  };

  // 过滤订单
  const filteredOrders = orders.filter((order) => {
    if (filters.keyword && !order.orderNo.toLowerCase().includes(filters.keyword.toLowerCase()) && !order.customer.includes(filters.keyword)) {
      return false;
    }
    if (filters.platform !== 'all' && order.platform !== filters.platform) {
      return false;
    }
    if (filters.status !== 'all' && order.status !== filters.status) {
      return false;
    }
    if (filters.dateRange && filters.dateRange.length === 2) {
      const orderDate = new Date(order.createdAt);
      if (orderDate < filters.dateRange[0].startOf('day').toDate() || orderDate > filters.dateRange[1].endOf('day').toDate()) {
        return false;
      }
    }
    if (activeTab !== 'all') {
      if (activeTab === 'pending' && order.status !== 'pending') return false;
      if (activeTab === 'paid' && !['paid', 'processing'].includes(order.status)) return false;
      if (activeTab === 'shipped' && order.status !== 'shipped') return false;
      if (activeTab === 'refund' && !['refunding', 'refunded'].includes(order.status)) return false;
    }
    return true;
  });

  // 查看订单详情
  const handleView = (order) => {
    setCurrentOrder(order);
    setDrawerVisible(true);
  };

  // 发货
  const handleShip = (order) => {
    Modal.confirm({
      title: '确认发货',
      content: `确定要发货订单"${order.orderNo}"吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await updateOrderStatus(order.id, 'shipped');
          message.success('发货成功');
          loadOrders(); // 重新拉取
        } catch (err) {
          message.error(`发货失败: ${err.message}`);
        }
      },
    });
  };

  // 处理退款
  const handleRefund = (order) => {
    Modal.confirm({
      title: '确认退款',
      content: `确定要退款订单"${order.orderNo}"吗？退款金额：¥${order.amount.toFixed(2)}`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await updateOrderStatus(order.id, 'refunded');
          message.success('退款成功');
          loadOrders();
        } catch (err) {
          message.error(`退款失败: ${err.message}`);
        }
      },
    });
  };

  // 批量发货
  const handleBatchShip = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择订单');
      return;
    }
    const pendingShipOrders = orders.filter(o => selectedRowKeys.includes(o.id) && ['paid', 'processing'].includes(o.status));
    if (pendingShipOrders.length === 0) {
      message.warning('选中的订单中没有待发货订单');
      return;
    }
    Modal.confirm({
      title: '批量发货',
      content: `确定要发货选中的 ${pendingShipOrders.length} 个订单吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        let success = 0;
        let fail = 0;
        for (const order of pendingShipOrders) {
          try {
            await updateOrderStatus(order.id, 'shipped');
            success++;
          } catch {
            fail++;
          }
        }
        setSelectedRowKeys([]);
        if (success > 0) message.success(`成功发货 ${success} 个订单`);
        if (fail > 0) message.warning(`${fail} 个订单发货失败`);
        loadOrders();
      },
    });
  };

  // 确认收货
  const handleConfirmReceipt = (order) => {
    Modal.confirm({
      title: '确认收货',
      content: `确认订单"${order.orderNo}"已收货吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await updateOrderStatus(order.id, 'completed');
          message.success('确认收货成功');
          loadOrders();
        } catch (err) {
          message.error(`确认收货失败: ${err.message}`);
        }
      },
    });
  };

  // 导出CSV
  const handleExportCSV = () => {
    const headers = ['订单号', '平台', '商品', '数量', '金额', '利润', '客户', '状态', '下单时间'];
    const csvContent = [
      headers.join(','),
      ...filteredOrders.map(o => [
        o.orderNo,
        o.platformName,
        o.product,
        o.quantity,
        o.amount.toFixed(2),
        o.profit.toFixed(2),
        o.customer,
        o.statusLabel,
        new Date(o.createdAt).toLocaleString(),
      ].join(',')),
    ].join('\n');
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `orders_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    message.success(`已导出 ${filteredOrders.length} 条订单`);
  };

  // 表格列配置
  const columns = [
    {
      title: '订单信息',
      dataIndex: 'orderNo',
      key: 'orderNo',
      width: 280,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>{text}</div>
          <Space size="small">
            <Tag color={record.platformColor}>{record.platformName}</Tag>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {new Date(record.createdAt).toLocaleString()}
            </Text>
          </Space>
        </div>
      ),
    },
    {
      title: '商品',
      dataIndex: 'product',
      key: 'product',
      width: 150,
      render: (text, record) => (
        <div>
          <div style={{ marginBottom: 4 }}>{text}</div>
          <Text type="secondary">x{record.quantity}</Text>
        </div>
      ),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      sorter: (a, b) => a.amount - b.amount,
      render: (val, record) => (
        <div>
          <div style={{ fontWeight: 500, color: '#165DFF' }}>¥{val.toFixed(2)}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>利润: ¥{record.profit.toFixed(2)}</Text>
        </div>
      ),
    },
    {
      title: '客户',
      dataIndex: 'customer',
      key: 'customer',
      width: 120,
      render: (text, record) => (
        <div>
          <div style={{ marginBottom: 4 }}>{text}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.phone}</Text>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'statusLabel',
      key: 'status',
      width: 100,
      render: (text, record) => (
        <Tag color={record.statusColor}>{text}</Tag>
      ),
    },
    {
      title: '物流',
      dataIndex: 'logisticsNo',
      key: 'logistics',
      width: 150,
      render: (text, record) => (
        text ? (
          <div>
            <div style={{ marginBottom: 4 }}>{record.logisticsCompany}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>{text}</Text>
          </div>
        ) : '-'
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看">
            <Button type="text" icon={<EyeOutlined />} onClick={() => handleView(record)} />
          </Tooltip>
          {['paid', 'processing'].includes(record.status) && (
            <Tooltip title="发货">
              <Button type="text" icon={<TruckOutlined />} onClick={() => handleShip(record)} />
            </Tooltip>
          )}
          {record.status === 'refunding' && (
            <Tooltip title="退款">
              <Button type="text" icon={<DollarOutlined />} onClick={() => handleRefund(record)} />
            </Tooltip>
          )}
          {record.status === 'shipped' && (
            <Tooltip title="确认收货">
              <Button type="text" icon={<CheckCircleOutlined />} onClick={() => handleConfirmReceipt(record)} style={{ color: '#00B42A' }} />
            </Tooltip>
          )}
          <Dropdown
            menu={{
              items: [
                { key: 'copy', icon: <CopyOutlined />, label: '复制订单号' },
                { key: 'print', icon: <PrinterOutlined />, label: '打印订单' },
                { key: 'message', icon: <MessageOutlined />, label: '联系客户' },
              ],
              onClick: ({ key }) => {
                if (key === 'copy') {
                  navigator.clipboard.writeText(record.orderNo);
                  message.success('订单号已复制');
                } else if (key === 'print') {
                  message.success('正在打印...');
                } else if (key === 'message') {
                  message.success('正在打开聊天窗口...');
                }
              },
            }}
            placement="bottomRight"
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  // 表格行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
    getCheckboxProps: (record) => ({
      disabled: !['pending', 'paid', 'processing'].includes(record.status),
    }),
  };

  return (
    <Spin spinning={loading} tip="加载订单中...">
      <div className="orders-page">
        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card bordered={false} className="stat-card">
              <Statistic
                title="待发货"
                value={stats.pendingShip}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#FF7D00' }}
              />
              <div style={{ marginTop: 8 }}>
                <Button type="link" size="small" style={{ padding: 0 }}>
                  去处理 →
                </Button>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card bordered={false} className="stat-card">
              <Statistic
                title="待处理退款"
                value={stats.pendingRefund}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#F53F3F' }}
              />
              <div style={{ marginTop: 8 }}>
                <Button type="link" size="small" style={{ padding: 0 }} danger>
                  去处理 →
                </Button>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card bordered={false} className="stat-card">
              <Statistic
                title="今日订单"
                value={stats.todayOrders}
                prefix={<ShoppingCartOutlined />}
                valueStyle={{ color: '#165DFF' }}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
                较昨日 +8.5%
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card bordered={false} className="stat-card">
              <Statistic
                title="今日营收"
                value={stats.todayRevenue}
                prefix={<DollarOutlined />}
                valueStyle={{ color: '#00B42A' }}
                formatter={(val) => `¥${Number(val).toLocaleString()}`}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
                较昨日 +12.3%
              </div>
            </Card>
          </Col>
        </Row>

        {/* 筛选区域 */}
        <Card bordered={false} style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]} align="middle">
            <Col flex="auto">
              <Space size="middle" wrap>
                <Input
                  placeholder="搜索订单号/客户"
                  prefix={<SearchOutlined />}
                  style={{ width: 220 }}
                  value={filters.keyword}
                  onChange={(e) => handleFilter({ keyword: e.target.value })}
                  allowClear
                />
                <Select
                  placeholder="平台"
                  style={{ width: 120 }}
                  value={filters.platform}
                  onChange={(val) => handleFilter({ platform: val })}
                >
                  <Option value="all">全部平台</Option>
                  <Option value="douyin">抖音</Option>
                  <Option value="pinduoduo">拼多多</Option>
                  <Option value="xianyu">闲鱼</Option>
                  <Option value="kuaishou">快手</Option>
                </Select>
                <Select
                  placeholder="状态"
                  style={{ width: 100 }}
                  value={filters.status}
                  onChange={(val) => handleFilter({ status: val })}
                >
                  <Option value="all">全部状态</Option>
                  <Option value="pending">待付款</Option>
                  <Option value="paid">待发货</Option>
                  <Option value="shipped">已发货</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="refunding">退款中</Option>
                </Select>
                <RangePicker
                  placeholder={['开始日期', '结束日期']}
                  value={filters.dateRange}
                  onChange={(val) => handleFilter({ dateRange: val })}
                />
                <Button icon={<ReloadOutlined />} onClick={() => { handleReset(); loadOrders(); }}>
                  刷新
                </Button>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button icon={<ExportOutlined />} onClick={handleExportCSV}>导出</Button>
                <Button icon={<PrinterOutlined />}>批量打印</Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 订单表格 */}
        <Card bordered={false}>
          {/* 标签页 */}
          <Tabs activeKey={activeTab} onChange={setActiveTab} style={{ marginBottom: 16 }}>
            <TabPane tab={`全部订单 (${orders.length})`} key="all" />
            <TabPane tab={`待付款 (${orders.filter(o => o.status === 'pending').length})`} key="pending" />
            <TabPane tab={`待发货 (${stats.pendingShip})`} key="paid" />
            <TabPane tab={`已发货 (${orders.filter(o => o.status === 'shipped').length})`} key="shipped" />
            <TabPane tab={`退款/售后 (${stats.pendingRefund})`} key="refund" />
          </Tabs>

          {/* 批量操作栏 */}
          {selectedRowKeys.length > 0 && (
            <div style={{
              marginBottom: 16,
              padding: '12px 16px',
              background: '#E6F7FF',
              borderRadius: 4,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <span>
                已选择 <Text strong>{selectedRowKeys.length}</Text> 个订单
              </span>
              <Space>
                <Button size="small" icon={<TruckOutlined />} onClick={handleBatchShip}>
                  批量发货
                </Button>
                <Button size="small" icon={<PrinterOutlined />}>
                  批量打印
                </Button>
                <Button size="small" type="link" onClick={() => setSelectedRowKeys([])}>
                  取消选择
                </Button>
              </Space>
            </div>
          )}

          {orders.length === 0 && !loading ? (
            <Empty
              description={
                <span>
                  暂无订单数据，请确认后端 <Text code>oms-service</Text> (port 8005) 已启动
                </span>
              }
            >
              <Button type="primary" icon={<SyncOutlined />} onClick={loadOrders}>
                重新加载
              </Button>
            </Empty>
          ) : (
            <Table
              columns={columns}
              dataSource={filteredOrders}
              rowKey="id"
              rowSelection={rowSelection}
              loading={loading}
              pagination={{
                total: filteredOrders.length,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条数据`,
              }}
              scroll={{ x: 1200 }}
            />
          )}
        </Card>

        {/* 订单详情抽屉 */}
        <Drawer
          title="订单详情"
          width={720}
          open={drawerVisible}
          onClose={() => setDrawerVisible(false)}
          extra={
            <Space>
              {['paid', 'processing'].includes(currentOrder?.status) && (
                <Button type="primary" onClick={() => {
                  setDrawerVisible(false);
                  handleShip(currentOrder);
                }}>
                  发货
                </Button>
              )}
              <Button onClick={() => setDrawerVisible(false)}>
                关闭
              </Button>
            </Space>
          }
        >
          {currentOrder && (
            <div>
              {/* 订单状态步骤条 */}
              {currentOrder.statusStep >= 0 ? (
                <Steps current={currentOrder.statusStep} size="small" style={{ marginBottom: 24 }}>
                  <Step title="待付款" />
                  <Step title="待发货" />
                  <Step title="已发货" />
                  <Step title="已完成" />
                </Steps>
              ) : (
                <div style={{
                  marginBottom: 24,
                  padding: 16,
                  background: '#FFF1F0',
                  borderRadius: 8,
                  textAlign: 'center',
                }}>
                  <Tag color={currentOrder.statusColor} style={{ fontSize: 14 }}>
                    {currentOrder.statusLabel}
                  </Tag>
                </div>
              )}

              <Descriptions title="订单信息" bordered column={2}>
                <Descriptions.Item label="订单号">{currentOrder.orderNo}</Descriptions.Item>
                <Descriptions.Item label="平台">
                  <Tag color={currentOrder.platformColor}>{currentOrder.platformName}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="订单状态">
                  <Tag color={currentOrder.statusColor}>{currentOrder.statusLabel}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="下单时间">
                  {new Date(currentOrder.createdAt).toLocaleString()}
                </Descriptions.Item>
                {currentOrder.paidAt && (
                  <Descriptions.Item label="付款时间">
                    {new Date(currentOrder.paidAt).toLocaleString()}
                  </Descriptions.Item>
                )}
                {currentOrder.shippedAt && (
                  <Descriptions.Item label="发货时间">
                    {new Date(currentOrder.shippedAt).toLocaleString()}
                  </Descriptions.Item>
                )}
              </Descriptions>

              <Divider />

              <Descriptions title="商品信息" bordered column={1}>
                <Descriptions.Item label="商品名称">{currentOrder.product}</Descriptions.Item>
                <Descriptions.Item label="数量">{currentOrder.quantity}</Descriptions.Item>
                <Descriptions.Item label="单价">¥{currentOrder.price.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="总价">
                  <Text strong style={{ color: '#165DFF', fontSize: 16 }}>
                    ¥{currentOrder.amount.toFixed(2)}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="利润">
                  <Text style={{ color: '#00B42A' }}>¥{currentOrder.profit.toFixed(2)}</Text>
                </Descriptions.Item>
              </Descriptions>

              <Divider />

              <Descriptions title="客户信息" bordered column={1}>
                <Descriptions.Item label="客户姓名">{currentOrder.customer}</Descriptions.Item>
                <Descriptions.Item label="联系电话">{currentOrder.phone}</Descriptions.Item>
                <Descriptions.Item label="收货地址">{currentOrder.address}</Descriptions.Item>
                {currentOrder.remark && (
                  <Descriptions.Item label="备注">{currentOrder.remark}</Descriptions.Item>
                )}
              </Descriptions>

              {currentOrder.logisticsNo && (
                <>
                  <Divider />
                  <Descriptions title="物流信息" bordered column={1}>
                    <Descriptions.Item label="物流公司">{currentOrder.logisticsCompany}</Descriptions.Item>
                    <Descriptions.Item label="物流单号">{currentOrder.logisticsNo}</Descriptions.Item>
                  </Descriptions>
                </>
              )}

              <Divider />

              <Title level={5}>订单日志</Title>
              <Timeline style={{ marginTop: 16 }}>
                <Timeline.Item color="green">
                  {new Date(currentOrder.createdAt).toLocaleString()} - 订单创建
                </Timeline.Item>
                {currentOrder.paidAt && (
                  <Timeline.Item color="green">
                    {new Date(currentOrder.paidAt).toLocaleString()} - 买家已付款
                  </Timeline.Item>
                )}
                {currentOrder.shippedAt && (
                  <Timeline.Item color="blue">
                    {new Date(currentOrder.shippedAt).toLocaleString()} - 卖家已发货
                  </Timeline.Item>
                )}
                {currentOrder.completedAt && (
                  <Timeline.Item color="green">
                    {new Date(currentOrder.completedAt).toLocaleString()} - 订单完成
                  </Timeline.Item>
                )}
              </Timeline>
            </div>
          )}
        </Drawer>
      </div>
    </Spin>
  );
};

export default Orders;
