import { Show, UserButton, SignIn } from "@clerk/react";
import {useLocation} from 'react-router-dom';
import AuthEntryButton from "../components/AuthEntryButton";

export default function AuthPage() {
  const location = useLocation();
  if (!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY) return <section className="page-panel"><h1>Connect your account</h1><p>Add VITE_CLERK_PUBLISHABLE_KEY to frontend/.env.local and restart Vite. Saved conversations require sign-in.</p></section>;
  return (
    <section className="page-panel auth-panel">
      <h1>Access your private space</h1>
      <p className="muted">
        Sign in to open your conversations, journal and memory.
      </p>

      <Show when="signed-out">
        <div className="hero-actions">
          <SignIn routing="path" path="/auth" forceRedirectUrl={location.state?.from || '/talk'} />
        </div>
      </Show>

      <Show when="signed-in">
        <div className="card" style={{ marginTop: "14px" }}>
          <p className="muted">You are signed in.</p>
          <UserButton />
        </div>
      </Show>
    </section>
  );
}
