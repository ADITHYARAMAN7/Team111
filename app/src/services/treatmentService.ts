/**
 * Treatment Service
 * Returns source-backed treatment recommendations.
 */

import { Treatment } from '@/types/diagnosis';
import { getTreatmentByDiseaseId } from '@/data/mockTreatments';

// ─── Integration Point ──────────────────────────────────────────────────────
// Replace with Knowledge Graph treatment data API.
// Should return verified, source-attributed treatment recommendations.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Returns treatment information for a confirmed disease.
 */
export async function getTreatment(
  diseaseId: string
): Promise<Treatment | null> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(getTreatmentByDiseaseId(diseaseId) ?? null);
    }, 800);
  });
}
