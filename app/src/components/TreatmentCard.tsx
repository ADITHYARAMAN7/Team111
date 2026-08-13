import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Treatment } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface TreatmentCardProps {
  treatment: Treatment;
}

export function TreatmentCard({ treatment }: TreatmentCardProps) {
  const { t, language } = useLanguage();
  
  return (
    <View style={styles.card}>
      <View style={styles.section}>
        <View style={styles.headerRow}>
          <Text style={styles.headerIcon}>💊</Text>
          <Text style={styles.headerText}>{t('whatToDo')}</Text>
        </View>
        <View style={styles.list}>
          {treatment.management.map((step, index) => (
            <View key={index} style={styles.listItem}>
              <Text style={styles.bullet}>•</Text>
              <Text style={styles.listText}>
                {language === 'ta' ? step.tamilText : step.text}
              </Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.divider} />

      <View style={styles.section}>
        <View style={styles.headerRow}>
          <Text style={styles.headerIcon}>🛡️</Text>
          <Text style={styles.headerText}>{t('prevention')}</Text>
        </View>
        <View style={styles.list}>
          {treatment.prevention.map((item, index) => (
            <View key={index} style={styles.listItem}>
              <Text style={styles.bullet}>•</Text>
              <Text style={styles.listText}>
                {language === 'ta' ? item.tamilText : item.text}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {treatment.warnings && treatment.warnings.length > 0 && (
        <>
          <View style={styles.divider} />
          <View style={styles.section}>
            <View style={styles.headerRow}>
              <Text style={styles.headerIcon}>⚠️</Text>
              <Text style={[styles.headerText, { color: Colors.warning }]}>
                {t('warnings')}
              </Text>
            </View>
            <View style={styles.list}>
              {treatment.warnings.map((warning, index) => (
                <View key={index} style={styles.listItem}>
                  <Text style={[styles.bullet, { color: Colors.warning }]}>!</Text>
                  <Text style={styles.listText}>
                    {language === 'ta' ? warning.tamilText : warning.text}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: Colors.surface, borderRadius: BorderRadius.lg, padding: Spacing.xl, ...Shadows.sm },
  section: { gap: Spacing.sm },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.xs },
  headerIcon: { fontSize: 20 },
  headerText: { fontSize: FontSizes.md, fontWeight: '700', color: Colors.textPrimary },
  list: { gap: Spacing.sm },
  listItem: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm, paddingLeft: Spacing.sm },
  bullet: { fontSize: FontSizes.base, color: Colors.primary, fontWeight: '700', marginTop: -2 },
  listText: { flex: 1, fontSize: FontSizes.base, color: Colors.textSecondary, lineHeight: 24 },
  divider: { height: 1, backgroundColor: Colors.borderLight, marginVertical: Spacing.lg },
});
