/**
 * Treatment Screen — Treatment & Prevention
 */

import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ProgressIndicator } from '@/components/ProgressIndicator';
import { TreatmentCard } from '@/components/TreatmentCard';
import { SourceCard } from '@/components/SourceCard';
import { TamilVoiceButton } from '@/components/TamilVoiceButton';
import { LoadingState } from '@/components/LoadingState';
import { ErrorState } from '@/components/ErrorState';
import { getTreatment } from '@/services/treatmentService';
import { Treatment } from '@/types/diagnosis';
import { Colors, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export default function TreatmentScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const diseaseId = params.diseaseId as string;
  const { t } = useLanguage();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [treatment, setTreatment] = useState<Treatment | null>(null);

  useEffect(() => {
    loadData();
  }, [diseaseId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTreatment(diseaseId);
      if (!data) throw new Error('Treatment not found');
      setTreatment(data);
    } catch (err) {
      setError(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const handleListen = async () => {
    router.push({
      pathname: '/voice-response',
      params: { diseaseId }
    });
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="treatment" />
        <View style={styles.contentCenter}>
          <LoadingState message={t('loading')} />
        </View>
      </View>
    );
  }

  if (error || !treatment) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="treatment" />
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
      <ProgressIndicator currentStep="treatment" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <TreatmentCard treatment={treatment} />
        
        <View style={styles.bottomSection}>
          <SourceCard source={treatment.source} sourceUrl={treatment.sourceUrl || ''} />
          <TamilVoiceButton onPress={handleListen} label={t('listenInTamil')} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  safeArea: { flex: 1, backgroundColor: Colors.background },
  contentCenter: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: Spacing.xl, paddingTop: Spacing.md, gap: Spacing.xl },
  bottomSection: { gap: Spacing.xl, marginTop: Spacing.md },
});
