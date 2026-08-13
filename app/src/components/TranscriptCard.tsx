/**
 * TranscriptCard — Displays Tamil ASR transcript with audio playback placeholder.
 */

import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface TranscriptCardProps {
  transcript: string;
  onPlayAudio?: () => void;
}

export function TranscriptCard({ transcript, onPlayAudio }: TranscriptCardProps) {
  const { t } = useLanguage();

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.headerIcon}>📝</Text>
        <Text style={styles.headerText}>{t('transcriptHeader')}</Text>
        {onPlayAudio && (
          <Pressable
            onPress={onPlayAudio}
            style={({ pressed }) => [
              styles.playButton,
              pressed && styles.playButtonPressed,
            ]}
          >
            <Text style={styles.playIcon}>🔊</Text>
          </Pressable>
        )}
      </View>
      <View style={styles.transcriptBox}>
        <Text style={styles.transcriptText}>"{transcript}"</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    padding: Spacing.base,
    gap: Spacing.md,
    ...Shadows.sm,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  headerIcon: {
    fontSize: 20,
  },
  headerText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.textPrimary,
    flex: 1,
  },
  playButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.primaryLight + '20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  playButtonPressed: {
    backgroundColor: Colors.primaryLight + '40',
  },
  playIcon: {
    fontSize: 18,
  },
  transcriptBox: {
    backgroundColor: Colors.successLight,
    borderRadius: BorderRadius.sm,
    padding: Spacing.base,
    borderLeftWidth: 3,
    borderLeftColor: Colors.primary,
  },
  transcriptText: {
    fontSize: FontSizes.base,
    lineHeight: 26,
    color: Colors.textPrimary,
    fontStyle: 'italic',
  },
});
