import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { BorderRadius, Colors, FontSizes, Spacing } from '@/constants/theme';
import { ExternalLink } from './external-link';
import { useLanguage } from '@/contexts/LanguageContext';

interface SourceCardProps {
  source: string;
  sourceUrl: string;
}

export function SourceCard({ source, sourceUrl }: SourceCardProps) {
  const { t } = useLanguage();

  return (
    <View style={styles.card}>
      <Text style={styles.icon}>📚</Text>
      <View style={styles.content}>
        <Text style={styles.label}>{t('dataSource')}:</Text>
        <ExternalLink href={sourceUrl as any}>
          <Text style={styles.source}>{source}</Text>
        </ExternalLink>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    backgroundColor: Colors.surfaceElevated,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  icon: {
    fontSize: 24,
  },
  content: {
    flex: 1,
  },
  label: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  source: {
    fontSize: FontSizes.sm,
    fontWeight: '600',
    color: Colors.info,
    textDecorationLine: 'underline',
  },
});
