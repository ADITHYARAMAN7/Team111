/**
 * Result Screen — Diagnosis Result
 */

import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { getDiseaseById } from '@/data/mockDiseases';
import { getImagesByDiseaseId } from '@/data/mockImages';
import { DiseaseCandidate, DiseaseImage } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export default function ResultScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const diseaseId = params.diseaseId as string;
  const { t, language } = useLanguage();

  const [loading, setLoading] = useState(true);
  const [disease, setDisease] = useState<DiseaseCandidate | null>(null);
  const [image, setImage] = useState<DiseaseImage | null>(null);

  useEffect(() => {
    if (diseaseId) {
      const candidate = getDiseaseById(diseaseId);
      setDisease(candidate || null);
      
      const images = getImagesByDiseaseId(diseaseId);
      if (images.length > 0) {
        setImage(images[0]);
      }
    }
    setLoading(false);
  }, [diseaseId]);

  const handleContinue = () => {
    router.push({
      pathname: '/treatment',
      params: { diseaseId }
    });
  };

  const handleHome = () => {
    router.dismissAll();
    router.replace('/(tabs)');
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.contentCenter}>
          <LoadingState message={t('loading')} />
        </View>
      </View>
    );
  }

  if (!disease) {
    return (
      <View style={styles.container}>
        <ErrorState
          title={t('missingDataTitle')}
          message={t('missingDataMessage')}
          onRetry={handleHome}
          retryLabel={t('goToHome')}
        />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.successBadge}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successText}>{t('diseaseConfirmed')}</Text>
        </View>

        <View style={styles.resultCard}>
          {image && (
            <View style={styles.imagePlaceholder}>
              <Text style={styles.imagePlaceholderIcon}>🍅</Text>
            </View>
          )}
          
          <View style={styles.nameSection}>
            <Text style={styles.mainName}>
              {language === 'ta' ? disease.tamilName : disease.name}
            </Text>
            <Text style={styles.subName}>
              {language === 'ta' ? disease.name : disease.tamilName}
            </Text>
            {disease.scientificName && (
              <Text style={styles.scientificName}>{disease.scientificName}</Text>
            )}
          </View>

          <View style={styles.verificationBadge}>
            <Text style={styles.verificationIcon}>✓</Text>
            <Text style={styles.verificationText}>{t('verificationBadge')}</Text>
          </View>

          <View style={styles.symptomsBox}>
            <Text style={styles.symptomsTitle}>{t('keySymptomsTitle')}</Text>
            {disease.matchedSymptoms.map((sym) => (
              <Text key={sym.id} style={styles.symptomItem}>
                • {language === 'ta' ? sym.tamilName : sym.name}
              </Text>
            ))}
          </View>
        </View>

        <Pressable
          onPress={handleContinue}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>{t('viewTreatmentsBtn')}</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  safeArea: { flex: 1, backgroundColor: Colors.background },
  contentCenter: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: Spacing.xl, paddingTop: Spacing.md, gap: Spacing.xl, alignItems: 'center' },
  successBadge: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.sm,
    backgroundColor: Colors.successLight, paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.lg, borderRadius: BorderRadius.full,
    borderWidth: 1, borderColor: Colors.primary + '30',
  },
  successIcon: { fontSize: 20 },
  successText: { fontSize: FontSizes.base, fontWeight: '700', color: Colors.primaryDark },
  resultCard: { width: '100%', backgroundColor: Colors.surface, borderRadius: BorderRadius.xl, overflow: 'hidden', ...Shadows.lg },
  imagePlaceholder: { height: 200, backgroundColor: Colors.surfaceElevated, alignItems: 'center', justifyContent: 'center' },
  imagePlaceholderIcon: { fontSize: 64 },
  nameSection: { padding: Spacing.xl, alignItems: 'center', gap: 4, borderBottomWidth: 1, borderBottomColor: Colors.borderLight },
  mainName: { fontSize: FontSizes.xl, fontWeight: '800', color: Colors.textPrimary, textAlign: 'center' },
  subName: { fontSize: FontSizes.md, color: Colors.textSecondary, textAlign: 'center' },
  scientificName: { fontSize: FontSizes.sm, color: Colors.textTertiary, fontStyle: 'italic', textAlign: 'center', marginTop: 4 },
  verificationBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: Spacing.xs, paddingVertical: Spacing.md, backgroundColor: '#F5FAFF', borderBottomWidth: 1, borderBottomColor: Colors.borderLight },
  verificationIcon: { fontSize: 16, color: '#0284C7', fontWeight: '700' },
  verificationText: { fontSize: FontSizes.sm, color: '#0284C7', fontWeight: '600' },
  symptomsBox: { padding: Spacing.xl, gap: Spacing.sm },
  symptomsTitle: { fontSize: FontSizes.base, fontWeight: '600', color: Colors.textSecondary, marginBottom: Spacing.xs },
  symptomItem: { fontSize: FontSizes.base, color: Colors.textPrimary, lineHeight: 24 },
  primaryButton: { width: '100%', backgroundColor: Colors.primary, borderRadius: BorderRadius.md, paddingVertical: Spacing.lg, minHeight: TouchTargets.button, alignItems: 'center', justifyContent: 'center', ...Shadows.md },
  buttonPressed: { opacity: 0.9, transform: [{ scale: 0.98 }] },
  primaryButtonText: { color: Colors.white, fontSize: FontSizes.lg, fontWeight: '700' },
});
