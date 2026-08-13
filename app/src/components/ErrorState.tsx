/**
 * ErrorState — Reusable error display with multi-language messages and retry action.
 */

import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface ErrorStateProps {
  icon?: string;
  title?: string;
  message: string;
  retryLabel?: string;
  onRetry?: () => void;
}

export function ErrorState({
  icon = '❌',
  title,
  message,
  retryLabel,
  onRetry,
}: ErrorStateProps) {
  const { t } = useLanguage();
  
  return (
    <View style={styles.container}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={styles.title}>{title || t('error')}</Text>
      <Text style={styles.message}>{message}</Text>
      {onRetry && (
        <Pressable
          onPress={onRetry}
          style={({ pressed }) => [
            styles.retryButton,
            pressed && styles.retryButtonPressed,
          ]}
        >
          <Text style={styles.retryButtonText}>{retryLabel || t('retry')}</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xxl,
    gap: Spacing.md,
  },
  icon: {
    fontSize: 56,
    marginBottom: Spacing.sm,
  },
  title: {
    fontSize: FontSizes.lg,
    fontWeight: '700',
    color: Colors.error,
    textAlign: 'center',
  },
  message: {
    fontSize: FontSizes.base,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  retryButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xxl,
    minHeight: TouchTargets.min,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: Spacing.base,
    ...Shadows.sm,
  },
  retryButtonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.96 }],
  },
  retryButtonText: {
    fontSize: FontSizes.base,
    fontWeight: '600',
    color: Colors.white,
  },
});
