import React, { useState, useEffect, useCallback } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Space,
  Button,
  Input,
  Select,
  DatePicker,
  Avatar,
  Typography,
  Drawer,
  Descriptions,
  Tabs,
  Progress,
  Modal,
  Form,
  message,
  Divider,
  Badge,
  Tooltip,
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  EyeOutlined,
  MessageOutlined,
  TeamOutlined,
  CrownOutlined,
  StarOutlined,
  ShoppingCartOutlined,
  DollarOutlined,
  EnvironmentOutlined,
  ManOutlined,
  WomanOutlined,
  FilterOutlined,
  ExportOutlined,
  ImportOutlined,
  PhoneOutlined,
  MailOutlined,
  TagOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  fetchCustomerStats,
  fetchCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
} from '../../api';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

// 获取等级对应的图标和颜色
const getLevelInfo = (level) => {
  const levelMap = {
    '普通': { icon: <UserOutlined />, color: '#8c8c8c' },
    '银卡': { icon: <StarOutlined />, color: '#bfbfbf' },
    '金卡': { icon: <StarOutlined />, color: '#faad14' },
    '钻石': { icon: <CrownOutlined />, color: '#722ed1' },
  };
  return levelMap[level] || levelMap['普通'];
};

// 获取标签颜色
const getTagColor = (tag) => {
  const tagColors = {
    '新客户': 'blue',
    '活跃': 'green',
    '沉睡': 'orange',
    '流失': 'red',
    'VIP': 'purple',
    '高价值': 'gold',
  };
  return tagColors[tag] || 'default';
};

