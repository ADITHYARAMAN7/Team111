/**
 * Voice Response Screen — Tamil Text-to-Speech
 */

import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ScrollView, Pressable } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { TamilVoiceButton } from '@/components/TamilVoiceButton';
import { generateTamilResponse, speakTamil, stopSpeaking } from '@/services/ttsService';
import { getDiseaseById } from '@/data/mockDiseases';
import { getTreatment } from '@/services/treatmentService';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export default function VoiceResponseScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const diseaseId = params.diseaseId as string;
  const { t } = useLanguage();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [speechText, setSpeechText] = useState('');

  useEffect(() => {
    loadData();
    return () => {
      stopSpeaking();
    };
  }, [diseaseId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const disease = getDiseaseById(diseaseId);
      const treatment = await getTreatment(diseaseId);
      
      if (!disease || !treatment) throw new Error('Data not found');
      
      const text = generateTamilResponse(disease, treatment);
      setSpeechText(text);
      
      speakTamil(text).catch((err) => console.log('TTS Error:', err));
    } catch (err) {
      setError(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = async () => {
    await speakTamil(speechText);
  };

  const handleHome = () => {
    stopSpeaking();
    router.dismissAll();
    router.replace('/(tabs)');
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.contentCenter}>
          <LoadingState message={t('preparingAudio')} />
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <ErrorState
          title={t('error')}
          message={error}
          onRetry={loadData}
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
        <View style={styles.speakerIconContainer}>
          <Text style={styles.speakerIcon}>🗣️</Text>
        </View>

        <View style={styles.transcriptCard}>
          <Text style={styles.transcriptText}>{speechText}</Text>
        </View>

        <View style={styles.controls}>
          <TamilVoiceButton onPress={handlePlay} label={t('listenAgain')} />
          
          <Pressable
            onPress={handleHome}
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.buttonPressed,
            ]}
          >
            <Text style={styles.secondaryButtonText}>{t('returnHome')}</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  safeArea: { flex: 1, backgroundColor: Colors.background },
  contentCenter: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: Spacing.xl, paddingTop: Spacing.xxl, gap: Spacing.xxl, alignItems: 'center' },
  speakerIconContainer: { width: 100, height: 100, borderRadius: 50, backgroundColor: Colors.tamilGold + '30', alignItems: 'center', justifyContent: 'center' },
  speakerIcon: { fontSize: 56 },
  transcriptCard: { width: '100%', backgroundColor: Colors.surface, borderRadius: BorderRadius.lg, padding: Spacing.xl, borderLeftWidth: 4, borderLeftColor: Colors.tamilGold, ...Shadows.sm },
  transcriptText: { fontSize: FontSizes.lg, color: Colors.textPrimary, lineHeight: 32, textAlign: 'center' },
  controls: { width: '100%', gap: Spacing.lg, marginTop: Spacing.xl },
  secondaryButton: { width: '100%', paddingVertical: Spacing.md, borderRadius: BorderRadius.md, backgroundColor: Colors.surfaceElevated, borderWidth: 1, borderColor: Colors.border, minHeight: TouchTargets.button, alignItems: 'center', justifyContent: 'center' },
  secondaryButtonText: { fontSize: FontSizes.base, fontWeight: '600', color: Colors.textSecondary },
  buttonPressed: { opacity: 0.8, transform: [{ scale: 0.98 }] },
});
