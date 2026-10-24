import type { PublicMentor } from "@/lib/types";

// Fixture mentors. Blank sheet fields are null on purpose so the
// "Not stated" evidence rows can be exercised.
const noTools = { tableau: null, hubspot: null, google_analytics: null, jira: null, excel: null, mixpanel: null };

export const MENTORS: PublicMentor[] = [
  {
    id: "M003", name: "Asha Raman", city: "Bengaluru", domain: "Product Management", company: "Razorpay",
    sector: "Fintech", sectors: ["Fintech", "Payments"], roles: ["Product Manager", "Group PM"],
    seniority: "Senior", built_ai: true, ai_tools: ["ChatGPT", "Claude"],
    tools: { ...noTools, jira: true, mixpanel: true, excel: true }, quality: "Excellent", activities: 42,
  },
  {
    id: "M007", name: "Vikram Nair", city: "Mumbai", domain: "Data Analytics", company: "HDFC Bank",
    sector: "Banking", sectors: ["Banking", "Fintech"], roles: ["Data Analyst", "Analytics Lead"],
    seniority: "Senior", built_ai: false, ai_tools: [],
    tools: { ...noTools, tableau: true, excel: true }, quality: "Good", activities: 31,
  },
  {
    id: "M011", name: "Meera Iyer", city: "Chennai", domain: "Marketing", company: null,
    sector: "Consumer Internet", sectors: ["Consumer Internet", "D2C"], roles: ["Growth Marketer", "Brand Manager"],
    seniority: "Mid-career", built_ai: null, ai_tools: [],
    tools: { ...noTools, hubspot: true, google_analytics: true }, quality: "Good", activities: 18,
  },
  {
    id: "M013", name: "Rohan Deshmukh", city: "Pune", domain: "Product Management", company: "Zomato",
    sector: "Consumer Internet", sectors: ["Consumer Internet", "Food Tech"], roles: ["Product Manager"],
    seniority: "Mid-career", built_ai: true, ai_tools: ["Claude", "Midjourney"],
    tools: { ...noTools, jira: true, google_analytics: true }, quality: "Excellent", activities: 27,
  },
  {
    id: "M015", name: "Priya Subramanian", city: null, domain: "Data Science", company: "Flipkart",
    sector: "E-commerce", sectors: ["E-commerce"], roles: ["Data Scientist", "ML Engineer"],
    seniority: "Senior", built_ai: true, ai_tools: ["PyTorch", "Claude"],
    tools: { ...noTools, tableau: true }, quality: "Excellent", activities: 55,
  },
  {
    id: "M021", name: "Kabir Malhotra", city: "Delhi", domain: "Consulting", company: "Deloitte",
    sector: null, sectors: ["Public Sector", "Healthcare"], roles: ["Consultant", "Engagement Manager"],
    seniority: "Senior", built_ai: false, ai_tools: [],
    tools: { ...noTools, excel: true }, quality: "Good", activities: 22,
  },
  {
    id: "M024", name: "Sneha Kulkarni", city: "Hyderabad", domain: "UX Design", company: "Swiggy",
    sector: "Consumer Internet", sectors: ["Consumer Internet"], roles: ["Product Designer", "Design Lead"],
    seniority: "Mid-career", built_ai: null, ai_tools: [],
    tools: noTools, quality: null, activities: null,
  },
  {
    id: "M029", name: "Arjun Bhatia", city: "Gurugram", domain: "Marketing", company: "Nykaa",
    sector: "E-commerce", sectors: ["E-commerce", "Beauty"], roles: ["Performance Marketing Manager"],
    seniority: "Mid-career", built_ai: false, ai_tools: [],
    tools: { ...noTools, google_analytics: true, hubspot: true }, quality: "Good", activities: 14,
  },
  {
    id: "M033", name: "Divya Menon", city: "Kochi", domain: "Operations", company: "Delhivery",
    sector: "Logistics", sectors: ["Logistics", "Supply Chain"], roles: ["Operations Manager"],
    seniority: "Senior", built_ai: null, ai_tools: [],
    tools: { ...noTools, excel: true }, quality: "Good", activities: 9,
  },
  {
    id: "M038", name: "Nikhil Rao", city: "Bengaluru", domain: "Software Engineering", company: "Postman",
    sector: "SaaS", sectors: ["SaaS", "Developer Tools"], roles: ["Engineering Manager", "Backend Engineer"],
    seniority: "Senior", built_ai: true, ai_tools: ["Claude", "Copilot"],
    tools: { ...noTools, jira: true }, quality: "Excellent", activities: 61,
  },
  {
    id: "M042", name: "Farah Siddiqui", city: "Mumbai", domain: "Finance", company: null,
    sector: "Fintech", sectors: ["Fintech", "Investing"], roles: ["Investment Analyst"],
    seniority: null, built_ai: null, ai_tools: [],
    tools: { ...noTools, excel: true }, quality: null, activities: 4,
  },
  {
    id: "M047", name: "Tanvi Joshi", city: "Ahmedabad", domain: "Human Resources", company: "Infosys",
    sector: "IT Services", sectors: ["IT Services"], roles: ["HR Business Partner", "Talent Lead"],
    seniority: "Mid-career", built_ai: false, ai_tools: [],
    tools: noTools, quality: "Good", activities: 11,
  },
];

// Keyword rules that drive the mock chat. Each maps words in the message to mentor ids.
export const KEYWORD_MENTORS: { words: RegExp; ids: string[]; reasonFields: string[] }[] = [
  { words: /product|pm\b|roadmap/i, ids: ["M003", "M013", "M038"], reasonFields: ["domain", "sector", "roles"] },
  { words: /data|analy|sql|tableau|machine learning|\bml\b|\bai\b/i, ids: ["M015", "M007", "M038"], reasonFields: ["domain", "tools", "built_ai"] },
  { words: /fintech|bank|finance|invest|payment/i, ids: ["M003", "M042", "M007"], reasonFields: ["sector", "domain", "sectors"] },
  { words: /market|brand|growth|seo|ads/i, ids: ["M029", "M011", "M013"], reasonFields: ["domain", "sector", "tools"] },
  { words: /design|ux|ui\b/i, ids: ["M024", "M013", "M011"], reasonFields: ["domain", "sector", "roles"] },
  { words: /consult|strategy|case/i, ids: ["M021", "M007", "M033"], reasonFields: ["domain", "roles", "seniority"] },
  { words: /code|software|engineer|developer|backend/i, ids: ["M038", "M015", "M003"], reasonFields: ["domain", "roles", "sector"] },
  { words: /operation|logistic|supply|hr\b|hiring|resume/i, ids: ["M033", "M047", "M021"], reasonFields: ["domain", "roles", "sector"] },
];
