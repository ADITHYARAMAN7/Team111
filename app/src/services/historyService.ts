/**
 * History Service
 * Persists diagnosis sessions using AsyncStorage.
 */

import { DiagnosisHistory, DiagnosisSession } from '@/types/diagnosis';

// ─── Integration Point ──────────────────────────────────────────────────────
// Currently uses AsyncStorage for local persistence.
// Can be upgraded to a cloud backend for cross-device sync.
// ─────────────────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'diagnosis_history';

// Mock history data for prototype
const MOCK_HISTORY: DiagnosisHistory[] = [
  {
    id: 'hist-1',
    date: '2026-08-10T09:30:00+05:30',
    cropName: 'Tomato',
    tamilCropName: 'தக்காளி',
    diseaseName: 'Early Blight',
    tamilDiseaseName: 'ஆரம்ப கருகல் நோய்',
    status: 'completed',
    matchLevel: 'high',
    symptomCount: 3,
  },
  {
    id: 'hist-2',
    date: '2026-08-08T14:15:00+05:30',
    cropName: 'Tomato',
    tamilCropName: 'தக்காளி',
    diseaseName: 'Yellow Leaf Curl Virus',
    tamilDiseaseName: 'மஞ்சள் இலை சுருட்டு வைரஸ்',
    status: 'completed',
    matchLevel: 'high',
    symptomCount: 3,
  },
  {
    id: 'hist-3',
    date: '2026-08-05T11:00:00+05:30',
    cropName: 'Tomato',
    tamilCropName: 'தக்காளி',
    status: 'incomplete',
    symptomCount: 1,
  },
  {
    id: 'hist-4',
    date: '2026-08-01T16:45:00+05:30',
    cropName: 'Tomato',
    tamilCropName: 'தக்காளி',
    diseaseName: 'Leaf Mold',
    tamilDiseaseName: 'இலை பூஞ்சை நோய்',
    status: 'completed',
    matchLevel: 'medium',
    symptomCount: 2,
  },
];

/**
 * Saves a completed diagnosis session to history.
 */
export async function saveSession(
  _session: DiagnosisSession
): Promise<void> {
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    const existing = await AsyncStorage.getItem(STORAGE_KEY);
    const history: DiagnosisHistory[] = existing ? JSON.parse(existing) : [];
    
    const entry: DiagnosisHistory = {
      id: _session.id,
      date: _session.startedAt,
      cropName: 'Tomato',
      tamilCropName: 'தக்காளி',
      diseaseName: _session.confirmedDisease?.name,
      tamilDiseaseName: _session.confirmedDisease?.tamilName,
      status: _session.confirmedDisease ? 'completed' : 'incomplete',
      matchLevel: _session.confirmedDisease?.matchLevel,
      symptomCount: _session.symptoms.length,
    };

    history.unshift(entry);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch {
    console.log('[History] Failed to save session — using mock storage');
  }
}

/**
 * Retrieves diagnosis history.
 */
export async function getHistory(): Promise<DiagnosisHistory[]> {
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    const data = await AsyncStorage.getItem(STORAGE_KEY);
    if (data) {
      return JSON.parse(data);
    }
  } catch {
    console.log('[History] Failed to load — returning mock data');
  }
  return MOCK_HISTORY;
}

/**
 * Gets a specific past session by ID.
 */
export async function getSessionById(
  id: string
): Promise<DiagnosisHistory | undefined> {
  const history = await getHistory();
  return history.find((h) => h.id === id);
}
