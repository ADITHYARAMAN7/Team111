/**
 * TTS (Text-to-Speech) Service
 * Uses expo-speech for Tamil text-to-speech.
 */

import { DiseaseCandidate, Treatment } from '@/types/diagnosis';

// ─── Integration Point ──────────────────────────────────────────────────────
// Currently uses expo-speech (basic TTS).
// Can be upgraded to a dedicated Tamil TTS service for better quality:
// - AI4Bharat IndicTTS
// - Google Cloud TTS (Tamil)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Generates a Tamil summary text for TTS playback.
 */
export function generateTamilResponse(
  disease: DiseaseCandidate,
  treatment: Treatment
): string {
  const intro = `கண்டறியப்பட்ட நோய்: ${disease.tamilName}.`;
  
  const managementSummary = treatment.management
    .slice(0, 2)
    .map((m) => m.tamilText)
    .join('. ');

  const preventionSummary = treatment.prevention
    .slice(0, 2)
    .map((p) => p.tamilText)
    .join('. ');

  const warningSummary = treatment.warnings.length > 0
    ? `கவனிக்கவும்: ${treatment.warnings[0].tamilText}`
    : '';

  return [
    intro,
    `சிகிச்சை: ${managementSummary}.`,
    `தடுப்பு: ${preventionSummary}.`,
    warningSummary,
  ]
    .filter(Boolean)
    .join(' ');
}

/**
 * Speaks Tamil text using expo-speech.
 * In production, may use a higher-quality dedicated Tamil TTS API.
 */
export async function speakTamil(text: string): Promise<void> {
  // Dynamic import to avoid crash if expo-speech is not installed yet
  try {
    const Speech = await import('expo-speech');
    return new Promise((resolve, reject) => {
      Speech.speak(text, {
        language: 'ta-IN',
        rate: 0.85,
        onDone: () => resolve(),
        onError: (error) => reject(error),
      });
    });
  } catch {
    // Fallback: log the text that would be spoken
    console.log('[TTS Mock] Would speak:', text);
    return new Promise((resolve) => setTimeout(resolve, 2000));
  }
}

/**
 * Stops any ongoing speech.
 */
export async function stopSpeaking(): Promise<void> {
  try {
    const Speech = await import('expo-speech');
    Speech.stop();
  } catch {
    console.log('[TTS Mock] Stop speaking');
  }
}
