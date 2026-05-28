import React, { useState, useEffect, useCallback } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Tabs,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  Switch,
  Typography,
  Divider,
  message,
  Popconfirm,
  Tooltip,
  Badge,
  Progress,
  Avatar,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SendOutlined,
  StopOutlined,
  PlayCircleOutlined,
  GiftOutlined,
  TeamOutlined,
  DollarOutlined,
  PercentageOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  FilterOutlined,
  CopyOutlined,
  EyeOutlined,
  SettingOutlined,
  FireOutlined,
  ThunderboltOutlined,
  CrownOutlined,
  UserOutlined,
  ShopOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  fetchMarketingStats,
  fetchCoupons,
  createCoupon,
  updateCoupon,
  deleteCoupon,
  fetchCampaigns,
  createCampaign,
  deleteCampaign,
  fetchDistributors,
  fetchCommissionSettings,
  saveCommissionSettings,
} from '../../api';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

export default function Marketing() {
  const [activeTab, setActiveTab] = useState('coupons');
  const [coupons, setCoupons] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [distributors, setDistributors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  // 统计数据
  const [stats, setStats] = useState({
    activeCampaigns: 0,
    totalCoupons: 0,
    marketingRevenue: 0,
    roi: 0,
  });

  // 佣金设置
  const [commissionSettings, setCommissionSettings] = useState(null);

  // 优惠券弹窗
  const [couponModalVisible, setCouponModalVisible] = useState(false);
  const [couponModalType, setCouponModalType] = useState('create');
  const [editingCoupon, setEditingCoupon] = useState(null);
  const [couponForm] = Form.useForm();

  // 活动弹窗
  const [campaignModalVisible, setCampaignModalVisible] = useState(false);
  const [campaignForm] = Form.useForm();

  // 佣金设置抽屉
  const [commissionDrawerVisible, setCommissionDrawerVisible] = useState(false);
  const [commissionForm] = Form.useForm();

  // 加载所有数据
  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, couponsRes, campaignsRes, distributorsRes] = await Promise.all([
        fetchMarketingStats(),
        fetchCoupons(),
        fetchCampaigns(),
        fetchDistributors(),
      ]);
      setStats({
        activeCampaigns: statsRes.activeCampaigns || 0,
        totalCoupons: statsRes.totalCoupons || 0,
        marketingRevenue: statsRes.marketingRevenue || 0,
        roi: statsRes.roi || 0,
      });
      setCoupons(couponsRes.items || []);
      setCampaigns(campaignsRes.items || []);
      setDistributors(distributorsRes.items || []);
    } catch (err) {
      console.error('加载营销数据失败:', err);
      message.error('加载营销数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // 创建/编辑优惠券
  const handleCouponSubmit = async () => {
    try {
      const values = await couponForm.validateFields();
      setSubmitting(true);
      const payload = {
        ...values,
        startTime: values.dateRange[0].format('YYYY-MM-DD'),
        endTime: values.dateRange[1].format('YYYY-MM-DD'),
      };
      delete payload.dateRange;

      if (couponModalType === 'create') {
        const result = await createCoupon(payload);
        if (result.success !== false) {
          message.success('优惠券创建成功');
          setCouponModalVisible(false);
          couponForm.resetFields();
          // 重新加载列表
          const res = await fetchCoupons();
          setCoupons(res.items || []);
          // 刷新统计
          const statsRes = await fetchMarketingStats();
          setStats(prev => ({ ...prev, totalCoupons: statsRes.totalCoupons || prev.totalCoupons }));
        } else {
          message.error(result.message || '创建失败');
        }
      } else {
        const result = await updateCoupon(editingCoupon.id, payload);
        if (result.success !== false) {
          message.success('优惠券更新成功');
          setCouponModalVisible(false);
          couponForm.resetFields();
          const res = await fetchCoupons();
          setCoupons(res.items || []);
        } else {
          message.error(result.message || '更新失败');
        }
      }
    } catch (err) {
      if (err.errorFields) return; // form validation
      console.error('优惠券操作失败:', err);
      message.error('操作失败，请重试');
    } finally {
      setSubmitting(false);
    }
  };

  // 编辑优惠券
  const handleEditCoupon = (record) => {
    setCouponModalType('edit');
    setEditingCoupon(record);
    couponForm.setFieldsValue({
      ...record,
      dateRange: [dayjs(record.startTime), dayjs(record.endTime)],
    });
    setCouponModalVisible(true);
  };

  // 删除优惠券
  const handleDeleteCoupon = async (id) => {
    try {
      const result = await deleteCoupon(id);
      if (result.success !== false) {
        message.success('优惠券已删除');
        setCoupons(prev => prev.filter(c => c.id !== id));
      } else {
        message.error(result.message || '删除失败');
      }
    } catch (err) {
      message.error('删除失败，请重试');
    }
  };

  // 批量发放
  const handleBatchSend = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要发放的优惠券');
      return;
    }
    message.success(`已发放 ${selectedRowKeys.length} 张优惠券`);
    setSelectedRowKeys([]);
  };

  // 批量停用
  const handleBatchStop = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要停用的优惠券');
      return;
    }
    let success = 0;
    for (const id of selectedRowKeys) {
      const result = await updateCoupon(id, { status: 'stopped' });
      if (result.success !== false) success++;
    }
    message.success(`已停用 ${success} 张优惠券`);
    setSelectedRowKeys([]);
    const res = await fetchCoupons();
    setCoupons(res.items || []);
  };

  // 创建活动
  const handleCampaignSubmit = async () => {
    try {
      const values = await campaignForm.validateFields();
      setSubmitting(true);
      const payload = {
        ...values,
        startTime: values.dateRange[0].format('YYYY-MM-DD'),
        endTime: values.dateRange[1].format('YYYY-MM-DD'),
      };
      delete payload.dateRange;

      const result = await createCampaign(payload);
      if (result.success !== false) {
        message.success('活动创建成功');
        setCampaignModalVisible(false);
        campaignForm.resetFields();
        const res = await fetchCampaigns();
        setCampaigns(res.items || []);
      } else {
        message.error(result.message || '创建失败');
      }
    } catch (err) {
      if (err.errorFields) return;
      console.error('活动创建失败:', err);
      message.error('创建失败，请重试');
    } finally {
      setSubmitting(false);
    }
  };

  // 删除活动
  const handleDeleteCampaign = async (id) => {
    try {
      const result = await deleteCampaign(id);
      if (result.success !== false) {
        message.success('活动已删除');
        setCampaigns(prev => prev.filter(c => c.id !== id));
      }
    } catch (err) {
      message.error('删除失败');
    }
  };

  // 加载佣金设置
  const loadCommissionSettings = async () => {
    try {
      const data = await fetchCommissionSettings();
      setCommissionSettings(data);
      commissionForm.setFieldsValue(data);
    } catch (err) {
      console.error('加载佣金设置失败:', err);
    }
  };

  // 保存佣金设置
  const handleSaveCommission = async () => {
    try {
      const values = await commissionForm.validateFields();
      setSubmitting(true);
      const result = await saveCommissionSettings(values);
      if (result.success !== false) {
        message.success('佣金设置已保存');
        setCommissionDrawerVisible(false);
      } else {
        message.error(result.message || '保存失败');
      }
    } catch (err) {
      if (err.errorFields) return;
      message.error('保存失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 优惠券表格列
  const couponColumns = [
    {
      title: '优惠券名称',
      dataIndex: 'name',
      key: 'name',
      render: (text) => (
        <Space>
          <GiftOutlined style={{ color: '#165DFF' }} />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const colorMap = { '满减券': 'blue', '折扣券': 'green', '无门槛券': 'orange' };
        return <Tag color={colorMap[type]}>{type}</Tag>;
      },
    },
    {
      title: '面值',
      dataIndex: 'discount',
      key: 'discount',
      render: (val, record) => (
        <Text strong style={{ color: '#F53F3F', fontSize: 16 }}>
          {record.type === '折扣券' ? `${val / 10}折` : `¥${val}`}
        </Text>
      ),
    },
    { title: '使用条件', dataIndex: 'condition', key: 'condition' },
    {
      title: '发放量',
      dataIndex: 'total',
      key: 'total',
      render: (val) => val.toLocaleString(),
      sorter: (a, b) => a.total - b.total,
    },
    {
      title: '已使用',
      dataIndex: 'used',
      key: 'used',
      render: (val, record) => (
        <Space direction="vertical" size={0}>
          <Text>{val.toLocaleString()}</Text>
          <Progress
            percent={Math.round((val / record.total) * 100)}
            size="small"
            showInfo={false}
            strokeColor="#165DFF"
          />
        </Space>
      ),
      sorter: (a, b) => a.used - b.used,
    },
    {
      title: '有效期',
      key: 'period',
      render: (_, record) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {record.startTime} ~ {record.endTime}
        </Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          active: { color: 'success', text: '进行中', icon: <CheckCircleOutlined /> },
          expired: { color: 'default', text: '已过期', icon: <ClockCircleOutlined /> },
          stopped: { color: 'error', text: '已停用', icon: <StopOutlined /> },
        };
        const config = statusMap[status] || statusMap.active;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button type="link" icon={<EditOutlined />} onClick={() => handleEditCoupon(record)} size="small" />
          </Tooltip>
          <Tooltip title="复制">
            <Button type="link" icon={<CopyOutlined />} size="small" onClick={() => {
              couponForm.setFieldsValue({
                ...record,
                name: `${record.name}(副本)`,
                dateRange: [dayjs(record.startTime), dayjs(record.endTime)],
              });
              setCouponModalType('create');
              setEditingCoupon(null);
              setCouponModalVisible(true);
            }} />
          </Tooltip>
          <Popconfirm
            title="确定要删除这张优惠券吗？"
            onConfirm={() => handleDeleteCoupon(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="link" danger icon={<DeleteOutlined />} size="small" />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 活动表格列
  const campaignColumns = [
    {
      title: '活动名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <ThunderboltOutlined style={{ color: '#FF7D00' }} />
          <div>
            <Text strong>{text}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.startTime} ~ {record.endTime}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const colorMap = {
          '满减活动': 'blue', '折扣活动': 'green',
          '秒杀活动': 'red', '新品活动': 'purple',
        };
        return <Tag color={colorMap[type]}>{type}</Tag>;
      },
    },
    {
      title: '参与商品',
      dataIndex: 'products',
      key: 'products',
      render: (val) => `${val} 件`,
      sorter: (a, b) => a.products - b.products,
    },
    {
      title: '销量',
      dataIndex: 'sales',
      key: 'sales',
      render: (val) => val.toLocaleString(),
      sorter: (a, b) => a.sales - b.sales,
    },
    {
      title: '营销收入',
      dataIndex: 'revenue',
      key: 'revenue',
      render: (val) => (
        <Text strong style={{ color: '#00B42A' }}>¥{val.toLocaleString()}</Text>
      ),
      sorter: (a, b) => a.revenue - b.revenue,
    },
    {
      title: '参与人数',
      dataIndex: 'participants',
      key: 'participants',
      render: (val) => val.toLocaleString(),
      sorter: (a, b) => a.participants - b.participants,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          ongoing: { color: 'processing', text: '进行中' },
          pending: { color: 'warning', text: '待开始' },
          ended: { color: 'default', text: '已结束' },
        };
        const config = statusMap[status] || statusMap.pending;
        return <Badge status={config.color} text={config.text} />;
      },
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button type="link" icon={<EyeOutlined />} size="small" />
          </Tooltip>
          <Tooltip title="编辑">
            <Button type="link" icon={<EditOutlined />} size="small" />
          </Tooltip>
          {record.status === 'pending' && (
            <Popconfirm title="确定要删除这个活动吗？" onConfirm={() => handleDeleteCampaign(record.id)}>
              <Tooltip title="删除">
                <Button type="link" danger icon={<DeleteOutlined />} size="small" />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 分销员表格列
  const distributorColumns = [
    {
      title: '分销员',
      key: 'distributor',
      render: (_, record) => (
        <Space>
          <Avatar
            style={{
              backgroundColor:
                record.level === '金牌分销员' ? '#FFD700'
                : record.level === '银牌分销员' ? '#C0C0C0'
                : '#CD7F32',
            }}
            icon={<UserOutlined />}
          />
          <div>
            <Text strong>{record.name}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>{record.phone}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '等级',
      dataIndex: 'level',
      key: 'level',
      render: (level) => {
        const colorMap = { '金牌分销员': 'gold', '银牌分销员': 'default', '铜牌分销员': 'orange' };
        return <Tag color={colorMap[level]} icon={<CrownOutlined />}>{level}</Tag>;
      },
    },
    {
      title: '销售额',
      dataIndex: 'sales',
      key: 'sales',
      render: (val) => <Text strong style={{ color: '#165DFF' }}>¥{val.toLocaleString()}</Text>,
      sorter: (a, b) => a.sales - b.sales,
    },
    {
      title: '订单数',
      dataIndex: 'orders',
      key: 'orders',
      render: (val) => val.toLocaleString(),
      sorter: (a, b) => a.orders - b.orders,
    },
    {
      title: '佣金',
      dataIndex: 'commission',
      key: 'commission',
      render: (val) => <Text strong style={{ color: '#00B42A' }}>¥{val.toLocaleString()}</Text>,
      sorter: (a, b) => a.commission - b.commission,
    },
    { title: '加入时间', dataIndex: 'joinDate', key: 'joinDate' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Badge
          status={status === 'active' ? 'success' : 'default'}
          text={status === 'active' ? '活跃' : '停用'}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 120,
      render: () => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button type="link" icon={<EyeOutlined />} size="small" />
          </Tooltip>
          <Tooltip title="编辑">
            <Button type="link" icon={<EditOutlined />} size="small" />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 统计卡片数据（来自API）
  const statsData = [
    {
      title: '进行中活动',
      value: stats.activeCampaigns,
      icon: <FireOutlined />,
      color: '#FF7D00',
      suffix: '个',
    },
    {
      title: '优惠券发放量',
      value: stats.totalCoupons,
      icon: <GiftOutlined />,
      color: '#165DFF',
      suffix: '张',
    },
    {
      title: '营销收入',
      value: stats.marketingRevenue,
      icon: <DollarOutlined />,
      color: '#00B42A',
      suffix: '元',
      precision: 0,
    },
    {
      title: 'ROI',
      value: stats.roi,
      icon: <PercentageOutlined />,
      color: '#722ED1',
      suffix: '',
      precision: 1,
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  return (
    <Spin spinning={loading && coupons.length === 0}>
      <div className="marketing-page">
        {/* 页面标题 */}
        <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              <ShopOutlined style={{ marginRight: 8, color: '#165DFF' }} />
              营销中心
            </Title>
            <Text type="secondary">管理优惠券、促销活动和分销体系</Text>
          </div>
          <Button icon={<ReloadOutlined />} onClick={loadAllData}>刷新</Button>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {statsData.map((stat, index) => (
            <Col xs={24} sm={12} md={6} key={index}>
              <Card hoverable style={{ borderRadius: 8 }} bodyStyle={{ padding: '20px 24px' }}>
                <Statistic
                  title={
                    <Space>
                      <span style={{
                        width: 32, height: 32, borderRadius: 8,
                        backgroundColor: `${stat.color}15`,
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        color: stat.color,
                      }}>
                        {stat.icon}
                      </span>
                      <span>{stat.title}</span>
                    </Space>
                  }
                  value={stat.value}
                  precision={stat.precision}
                  valueStyle={{ color: stat.color, fontSize: 28 }}
                  suffix={stat.suffix}
                />
              </Card>
            </Col>
          ))}
        </Row>

        {/* 主要内容区域 */}
        <Card style={{ borderRadius: 8 }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            tabBarExtraContent={
              <Space>
                {activeTab === 'coupons' && (
                  <>
                    <Button
                      icon={<SendOutlined />}
                      onClick={handleBatchSend}
                      disabled={selectedRowKeys.length === 0}
                    >
                      批量发放
                    </Button>
                    <Button
                      icon={<StopOutlined />}
                      onClick={handleBatchStop}
                      disabled={selectedRowKeys.length === 0}
                    >
                      批量停用
                    </Button>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => {
                        setCouponModalType('create');
                        setEditingCoupon(null);
                        couponForm.resetFields();
                        setCouponModalVisible(true);
                      }}
                      style={{ backgroundColor: '#165DFF' }}
                    >
                      创建优惠券
                    </Button>
                  </>
                )}
                {activeTab === 'campaigns' && (
                  <>
                    <Button icon={<FilterOutlined />}>筛选</Button>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => {
                        campaignForm.resetFields();
                        setCampaignModalVisible(true);
                      }}
                      style={{ backgroundColor: '#165DFF' }}
                    >
                      创建活动
                    </Button>
                  </>
                )}
                {activeTab === 'distributors' && (
                  <>
                    <Button icon={<SettingOutlined />} onClick={() => {
                      loadCommissionSettings();
                      setCommissionDrawerVisible(true);
                    }}>
                      佣金设置
                    </Button>
                    <Button type="primary" icon={<PlusOutlined />} style={{ backgroundColor: '#165DFF' }}>
                      添加分销员
                    </Button>
                  </>
                )}
              </Space>
            }
          >
            {/* 优惠券管理 */}
            <TabPane tab={<span><GiftOutlined /> 优惠券管理</span>} key="coupons">
              <Table
                columns={couponColumns}
                dataSource={coupons}
                rowKey="id"
                rowSelection={rowSelection}
                loading={loading}
                pagination={{
                  total: coupons.length,
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条`,
                }}
                scroll={{ x: 1200 }}
              />
            </TabPane>

            {/* 促销活动 */}
            <TabPane tab={<span><ThunderboltOutlined /> 促销活动</span>} key="campaigns">
              <Table
                columns={campaignColumns}
                dataSource={campaigns}
                rowKey="id"
                loading={loading}
                pagination={{
                  total: campaigns.length,
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条`,
                }}
                scroll={{ x: 1200 }}
              />
            </TabPane>

            {/* 分销管理 */}
            <TabPane tab={<span><TeamOutlined /> 分销管理</span>} key="distributors">
              <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                <Col xs={24} sm={8}>
                  <Card size="small" style={{ borderRadius: 8 }}>
                    <Statistic
                      title="分销员总数"
                      value={distributors.length}
                      prefix={<TeamOutlined style={{ color: '#165DFF' }} />}
                      suffix="人"
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={8}>
                  <Card size="small" style={{ borderRadius: 8 }}>
                    <Statistic
                      title="本月分销额"
                      value={distributors.reduce((sum, d) => sum + (d.sales || 0), 0)}
                      precision={0}
                      prefix={<DollarOutlined style={{ color: '#00B42A' }} />}
                      suffix="元"
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={8}>
                  <Card size="small" style={{ borderRadius: 8 }}>
                    <Statistic
                      title="本月佣金支出"
                      value={distributors.reduce((sum, d) => sum + (d.commission || 0), 0)}
                      precision={0}
                      prefix={<PercentageOutlined style={{ color: '#FF7D00' }} />}
                      suffix="元"
                    />
                  </Card>
                </Col>
              </Row>

              <Table
                columns={distributorColumns}
                dataSource={distributors}
                rowKey="id"
                loading={loading}
                pagination={{
                  total: distributors.length,
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条`,
                }}
                scroll={{ x: 1000 }}
              />
            </TabPane>
          </Tabs>
        </Card>

        {/* 创建/编辑优惠券弹窗 */}
        <Modal
          title={couponModalType === 'create' ? '创建优惠券' : '编辑优惠券'}
          open={couponModalVisible}
          onOk={handleCouponSubmit}
          onCancel={() => {
            setCouponModalVisible(false);
            couponForm.resetFields();
          }}
          width={600}
          okText="确定"
          cancelText="取消"
          confirmLoading={submitting}
          okButtonProps={{ style: { backgroundColor: '#165DFF' } }}
        >
          <Form form={couponForm} layout="vertical" style={{ marginTop: 24 }}>
            <Form.Item
              name="name"
              label="优惠券名称"
              rules={[{ required: true, message: '请输入优惠券名称' }]}
            >
              <Input placeholder="请输入优惠券名称" maxLength={50} showCount />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="type"
                  label="优惠类型"
                  rules={[{ required: true, message: '请选择优惠类型' }]}
                >
                  <Select placeholder="请选择优惠类型">
                    <Option value="满减券">满减券</Option>
                    <Option value="折扣券">折扣券</Option>
                    <Option value="无门槛券">无门槛券</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="discount"
                  label="面值"
                  rules={[{ required: true, message: '请输入面值' }]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={1}
                    max={10000}
                    placeholder="请输入面值"
                    addonAfter="元"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="condition"
              label="使用条件"
              rules={[{ required: true, message: '请输入使用条件' }]}
            >
              <Input placeholder="例如：满100可用" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="total"
                  label="发放数量"
                  rules={[{ required: true, message: '请输入发放数量' }]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={1}
                    max={1000000}
                    placeholder="请输入发放数量"
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="dateRange"
                  label="有效期"
                  rules={[{ required: true, message: '请选择有效期' }]}
                >
                  <RangePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="description" label="使用说明">
              <TextArea
                rows={3}
                placeholder="请输入优惠券使用说明（选填）"
                maxLength={200}
                showCount
              />
            </Form.Item>
          </Form>
        </Modal>

        {/* 创建活动弹窗 */}
        <Modal
          title="创建促销活动"
          open={campaignModalVisible}
          onOk={handleCampaignSubmit}
          onCancel={() => {
            setCampaignModalVisible(false);
            campaignForm.resetFields();
          }}
          width={600}
          okText="确定"
          cancelText="取消"
          confirmLoading={submitting}
          okButtonProps={{ style: { backgroundColor: '#165DFF' } }}
        >
          <Form form={campaignForm} layout="vertical" style={{ marginTop: 24 }}>
            <Form.Item
              name="name"
              label="活动名称"
              rules={[{ required: true, message: '请输入活动名称' }]}
            >
              <Input placeholder="请输入活动名称" maxLength={50} showCount />
            </Form.Item>

            <Form.Item
              name="type"
              label="活动类型"
              rules={[{ required: true, message: '请选择活动类型' }]}
            >
              <Select placeholder="请选择活动类型">
                <Option value="满减活动">满减活动</Option>
                <Option value="折扣活动">折扣活动</Option>
                <Option value="秒杀活动">秒杀活动</Option>
                <Option value="新品活动">新品活动</Option>
                <Option value="拼团活动">拼团活动</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="dateRange"
              label="活动时间"
              rules={[{ required: true, message: '请选择活动时间' }]}
            >
              <RangePicker
                style={{ width: '100%' }}
                showTime
                format="YYYY-MM-DD HH:mm:ss"
              />
            </Form.Item>

            <Form.Item
              name="budget"
              label="活动预算"
              rules={[{ required: true, message: '请输入活动预算' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                max={10000000}
                placeholder="请输入活动预算"
                formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value.replace(/¥\s?|(,*)/g, '')}
              />
            </Form.Item>

            <Form.Item name="description" label="活动描述">
              <TextArea
                rows={3}
                placeholder="请输入活动描述（选填）"
                maxLength={500}
                showCount
              />
            </Form.Item>
          </Form>
        </Modal>

        {/* 佣金设置抽屉 */}
        <Modal
          title="佣金设置"
          open={commissionDrawerVisible}
          onOk={handleSaveCommission}
          onCancel={() => setCommissionDrawerVisible(false)}
          width={480}
          okText="保存设置"
          cancelText="取消"
          confirmLoading={submitting}
          okButtonProps={{ style: { backgroundColor: '#165DFF' } }}
        >
          <Form form={commissionForm} layout="vertical">
            <Divider orientation="left">分销等级佣金比例</Divider>

            <Form.Item label="金牌分销员" name="goldRate" initialValue={8}>
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                max={100}
                formatter={(value) => `${value}%`}
                parser={(value) => value.replace('%', '')}
              />
            </Form.Item>

            <Form.Item label="银牌分销员" name="silverRate" initialValue={6}>
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                max={100}
                formatter={(value) => `${value}%`}
                parser={(value) => value.replace('%', '')}
              />
            </Form.Item>

            <Form.Item label="铜牌分销员" name="bronzeRate" initialValue={4}>
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                max={100}
                formatter={(value) => `${value}%`}
                parser={(value) => value.replace('%', '')}
              />
            </Form.Item>

            <Divider orientation="left">佣金结算规则</Divider>

            <Form.Item label="结算周期" name="settlementCycle" initialValue="monthly">
              <Select>
                <Option value="daily">每日结算</Option>
                <Option value="weekly">每周结算</Option>
                <Option value="monthly">每月结算</Option>
              </Select>
            </Form.Item>

            <Form.Item label="佣金冻结期" name="freezeDays" initialValue={7}>
              <InputNumber style={{ width: '100%' }} min={0} max={30} addonAfter="天" />
            </Form.Item>

            <Form.Item label="最低提现金额" name="minWithdraw" initialValue={100}>
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                formatter={(value) => `¥ ${value}`}
                parser={(value) => value.replace(/¥\s?|(,*)/g, '')}
              />
            </Form.Item>

            <Divider orientation="left">其他设置</Divider>

            <Form.Item label="允许自购佣金" name="allowSelfPurchase" valuePropName="checked" initialValue={false}>
              <Switch />
            </Form.Item>

            <Form.Item label="允许二级分销" name="allowSecondLevel" valuePropName="checked" initialValue={true}>
              <Switch />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </Spin>
  );
}
