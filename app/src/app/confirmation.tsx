/**
 * Confirmation Screen — Image Confirmation
 */

import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ProgressIndicator } from '@/components/ProgressIndicator';
import { DiseaseImageCard } from '@/components/DiseaseImageCard';
import { ConfirmationModal } from '@/components/ConfirmationModal';
import { LoadingState } from '@/components/LoadingState';
import { ErrorState } from '@/components/ErrorState';
import { getDiseaseImages } from '@/services/imageService';
import { confirmDisease } from '@/services/diagnosisService';
import { DiseaseCandidate, DiseaseImage } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { getDiseaseById } from '@/data/mockDiseases';
import { useLanguage } from '@/contexts/LanguageContext';

// Polyfill for useLocalSearchParams if using standard expo-router
import { useLocalSearchParams as useExpoSearchParams } from 'expo-router';
import { useRouter as useExpoRouter } from 'expo-router';


export default function ConfirmationScreen() {
  const router = useExpoRouter();
  const params = useExpoSearchParams();
  const diseaseId = params.diseaseId as string || 'early-blight'; 
  const { t } = useLanguage();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [images, setImages] = useState<DiseaseImage[]>([]);
  const [disease, setDisease] = useState<DiseaseCandidate | null>(null);
  
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  useEffect(() => {
    loadData();
  }, [diseaseId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const candidate = getDiseaseById(diseaseId);
      if (!candidate) throw new Error('Disease not found');
      setDisease(candidate);
      
      const imgs = await getDiseaseImages(diseaseId);
      setImages(imgs);
    } catch (err) {
      setError(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setShowConfirmModal(false);
    setLoading(true);
    await confirmDisease(diseaseId);
    
    router.replace({
      pathname: '/result',
      params: { diseaseId }
    });
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="confirm" />
        <View style={styles.contentCenter}>
          <LoadingState message={t('loading')} />
        </View>
      </View>
    );
  }

  if (error || !disease || images.length === 0) {
    return (
      <View style={styles.container}>
        <ProgressIndicator currentStep="confirm" />
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
      <ProgressIndicator currentStep="confirm" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{t('confirmImagesTitle')}</Text>
          <Text style={styles.headerSubtitle}>
            {t('confirmImagesSubtitle')}
          </Text>
        </View>

        <View style={styles.imagesList}>
          {images.map((image) => (
            <DiseaseImageCard
              key={image.id}
              image={image}
              isSelected={selectedImageId === image.id}
              onSelect={() => {
                setSelectedImageId(image.id);
                setShowConfirmModal(true);
              }}
            />
          ))}
        </View>
        
        <View style={styles.fallbackSection}>
           <Text style={styles.fallbackText}>{t('noImageMatches')}</Text>
           <Pressable
             onPress={() => router.back()}
             style={({ pressed }) => [
               styles.fallbackButton,
               pressed && styles.buttonPressed,
             ]}
           >
             <Text style={styles.fallbackButtonText}>{t('viewOtherDisease')}</Text>
           </Pressable>
        </View>
      </ScrollView>

      <ConfirmationModal
        visible={showConfirmModal}
        diseaseTamilName={disease.tamilName}
        diseaseEnglishName={disease.name}
        onConfirm={handleConfirm}
        onCancel={() => {
          setShowConfirmModal(false);
          setSelectedImageId(null);
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  safeArea: { flex: 1, backgroundColor: Colors.background },
  contentCenter: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: Spacing.xl, paddingTop: Spacing.md, gap: Spacing.xl },
  header: { gap: Spacing.xs },
  headerTitle: { fontSize: FontSizes.lg, fontWeight: '700', color: Colors.textPrimary, lineHeight: 28 },
  headerSubtitle: { fontSize: FontSizes.base, color: Colors.textSecondary, lineHeight: 24 },
  imagesList: { gap: Spacing.xl },
  fallbackSection: { alignItems: 'center', gap: Spacing.sm, marginTop: Spacing.lg, paddingTop: Spacing.lg, borderTopWidth: 1, borderTopColor: Colors.borderLight },
  fallbackText: { fontSize: FontSizes.sm, color: Colors.textSecondary },
  fallbackButton: { paddingVertical: Spacing.sm, paddingHorizontal: Spacing.lg, borderRadius: BorderRadius.full, backgroundColor: Colors.surfaceElevated, borderWidth: 1, borderColor: Colors.border },
  fallbackButtonText: { fontSize: FontSizes.sm, fontWeight: '600', color: Colors.textPrimary },
  buttonPressed: { opacity: 0.8 },
});
