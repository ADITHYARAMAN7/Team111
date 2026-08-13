import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { DiseaseCandidate } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface DiseaseCardProps {
  disease: DiseaseCandidate;
  isSelected?: boolean;
  onPress?: () => void;
}

export function DiseaseCard({ disease, isSelected, onPress }: DiseaseCardProps) {
  const { t, language } = useLanguage();

  const getMatchConfig = () => {
    switch (disease.matchLevel) {
      case 'high': return { color: Colors.matchHigh, bg: '#F0FDF4', label: t('matchHigh'), icon: '🟢' };
      case 'medium': return { color: Colors.matchMedium, bg: '#FEFCE8', label: t('matchMedium'), icon: '🟡' };
      case 'low': return { color: Colors.matchLow, bg: '#FEF2F2', label: t('matchLow'), icon: '🔴' };
    }
  };

  const matchConfig = getMatchConfig();

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        isSelected && styles.cardSelected,
        pressed && styles.cardPressed,
      ]}
    >
      <View style={styles.header}>
        <View style={styles.titleArea}>
          <Text style={styles.mainName}>
             {language === 'ta' ? disease.tamilName : disease.name}
          </Text>
          <Text style={styles.subName}>
             {language === 'ta' ? disease.name : disease.tamilName}
          </Text>
        </View>
        <View style={[styles.matchBadge, { backgroundColor: matchConfig.bg }]}>
          <Text style={styles.matchIcon}>{matchConfig.icon}</Text>
          <Text style={[styles.matchText, { color: matchConfig.color }]}>
            {matchConfig.label}
          </Text>
        </View>
      </View>

      <View style={styles.divider} />

      <View style={styles.symptomsBox}>
        <Text style={styles.symptomsLabel}>{t('matchedSymptomsLabel')}</Text>
        <Text style={styles.symptomsText} numberOfLines={2}>
          {disease.matchedSymptoms.map(s => language === 'ta' ? s.tamilName : s.name).join(' • ')}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: Colors.surface, borderRadius: BorderRadius.md, padding: Spacing.xl, borderWidth: 2, borderColor: Colors.borderLight, ...Shadows.sm },
  cardSelected: { borderColor: Colors.primary, backgroundColor: Colors.primaryLight + '10' },
  cardPressed: { opacity: 0.9, transform: [{ scale: 0.98 }] },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: Spacing.md },
  titleArea: { flex: 1, gap: 2 },
  mainName: { fontSize: FontSizes.lg, fontWeight: '700', color: Colors.textPrimary },
  subName: { fontSize: FontSizes.sm, color: Colors.textSecondary },
  matchBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  matchIcon: { fontSize: 10 },
  matchText: { fontSize: FontSizes.xs, fontWeight: '700' },
  divider: { height: 1, backgroundColor: Colors.borderLight, marginVertical: Spacing.md },
  symptomsBox: { gap: 4 },
  symptomsLabel: { fontSize: FontSizes.xs, fontWeight: '600', color: Colors.textTertiary, textTransform: 'uppercase' },
  symptomsText: { fontSize: FontSizes.sm, color: Colors.textSecondary, lineHeight: 20 },
});
