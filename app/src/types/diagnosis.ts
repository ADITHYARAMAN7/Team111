/**
 * Core TypeScript interfaces for the Tomato Disease Diagnosis system.
 */

// ─── Symptom Types ───────────────────────────────────────────────────────────

export type PlantPart = 'leaf' | 'stem' | 'fruit' | 'root' | 'flower' | 'whole';

export interface Symptom {
  id: string;
  name: string;
  tamilName: string;
  plantPart: PlantPart;
  description?: string;
  tamilDescription?: string;
}

// ─── Disease Types ───────────────────────────────────────────────────────────

export type MatchLevel = 'high' | 'medium' | 'low';

export interface DiseaseCandidate {
  id: string;
  name: string;
  tamilName: string;
  scientificName?: string;
  matchLevel: MatchLevel;
  matchedSymptoms: Symptom[];
  description?: string;
  tamilDescription?: string;
}

// ─── Image Types ─────────────────────────────────────────────────────────────

export interface DiseaseImage {
  id: string;
  diseaseId: string;
  imageUrl: string;
  description: string;
  tamilDescription: string;
  source: string;
  sourceUrl?: string;
}

// ─── Treatment Types ─────────────────────────────────────────────────────────

export interface TreatmentStep {
  text: string;
  tamilText: string;
  icon?: string;
}

export interface Treatment {
  diseaseId: string;
  diseaseName: string;
  tamilDiseaseName: string;
  management: TreatmentStep[];
  prevention: TreatmentStep[];
  warnings: TreatmentStep[];
  source: string;
  sourceUrl?: string;
}

// ─── Session Types ───────────────────────────────────────────────────────────

export type DiagnosisStep =
  | 'idle'
  | 'recording'
  | 'transcribing'
  | 'extracting'
  | 'diagnosing'
  | 'confirming'
  | 'result'
  | 'treatment'
  | 'voice-response';

export interface DiagnosisSession {
  id: string;
  startedAt: string;
  completedAt?: string;
  currentStep: DiagnosisStep;
  audioUri?: string;
  transcript?: string;
  symptoms: Symptom[];
  candidates: DiseaseCandidate[];
  confirmedDisease?: DiseaseCandidate;
  confirmedImageId?: string;
  treatment?: Treatment;
}

// ─── History Types ───────────────────────────────────────────────────────────

export type DiagnosisStatus = 'completed' | 'incomplete' | 'no-match';

export interface DiagnosisHistory {
  id: string;
  date: string;
  cropName: string;
  tamilCropName: string;
  diseaseName?: string;
  tamilDiseaseName?: string;
  status: DiagnosisStatus;
  matchLevel?: MatchLevel;
  symptomCount: number;
  thumbnailUrl?: string;
}

// ─── API Service Interfaces ──────────────────────────────────────────────────

export interface ASRResult {
  transcript: string;
  confidence: number;
  language: 'ta' | 'en';
}

export interface SymptomExtractionResult {
  crop: string;
  tamilCrop: string;
  affectedPart: PlantPart;
  tamilAffectedPart: string;
  symptoms: Symptom[];
}
