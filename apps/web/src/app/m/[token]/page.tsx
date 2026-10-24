import type { Metadata } from "next";
import { MentorView } from "@/components/mentor-view";

export const metadata: Metadata = { title: "Mentor call", robots: { index: false } };

export default async function MentorPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <div className="page"><MentorView token={token} /></div>;
}
