import type { Metadata } from "next";
import Home from "@/app/page";

export const metadata: Metadata = { title: "Chat" };

// Same screen as the home page, so /chat works as a direct link.
export default function ChatPage() {
  return <Home />;
}
