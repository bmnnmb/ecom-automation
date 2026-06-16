/**
 * 消息中心
 * 系统通知、订单提醒、库存预警、营销消息等
 */
import React, { useState, useMemo } from 'react';
import {
  Card,
  List,
  Tag,
  Badge,
  Button,
  Space,
  Tabs,
  Typography,
  Empty,
  Avatar,
  Tooltip,
  Popconfirm,
  message,
  Row,
  Col,
  Statistic,
  Switch,
} from 'antd';
import {
  BellOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  DollarOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  InboxOutlined,
  MailOutlined,
  RiseOutlined,
  SettingOutlined,
  ShoppingCartOutlined,
  ShopOutlined,
  TagOutlined,
  TruckOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

// Mock 通知数据
const generateNotifications = () => [
  {
    id: 1,
    type: 'order',
    title: '新订单提醒',
    content: '订单 #ORD-30001 已支付，金额 ¥299.00，请尽快发货',
    time: '2分钟前',
    timestamp: Date.now() - 120000,
    read: false,
    icon: <ShoppingCartOutlined />,
    color: '#165DFF',
    bgColor: '#E8F3FF',
  },
  {
    id: 2,
    type: 'stock',
    title: '库存预警',
    content: '蓝牙耳机Pro Max 库存仅剩 3 件，日均销量 5 件，预计今日售罄',
    time: '15分钟前',
    timestamp: Date.now() - 900000,
    read: false,
    icon: <WarningOutlined />,
    color: '#FF7D00',
    bgColor: '#FFF7E8',
  },
  {
    id: 3,
    type: 'refund',
    title: '退款申请',
    content: '订单 #ORD-29985 申请退款，金额 ¥459.00，原因：不想要了',
    time: '32分钟前',
    timestamp: Date.now() - 1920000,
    read: false,
    icon: <DollarOutlined />,
    color: '#F53F3F',
    bgColor: '#FFECE8',
  },
  {
    id: 4,
    type: 'review',
    title: '差评预警',
    content: '"智能手表S3" 收到 1 星差评：质量太差，用了两天就坏了',
    time: '1小时前',
    timestamp: Date.now() - 3600000,
    read: false,
    icon: <ExclamationCircleOutlined />,
    color: '#F53F3F',
    bgColor: '#FFECE8',
  },
  {
    id: 5,
    type: 'order',
    title: '发货超时提醒',
    content: '有 8 个订单已超过 24 小时未发货，平台将扣分处理',
    time: '2小时前',
    timestamp: Date.now() - 7200000,
    read: true,
    icon: <TruckOutlined />,
    color: '#FF7D00',
    bgColor: '#FFF7E8',
  },
  {
    id: 6,
    type: 'competitor',
    title: '竞品价格变动',
    content: '竞品"XX蓝牙耳机"降价 15%，当前售价 ¥169，建议跟进调整',
    time: '3小时前',
    timestamp: Date.now() - 10800000,
    read: true,
    icon: <RiseOutlined />,
    color: '#722ED1',
    bgColor: '#F9F0FF',
  },
  {
    id: 7,
    type: 'system',
    title: '系统更新通知',
    content: '系统将于今晚 22:00-23:00 进行维护升级，届时部分功能暂不可用',
    time: '5小时前',
    timestamp: Date.now() - 18000000,
    read: true,
    icon: <SettingOutlined />,
    color: '#86909C',
    bgColor: '#F2F3F5',
  },
  {
    id: 8,
    type: 'marketing',
    title: '营销活动结束',
    content: '"春季焕新大促" 活动已结束，累计销售额 ¥1,256,800，参与人数 12,580',
    time: '6小时前',
    timestamp: Date.now() - 21600000,
    read: true,
    icon: <TagOutlined />,
    color: '#00B42A',
    bgColor: '#E8FFEA',
  },
  {
    id: 9,
    type: 'order',
    title: '订单自动取消',
    content: '订单 #ORD-29960 因超时未付款已自动取消',
    time: '8小时前',
    timestamp: Date.now() - 28800000,
    read: true,
    icon: <ShoppingCartOutlined />,
    color: '#86909C',
    bgColor: '#F2F3F5',
  },
  {
    id: 10,
    type: 'customer',
    title: 'VIP 客户到访',
    content: '钻石会员"刘强东"正在浏览店铺，累计消费 ¥198,500',
    time: '昨天',
    timestamp: Date.now() - 86400000,
    read: true,
    icon: <UserOutlined />,
    color: '#722ED1',
    bgColor: '#F9F0FF',
  },
  {
    id: 11,
    type: 'stock',
    title: '补货完成',
    content: '充电宝20000mAh 已补货 200 件，当前库存 212 件',
    time: '昨天',
    timestamp: Date.now() - 90000000,
    read: true,
    icon: <InboxOutlined />,
    color: '#00B42A',
    bgColor: '#E8FFEA',
  },
  {
    id: 12,
    type: 'order',
    title: '大额订单',
    content: '收到大额订单 #ORD-29945，金额 ¥8,999.00，来自抖音平台',
    time: '2天前',
    timestamp: Date.now() - 172800000,
    read: true,
    icon: <DollarOutlined />,
    color: '#165DFF',
    bgColor: '#E8F3FF',
  },
];

const typeTabs = [
  { key: 'all', label: '全部消息' },
  { key: 'unread', label: '未读' },
  { key: 'order', label: '订单' },
  { key: 'stock', label: '库存' },
  { key: 'refund', label: '退款' },
  { key: 'competitor', label: '竞品' },
  { key: 'system', label: '系统' },
];

export default function Notifications() {
  const [notifications, setNotifications] = useState(() => generateNotifications());
  const [activeTab, setActiveTab] = useState('all');

  // 统计
  const unreadCount = notifications.filter(n => !n.read).length;
  const stats = useMemo(() => ({
    total: notifications.length,
    unread: unreadCount,
    order: notifications.filter(n => n.type === 'order').length,
    stock: notifications.filter(n => n.type === 'stock').length,
    refund: notifications.filter(n => n.type === 'refund').length,
  }), [notifications, unreadCount]);

  // 筛选
  const filtered = useMemo(() => {
    if (activeTab === 'all') return notifications;
    if (activeTab === 'unread') return notifications.filter(n => !n.read);
    return notifications.filter(n => n.type === activeTab);
  }, [notifications, activeTab]);

  // 标记已读
  const markAsRead = (id) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  // 全部标记已读
  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    message.success('已全部标记为已读');
  };

  // 删除通知
  const deleteNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
    message.success('已删除');
  };

  // 清空已读
  const clearRead = () => {
    setNotifications(prev => prev.filter(n => !n.read));
    message.success('已清空已读消息');
  };

  return (
    <div style={{ background: '#F7F8FA', minHeight: '100vh', margin: '-24px', padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
            <BellOutlined style={{ marginRight: 8 }} />
            消息中心
          </Title>
          <Text type="secondary">查看系统通知、订单提醒和预警信息</Text>
        </div>
        <Space>
          {unreadCount > 0 && (
            <Button type="primary" onClick={markAllAsRead}>
              全部已读 ({unreadCount})
            </Button>
          )}
          <Button onClick={clearRead}>清空已读</Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="全部消息"
              value={stats.total}
              prefix={<MailOutlined style={{ color: '#165DFF' }} />}
              valueStyle={{ color: '#165DFF' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="未读消息"
              value={stats.unread}
              prefix={<BellOutlined style={{ color: '#F53F3F' }} />}
              valueStyle={{ color: '#F53F3F' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="订单通知"
              value={stats.order}
              prefix={<ShoppingCartOutlined style={{ color: '#FF7D00' }} />}
              valueStyle={{ color: '#FF7D00' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="库存预警"
              value={stats.stock}
              prefix={<WarningOutlined style={{ color: '#722ED1' }} />}
              valueStyle={{ color: '#722ED1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 消息列表 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={typeTabs.map(tab => ({
            key: tab.key,
            label: tab.key === 'unread' && unreadCount > 0
              ? <span>{tab.label} <Badge count={unreadCount} size="small" /></span>
              : tab.label,
          }))}
          style={{ marginBottom: 0 }}
        />

        {filtered.length === 0 ? (
          <Empty
            description="暂无消息"
            style={{ padding: '60px 0' }}
          />
        ) : (
          <List
            dataSource={filtered}
            renderItem={(item) => (
              <List.Item
                style={{
                  padding: '16px 0',
                  opacity: item.read ? 0.65 : 1,
                  transition: 'all 0.3s',
                }}
                actions={[
                  !item.read && (
                    <Tooltip title="标记已读" key="read">
                      <Button
                        type="text"
                        icon={<EyeOutlined />}
                        onClick={() => markAsRead(item.id)}
                      />
                    </Tooltip>
                  ),
                  <Popconfirm
                    key="delete"
                    title="确定删除此消息？"
                    onConfirm={() => deleteNotification(item.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button type="text" danger icon={<DeleteOutlined />} />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Badge dot={!item.read} offset={[-4, 4]}>
                      <Avatar
                        icon={item.icon}
                        size={44}
                        style={{ backgroundColor: item.bgColor, color: item.color, fontSize: 20 }}
                      />
                    </Badge>
                  }
                  title={
                    <Space>
                      <Text strong={!item.read} style={{ fontSize: 14 }}>{item.title}</Text>
                      {!item.read && <Tag color="red" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>未读</Tag>}
                    </Space>
                  }
                  description={
                    <div>
                      <div style={{ color: '#4E5969', fontSize: 13, marginBottom: 4 }}>{item.content}</div>
                      <Text type="secondary" style={{ fontSize: 12 }}>{item.time}</Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
}
