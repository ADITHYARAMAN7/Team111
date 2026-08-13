import React from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';
import { useLanguage } from '@/contexts/LanguageContext';
import { Colors, FontSizes, Shadows, BorderRadius, Spacing } from '@/constants/theme';

export function LanguageToggle() {
  const { language, toggleLanguage } = useLanguage();

  return (
    <Pressable 
      onPress={toggleLanguage}
      style={({ pressed }) => [
        styles.button,
        pressed && styles.pressed
      ]}
    >
      <Text style={[styles.text, language === 'en' && styles.activeText]}>A</Text>
      <Text style={styles.divider}>/</Text>
      <Text style={[styles.text, language === 'ta' && styles.activeText]}>அ</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceElevated,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    marginRight: Spacing.base,
    ...Shadows.sm,
  },
  pressed: {
    opacity: 0.7,
    transform: [{ scale: 0.95 }],
  },
  text: {
    fontSize: FontSizes.sm,
    fontWeight: '500',
    color: Colors.textTertiary,
  },
  activeText: {
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  divider: {
    fontSize: FontSizes.xs,
    color: Colors.textTertiary,
    marginHorizontal: 4,
  }
});
