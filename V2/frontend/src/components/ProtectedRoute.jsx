import { useAuth } from "@clerk/react";
import { Navigate, useLocation } from "react-router-dom";

export default function ProtectedRoute({ children }) {
  if (!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY) return <section className="page-panel"><h1>Sign-in setup required</h1><p>Set VITE_CLERK_PUBLISHABLE_KEY in V2/frontend/.env.local, then restart the frontend. Private API routes require a signed-in account.</p></section>;
  return <SignedInRoute>{children}</SignedInRoute>;
}

function SignedInRoute({children}) {
  const location = useLocation();
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return <p className="page-panel" role="status">Loading your account…</p>;
  }

  if (!isSignedIn) {
    return <Navigate to="/auth" state={{from: location.pathname + location.search}} replace />;
  }

  return children;
}
