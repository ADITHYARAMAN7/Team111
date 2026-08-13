/**
 * ConfirmationModal — Dialog for confirming disease selection.
 */

import React from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface ConfirmationModalProps {
  visible: boolean;
  diseaseTamilName: string;
  diseaseEnglishName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmationModal({
  visible,
  diseaseTamilName,
  diseaseEnglishName,
  onConfirm,
  onCancel,
}: ConfirmationModalProps) {
  const { t, language } = useLanguage();

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <View style={styles.overlay}>
        <View style={styles.dialog}>
          <Text style={styles.icon}>✅</Text>
          <Text style={styles.title}>{t('confirmModalTitle')}</Text>
          <Text style={styles.message}>
            {t('confirmModalMessage')}
          </Text>
          <View style={styles.diseaseNameBox}>
            <Text style={styles.diseaseMainName}>
              {language === 'ta' ? diseaseTamilName : diseaseEnglishName}
            </Text>
            <Text style={styles.diseaseSubName}>
              {language === 'ta' ? diseaseEnglishName : diseaseTamilName}
            </Text>
          </View>
          <Text style={styles.confirmQuestion}>
            {t('confirmModalQuestion')}
          </Text>

          <View style={styles.buttonRow}>
            <Pressable
              onPress={onCancel}
              style={({ pressed }) => [
                styles.cancelButton,
                pressed && styles.buttonPressed,
              ]}
            >
              <Text style={styles.cancelButtonText}>{t('goBack')}</Text>
            </Pressable>
            <Pressable
              onPress={onConfirm}
              style={({ pressed }) => [
                styles.confirmButton,
                pressed && styles.buttonPressed,
              ]}
            >
              <Text style={styles.confirmButtonText}>{t('confirmBtn')}</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: Colors.overlay,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  dialog: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    padding: Spacing.xl,
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
    gap: Spacing.md,
    ...Shadows.lg,
  },
  icon: {
    fontSize: 48,
    marginBottom: Spacing.xs,
  },
  title: {
    fontSize: FontSizes.lg,
    fontWeight: '700',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  message: {
    fontSize: FontSizes.base,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  diseaseNameBox: {
    backgroundColor: Colors.successLight,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    width: '100%',
    alignItems: 'center',
    gap: 4,
    borderWidth: 1,
    borderColor: Colors.primary + '30',
  },
  diseaseMainName: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  diseaseSubName: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  confirmQuestion: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.md,
    width: '100%',
    marginTop: Spacing.sm,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    backgroundColor: Colors.surfaceElevated,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  confirmButton: {
    flex: 1,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    backgroundColor: Colors.primary,
  },
  cancelButtonText: {
    fontSize: FontSizes.base,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  confirmButtonText: {
    fontSize: FontSizes.base,
    fontWeight: '600',
    color: Colors.white,
  },
  buttonPressed: {
    opacity: 0.7,
    transform: [{ scale: 0.97 }],
  },
});
