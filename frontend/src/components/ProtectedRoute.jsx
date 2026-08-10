import {
  Navigate,
  useLocation,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";


function ProtectedRoute({
  children,
}) {
  const {
    isAuthenticated,
    authLoading,
  } = useAuth();

  const location =
    useLocation();

  if (authLoading) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">
            Autonomous DevOps Platform
          </p>

          <h1>
            Loading...
          </h1>

          <p className="empty-state">
            Restoring your session.
          </p>
        </section>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from:
            location.pathname,
        }}
      />
    );
  }

  return children;
}

export default ProtectedRoute;