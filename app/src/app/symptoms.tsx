/**
 * Symptoms Screen — Transcript & Extracted Symptoms
 */

import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ProgressIndicator } from '@/components/ProgressIndicator';
import { TranscriptCard } from '@/components/TranscriptCard';
import { SymptomCard } from '@/components/SymptomCard';
import { LoadingState } from '@/components/LoadingState';
import { ErrorState } from '@/components/ErrorState';
import { extractSymptoms } from '@/services/symptomService';
import { transcribeAudio as getTranscription } from '@/services/asrService';
import { SymptomExtractionResult, ASRResult } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export default function SymptomsScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transcriptData, setTranscriptData] = useState<ASRResult | null>(null);
  const [symptomsData, setSymptomsData] = useState<SymptomExtractionResult | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const asr = await getTranscription('mock-uri');
      setTranscriptData(asr);
      
      const symptoms = await extractSymptoms(asr.transcript);
      setSymptomsData(symptoms);
      
    } catch (err) {
      setError(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const handleDiagnose = () => {
    router.push('/diagnosis');
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="symptoms" />
        <View style={styles.contentCenter}>
          <LoadingState message={t('loading')} />
        </View>
      </View>
    );
  }

  if (error || !transcriptData || !symptomsData) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="symptoms" />
        <ErrorState
          title={t('error')}
          message={error || t('error')}
          onRetry={loadData}
        />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ProgressIndicator currentStep="symptoms" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.section}>
          <TranscriptCard
            transcript={transcriptData.transcript}
            onPlayAudio={() => console.log('Play audio')}
          />
        </View>

        <View style={styles.section}>
          <SymptomCard data={symptomsData} />
        </View>

        <Pressable
          onPress={handleDiagnose}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>{t('diagnoseBtn')}</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  safeArea: { flex: 1, backgroundColor: Colors.background },
  contentCenter: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: Spacing.xl, paddingTop: Spacing.md, gap: Spacing.xl },
  section: { gap: Spacing.md },
  primaryButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.md,
    minHeight: TouchTargets.button,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: Spacing.md,
    ...Shadows.md,
  },
  buttonPressed: { opacity: 0.9, transform: [{ scale: 0.98 }] },
  primaryButtonText: { color: Colors.white, fontSize: FontSizes.lg, fontWeight: '700' },
});
