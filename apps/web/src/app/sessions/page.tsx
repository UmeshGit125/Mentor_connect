import type { Metadata } from "next";
import { SessionsList } from "@/components/sessions-list";

export const metadata: Metadata = { title: "My sessions" };

export default function SessionsPage() {
  return (
    <div className="page">
      <h1 className="h-page mb-8">My sessions</h1>
      <SessionsList />
    </div>
  );
}
