export interface Source {
  id: string | null;
  topic: string | null;
  source_org: string | null;
  source_url: string | null;
  score: number | null;
}

export interface Safety {
  checked: boolean;
  blocked: boolean;
  groundedness?: string | null;
  medical_safety?: string | null;
  violations: string[];
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  safety: Safety;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  safety?: Safety;
}
