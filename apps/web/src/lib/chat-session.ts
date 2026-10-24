// Remembers the latest chat session id so the booking step can send it.
const KEY = "mc_chat_session";

export function rememberChatSession(id: string) {
  try {
    window.localStorage.setItem(KEY, id);
  } catch {
    // storage unavailable: booking falls back to an empty session id
  }
}

export function lastChatSession(): string {
  try {
    return window.localStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
}
