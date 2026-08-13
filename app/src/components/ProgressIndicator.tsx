/**
 * ProgressIndicator — Horizontal step indicator for the diagnosis workflow.
 * 🎙️ Voice → 📝 Symptoms → 🧠 Analysis → 📷 Confirm → 🌱 Treatment
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Colors, FontSizes, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

export type WorkflowStep = 'voice' | 'symptoms' | 'analysis' | 'confirm' | 'treatment';

interface ProgressIndicatorProps {
  currentStep: WorkflowStep;
}

export function ProgressIndicator({ currentStep }: ProgressIndicatorProps) {
  const { t, language } = useLanguage();

  const STEPS = [
    { id: 'voice', icon: '🎙️' },
    { id: 'symptoms', icon: '📝' },
    { id: 'analysis', icon: '🧠' },
    { id: 'confirm', icon: '📷' },
    { id: 'treatment', icon: '🌱' },
  ];

  const getShortTitle = (id: string) => {
    const taMap: Record<string, string> = { voice: 'குரல்', symptoms: 'அறிகுறி', analysis: 'பகுப்பாய்வு', confirm: 'உறுதி', treatment: 'சிகிச்சை' };
    const enMap: Record<string, string> = { voice: 'Voice', symptoms: 'Symptoms', analysis: 'Analysis', confirm: 'Confirm', treatment: 'Treatment' };
    return language === 'ta' ? taMap[id] : enMap[id];
  };

  const currentIndex = STEPS.findIndex((s) => s.id === currentStep);

  return (
    <View style={styles.container}>
      {STEPS.map((step, index) => {
        const isActive = index === currentIndex;
        const isCompleted = index < currentIndex;

        return (
          <React.Fragment key={step.id}>
            {index > 0 && (
              <View
                style={[
                  styles.connector,
                  { backgroundColor: isCompleted ? Colors.primary : Colors.border },
                ]}
              />
            )}
            <View style={styles.stepWrapper}>
              <View
                style={[
                  styles.stepCircle,
                  isActive && styles.stepCircleActive,
                  isCompleted && styles.stepCircleCompleted,
                ]}
              >
                <Text style={styles.stepIcon}>{step.icon}</Text>
              </View>
              <Text
                style={[
                  styles.stepLabel,
                  isActive && styles.stepLabelActive,
                  isCompleted && styles.stepLabelCompleted,
                ]}
                numberOfLines={1}
              >
                {getShortTitle(step.id)}
              </Text>
            </View>
          </React.Fragment>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.md,
  },
  stepWrapper: {
    alignItems: 'center',
    gap: Spacing.xs,
  },
  stepCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surfaceElevated,
    borderWidth: 2,
    borderColor: Colors.border,
  },
  stepCircleActive: {
    backgroundColor: Colors.successLight,
    borderColor: Colors.primary,
    borderWidth: 2.5,
  },
  stepCircleCompleted: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  stepCircleUpcoming: {
    backgroundColor: Colors.surfaceElevated,
    borderColor: Colors.borderLight,
  },
  stepIcon: {
    fontSize: 16,
  },
  stepLabel: {
    fontSize: FontSizes.xs,
    color: Colors.textTertiary,
    maxWidth: 56,
    textAlign: 'center',
  },
  stepLabelActive: {
    color: Colors.primary,
    fontWeight: '700',
  },
  stepLabelCompleted: {
    color: Colors.primaryDark,
    fontWeight: '600',
  },
  connector: {
    height: 2,
    flex: 1,
    marginHorizontal: 2,
    borderRadius: 1,
    marginBottom: 20,
  },
});
