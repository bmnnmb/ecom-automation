/**
 * 登录页面
 * 支持账号密码登录，登录成功后存储token和用户信息
 */
import React, { useState } from 'react';
import { Form, Input, Button, Checkbox, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

// 默认管理员账号
const DEFAULT_USERS = [
  { username: 'admin', password: 'admin123', name: '系统管理员', role: 'admin', avatar: '' },
  { username: 'operator', password: 'op123', name: '运营专员', role: 'operator', avatar: '' },
];

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    // 模拟登录验证
    await new Promise(resolve => setTimeout(resolve, 800));

    const user = DEFAULT_USERS.find(
      u => u.username === values.username && u.password === values.password
    );

    if (user) {
      const token = `token_${Date.now()}_${Math.random().toString(36).slice(2)}`;
      const userInfo = {
        username: user.username,
        name: user.name,
        role: user.role,
        loginTime: new Date().toISOString(),
      };

      localStorage.setItem('token', token);
      localStorage.setItem('userInfo', JSON.stringify(userInfo));

      message.success(`欢迎回来，${user.name}！`);
      navigate('/', { replace: true });
    } else {
      message.error('用户名或密码错误');
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <div style={{
        width: 420,
        padding: 48,
        background: '#fff',
        borderRadius: 16,
        boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: 'linear-gradient(135deg, #165DFF 0%, #722ED1 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            fontSize: 28,
            color: '#fff',
            fontWeight: 'bold',
          }}>
            E
          </div>
          <Title level={3} style={{ margin: 0, fontWeight: 600 }}>电商运营系统</Title>
          <Text type="secondary">Hermes 多平台电商自动化管理平台</Text>
        </div>

        <Form
          name="login"
          initialValues={{ username: 'admin', password: 'admin123', remember: true }}
          onFinish={onFinish}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Form.Item name="remember" valuePropName="checked" noStyle>
                <Checkbox>记住我</Checkbox>
              </Form.Item>
              <a style={{ color: '#165DFF' }}>忘记密码？</a>
            </div>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block
              style={{ height: 44, borderRadius: 8, fontSize: 16, fontWeight: 500 }}>
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{
          marginTop: 24,
          padding: '12px 16px',
          background: '#F7F8FA',
          borderRadius: 8,
          fontSize: 12,
          color: '#86909C',
        }}>
          <div style={{ fontWeight: 500, marginBottom: 4, color: '#4E5969' }}>演示账号：</div>
          <div>管理员：admin / admin123</div>
          <div>运营专员：operator / op123</div>
        </div>
      </div>
    </div>
  );
}
