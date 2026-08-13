/**
 * ASR (Automatic Speech Recognition) Service
 * Mock implementation — will connect to AI4Bharat IndicConformer Tamil ASR.
 */

import { ASRResult } from '@/types/diagnosis';
import { MOCK_TRANSCRIPT } from '@/data/mockDiseases';

// ─── Integration Point ──────────────────────────────────────────────────────
// Replace these mock implementations with:
// - expo-audio for recording
// - AI4Bharat IndicConformer API for Tamil ASR transcription
// ─────────────────────────────────────────────────────────────────────────────

const SIMULATED_RECORDING_DURATION_MS = 3000;

/**
 * Simulates audio recording.
 * In production, will use expo-audio to record from device microphone.
 */
export async function recordAudio(): Promise<string> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve('mock://recording-' + Date.now() + '.wav');
    }, SIMULATED_RECORDING_DURATION_MS);
  });
}

/**
 * Simulates audio transcription.
 * In production, will send audio to AI4Bharat IndicConformer Tamil ASR API.
 */
export async function transcribeAudio(_audioUri: string): Promise<ASRResult> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        transcript: MOCK_TRANSCRIPT,
        confidence: 0.87,
        language: 'ta',
      });
    }, 1500);
  });
}
