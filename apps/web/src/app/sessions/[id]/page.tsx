import type { Metadata } from "next";
import { SessionDetail } from "@/components/session-detail";

export const metadata: Metadata = { title: "Session" };

export default async function SessionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <div className="page"><SessionDetail id={id} /></div>;
}
