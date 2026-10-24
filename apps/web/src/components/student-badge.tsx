"use client";
import { saveStudent, useStudent } from "@/lib/student";

export function StudentBadge() {
  const { student, ready } = useStudent();
  if (!ready || !student) return null;
  return (
    <div className="flex items-center gap-2 text-sm text-muted">
      <span data-testid="student-name" className="max-w-[7rem] truncate font-medium text-ink sm:max-w-[10rem]">{student.name}</span>
      <button type="button" onClick={() => saveStudent(null)} className="btn btn-quiet !min-h-[38px] !px-3 !text-[0.8rem]">
        Sign out
      </button>
    </div>
  );
}
