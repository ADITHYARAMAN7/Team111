/**
 * Image Service
 * Returns disease reference images with provenance information.
 */

import { DiseaseImage } from '@/types/diagnosis';
import { getImagesByDiseaseId } from '@/data/mockImages';

// ─── Integration Point ──────────────────────────────────────────────────────
// Replace with Image Repository API that serves:
// 1. Verified disease images from PlantVillage/PlantDoc datasets
// 2. Region-specific images from TNAU
// 3. Source attribution and provenance metadata
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Returns disease reference images for visual confirmation.
 */
export async function getDiseaseImages(
  diseaseId: string
): Promise<DiseaseImage[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(getImagesByDiseaseId(diseaseId));
    }, 500);
  });
}
