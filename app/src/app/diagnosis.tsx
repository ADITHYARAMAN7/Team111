/**
 * Diagnosis Screen — Disease Analysis
 */

import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ProgressIndicator } from '@/components/ProgressIndicator';
import { DiseaseCard } from '@/components/DiseaseCard';
import { LoadingState } from '@/components/LoadingState';
import { ErrorState } from '@/components/ErrorState';
import { getDiseaseCandidates } from '@/services/diagnosisService';
import { DiseaseCandidate } from '@/types/diagnosis';
import { MOCK_SYMPTOMS_RESULT } from '@/data/mockDiseases';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export default function DiagnosisScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<DiseaseCandidate[]>([]);
  const [selectedDiseaseId, setSelectedDiseaseId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const results = await getDiseaseCandidates(MOCK_SYMPTOMS_RESULT.symptoms);
      setCandidates(results);
      if (results.length > 0) {
        setSelectedDiseaseId(results[0].id);
      }
    } catch (err) {
      setError(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    if (selectedDiseaseId) {
      router.push({
        pathname: '/confirmation',
        params: { diseaseId: selectedDiseaseId }
      });
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="analysis" />
        <View style={styles.contentCenter}>
          <LoadingState message={t('loading')} />
        </View>
      </View>
    );
  }

  if (error || candidates.length === 0) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="analysis" />
        <ErrorState
          title={t('noMatchTitle')}
          message={error || t('noMatchMessage')}
          onRetry={loadData}
        />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ProgressIndicator currentStep="analysis" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{t('possibleDiseasesTitle')}</Text>
          <Text style={styles.headerSubtitle}>
            {t('possibleDiseasesSubtitle')}
          </Text>
        </View>

        <View style={styles.candidatesList}>
          {candidates.map((candidate) => (
            <DiseaseCard
              key={candidate.id}
              disease={candidate}
              isSelected={candidate.id === selectedDiseaseId}
              onPress={() => setSelectedDiseaseId(candidate.id)}
            />
          ))}
        </View>

        <Pressable
          onPress={handleContinue}
          disabled={!selectedDiseaseId}
          style={({ pressed }) => [
            styles.primaryButton,
            !selectedDiseaseId && styles.buttonDisabled,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>{t('confirmWithImagesBtn')}</Text>
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
  header: { gap: Spacing.xs },
  headerTitle: { fontSize: FontSizes.lg, fontWeight: '700', color: Colors.textPrimary },
  headerSubtitle: { fontSize: FontSizes.base, color: Colors.textSecondary },
  candidatesList: { gap: Spacing.md },
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
  buttonDisabled: { backgroundColor: Colors.border },
  buttonPressed: { opacity: 0.9, transform: [{ scale: 0.98 }] },
  primaryButtonText: { color: Colors.white, fontSize: FontSizes.md, fontWeight: '700' },
});
