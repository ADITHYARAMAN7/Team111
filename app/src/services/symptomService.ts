/**
 * Symptom Extraction Service
 * Mock implementation — will connect to NLP backend for Tamil symptom extraction.
 */

import { SymptomExtractionResult } from '@/types/diagnosis';
import { MOCK_SYMPTOMS_RESULT } from '@/data/mockDiseases';

// ─── Integration Point ──────────────────────────────────────────────────────
// Replace with NLP-based symptom extraction from Tamil transcript.
// The NLP pipeline should:
// 1. Parse Tamil text for plant/crop mentions
// 2. Identify affected plant parts
// 3. Extract symptom descriptions
// 4. Map to structured symptom entities
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Extracts structured symptoms from a Tamil transcript.
 * In production, will use NLP to parse Tamil agricultural descriptions.
 */
export async function extractSymptoms(
  _transcript: string
): Promise<SymptomExtractionResult> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_SYMPTOMS_RESULT);
    }, 1200);
  });
}
