import { SignInButton } from "@clerk/react";

export default function AuthEntryButton({ className }) {
  return (
    <SignInButton mode="redirect" forceRedirectUrl="/dashboard">
      <button type="button" className={className}>
        Continue with Google
      </button>
    </SignInButton>
  );
}
