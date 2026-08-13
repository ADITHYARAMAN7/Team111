/**
 * History Screen — Past Diagnosis Sessions
 */

import React, { useEffect, useState } from 'react';
import { FlatList, StyleSheet, Text, View, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';

import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { getHistory } from '@/services/historyService';
import { DiagnosisHistory, DiagnosisStatus, MatchLevel } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export default function HistoryScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<DiagnosisHistory[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getHistory();
      setHistory(data);
    } catch (err) {
      setError(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const handleItemPress = (item: DiagnosisHistory) => {
    if (item.status === 'completed' && item.diseaseName) {
      const mockDiseaseId = item.diseaseName.toLowerCase().replace(/ /g, '-');
      router.push({
        pathname: '/result',
        params: { diseaseId: mockDiseaseId }
      });
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <LoadingState message={t('loading')} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <ErrorState title={t('error')} message={error} onRetry={loadData} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <FlatList
        data={history}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📝</Text>
            <Text style={styles.emptyText}>{t('noHistoryTitle')}</Text>
          </View>
        }
        renderItem={({ item }) => (
          <HistoryItem item={item} onPress={() => handleItemPress(item)} />
        )}
      />
    </SafeAreaView>
  );
}

function HistoryItem({ item, onPress }: { item: DiagnosisHistory; onPress: () => void }) {
  const { t, language } = useLanguage();
  
  const date = new Date(item.date).toLocaleDateString(language === 'ta' ? 'ta-IN' : 'en-US', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });

  const getStatusConfig = (status: DiagnosisStatus, matchLevel?: MatchLevel) => {
    if (status !== 'completed') {
      return { icon: '⏳', color: Colors.textTertiary, text: t('statusIncomplete') };
    }
    if (matchLevel === 'high') return { icon: '✅', color: Colors.matchHigh, text: t('statusHighMatch') };
    if (matchLevel === 'medium') return { icon: '⚠️', color: Colors.matchMedium, text: t('statusMediumMatch') };
    return { icon: '❓', color: Colors.matchLow, text: t('statusLowMatch') };
  };

  const statusConfig = getStatusConfig(item.status, item.matchLevel);

  return (
    <Pressable
      onPress={onPress}
      disabled={item.status !== 'completed'}
      style={({ pressed }) => [
        styles.historyCard,
        pressed && item.status === 'completed' && styles.cardPressed,
      ]}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.date}>{date}</Text>
        <View style={styles.statusBadge}>
          <Text style={styles.statusIcon}>{statusConfig.icon}</Text>
          <Text style={[styles.statusText, { color: statusConfig.color }]}>
            {statusConfig.text}
          </Text>
        </View>
      </View>

      <View style={styles.cardContent}>
        <View style={styles.cropBadge}>
          <Text style={styles.cropIcon}>🌿</Text>
          <Text style={styles.cropName}>{language === 'ta' ? item.tamilCropName : item.cropName}</Text>
        </View>

        {item.diseaseName ? (
          <Text style={styles.diseaseName}>
            {language === 'ta' ? item.tamilDiseaseName : item.diseaseName}
          </Text>
        ) : (
          <Text style={styles.noDiseaseText}>{t('noDiseaseDetected')}</Text>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  safeArea: { flex: 1, backgroundColor: Colors.background },
  listContent: { padding: Spacing.base, gap: Spacing.md },
  emptyState: { padding: Spacing.xxl, alignItems: 'center', justifyContent: 'center', gap: Spacing.md, marginTop: Spacing.xxl },
  emptyIcon: { fontSize: 48 },
  emptyText: { fontSize: FontSizes.base, color: Colors.textSecondary, textAlign: 'center' },
  historyCard: { backgroundColor: Colors.surface, borderRadius: BorderRadius.md, padding: Spacing.base, gap: Spacing.md, borderWidth: 1, borderColor: Colors.borderLight, ...Shadows.sm },
  cardPressed: { opacity: 0.8, transform: [{ scale: 0.98 }] },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: Colors.borderLight, paddingBottom: Spacing.sm },
  date: { fontSize: FontSizes.sm, color: Colors.textSecondary, fontWeight: '500' },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  statusIcon: { fontSize: 12 },
  statusText: { fontSize: FontSizes.xs, fontWeight: '600' },
  cardContent: { gap: Spacing.sm },
  cropBadge: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xs, backgroundColor: Colors.surfaceElevated, alignSelf: 'flex-start', paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  cropIcon: { fontSize: 14 },
  cropName: { fontSize: FontSizes.xs, color: Colors.textSecondary, fontWeight: '500' },
  diseaseName: { fontSize: FontSizes.lg, fontWeight: '700', color: Colors.textPrimary },
  noDiseaseText: { fontSize: FontSizes.base, color: Colors.textTertiary, fontStyle: 'italic' },
});
