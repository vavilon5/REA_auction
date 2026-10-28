import { Spin } from 'antd';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { AppLayout } from './components/Layout';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AuctionDetailPage } from './pages/AuctionDetailPage';
import { AuctionFormPage } from './pages/AuctionFormPage';
import { CabinetPage } from './pages/CabinetPage';
import { CatalogPage } from './pages/CatalogPage';
import { LoginPage } from './pages/LoginPage';
import { ModerationPage } from './pages/ModerationPage';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Spin style={{ display: 'block', margin: '25vh auto' }} size="large" />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RequireModerator({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user?.can_moderate) return <Navigate to="/auctions" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <Spin style={{ display: 'block', margin: '25vh auto' }} size="large" />;

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/auctions" replace /> : <LoginPage />} />

      <Route
        path="/*"
        element={
          <RequireAuth>
            <AppLayout>
              <Routes>
                <Route path="/auctions" element={<CatalogPage />} />
                <Route path="/auctions/new" element={<AuctionFormPage />} />
                <Route path="/auctions/:id" element={<AuctionDetailPage />} />
                <Route path="/auctions/:id/edit" element={<AuctionFormPage />} />
                <Route path="/cabinet" element={<CabinetPage />} />
                <Route
                  path="/moderation"
                  element={
                    <RequireModerator>
                      <ModerationPage />
                    </RequireModerator>
                  }
                />
                <Route path="*" element={<Navigate to="/auctions" replace />} />
              </Routes>
            </AppLayout>
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}
