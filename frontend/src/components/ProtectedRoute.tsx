import { Navigate, Outlet } from 'react-router';
import { useCurrentUser } from '../hooks/useCurrentUser';

export function ProtectedRoute() {
  const { user, isLoading, isResolved } = useCurrentUser();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#2a9d8f]"></div>
      </div>
    );
  }

  if (isResolved && !user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}