import React from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';

import { BorderRadius, Colors, FontSizes, Shadows, Spacing, TouchTargets } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface TamilVoiceButtonProps {
  onPress: () => void;
  label?: string;
  isSecondary?: boolean;
}

export function TamilVoiceButton({
  onPress,
  label,
  isSecondary,
}: TamilVoiceButtonProps) {
  const { t } = useLanguage();
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        isSecondary && styles.buttonSecondary,
        pressed && styles.buttonPressed,
      ]}
    >
      <Text style={[styles.text, isSecondary && styles.textSecondary]}>
        {label || t('listenInTamil')}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: Colors.tamilGold,
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xl,
    minHeight: TouchTargets.button,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    ...Shadows.md,
  },
  buttonSecondary: {
    backgroundColor: Colors.surfaceElevated,
    borderWidth: 1,
    borderColor: Colors.tamilGold,
  },
  buttonPressed: {
    opacity: 0.9,
    transform: [{ scale: 0.98 }],
  },
  text: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: '#3B2F00',
  },
  textSecondary: {
    color: Colors.tamilGold,
  },
});
