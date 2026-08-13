/**
 * Theme constants for the Tamil Voice-First Tomato Disease Diagnosis app.
 * Agricultural green palette designed for Tamil-speaking farmers.
 */

import { Platform } from 'react-native';

export const Colors = {
  primary: '#2E7D32',
  primaryLight: '#4CAF50',
  primaryDark: '#1B5E20',
  secondary: '#8D6E63',
  secondaryLight: '#A1887F',
  background: '#FAFAF5',
  surface: '#FFFFFF',
  surfaceElevated: '#F5F5F0',
  textPrimary: '#1A1A1A',
  textSecondary: '#5D4037',
  textTertiary: '#8D6E63',
  matchHigh: '#2E7D32',
  matchMedium: '#F57F17',
  matchLow: '#9E9E9E',
  error: '#C62828',
  errorLight: '#FFEBEE',
  warning: '#E65100',
  warningLight: '#FFF3E0',
  info: '#1565C0',
  infoLight: '#E3F2FD',
  success: '#2E7D32',
  successLight: '#E8F5E9',
  border: '#E0E0E0',
  borderLight: '#F0F0F0',
  overlay: 'rgba(0, 0, 0, 0.5)',
  white: '#FFFFFF',
  black: '#000000',
  recordingRed: '#D32F2F',
  recordingPulse: 'rgba(211, 47, 47, 0.3)',
  tamilGold: '#F9A825',
} as const;

export const Fonts = {
  regular: Platform.select({
    ios: 'System',
    android: 'Roboto',
    default: 'System',
  }) as string,
  bold: Platform.select({
    ios: 'System',
    android: 'Roboto',
    default: 'System',
  }) as string,
  mono: Platform.select({
    ios: 'Menlo',
    android: 'monospace',
    default: 'monospace',
  }) as string,
};

export const FontSizes = {
  xs: 11,
  sm: 13,
  base: 16,
  md: 18,
  lg: 22,
  xl: 26,
  xxl: 32,
  hero: 40,
} as const;

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  xxl: 32,
  xxxl: 48,
  hero: 64,
} as const;

export const BorderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
} as const;

export const Shadows = {
  sm: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.08,
      shadowRadius: 4,
    },
    android: { elevation: 2 },
    default: {},
  }),
  md: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.12,
      shadowRadius: 8,
    },
    android: { elevation: 4 },
    default: {},
  }),
  lg: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 16,
    },
    android: { elevation: 8 },
    default: {},
  }),
} as const;

export const TouchTargets = {
  min: 48,
  button: 56,
  primaryCTA: 80,
} as const;
