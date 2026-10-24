import type { Metadata } from "next";
import { ContactForm } from "@/components/contact-form";

export const metadata: Metadata = { title: "Contact" };

export default function ContactPage() {
  return (
    <div className="page">
      <h1 className="h-page mb-12 text-center md:!text-[2.25rem]">Get In Touch</h1>
      <ContactForm />
    </div>
  );
}
