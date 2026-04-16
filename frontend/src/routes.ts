import { createBrowserRouter } from 'react-router';
import Root from './Root';
import { ProtectedRoute } from './components/ProtectedRoute';
import LoginPage  from './pages/LoginPage';
import TriageWorkspace from './pages/TriageWorkspace';
import History from './pages/History';
import { AdminDashboard } from './pages/AdminDashboard';
// ===== ADMIN ROUTES =====
import { AdminSessionHistory } from './pages/AdminSessionHistory';
import { AdminChangeLog } from './pages/AdminChangeLog';
// ===== END ADMIN ROUTES =====

export const router = createBrowserRouter([
  {
    path: '/login',
    Component: LoginPage,
  },
  {
    // All routes under here require authentication
    Component: ProtectedRoute,
    children: [
      {
        path: '/',
        Component: Root,
        children: [
          { index: true, Component: TriageWorkspace },
          { path: "history", Component: History },
        ],
      },
      // ===== ADMIN ROUTES =====
      { path: '/admin', Component: AdminDashboard },
      { path: '/admin/sessions', Component: AdminSessionHistory },
      { path: '/admin/changelog', Component: AdminChangeLog },
      // ===== END ADMIN ROUTES =====
    ],
  },
]);