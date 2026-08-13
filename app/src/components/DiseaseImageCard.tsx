import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { DiseaseImage } from '@/types/diagnosis';
import { BorderRadius, Colors, FontSizes, Shadows, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface DiseaseImageCardProps {
  image: DiseaseImage;
  isSelected?: boolean;
  onSelect: () => void;
}

export function DiseaseImageCard({ image, isSelected, onSelect }: DiseaseImageCardProps) {
  const { t } = useLanguage();
  return (
    <Pressable
      onPress={onSelect}
      style={({ pressed }) => [
        styles.card,
        isSelected && styles.cardSelected,
        pressed && styles.cardPressed,
      ]}
    >
      <View style={styles.imagePlaceholder}>
        <Text style={styles.imagePlaceholderIcon}>🍅</Text>
      </View>
      <View style={styles.footer}>
        <Text style={[styles.selectText, isSelected && styles.selectTextActive]}>
          {isSelected ? t('selected') : t('thisMatches')}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: Colors.surface, borderRadius: BorderRadius.md, borderWidth: 2, borderColor: Colors.border, overflow: 'hidden', ...Shadows.sm },
  cardSelected: { borderColor: Colors.primary },
  cardPressed: { opacity: 0.9, transform: [{ scale: 0.98 }] },
  imagePlaceholder: { width: '100%', height: 220, backgroundColor: Colors.surfaceElevated, alignItems: 'center', justifyContent: 'center' },
  imagePlaceholderIcon: { fontSize: 64 },
  footer: { padding: Spacing.md, alignItems: 'center', backgroundColor: Colors.surface },
  selectText: { fontSize: FontSizes.md, fontWeight: '600', color: Colors.textSecondary },
  selectTextActive: { color: Colors.primaryDark, fontWeight: '700' },
});
