import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Tag,
  Input,
  Select,
  Row,
  Col,
  Statistic,
  Dropdown,
  Modal,
  Drawer,
  Form,
  InputNumber,
  Upload,
  Image,
  Tooltip,
  Badge,
  Divider,
  Typography,
  message,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  ImportOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  MoreOutlined,
  ShoppingOutlined,
  WarningOutlined,
  RiseOutlined,
  DollarOutlined,
  UploadOutlined,
  SyncOutlined,
  CopyOutlined,
  QrcodeOutlined,
  AppstoreOutlined,
  FireOutlined,
  InboxOutlined,
  BarChartOutlined,
} from '@ant-design/icons';

const { Option } = Select;
const { Title, Text } = Typography;
const { TextArea } = Input;

// API 基础路径
const API_BASE = '/api';

// API 请求封装
const api = {
  async get(url, params = {}) {
    const query = new URLSearchParams(params).toString();
    const fullUrl = query ? `${API_BASE}${url}?${query}` : `${API_BASE}${url}`;
    const res = await fetch(fullUrl);
    if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`);
    return res.json();
  },
  async post(url, body = {}) {
    const res = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `POST ${url} failed: ${res.status}`);
    }
    return res.json();
  },
  async patch(url, body = {}) {
    const res = await fetch(`${API_BASE}${url}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `PATCH ${url} failed: ${res.status}`);
    }
    return res.json();
  },
  async delete(url) {
    const res = await fetch(`${API_BASE}${url}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`DELETE ${url} failed: ${res.status}`);
    return res.json();
  },
};

// 抖音店铺后台风格 - 样式常量
const styles = {
  page: {
    background: '#F2F3F5',
    minHeight: '100vh',
    padding: 0,
  },
  statCard: (gradient) => ({
    borderRadius: 8,
    border: 'none',
    background: gradient,
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    transition: 'all 0.3s ease',
    cursor: 'pointer',
    overflow: 'hidden',
    position: 'relative',
  }),
  statCardHover: {
    transform: 'translateY(-2px)',
    boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
  },
  statNumber: {
    fontSize: 28,
    fontWeight: 700,
    lineHeight: 1.2,
  },
  statTitle: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.85)',
    marginBottom: 8,
  },
  statSub: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.65)',
    marginTop: 8,
  },
  card: {
    borderRadius: 8,
    border: 'none',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  },
  filterCard: {
    borderRadius: 8,
    border: 'none',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    marginBottom: 16,
  },
  tableCard: {
    borderRadius: 8,
    border: 'none',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  },
  productImage: {
    borderRadius: 6,
    objectFit: 'cover',
    border: '1px solid #f0f0f0',
  },
  batchBar: {
    marginBottom: 16,
    padding: '12px 16px',
    background: '#E6F7FF',
    borderRadius: 6,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    border: '1px solid #91D5FF',
  },
};

// 统计卡片组件 - 渐变背景 + hover效果
const StatCard = ({ title, value, prefix, gradient, subText, formatter }) => {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      style={{
        ...styles.statCard(gradient),
        ...(hovered ? styles.statCardHover : {}),
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{ padding: 20 }}>
        <div style={styles.statTitle}>{title}</div>
        <div style={{ ...styles.statNumber, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
          {prefix && <span style={{ fontSize: 20, opacity: 0.9 }}>{prefix}</span>}
          {formatter ? formatter(value) : value}
        </div>
        {subText && <div style={styles.statSub}>{subText}</div>}
      </div>
      {/* 装饰圆形 */}
      <div style={{
        position: 'absolute',
        right: -20,
        top: -20,
        width: 80,
        height: 80,
        borderRadius: '50%',
        background: 'rgba(255,255,255,0.1)',
      }} />
      <div style={{
        position: 'absolute',
        right: 10,
        bottom: -30,
        width: 60,
        height: 60,
        borderRadius: '50%',
        background: 'rgba(255,255,255,0.06)',
      }} />
    </div>
  );
};

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [currentProduct, setCurrentProduct] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [batchPriceModalVisible, setBatchPriceModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [batchPriceForm] = Form.useForm();

  // 统计数据
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    lowStock: 0,
    outOfStock: 0,
    totalValue: 0,
  });

  // 分页
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // 筛选
  const [filters, setFilters] = useState({
    keyword: '',
    platform: 'all',
    category: 'all',
    status: 'all',
  });

  // ============================================================
  // 数据加载
  // ============================================================

  const fetchProducts = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (filters.keyword) params.keyword = filters.keyword;
      if (filters.platform !== 'all') params.platform = filters.platform;
      if (filters.category !== 'all') params.category = filters.category;
      if (filters.status !== 'all') params.status = filters.status;

      const res = await api.get('/products', params);
      if (res.success) {
        setProducts(res.data);
        setPagination({
          current: res.meta.page,
          pageSize: res.meta.page_size,
          total: res.meta.total,
        });
      }
    } catch (err) {
      console.error('加载商品列表失败:', err);
      message.error('加载商品列表失败，请检查服务是否启动');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get('/products/stats');
      if (res.success) {
        setStats(res.data);
      }
    } catch (err) {
      console.error('加载统计数据失败:', err);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    fetchProducts();
    fetchStats();
  }, []);

  // 筛选变化时重新加载
  useEffect(() => {
    fetchProducts(1, pagination.pageSize);
    setSelectedRowKeys([]);
  }, [filters]);

  // ============================================================
  // 筛选处理
  // ============================================================

  const handleFilter = (changedValues) => {
    setFilters(prev => ({ ...prev, ...changedValues }));
  };

  const handleReset = () => {
    setFilters({
      keyword: '',
      platform: 'all',
      category: 'all',
      status: 'all',
    });
  };

  // ============================================================
  // 商品操作
  // ============================================================

  // 查看商品详情
  const handleView = (product) => {
    setCurrentProduct(product);
    setDrawerVisible(true);
  };

  // 编辑商品
  const handleEdit = (product) => {
    setCurrentProduct(product);
    form.setFieldsValue({
      name: product.name,
      sku: product.sku,
      category: product.category,
      platform: product.platform,
      price: product.price,
      cost: product.cost,
      stock: product.stock,
      description: product.description || '',
    });
    setModalVisible(true);
  };

  // 删除商品
  const handleDelete = (product) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除商品"${product.name}"吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/products/${product.db_id}`);
          message.success('删除成功');
          fetchProducts(pagination.current, pagination.pageSize);
          fetchStats();
        } catch (err) {
          message.error('删除失败: ' + err.message);
        }
      },
    });
  };

  // 添加/编辑商品提交
  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (currentProduct) {
        // 编辑
        await api.patch(`/products/${currentProduct.db_id}`, values);
        message.success('更新成功');
      } else {
        // 新增
        await api.post('/products', values);
        message.success('添加成功');
      }
      setModalVisible(false);
      form.resetFields();
      fetchProducts(pagination.current, pagination.pageSize);
      fetchStats();
    } catch (err) {
      if (err.errorFields) return; // 表单验证失败
      message.error('操作失败: ' + err.message);
    }
  };

  // 批量操作
  const handleBatchAction = (action) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择商品');
      return;
    }
    const actionLabel = action === 'delete' ? '删除' : '下架';
    Modal.confirm({
      title: `确认${actionLabel}`,
      content: `确定要${actionLabel}选中的 ${selectedRowKeys.length} 个商品吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.post(`/products/batch/${action}`, { product_ids: selectedRowKeys, action });
          message.success(`${actionLabel}成功`);
          setSelectedRowKeys([]);
          fetchProducts(pagination.current, pagination.pageSize);
          fetchStats();
        } catch (err) {
          message.error(`${actionLabel}失败: ` + err.message);
        }
      },
    });
  };

  // 批量调价
  const handleBatchPriceAdjust = async () => {
    try {
      const values = await batchPriceForm.validateFields();
      if (selectedRowKeys.length === 0) {
        message.warning('请先选择商品');
        return;
      }
      await api.post('/products/batch/price', {
        product_ids: selectedRowKeys,
        adjust_type: values.adjustType,
        adjust_value: values.adjustValue,
      });
      setBatchPriceModalVisible(false);
      batchPriceForm.resetFields();
      setSelectedRowKeys([]);
      message.success(`已调整 ${selectedRowKeys.length} 个商品的价格`);
      fetchProducts(pagination.current, pagination.pageSize);
      fetchStats();
    } catch (err) {
      if (err.errorFields) return;
      message.error('调价失败: ' + err.message);
    }
  };

  // 表格翻页
  const handleTableChange = (pag) => {
    fetchProducts(pag.current, pag.pageSize);
  };

  // ============================================================
  // 表格列配置
  // ============================================================

  const columns = [
    {
      title: '商品信息',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      render: (text, record) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 56,
            height: 56,
            borderRadius: 6,
            overflow: 'hidden',
            flexShrink: 0,
            border: '1px solid #f0f0f0',
          }}>
            <Image
              src={record.image}
              width={56}
              height={56}
              style={{ objectFit: 'cover', display: 'block' }}
              preview={false}
              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNTYiIGhlaWdodD0iNTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjU2IiBoZWlnaHQ9IjU2IiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iMjgiIHk9IjMyIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjYmJiIiBmb250LXNpemU9IjEyIj7lm77niYw8L3RleHQ+PC9zdmc+"
            />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontWeight: 500,
              fontSize: 13,
              marginBottom: 4,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: '#1D2129',
            }}>
              {text}
            </div>
            <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>
              SKU: {record.sku}
            </div>
            <Tag
              color={record.platformColor}
              style={{ fontSize: 11, lineHeight: '18px', padding: '0 6px', borderRadius: 4 }}
            >
              {record.platformName}
            </Tag>
          </div>
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (text) => (
        <Tag style={{ borderRadius: 4, background: '#F2F3F5', border: 'none', color: '#4E5969' }}>
          {text}
        </Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      sorter: (a, b) => a.price - b.price,
      render: (val) => (
        <span style={{ fontWeight: 600, color: '#165DFF', fontSize: 13 }}>
          ¥{Number(val).toFixed(2)}
        </span>
      ),
    },
    {
      title: '成本',
      dataIndex: 'cost',
      key: 'cost',
      width: 100,
      render: (val) => <Text type="secondary" style={{ fontSize: 13 }}>¥{Number(val).toFixed(2)}</Text>,
    },
    {
      title: '利润率',
      dataIndex: 'margin',
      key: 'margin',
      width: 90,
      sorter: (a, b) => parseFloat(a.margin) - parseFloat(b.margin),
      render: (val) => {
        const v = parseFloat(val);
        const color = v > 40 ? '#00B42A' : v > 20 ? '#165DFF' : '#FF7D00';
        const bg = v > 40 ? '#E8FFEA' : v > 20 ? '#E8F3FF' : '#FFF7E8';
        return (
          <Tag style={{ borderRadius: 4, background: bg, border: 'none', color, fontWeight: 500 }}>
            {val}%
          </Tag>
        );
      },
    },
    {
      title: '库存',
      dataIndex: 'stock',
      key: 'stock',
      width: 100,
      sorter: (a, b) => a.stock - b.stock,
      render: (val) => (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            color: val === 0 ? '#F53F3F' : val < 20 ? '#FF7D00' : '#00B42A',
            fontWeight: 600,
            fontSize: 13,
          }}>
            {val}
          </span>
          {val === 0 && (
            <Tag style={{ borderRadius: 4, background: '#FFECE8', border: 'none', color: '#F53F3F', fontSize: 11, lineHeight: '18px', padding: '0 5px' }}>
              缺货
            </Tag>
          )}
          {val > 0 && val < 20 && (
            <Tag style={{ borderRadius: 4, background: '#FFF7E8', border: 'none', color: '#FF7D00', fontSize: 11, lineHeight: '18px', padding: '0 5px' }}>
              预警
            </Tag>
          )}
        </span>
      ),
    },
    {
      title: '销量',
      dataIndex: 'sales',
      key: 'sales',
      width: 80,
      sorter: (a, b) => a.sales - b.sales,
      render: (val) => (
        <span style={{ fontWeight: 500, color: '#1D2129' }}>{val}</span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'statusLabel',
      key: 'status',
      width: 80,
      render: (text, record) => {
        const colorMap = {
          active: { color: '#00B42A', bg: '#E8FFEA' },
          draft: { color: '#86909C', bg: '#F2F3F5' },
          out_of_stock: { color: '#F53F3F', bg: '#FFECE8' },
          disabled: { color: '#86909C', bg: '#F2F3F5' },
        };
        const c = colorMap[record.status] || colorMap.draft;
        return (
          <Tag style={{ borderRadius: 4, background: c.bg, border: 'none', color: c.color, fontWeight: 500 }}>
            {text}
          </Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      fixed: 'right',
      render: (_, record) => (
        <Space size={4}>
          <Tooltip title="查看">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
              style={{ color: '#165DFF' }}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              style={{ color: '#165DFF' }}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                { key: 'copy', icon: <CopyOutlined />, label: '复制商品' },
                { key: 'qrcode', icon: <QrcodeOutlined />, label: '生成二维码' },
                { type: 'divider' },
                { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true },
              ],
              onClick: ({ key }) => {
                if (key === 'delete') handleDelete(record);
                else if (key === 'copy') message.success('商品已复制');
                else if (key === 'qrcode') message.success('二维码已生成');
              },
            }}
            placement="bottomRight"
          >
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  // 表格行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
    selections: [
      Table.SELECTION_ALL,
      Table.SELECTION_INVERT,
      Table.SELECTION_NONE,
    ],
  };

  return (
    <div className="products-page" style={styles.page}>
      {/* 统计卡片 - 渐变背景 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="在售商品"
            value={stats.active}
            prefix={<ShoppingOutlined />}
            gradient="linear-gradient(135deg, #165DFF 0%, #4080FF 100%)"
            subText={`总计 ${stats.total} 个商品`}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="库存预警"
            value={stats.lowStock}
            prefix={<WarningOutlined />}
            gradient="linear-gradient(135deg, #FF7D00 0%, #FFB74D 100%)"
            subText={`缺货 ${stats.outOfStock} 个`}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="今日销量"
            value={Math.floor(Math.random() * 100)}
            prefix={<FireOutlined />}
            gradient="linear-gradient(135deg, #00B42A 0%, #52C41A 100%)"
            subText="较昨日 +12.5%"
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="库存总值"
            value={stats.totalValue}
            prefix={<DollarOutlined />}
            gradient="linear-gradient(135deg, #722ED1 0%, #B37FEB 100%)"
            subText="平均利润率 35.2%"
            formatter={(val) => `¥${Number(val).toLocaleString()}`}
          />
        </Col>
      </Row>

      {/* 筛选区域 */}
      <div style={styles.filterCard}>
        <div style={{ padding: '16px 20px' }}>
          <Row gutter={[16, 12]} align="middle">
            <Col flex="auto">
              <Space size={12} wrap>
                <Input
                  placeholder="搜索商品名称/SKU"
                  prefix={<SearchOutlined style={{ color: '#c9cdd4' }} />}
                  style={{ width: 240, borderRadius: 6 }}
                  value={filters.keyword}
                  onChange={(e) => handleFilter({ keyword: e.target.value })}
                  allowClear
                />
                <Select
                  placeholder="平台"
                  style={{ width: 120, borderRadius: 6 }}
                  value={filters.platform}
                  onChange={(val) => handleFilter({ platform: val })}
                >
                  <Option value="all">全部平台</Option>
                  <Option value="douyin">抖音</Option>
                  <Option value="pdd">拼多多</Option>
                  <Option value="xianyu">闲鱼</Option>
                  <Option value="kuaishou">快手</Option>
                </Select>
                <Select
                  placeholder="分类"
                  style={{ width: 120, borderRadius: 6 }}
                  value={filters.category}
                  onChange={(val) => handleFilter({ category: val })}
                >
                  <Option value="all">全部分类</Option>
                  <Option value="数码配件">数码配件</Option>
                  <Option value="家居日用">家居日用</Option>
                  <Option value="服饰鞋包">服饰鞋包</Option>
                  <Option value="美妆个护">美妆个护</Option>
                  <Option value="食品生鲜">食品生鲜</Option>
                  <Option value="办公用品">办公用品</Option>
                </Select>
                <Select
                  placeholder="状态"
                  style={{ width: 100, borderRadius: 6 }}
                  value={filters.status}
                  onChange={(val) => handleFilter({ status: val })}
                >
                  <Option value="all">全部状态</Option>
                  <Option value="active">在售</Option>
                  <Option value="draft">草稿</Option>
                  <Option value="out_of_stock">缺货</Option>
                  <Option value="disabled">已下架</Option>
                </Select>
                <Button icon={<ReloadOutlined />} onClick={handleReset} style={{ borderRadius: 6 }}>
                  重置
                </Button>
              </Space>
            </Col>
            <Col>
              <Space size={8}>
                <Button icon={<ImportOutlined />} style={{ borderRadius: 6 }}>导入</Button>
                <Button icon={<ExportOutlined />} style={{ borderRadius: 6 }}>导出</Button>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  style={{ borderRadius: 6, background: '#165DFF', boxShadow: '0 2px 0 rgba(22,93,255,0.1)' }}
                  onClick={() => {
                    setCurrentProduct(null);
                    form.resetFields();
                    setModalVisible(true);
                  }}
                >
                  添加商品
                </Button>
              </Space>
            </Col>
          </Row>
        </div>
      </div>

      {/* 商品表格 */}
      <div style={styles.tableCard}>
        <div style={{ padding: '16px 20px 20px' }}>
          {/* 批量操作栏 */}
          {selectedRowKeys.length > 0 && (
            <div style={styles.batchBar}>
              <span style={{ fontSize: 13, color: '#1D2129' }}>
                已选择 <Text strong style={{ color: '#165DFF' }}>{selectedRowKeys.length}</Text> 个商品
              </span>
              <Space size={8}>
                <Button size="small" style={{ borderRadius: 4 }} onClick={() => handleBatchAction('disable')}>
                  批量下架
                </Button>
                <Button size="small" style={{ borderRadius: 4 }} onClick={() => setBatchPriceModalVisible(true)}>
                  批量调价
                </Button>
                <Button size="small" danger style={{ borderRadius: 4 }} onClick={() => handleBatchAction('delete')}>
                  批量删除
                </Button>
                <Button size="small" type="link" onClick={() => setSelectedRowKeys([])}>
                  取消选择
                </Button>
              </Space>
            </div>
          )}

          <Table
            columns={columns}
            dataSource={products}
            rowKey="db_id"
            rowSelection={rowSelection}
            loading={loading}
            size="middle"
            pagination={{
              ...pagination,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => <span style={{ color: '#86909C' }}>共 {total} 条数据</span>,
              style: { marginTop: 16 },
            }}
            onChange={handleTableChange}
            scroll={{ x: 1200 }}
            rowClassName={(_, index) => index % 2 === 1 ? 'products-table-row-striped' : ''}
          />
        </div>
      </div>

      {/* 注入斑马纹样式 */}
      <style>{`
        .products-page .ant-table {
          border-radius: 8px;
          overflow: hidden;
        }
        .products-page .ant-table-thead > tr > th {
          background: #F7F8FA !important;
          font-weight: 600 !important;
          color: #1D2129 !important;
          font-size: 13px !important;
          padding: 12px 16px !important;
          border-bottom: 1px solid #E5E6EB !important;
        }
        .products-page .ant-table-tbody > tr > td {
          padding: 10px 16px !important;
          font-size: 13px !important;
          color: #4E5969 !important;
          border-bottom: 1px solid #F2F3F5 !important;
        }
        .products-table-row-striped > td {
          background: #FAFBFC !important;
        }
        .products-page .ant-table-tbody > tr:hover > td {
          background: #F2F3FF !important;
        }
        .products-page .ant-table-cell-row-hover {
          background: #F2F3FF !important;
        }
        .products-page .ant-pagination .ant-pagination-item-active {
          border-color: #165DFF !important;
        }
        .products-page .ant-pagination .ant-pagination-item-active a {
          color: #165DFF !important;
        }
      `}</style>

      {/* 商品详情抽屉 */}
      <Drawer
        title={
          <span style={{ fontSize: 15, fontWeight: 600, color: '#1D2129' }}>商品详情</span>
        }
        width={560}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        styles={{ header: { borderBottom: '1px solid #F2F3F5', padding: '16px 20px' }, body: { padding: 20 } }}
        extra={
          <Space size={8}>
            <Button onClick={() => {
              setDrawerVisible(false);
              if (currentProduct) handleEdit(currentProduct);
            }} style={{ borderRadius: 6 }}>
              编辑
            </Button>
            <Button type="primary" onClick={() => setDrawerVisible(false)} style={{ borderRadius: 6 }}>
              关闭
            </Button>
          </Space>
        }
      >
        {currentProduct && (
          <div>
            {/* 商品图片 */}
            <div style={{
              textAlign: 'center',
              marginBottom: 24,
              padding: 20,
              background: '#F7F8FA',
              borderRadius: 8,
            }}>
              <Image
                src={currentProduct.image}
                width={180}
                height={180}
                style={{ borderRadius: 8, objectFit: 'cover' }}
              />
            </div>

            {/* 商品名称和标签 */}
            <Title level={5} style={{ marginBottom: 12, color: '#1D2129' }}>
              {currentProduct.name}
            </Title>
            <div style={{ marginBottom: 20, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Tag color={currentProduct.platformColor} style={{ borderRadius: 4 }}>{currentProduct.platformName}</Tag>
              <Tag style={{ borderRadius: 4, background: '#F2F3F5', border: 'none', color: '#4E5969' }}>{currentProduct.category}</Tag>
              <Tag color={currentProduct.statusColor} style={{ borderRadius: 4 }}>{currentProduct.statusLabel}</Tag>
            </div>

            <Divider style={{ margin: '16px 0' }} />

            {/* 商品信息网格 */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 16,
              marginBottom: 20,
            }}>
              {[
                { label: 'SKU', value: currentProduct.sku, color: '#1D2129' },
                { label: '售价', value: `¥${Number(currentProduct.price).toFixed(2)}`, color: '#165DFF', fontWeight: 600 },
                { label: '成本', value: `¥${Number(currentProduct.cost).toFixed(2)}`, color: '#4E5969' },
                { label: '利润率', value: `${currentProduct.margin}%`, color: parseFloat(currentProduct.margin) > 40 ? '#00B42A' : '#FF7D00', fontWeight: 600 },
                { label: '库存', value: currentProduct.stock, color: currentProduct.stock < 20 ? '#FF7D00' : '#00B42A', fontWeight: 600 },
                { label: '销量', value: currentProduct.sales, color: '#1D2129' },
              ].map((item, idx) => (
                <div key={idx} style={{
                  padding: '12px 16px',
                  background: '#F7F8FA',
                  borderRadius: 8,
                }}>
                  <div style={{ fontSize: 12, color: '#86909C', marginBottom: 6 }}>{item.label}</div>
                  <div style={{ fontSize: 15, color: item.color, fontWeight: item.fontWeight || 400 }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>

            {/* 时间信息 */}
            <div style={{
              padding: '12px 16px',
              background: '#F7F8FA',
              borderRadius: 8,
            }}>
              <Row gutter={[16, 8]}>
                <Col span={12}>
                  <div style={{ fontSize: 12, color: '#86909C', marginBottom: 4 }}>创建时间</div>
                  <div style={{ fontSize: 13, color: '#4E5969' }}>{currentProduct.createdAt ? new Date(currentProduct.createdAt).toLocaleString() : '-'}</div>
                </Col>
                <Col span={12}>
                  <div style={{ fontSize: 12, color: '#86909C', marginBottom: 4 }}>更新时间</div>
                  <div style={{ fontSize: 13, color: '#4E5969' }}>{currentProduct.updatedAt ? new Date(currentProduct.updatedAt).toLocaleString() : '-'}</div>
                </Col>
              </Row>
            </div>
          </div>
        )}
      </Drawer>

      {/* 添加/编辑商品弹窗 */}
      <Modal
        title={
          <span style={{ fontSize: 15, fontWeight: 600, color: '#1D2129' }}>
            {currentProduct ? '编辑商品' : '添加商品'}
          </span>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleFormSubmit}
        width={600}
        okText="确定"
        cancelText="取消"
        okButtonProps={{ style: { background: '#165DFF', borderRadius: 6 } }}
        cancelButtonProps={{ style: { borderRadius: 6 } }}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="商品名称" rules={[{ required: true, message: '请输入商品名称' }]}>
                <Input placeholder="请输入商品名称" style={{ borderRadius: 6 }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="sku" label="SKU" rules={[{ required: true, message: '请输入SKU' }]}>
                <Input placeholder="请输入SKU" style={{ borderRadius: 6 }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="platform" label="平台" rules={[{ required: true, message: '请选择平台' }]}>
                <Select placeholder="请选择平台" style={{ borderRadius: 6 }}>
                  <Option value="douyin">抖音</Option>
                  <Option value="pdd">拼多多</Option>
                  <Option value="xianyu">闲鱼</Option>
                  <Option value="kuaishou">快手</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="category" label="分类" rules={[{ required: true, message: '请选择分类' }]}>
                <Select placeholder="请选择分类" style={{ borderRadius: 6 }}>
                  <Option value="数码配件">数码配件</Option>
                  <Option value="家居日用">家居日用</Option>
                  <Option value="服饰鞋包">服饰鞋包</Option>
                  <Option value="美妆个护">美妆个护</Option>
                  <Option value="食品生鲜">食品生鲜</Option>
                  <Option value="办公用品">办公用品</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="price" label="售价" rules={[{ required: true, message: '请输入售价' }]}>
                <InputNumber
                  style={{ width: '100%', borderRadius: 6 }}
                  min={0}
                  precision={2}
                  prefix="¥"
                  placeholder="请输入售价"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="cost" label="成本" rules={[{ required: true, message: '请输入成本' }]}>
                <InputNumber
                  style={{ width: '100%', borderRadius: 6 }}
                  min={0}
                  precision={2}
                  prefix="¥"
                  placeholder="请输入成本"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="stock" label="库存" rules={[{ required: true, message: '请输入库存' }]}>
                <InputNumber
                  style={{ width: '100%', borderRadius: 6 }}
                  min={0}
                  placeholder="请输入库存"
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="商品描述">
            <TextArea rows={4} placeholder="请输入商品描述" style={{ borderRadius: 6 }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量调价弹窗 */}
      <Modal
        title={
          <span style={{ fontSize: 15, fontWeight: 600, color: '#1D2129' }}>
            批量调价
          </span>
        }
        open={batchPriceModalVisible}
        onCancel={() => {
          setBatchPriceModalVisible(false);
          batchPriceForm.resetFields();
        }}
        onOk={handleBatchPriceAdjust}
        width={480}
        okText="确定调整"
        cancelText="取消"
        okButtonProps={{ style: { background: '#165DFF', borderRadius: 6 } }}
      >
        <div style={{
          marginBottom: 16,
          padding: '12px 16px',
          background: '#E6F7FF',
          borderRadius: 6,
          border: '1px solid #91D5FF',
        }}>
          <Text>将对选中的 <Text strong style={{ color: '#165DFF' }}>{selectedRowKeys.length}</Text> 个商品进行价格调整</Text>
        </div>
        <Form form={batchPriceForm} layout="vertical" initialValues={{ adjustType: 'increase_pct' }}>
          <Form.Item name="adjustType" label="调整方式" rules={[{ required: true, message: '请选择调整方式' }]}>
            <Select>
              <Option value="increase_pct">按百分比涨价</Option>
              <Option value="decrease_pct">按百分比降价</Option>
              <Option value="increase_amt">按金额涨价</Option>
              <Option value="decrease_amt">按金额降价</Option>
            </Select>
          </Form.Item>
          <Form.Item name="adjustValue" label="调整数值" rules={[{ required: true, message: '请输入调整数值' }]}>
            <InputNumber
              style={{ width: '100%', borderRadius: 6 }}
              min={0}
              precision={2}
              placeholder="请输入数值"
              addonAfter={"元 / %"}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Products;
