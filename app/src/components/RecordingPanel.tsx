/**
 * RecordingPanel — Full-screen recording interface with animated indicator and timer.
 */

import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from 'react-native-reanimated';

import { VoiceButton } from './VoiceButton';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface RecordingPanelProps {
  isRecording: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onContinue: () => void;
  recordingComplete: boolean;
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export function RecordingPanel({
  isRecording,
  onStartRecording,
  onStopRecording,
  onContinue,
  recordingComplete,
}: RecordingPanelProps) {
  const [timer, setTimer] = useState(0);
  const barAnimation = useSharedValue(0);
  const { t } = useLanguage();

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isRecording) {
      setTimer(0);
      interval = setInterval(() => {
        setTimer((prev) => prev + 1);
      }, 1000);
      barAnimation.value = withRepeat(
        withSequence(
          withTiming(1, { duration: 300, easing: Easing.inOut(Easing.ease) }),
          withTiming(0.3, { duration: 300, easing: Easing.inOut(Easing.ease) })
        ),
        -1,
        false
      );
    } else {
      barAnimation.value = withTiming(0, { duration: 300 });
    }
    return () => clearInterval(interval);
  }, [isRecording, barAnimation]);

  const barStyle = useAnimatedStyle(() => ({
    opacity: barAnimation.value,
  }));

  return (
    <View style={styles.container}>
      {/* Recording indicator bars */}
      {isRecording && (
        <Animated.View style={[styles.barsContainer, barStyle]}>
          {[0.6, 0.8, 1, 0.7, 0.9, 0.5, 0.8].map((height, i) => (
            <View
              key={i}
              style={[
                styles.bar,
                { height: 30 * height, animationDelay: `${i * 100}ms` },
              ]}
            />
          ))}
        </Animated.View>
      )}

      {/* Timer */}
      <Text style={[styles.timer, isRecording && styles.timerActive]}>
        {formatTime(timer)}
      </Text>

      {/* Instructions */}
      <Text style={styles.instruction}>
        {isRecording
          ? t('recordingInstruction')
          : recordingComplete
          ? t('recordingComplete')
          : t('recordingHintButton')}
      </Text>

      {/* Hints */}
      {isRecording && (
        <View style={styles.hintsBox}>
          <Text style={styles.hintTitle}>{t('hintsTitle')}</Text>
          <Text style={styles.hint}>{t('hint1')}</Text>
          <Text style={styles.hint}>{t('hint2')}</Text>
          <Text style={styles.hint}>{t('hint3')}</Text>
        </View>
      )}

      {/* Voice Button */}
      <View style={styles.buttonSection}>
        {!recordingComplete ? (
          <VoiceButton
            onPress={isRecording ? onStopRecording : onStartRecording}
            isRecording={isRecording}
          />
        ) : (
          <View style={styles.completeActions}>
            <Pressable
              onPress={onStartRecording}
              style={({ pressed }) => [
                styles.reRecordButton,
                pressed && styles.buttonPressed,
              ]}
            >
              <Text style={styles.reRecordText}>{t('reRecord')}</Text>
            </Pressable>
            <Pressable
              onPress={onContinue}
              style={({ pressed }) => [
                styles.continueButton,
                pressed && styles.buttonPressed,
              ]}
            >
              <Text style={styles.continueText}>{t('continueBtn')}</Text>
            </Pressable>
          </View>
        )}
      </View>

      {isRecording && (
        <Text style={styles.statusText}>{t('recordingStatus')}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
    gap: Spacing.xl,
  },
  barsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    height: 40,
  },
  bar: {
    width: 4,
    backgroundColor: Colors.recordingRed,
    borderRadius: 2,
  },
  timer: {
    fontSize: FontSizes.hero,
    fontWeight: '300',
    color: Colors.textTertiary,
    letterSpacing: 4,
  },
  timerActive: {
    color: Colors.recordingRed,
    fontWeight: '500',
  },
  instruction: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 28,
    paddingHorizontal: Spacing.base,
  },
  hintsBox: {
    backgroundColor: Colors.surfaceElevated,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    gap: Spacing.xs,
    alignSelf: 'stretch',
  },
  hintTitle: {
    fontSize: FontSizes.sm,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: Spacing.xs,
  },
  hint: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  buttonSection: {
    marginTop: Spacing.base,
  },
  completeActions: {
    alignItems: 'center',
    gap: Spacing.base,
  },
  reRecordButton: {
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xxl,
    borderRadius: BorderRadius.md,
    backgroundColor: Colors.surfaceElevated,
    borderWidth: 1,
    borderColor: Colors.border,
    minHeight: TouchTargets.min,
    alignItems: 'center',
    justifyContent: 'center',
  },
  continueButton: {
    paddingVertical: Spacing.base,
    paddingHorizontal: Spacing.xxxl,
    borderRadius: BorderRadius.md,
    backgroundColor: Colors.primary,
    minHeight: TouchTargets.button,
    alignItems: 'center',
    justifyContent: 'center',
    ...Shadows.md,
  },
  reRecordText: {
    fontSize: FontSizes.base,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  continueText: {
    fontSize: FontSizes.md,
    color: Colors.white,
    fontWeight: '700',
  },
  buttonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.96 }],
  },
  statusText: {
    fontSize: FontSizes.sm,
    color: Colors.recordingRed,
    fontWeight: '600',
  },
});
