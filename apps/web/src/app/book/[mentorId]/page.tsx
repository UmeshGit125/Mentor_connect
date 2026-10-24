import type { Metadata } from "next";
import { BookFlow } from "@/components/book-flow";

export const metadata: Metadata = { title: "Book a call" };

export default async function BookPage({ params, searchParams }: { params: Promise<{ mentorId: string }>; searchParams: Promise<{ slot?: string }> }) {
  const [{ mentorId }, { slot }] = await Promise.all([params, searchParams]);
  return <div className="page"><BookFlow mentorId={mentorId} initialSlot={slot} /></div>;
}
