import { Layout as AntLayout, Menu, Button, Space, Typography } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { logout } from '../api/auth';

const { Header, Content } = AntLayout;

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const selectedKey = location.pathname.startsWith('/cabinet')
    ? 'cabinet'
    : location.pathname.startsWith('/moderation')
    ? 'moderation'
    : location.pathname.startsWith('/auctions/new')
    ? 'new'
    : 'catalog';

  const handleLogout = async () => {
    await logout().catch(() => {});
    setUser(null);
    navigate('/login');
  };

  const menuItems = [
    { key: 'catalog', label: <Link to="/auctions">Каталог</Link> },
    { key: 'cabinet', label: <Link to="/cabinet">Мой кабинет</Link> },
    ...(user?.can_moderate
      ? [{ key: 'moderation', label: <Link to="/moderation">Модерация</Link> }]
      : []),
  ];

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
        }}
      >
        <Space>
          <Typography.Text strong style={{ color: '#fff', fontSize: 18, marginRight: 24 }}>
            REA Аукцион
          </Typography.Text>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[selectedKey]}
            items={menuItems}
            style={{ background: 'transparent', border: 'none', minWidth: 320 }}
          />
        </Space>
        {user && (
          <Space>
            <Button type="link" style={{ color: '#fff' }} onClick={() => navigate('/auctions/new')}>
              + Новая задача
            </Button>
            <Typography.Text style={{ color: '#aaa' }}>{user.username}</Typography.Text>
            <Button size="small" onClick={handleLogout}>
              Выйти
            </Button>
          </Space>
        )}
      </Header>
      <Content style={{ padding: '24px 48px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        {children}
      </Content>
    </AntLayout>
  );
}
