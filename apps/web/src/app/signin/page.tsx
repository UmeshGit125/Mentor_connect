import type { Metadata } from "next";
import { SignInPage } from "@/components/signin-page";

export const metadata: Metadata = { title: "Sign in" };

export default function Page() {
  return (
    <div className="page">
      <SignInPage />
    </div>
  );
}
