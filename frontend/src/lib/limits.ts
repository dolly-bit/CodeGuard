// Mirrors backend/app/config.py
export const LIMITS = {
  reportChars: 10_000,
  files: 300,
  fileBytes: 500_000,
  totalBytes: 5_000_000,
  zipBytes: 20_000_000,
  zipEntries: 2_000,
  topK: { min: 1, max: 20 },
  llmEvidence: 10,
} as const;
