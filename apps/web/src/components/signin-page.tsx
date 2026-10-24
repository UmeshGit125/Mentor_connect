"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SignIn } from "@/components/sign-in";
import { useStudent } from "@/lib/student";

/** The header's Sign in and Get started both land here: the same name and email form, no password. */
export function SignInPage() {
  const router = useRouter();
  const { student, ready } = useStudent();
  return (
    <div className="mx-auto max-w-md">
      <h1 className="h-page mb-6 text-center">Sign in or get started</h1>
      {ready && student ? (
        <div className="panel p-6 text-center">
          <p>You are signed in as <strong>{student.name}</strong>.</p>
          <Link href="/" className="btn btn-primary mt-4">Find a mentor</Link>
        </div>
      ) : (
        <SignIn onDone={() => router.push("/")} />
      )}
    </div>
  );
}
