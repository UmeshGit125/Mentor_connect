import type { Metadata } from "next";
import { FaqList, type Faq } from "@/components/faq-list";

export const metadata: Metadata = { title: "FAQs" };

const FAQS: Faq[] = [
  {
    q: "How does matching work?",
    a: "You describe where you are stuck in your own words. We read the problem and pick up to three mentors from our list of 50 whose profile details fit it. If your message is too vague we ask a short question first, and if nobody on the list fits we say so instead of guessing.",
  },
  {
    q: "What do I see about each mentor?",
    a: "Only fields from the mentor list: domain, company, city, sector, areas and roles of expertise, seniority, whether they have built AI, tools they use, and how many sessions they have done. Every pick shows the exact values behind it, and anything the list leaves blank is shown as Not stated.",
  },
  {
    q: "How do I book a call?",
    a: "Open a mentor, choose one of the open 30-minute times in the next seven days and confirm. A time can only be booked once, so if someone else gets it first you are asked to pick another. You can have up to three active bookings at a time and you can cancel a call before it happens.",
  },
  {
    q: "What is the write-up after my call?",
    a: "The call happens outside this app. Afterwards your mentor closes it and adds notes. From those notes you get a short write-up of what you discussed, what to work on and your next steps, under My sessions. If the mentor adds no notes, there is no write-up, because we never write one from nothing.",
  },
  {
    q: "Is my information private?",
    a: "Mentor email addresses, phone numbers and LinkedIn profiles are never shown anywhere in the app. Your name and email are used only to keep your chats and bookings together, and your mentor sees a short brief of your problem so the call can start well.",
  },
  {
    q: "What does it cost?",
    a: "Nothing in this prototype. Booking a call is free while we test it with students. If that changes, the price is shown before you confirm a booking.",
  },
];

export default function FaqsPage() {
  return (
    <div className="page">
      <h1 className="h-page mb-10 text-center md:!text-[2.25rem]">Frequently Asked Questions</h1>
      <div className="mx-auto max-w-[840px]">
        <FaqList items={FAQS} />
      </div>
    </div>
  );
}
