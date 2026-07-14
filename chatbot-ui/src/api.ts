import type { AskResponse, ChatMessage } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {}

export async function ask(question: string, history: ChatMessage[]): Promise<AskResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        history: history.map((m) => ({ role: m.role, content: m.content })),
      }),
    });
  } catch {
    throw new ApiError("Could not reach the assistant. Is the backend running?");
  }
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* keep default */
    }
    throw new ApiError(detail);
  }
  return res.json() as Promise<AskResponse>;
}
