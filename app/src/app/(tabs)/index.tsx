/**
 * Home Screen — Welcome screen with voice-first CTA.
 * தக்காளி நோய் கண்டறிதல் (Tomato Disease Diagnosis)
 */

import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { VoiceButton } from '@/components/VoiceButton';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export default function HomeScreen() {
  const router = useRouter();
  const { t } = useLanguage();

  const handleStartRecording = () => {
    router.push('/recording');
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <Text style={styles.heroEmoji}>🍅</Text>
          <Text style={styles.heroTitle}>{t('homeWelcomeTitle')}</Text>
          <Text style={styles.heroSubtitle}>
            {t('homeSubtitle')}
          </Text>
        </View>

        {/* Voice Button CTA */}
        <View style={styles.ctaSection}>
          <VoiceButton onPress={handleStartRecording} size={90} />
          <Text style={styles.ctaHint}>
            {t('tapToSpeak')}
          </Text>
        </View>

        {/* Example Prompts */}
        <View style={styles.promptsSection}>
          <Text style={styles.promptsTitle}>{t('examplesTitle')}</Text>
          <View style={styles.promptsList}>
            <PromptChip text={t('example1')} />
            <PromptChip text={t('example2')} />
            <PromptChip text={t('example3')} />
          </View>
        </View>

        {/* How it works */}
        <View style={styles.stepsSection}>
          <Text style={styles.stepsTitle}>{t('howToUse')}</Text>
          <StepItem
            number="1"
            icon="🎙️"
            text={t('step1')}
          />
          <StepItem
            number="2"
            icon="🔍"
            text={t('step2')}
          />
          <StepItem
            number="3"
            icon="📷"
            text={t('step3')}
          />
          <StepItem
            number="4"
            icon="🌱"
            text={t('step4')}
          />
        </View>

        {/* Disclaimer */}
        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerIcon}>⚠️</Text>
          <Text style={styles.disclaimerText}>
            {t('disclaimer')}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function PromptChip({ text }: { text: string }) {
  return (
    <View style={styles.promptChip}>
      <Text style={styles.promptChipText}>"{text}"</Text>
    </View>
  );
}

function StepItem({ number, icon, text }: { number: string; icon: string; text: string }) {
  return (
    <View style={styles.stepItem}>
      <View style={styles.stepNumber}>
        <Text style={styles.stepNumberText}>{number}</Text>
      </View>
      <Text style={styles.stepIcon}>{icon}</Text>
      <Text style={styles.stepText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    paddingHorizontal: Spacing.xl,
    paddingBottom: Spacing.xxl,
  },
  heroSection: {
    alignItems: 'center',
    paddingTop: Spacing.xl,
    gap: Spacing.md,
  },
  heroEmoji: {
    fontSize: 64,
  },
  heroTitle: {
    fontSize: FontSizes.xxl,
    fontWeight: '800',
    color: Colors.primaryDark,
    textAlign: 'center',
    lineHeight: 42,
  },
  heroSubtitle: {
    fontSize: FontSizes.base,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 26,
    paddingHorizontal: Spacing.base,
  },
  ctaSection: {
    alignItems: 'center',
    paddingVertical: Spacing.xxl,
    gap: Spacing.base,
  },
  ctaHint: {
    fontSize: FontSizes.sm,
    color: Colors.textTertiary,
    fontWeight: '500',
  },
  promptsSection: {
    gap: Spacing.md,
  },
  promptsTitle: {
    fontSize: FontSizes.base,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  promptsList: {
    gap: Spacing.sm,
  },
  promptChip: {
    backgroundColor: Colors.surfaceElevated,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderLeftWidth: 3,
    borderLeftColor: Colors.primaryLight,
  },
  promptChipText: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    lineHeight: 22,
  },
  stepsSection: {
    marginTop: Spacing.xxl,
    gap: Spacing.md,
  },
  stepsTitle: {
    fontSize: FontSizes.base,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: Spacing.xs,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    ...Shadows.sm,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumberText: {
    fontSize: FontSizes.sm,
    fontWeight: '700',
    color: Colors.white,
  },
  stepIcon: {
    fontSize: 22,
  },
  stepText: {
    flex: 1,
    fontSize: FontSizes.sm,
    color: Colors.textPrimary,
    lineHeight: 22,
  },
  disclaimer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
    marginTop: Spacing.xxl,
    padding: Spacing.base,
    backgroundColor: Colors.warningLight,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.warning + '30',
  },
  disclaimerIcon: {
    fontSize: 16,
    marginTop: 2,
  },
  disclaimerText: {
    flex: 1,
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
});