// 模拟订单数据（订单API暂未对接，保留mock）
const generateOrders = () => {
  const orders = [];
  for (let i = 1; i <= 10; i++) {
    orders.push({
      key: i,
      orderId: `ORD${String(i).padStart(8, '0')}`,
      amount: Math.floor(Math.random() * 2000) + 100,
      status: ['已完成', '待发货', '已发货', '已取消'][Math.floor(Math.random() * 4)],
      time: dayjs().subtract(Math.floor(Math.random() * 30), 'day').format('YYYY-MM-DD HH:mm'),
      products: Math.floor(Math.random() * 5) + 1,
    });
  }
  return orders;
};

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('add'); // 'add' | 'edit'
  const [form] = Form.useForm();
  const [orders] = useState(() => generateOrders());
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [batchTagModalVisible, setBatchTagModalVisible] = useState(false);
  const [batchTagForm] = Form.useForm();

  // 筛选状态
  const [filters, setFilters] = useState({
    keyword: '',
    level: undefined,
    dateRange: null,
  });

  // 分页状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  // 统计数据
  const [stats, setStats] = useState({
    total: 0,
    newCustomers: 0,
    activeCustomers: 0,
    vipCustomers: 0,
  });

  // 加载客户列表
  const loadCustomers = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (filters.keyword) params.keyword = filters.keyword;
      if (filters.level) params.level = filters.level;

      const result = await fetchCustomers(params);
      setCustomers(result.items || []);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: result.total || 0,
      }));
    } catch (err) {
      console.error('加载客户列表失败:', err);
      message.error('加载客户列表失败');
    } finally {
      setLoading(false);
    }
  }, [filters.keyword, filters.level]);

  // 加载统计数据
  const loadStats = async () => {
    try {
      const data = await fetchCustomerStats();
      setStats({
        total: data.total || 0,
        newCustomers: data.newCustomers || 0,
        activeCustomers: data.activeCustomers || 0,
        vipCustomers: data.vipCustomers || 0,
      });
    } catch (err) {
      console.error('加载统计失败:', err);
    }
  };

  useEffect(() => {
    loadCustomers();
    loadStats();
  }, []);

  // 处理筛选
  const handleFilter = () => {
    loadCustomers(1, pagination.pageSize);
  };

  // 重置筛选
  const handleReset = () => {
    setFilters({ keyword: '', level: undefined, dateRange: null });
    // 延迟一帧等状态更新后再加载
    setTimeout(() => {
      loadCustomers(1, pagination.pageSize);
    }, 0);
  };

  // 查看客户详情
  const handleView = (record) => {
    setSelectedCustomer(record);
    setDrawerVisible(true);
  };

  // 编辑客户
  const handleEdit = (record) => {
    setSelectedCustomer(record);
    setModalType('edit');
    form.setFieldsValue({
      name: record.name,
      phone: record.phone,
      email: record.email,
      gender: record.gender,
      level: record.level,
      address: record.address,
    });
    setModalVisible(true);
  };

  // 添加客户
  const handleAdd = () => {
    setSelectedCustomer(null);
    setModalType('add');
    form.resetFields();
    setModalVisible(true);
  };

  // 提交表单（调用真实API）
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (modalType === 'add') {
        const result = await createCustomer({
          name: values.name,
          phone: values.phone,
          email: values.email,
          gender: values.gender,
          level: values.level || '普通',
          address: values.address || '',
          tags: ['新客户'],
        });
        if (result.success) {
          message.success('客户添加成功');
          setModalVisible(false);
          form.resetFields();
          loadCustomers(pagination.current, pagination.pageSize);
          loadStats();
        } else {
          message.error(result.message || '添加失败');
        }
      } else {
        const result = await updateCustomer(selectedCustomer.db_id, {
          name: values.name,
          phone: values.phone,
          email: values.email,
          gender: values.gender,
          level: values.level,
          address: values.address,
        });
        if (result.success) {
          message.success('客户信息更新成功');
          setModalVisible(false);
          form.resetFields();
          loadCustomers(pagination.current, pagination.pageSize);
        } else {
          message.error(result.message || '更新失败');
        }
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 删除客户
  const handleDelete = (record) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除客户 "${record.name}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        const result = await deleteCustomer(record.db_id);
        if (result.success) {
          message.success('客户已删除');
          loadCustomers(pagination.current, pagination.pageSize);
          loadStats();
        } else {
          message.error(result.message || '删除失败');
        }
      },
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个客户吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        let success = 0;
        for (const dbId of selectedRowKeys) {
          const result = await deleteCustomer(dbId);
          if (result.success) success++;
        }
        message.success(`已删除 ${success} 个客户`);
        setSelectedRowKeys([]);
        loadCustomers(pagination.current, pagination.pageSize);
        loadStats();
      },
    });
  };

  // 发送消息
  const handleSendMessage = (record) => {
    message.info(`正在向 ${record.name} 发送消息...`);
  };

  // 表格列配置
  const columns = [
    {
      title: '客户信息',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      render: (text, record) => (
        <Space>
          <Avatar src={record.avatar} size={40} icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <PhoneOutlined style={{ marginRight: 4 }} />
              {record.phone}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '客户等级',
      dataIndex: 'level',
      key: 'level',
      width: 120,
      filters: [
        { text: '普通', value: '普通' },
        { text: '银卡', value: '银卡' },
        { text: '金卡', value: '金卡' },
        { text: '钻石', value: '钻石' },
      ],
      onFilter: (value, record) => record.level === value,
      render: (level) => {
        const levelInfo = getLevelInfo(level);
        return (
          <Tag icon={levelInfo.icon} color={levelInfo.color}>
            {level}
          </Tag>
        );
      },
    },
    {
      title: '消费统计',
      key: 'spending',
      width: 200,
      render: (_, record) => (
        <div>
          <div>
            <Text strong>¥{(record.totalSpent || 0).toLocaleString()}</Text>
            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
              {record.orderCount || 0}单
            </Text>
          </div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            最近: {record.lastOrderTime || '-'}
          </Text>
        </div>
      ),
      sorter: (a, b) => (a.totalSpent || 0) - (b.totalSpent || 0),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 150,
      render: (tags) => (
        <Space size={[0, 4]} wrap>
          {(tags || []).map((tag) => (
            <Tag key={tag} color={getTagColor(tag)}>
              {tag}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'registerTime',
      key: 'registerTime',
      width: 120,
      sorter: (a, b) => dayjs(a.registerTime || 0).unix() - dayjs(b.registerTime || 0).unix(),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button type="link" icon={<EyeOutlined />} onClick={() => handleView(record)}>
              查看
            </Button>
          </Tooltip>
          <Tooltip title="编辑客户">
            <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
              编辑
            </Button>
          </Tooltip>
          <Tooltip title="删除客户">
            <Button type="link" danger onClick={() => handleDelete(record)}>
              删除
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 订单表格列配置
  const orderColumns = [
    { title: '订单号', dataIndex: 'orderId', key: 'orderId' },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (val) => `¥${val.toLocaleString()}`,
    },
    { title: '商品数', dataIndex: 'products', key: 'products' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusColors = {
          '已完成': 'success',
          '待发货': 'warning',
          '已发货': 'processing',
          '已取消': 'default',
        };
        return <Badge status={statusColors[status]} text={status} />;
      },
    },
    { title: '下单时间', dataIndex: 'time', key: 'time' },
  ];

  // 分群分析计数
  const segmentCounts = {
    highValue: customers.filter(c => (c.totalSpent || 0) > 30000).length,
    active: customers.filter(c => (c.tags || []).includes('活跃')).length,
    sleeping: customers.filter(c => (c.tags || []).includes('沉睡')).length,
    churning: customers.filter(c => (c.tags || []).includes('流失')).length,
    newCustomers: customers.filter(c => (c.tags || []).includes('新客户')).length,
  };

  return (
    <div className="customers-page">
      {/* 页面标题 */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          <TeamOutlined style={{ marginRight: 8 }} />
          客户中心
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => { loadCustomers(); loadStats(); }}>
            刷新
          </Button>
          <Button icon={<ImportOutlined />}>导入</Button>
          <Button icon={<ExportOutlined />}>导出</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加客户
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="客户总数"
              value={stats.total}
              prefix={<TeamOutlined style={{ color: '#165DFF' }} />}
              valueStyle={{ color: '#165DFF' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="新增客户(30天)"
              value={stats.newCustomers}
              prefix={<UserOutlined style={{ color: '#00B42A' }} />}
              valueStyle={{ color: '#00B42A' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃客户"
              value={stats.activeCustomers}
              prefix={<ShoppingCartOutlined style={{ color: '#FF7D00' }} />}
              valueStyle={{ color: '#FF7D00' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="会员客户"
              value={stats.vipCustomers}
              prefix={<CrownOutlined style={{ color: '#722ED1' }} />}
              valueStyle={{ color: '#722ED1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 客户分群分析 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ fontSize: 14 }}>客户分群分析</Text>
        </div>
        <Row gutter={[16, 8]}>
          {[
            { label: '高价值客户', count: segmentCounts.highValue, color: '#722ED1', bg: '#F9F0FF', desc: '消费>3万' },
            { label: '活跃客户', count: segmentCounts.active, color: '#00B42A', bg: '#E8FFEA', desc: '近30天购买' },
            { label: '沉睡客户', count: segmentCounts.sleeping, color: '#FF7D00', bg: '#FFF7E8', desc: '需唤醒' },
            { label: '流失风险', count: segmentCounts.churning, color: '#F53F3F', bg: '#FFECE8', desc: '需挽回' },
            { label: '新客户', count: segmentCounts.newCustomers, color: '#165DFF', bg: '#E8F3FF', desc: '首次购买' },
          ].map((item, idx) => (
            <Col key={idx} xs={12} sm={8} md={4} lg={4} style={{ textAlign: 'center' }}>
              <div style={{
                padding: '16px 12px',
                background: item.bg,
                borderRadius: 8,
                cursor: 'pointer',
                transition: 'all 0.3s',
              }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: item.color }}>{item.count}</div>
                <div style={{ fontSize: 13, color: '#1D2129', marginTop: 4 }}>{item.label}</div>
                <div style={{ fontSize: 11, color: '#86909C', marginTop: 2 }}>{item.desc}</div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 筛选区域 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索客户姓名/手机号/ID"
              prefix={<SearchOutlined />}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              onPressEnter={handleFilter}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="客户等级"
              style={{ width: '100%' }}
              value={filters.level}
              onChange={(value) => setFilters({ ...filters, level: value })}
              allowClear
            >
              <Option value="普通">普通</Option>
              <Option value="银卡">银卡</Option>
              <Option value="金卡">金卡</Option>
              <Option value="钻石">钻石</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['注册开始时间', '注册结束时间']}
              value={filters.dateRange}
              onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <Button type="primary" icon={<FilterOutlined />} onClick={handleFilter}>
                筛选
              </Button>
              <Button onClick={handleReset}>重置</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 客户表格 */}
      <Card>
        {/* 批量操作栏 */}
        {selectedRowKeys.length > 0 && (
          <div style={{
            marginBottom: 16,
            padding: '12px 16px',
            background: '#E6F7FF',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            border: '1px solid #91D5FF',
          }}>
            <span style={{ fontSize: 13, color: '#1D2129' }}>
              已选择 <Text strong style={{ color: '#165DFF' }}>{selectedRowKeys.length}</Text> 个客户
            </span>
            <Space size={8}>
              <Button size="small" icon={<TagOutlined />} onClick={() => setBatchTagModalVisible(true)}>
                批量打标签
              </Button>
              <Button size="small" icon={<MessageOutlined />} onClick={() => {
                message.success(`已向 ${selectedRowKeys.length} 个客户发送消息`);
                setSelectedRowKeys([]);
              }}>
                批量发消息
              </Button>
              <Button size="small" danger onClick={handleBatchDelete}>
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
          dataSource={customers}
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
            selections: [Table.SELECTION_ALL, Table.SELECTION_INVERT, Table.SELECTION_NONE],
          }}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({ ...prev, current: page, pageSize }));
              loadCustomers(page, pageSize);
            },
          }}
          scroll={{ x: 1200 }}
          rowKey="db_id"
        />
      </Card>

      {/* 客户详情抽屉 */}
      <Drawer
        title="客户详情"
        width={720}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        extra={
          <Space>
            <Button onClick={() => { setDrawerVisible(false); handleEdit(selectedCustomer); }}>编辑</Button>
            <Button type="primary" onClick={() => handleSendMessage(selectedCustomer)}>
              发送消息
            </Button>
          </Space>
        }
      >
        {selectedCustomer && (
          <div>
            {/* 基本信息 */}
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Avatar src={selectedCustomer.avatar} size={80} icon={<UserOutlined />} />
              <Title level={4} style={{ marginTop: 16, marginBottom: 4 }}>
                {selectedCustomer.name}
                {selectedCustomer.gender === '男' ? (
                  <ManOutlined style={{ color: '#165DFF', marginLeft: 8 }} />
                ) : selectedCustomer.gender === '女' ? (
                  <WomanOutlined style={{ color: '#F53F3F', marginLeft: 8 }} />
                ) : null}
              </Title>
              <Space size={[0, 8]} wrap style={{ marginTop: 8 }}>
                {(selectedCustomer.tags || []).map((tag) => (
                  <Tag key={tag} color={getTagColor(tag)}>
                    {tag}
                  </Tag>
                ))}
              </Space>
            </div>

            <Divider />

            <Tabs defaultActiveKey="1">
              <TabPane tab="基本信息" key="1">
                <Descriptions column={2} bordered>
                  <Descriptions.Item label="客户ID">{selectedCustomer.id}</Descriptions.Item>
                  <Descriptions.Item label="客户等级">
                    <Tag icon={getLevelInfo(selectedCustomer.level).icon} color={getLevelInfo(selectedCustomer.level).color}>
                      {selectedCustomer.level}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="手机号">{selectedCustomer.phone}</Descriptions.Item>
                  <Descriptions.Item label="邮箱">{selectedCustomer.email}</Descriptions.Item>
                  <Descriptions.Item label="注册时间">{selectedCustomer.registerTime}</Descriptions.Item>
                  <Descriptions.Item label="积分">{selectedCustomer.points}</Descriptions.Item>
                  <Descriptions.Item label="地址" span={2}>
                    <EnvironmentOutlined style={{ marginRight: 8 }} />
                    {selectedCustomer.address || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="账户余额" span={2}>
                    <Text strong style={{ color: '#165DFF' }}>
                      ¥{(selectedCustomer.balance || 0).toLocaleString()}
                    </Text>
                  </Descriptions.Item>
                </Descriptions>
              </TabPane>

              <TabPane tab="消费统计" key="2">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card>
                      <Statistic
                        title="消费总额"
                        value={selectedCustomer.totalSpent || 0}
                        prefix={<DollarOutlined style={{ color: '#165DFF' }} />}
                        suffix="元"
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card>
                      <Statistic
                        title="订单总数"
                        value={selectedCustomer.orderCount || 0}
                        prefix={<ShoppingCartOutlined style={{ color: '#00B42A' }} />}
                        suffix="单"
                      />
                    </Card>
                  </Col>
                </Row>
                <Card style={{ marginTop: 16 }}>
                  <div style={{ marginBottom: 16 }}>
                    <Text>消费等级进度</Text>
                  </div>
                  <Progress
                    percent={Math.min(((selectedCustomer.totalSpent || 0) / 50000) * 100, 100)}
                    status="active"
                    strokeColor={{
                      '0%': '#165DFF',
                      '100%': '#722ED1',
                    }}
                  />
                  <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">当前: ¥{(selectedCustomer.totalSpent || 0).toLocaleString()}</Text>
                    <Text type="secondary">目标: ¥50,000</Text>
                  </div>
                </Card>
              </TabPane>

              <TabPane tab="订单记录" key="3">
                <Table
                  columns={orderColumns}
                  dataSource={orders}
                  pagination={false}
                  size="small"
                  rowKey="key"
                />
              </TabPane>

              <TabPane tab="标签管理" key="4">
                <div style={{ marginBottom: 16 }}>
                  <Text strong>当前标签</Text>
                  <div style={{ marginTop: 8 }}>
                    <Space size={[0, 8]} wrap>
                      {(selectedCustomer.tags || []).map((tag) => (
                        <Tag
                          key={tag}
                          color={getTagColor(tag)}
                          closable
                          onClose={async () => {
                            const newTags = (selectedCustomer.tags || []).filter((t) => t !== tag);
                            const result = await updateCustomer(selectedCustomer.db_id, { tags: newTags });
                            if (result.success) {
                              setSelectedCustomer({ ...selectedCustomer, tags: newTags });
                              loadCustomers(pagination.current, pagination.pageSize);
                              message.success('标签已更新');
                            }
                          }}
                        >
                          {tag}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                </div>
                <Divider />
                <div>
                  <Text strong>添加标签</Text>
                  <div style={{ marginTop: 8 }}>
                    <Space size={[0, 8]} wrap>
                      {['新客户', '活跃', '沉睡', '流失', 'VIP', '高价值'].map((tag) => (
                        <Tag
                          key={tag}
                          style={{ cursor: 'pointer' }}
                          onClick={async () => {
                            if (!(selectedCustomer.tags || []).includes(tag)) {
                              const newTags = [...(selectedCustomer.tags || []), tag];
                              const result = await updateCustomer(selectedCustomer.db_id, { tags: newTags });
                              if (result.success) {
                                setSelectedCustomer({ ...selectedCustomer, tags: newTags });
                                loadCustomers(pagination.current, pagination.pageSize);
                                message.success('标签已添加');
                              }
                            }
                          }}
                        >
                          + {tag}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                </div>
              </TabPane>
            </Tabs>
          </div>
        )}
      </Drawer>

      {/* 添加/编辑客户弹窗 */}
      <Modal
        title={modalType === 'add' ? '添加客户' : '编辑客户'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        width={640}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="客户姓名"
                rules={[{ required: true, message: '请输入客户姓名' }]}
              >
                <Input placeholder="请输入客户姓名" prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
                ]}
              >
                <Input placeholder="请输入手机号" prefix={<PhoneOutlined />} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[{ type: 'email', message: '请输入正确的邮箱格式' }]}
              >
                <Input placeholder="请输入邮箱" prefix={<MailOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="gender" label="性别">
                <Select placeholder="请选择性别">
                  <Option value="男">男</Option>
                  <Option value="女">女</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="level" label="客户等级">
                <Select placeholder="请选择客户等级">
                  <Option value="普通">普通</Option>
                  <Option value="银卡">银卡</Option>
                  <Option value="金卡">金卡</Option>
                  <Option value="钻石">钻石</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="address" label="地址">
            <Input.TextArea rows={2} placeholder="请输入详细地址" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量打标签弹窗 */}
      <Modal
        title="批量打标签"
        open={batchTagModalVisible}
        onOk={async () => {
          const selectedTags = batchTagForm.getFieldValue('tags') || [];
          if (selectedTags.length === 0) {
            message.warning('请至少选择一个标签');
            return;
          }
          let success = 0;
          for (const dbId of selectedRowKeys) {
            const customer = customers.find(c => c.db_id === dbId);
            if (!customer) continue;
            const newTags = [...new Set([...(customer.tags || []), ...selectedTags])];
            const result = await updateCustomer(dbId, { tags: newTags });
            if (result.success) success++;
          }
          setBatchTagModalVisible(false);
          batchTagForm.resetFields();
          setSelectedRowKeys([]);
          message.success(`已为 ${success} 个客户添加标签`);
          loadCustomers(pagination.current, pagination.pageSize);
        }}
        onCancel={() => {
          setBatchTagModalVisible(false);
          batchTagForm.resetFields();
        }}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <Text>为选中的 <Text strong style={{ color: '#165DFF' }}>{selectedRowKeys.length}</Text> 个客户添加标签：</Text>
        </div>
        <Form form={batchTagForm} layout="vertical">
          <Form.Item name="tags" label="选择标签">
            <Select mode="multiple" placeholder="请选择标签" style={{ width: '100%' }}>
              <Option value="新客户">新客户</Option>
              <Option value="活跃">活跃</Option>
              <Option value="沉睡">沉睡</Option>
              <Option value="流失">流失</Option>
              <Option value="VIP">VIP</Option>
              <Option value="高价值">高价值</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
