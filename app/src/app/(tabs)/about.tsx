/**
 * About Screen — App Info & Settings
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { ExternalLink } from '@/components/external-link';
import { useLanguage } from '@/contexts/LanguageContext';

export default function AboutScreen() {
  const { t } = useLanguage();

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.appInfoSection}>
          <View style={styles.iconPlaceholder}>
            <Text style={styles.iconEmoji}>🍅</Text>
          </View>
          <Text style={styles.appName}>{t('appTitle')}</Text>
          <Text style={styles.version}>{t('versionInfo')}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('aboutTitle')}</Text>
          <View style={styles.card}>
            <Text style={styles.descriptionText}>
              {t('aboutDescription')}
            </Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('dataSourcesTitle')}</Text>
          <View style={styles.card}>
            <SourceItem
              title={t('sourceTreatments')}
              source="TNAU Agritech Portal"
              url="https://agritech.tnau.ac.in"
            />
            <View style={styles.divider} />
            <SourceItem
              title={t('sourceImages')}
              source="PlantVillage Dataset & PlantDoc"
              url="https://plantvillage.psu.edu"
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('settingsTitle')}</Text>
          <View style={styles.card}>
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>{t('languageLabel')}</Text>
              <View style={styles.settingValueBadge}>
                <Text style={styles.settingValueText}>தமிழ் (Tamil) / English</Text>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.disclaimerSection}>
          <Text style={styles.disclaimerTitle}>{t('disclaimerTitle')}</Text>
          <Text style={styles.disclaimerText}>
            {t('disclaimerFullText')}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function SourceItem({ title, source, url }: { title: string; source: string; url: string }) {
  return (
    <View style={styles.sourceItem}>
      <Text style={styles.sourceTitle}>{title}</Text>
      <Text style={styles.sourceName}>{source}</Text>
      <ExternalLink href={url as any}>
        <Text style={styles.sourceUrl}>{url}</Text>
      </ExternalLink>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: Colors.background },
  scrollContent: { padding: Spacing.xl, gap: Spacing.xl, paddingBottom: Spacing.xxl },
  appInfoSection: { alignItems: 'center', gap: Spacing.sm, paddingVertical: Spacing.lg },
  iconPlaceholder: { width: 80, height: 80, borderRadius: 24, backgroundColor: Colors.primaryLight + '20', alignItems: 'center', justifyContent: 'center', marginBottom: Spacing.sm },
  iconEmoji: { fontSize: 48 },
  appName: { fontSize: FontSizes.lg, fontWeight: '700', color: Colors.primaryDark },
  version: { fontSize: FontSizes.sm, color: Colors.textTertiary },
  section: { gap: Spacing.sm },
  sectionTitle: { fontSize: FontSizes.base, fontWeight: '600', color: Colors.textPrimary, paddingHorizontal: Spacing.xs },
  card: { backgroundColor: Colors.surface, borderRadius: BorderRadius.lg, padding: Spacing.base, ...Shadows.sm },
  descriptionText: { fontSize: FontSizes.base, color: Colors.textSecondary, lineHeight: 24 },
  sourceItem: { gap: 4 },
  sourceTitle: { fontSize: FontSizes.sm, fontWeight: '600', color: Colors.textPrimary },
  sourceName: { fontSize: FontSizes.sm, color: Colors.textSecondary },
  sourceUrl: { fontSize: FontSizes.xs, color: Colors.info, textDecorationLine: 'underline' },
  divider: { height: 1, backgroundColor: Colors.borderLight, marginVertical: Spacing.md },
  settingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  settingLabel: { fontSize: FontSizes.base, color: Colors.textPrimary, fontWeight: '500' },
  settingValueBadge: { backgroundColor: Colors.surfaceElevated, paddingHorizontal: Spacing.md, paddingVertical: Spacing.xs, borderRadius: BorderRadius.full },
  settingValueText: { fontSize: FontSizes.sm, color: Colors.primaryDark, fontWeight: '600' },
  disclaimerSection: { backgroundColor: Colors.warningLight, padding: Spacing.base, borderRadius: BorderRadius.md, borderWidth: 1, borderColor: Colors.warning + '40', gap: Spacing.xs },
  disclaimerTitle: { fontSize: FontSizes.sm, fontWeight: '700', color: Colors.warning },
  disclaimerText: { fontSize: FontSizes.xs, color: Colors.textSecondary, lineHeight: 20 },
});
