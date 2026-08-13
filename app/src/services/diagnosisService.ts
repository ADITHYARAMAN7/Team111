/**
 * Diagnosis Service
 * Mock implementation — will connect to Knowledge Graph API for disease matching.
 */

import { DiseaseCandidate, Symptom } from '@/types/diagnosis';
import { DISEASES } from '@/data/mockDiseases';

// ─── Integration Point ──────────────────────────────────────────────────────
// Replace with Knowledge Graph-based disease matching.
// The KG should:
// 1. Match extracted symptoms against disease-symptom relationships
// 2. Return candidates with qualitative match levels (not fake percentages)
// 3. Consider symptom combinations and co-occurrence patterns
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Returns disease candidates based on extracted symptoms.
 * Uses qualitative match levels instead of fake percentages.
 */
export async function getDiseaseCandidates(
  _symptoms: Symptom[]
): Promise<DiseaseCandidate[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Return top 3 candidates (excluding healthy)
      const candidates = DISEASES.filter((d) => d.id !== 'healthy').slice(0, 3);
      resolve(candidates);
    }, 1500);
  });
}

/**
 * Confirms the farmer's disease selection.
 * In production, logs this confirmation for ML model improvement.
 */
export async function confirmDisease(
  diseaseId: string
): Promise<DiseaseCandidate | null> {
  return new Promise((resolve) => {
    setTimeout(() => {
      const disease = DISEASES.find((d) => d.id === diseaseId) ?? null;
      resolve(disease);
    }, 300);
  });
}
