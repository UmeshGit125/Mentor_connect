import type { Metadata } from "next";
import { Legal } from "@/components/legal";

export const metadata: Metadata = { title: "Terms and Condition" };

export default function TermsPage() {
  return (
    <Legal
      title="Terms and Condition"
      updated="24 October 2026"
      sections={[
        { h: "Using Mentor Connect", p: ["Mentor Connect helps students describe a career problem, see mentors who may fit, and book a call. You agree to use it for that purpose and to give accurate details when you sign in."] },
        { h: "Matches are suggestions", p: ["We suggest up to three mentors from a fixed list using the profile details on that list. A suggestion is not a promise of any result, job or admission, and mentors give their own views."] },
        { h: "Bookings and calls", p: ["A time slot can be booked once. You can cancel a call before it happens. The call takes place outside this app, and mentors may mark a call as completed or as a no-show.", "Please turn up on time and be respectful. We may stop access for misuse."] },
        { h: "Write-ups", p: ["A write-up is made only from the notes your mentor adds after the call. If there are no notes there is no write-up. Check it with your mentor before relying on it."] },
        { h: "Changes and contact", p: ["We may change these terms while the product is in testing. Questions can be sent through the Contact page."] },
      ]}
    />
  );
}
