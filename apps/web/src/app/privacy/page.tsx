import type { Metadata } from "next";
import { Legal } from "@/components/legal";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <Legal
      title="Privacy Policy"
      updated="24 October 2026"
      sections={[
        { h: "What we collect", p: ["Your name and email when you sign in, the messages you write in the chat, the bookings you make, and any message you send through the Contact page."] },
        { h: "How we use it", p: ["To keep your chats and bookings together, to match you with mentors, to give your mentor a short brief before the call, and to prepare your write-up. The Mesa team sees summary counts and problems that found no match, to improve the service."] },
        { h: "Mentor details", p: ["We show only the profile fields on the mentor list. Mentor email addresses, phone numbers and LinkedIn profiles are never shown to students and are never sent to the AI service."] },
        { h: "AI service", p: ["Your chat message may be processed by an AI model to understand your problem and explain matches. Matches are checked against the mentor list before they are shown."] },
        { h: "Your choices", p: ["Sign out at any time from the header. To ask for your data to be removed, write to us from the Contact page."] },
      ]}
    />
  );
}
