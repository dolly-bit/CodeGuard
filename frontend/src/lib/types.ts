export interface SourceFile { path: string; content: string }
export interface SkippedFile { path: string; reason: string }

export interface Signals {
  lexical: number;
  stack_file: boolean;
  stack_line: boolean;
  stack_function: boolean;
  symbol_mentioned: boolean;
}

export interface Evidence {
  chunk_id: string;
  path: string;
  language: string;
  symbol: string | null;
  chunking: "python-ast" | "heuristic-brace" | "lines" | string;
  start_line: number;
  end_line: number;
  content: string;
  similarity_score: number;
  score_interpretation: string;
  signals: Signals;
}

export interface AnalyzeResponse {
  mode: "retrieval-only";
  notice: string;
  request_id?: string | null;
  files_indexed: number;
  chunks_searched: number;
  skipped: SkippedFile[];
  warnings: string[];
  evidence: Evidence[];
}

export interface Hypothesis {
  claim: string;
  evidence_ids: number[];
  confidence: "low" | "medium" | "high";
  counter_evidence: string;
}

export interface ExplainResponse {
  label: string;
  summary: string;
  hypotheses: Hypothesis[];
  next_steps: string[];
  insufficient_evidence: boolean;
  model: string;
}

export type FeedbackLabel = "useful" | "irrelevant";

export interface ExplainState {
  status: "idle" | "loading" | "done" | "error";
  data?: ExplainResponse;
  error?: string;
}

export interface Turn {
  id: string;
  report: string;
  fileCount: number;
  topK: number;
  time: string;
  status: "loading" | "done" | "error";
  data?: AnalyzeResponse;
  error?: string;
  explain?: ExplainState;
  feedback?: Record<string, FeedbackLabel>;
}
