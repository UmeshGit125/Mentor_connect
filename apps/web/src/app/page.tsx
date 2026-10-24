import { Chat } from "@/components/chat";
import { CategoriesSection, DiscoverSection, FeaturesSection, WorkflowSection } from "@/components/home-sections";
import { api } from "@/lib/api";
import type { PublicMentor } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  // The category and mentor sections use the real list. If the API is down, the page still works without them.
  let mentors: PublicMentor[] = [];
  try {
    mentors = await api.listMentors();
  } catch {
    mentors = [];
  }
  return (
    <Chat
      below={
        <>
          <WorkflowSection />
          <CategoriesSection mentors={mentors} />
          <FeaturesSection />
          <DiscoverSection mentors={mentors} />
        </>
      }
    />
  );
}
