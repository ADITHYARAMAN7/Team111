import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { SymptomExtractionResult, Symptom } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface SymptomCardProps {
  data: SymptomExtractionResult;
}

export function SymptomCard({ data }: SymptomCardProps) {
  const { t, language } = useLanguage();
  
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.headerIcon}>🔍</Text>
        <Text style={styles.headerText}>{t('extractedInfo')}</Text>
      </View>

      <View style={styles.infoRow}>
        <View style={styles.infoBadge}>
          <Text style={styles.infoBadgeIcon}>🌿</Text>
          <View>
            <Text style={styles.infoLabel}>{t('crop')}</Text>
            <Text style={styles.infoValue}>
               {language === 'ta' ? data.tamilCrop : data.crop}
            </Text>
          </View>
        </View>
        <View style={styles.infoBadge}>
          <Text style={styles.infoBadgeIcon}>📍</Text>
          <View>
            <Text style={styles.infoLabel}>{t('affectedPart')}</Text>
            <Text style={styles.infoValue}>
               {language === 'ta' ? data.tamilAffectedPart : data.affectedPart}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.symptomsSection}>
        <Text style={styles.sectionTitle}>{t('symptoms')}:</Text>
        {data.symptoms.map((symptom, index) => (
          <SymptomRow key={symptom.id} symptom={symptom} index={index} />
        ))}
      </View>
    </View>
  );
}

function SymptomRow({ symptom, index }: { symptom: Symptom; index: number }) {
  const { language } = useLanguage();
  return (
    <View style={styles.symptomRow}>
      <View style={styles.symptomNumber}>
        <Text style={styles.symptomNumberText}>{index + 1}</Text>
      </View>
      <Text style={styles.symptomText}>
         {language === 'ta' ? symptom.tamilName : symptom.name}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: Colors.surface, borderRadius: BorderRadius.lg, padding: Spacing.xl, ...Shadows.sm },
  header: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.lg, paddingBottom: Spacing.sm, borderBottomWidth: 1, borderBottomColor: Colors.borderLight },
  headerIcon: { fontSize: 24 },
  headerText: { fontSize: FontSizes.lg, fontWeight: '700', color: Colors.primaryDark },
  infoRow: { flexDirection: 'row', gap: Spacing.md, marginBottom: Spacing.lg },
  infoBadge: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, backgroundColor: Colors.surfaceElevated, padding: Spacing.md, borderRadius: BorderRadius.md, borderWidth: 1, borderColor: Colors.borderLight },
  infoBadgeIcon: { fontSize: 24 },
  infoLabel: { fontSize: FontSizes.xs, color: Colors.textSecondary, marginBottom: 2 },
  infoValue: { fontSize: FontSizes.base, fontWeight: '600', color: Colors.textPrimary },
  symptomsSection: { gap: Spacing.sm },
  sectionTitle: { fontSize: FontSizes.sm, fontWeight: '600', color: Colors.textSecondary, marginBottom: Spacing.xs },
  symptomRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  symptomNumber: { width: 28, height: 28, borderRadius: 14, backgroundColor: Colors.primaryLight + '30', alignItems: 'center', justifyContent: 'center' },
  symptomNumberText: { fontSize: FontSizes.sm, fontWeight: '700', color: Colors.primaryDark },
  symptomText: { flex: 1, fontSize: FontSizes.base, color: Colors.textPrimary },
});
