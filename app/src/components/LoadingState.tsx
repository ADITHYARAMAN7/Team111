/**
 * LoadingState — Loading screen with multi-language status messages and animation.
 */

import React, { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';

import { Colors, FontSizes, Spacing } from '@/constants/theme';
import { useLanguage } from '@/contexts/LanguageContext';

interface LoadingStateProps {
  message?: string;
  icon?: string;
}

export function LoadingState({
  message,
  icon = '🔍',
}: LoadingStateProps) {
  const rotation = useSharedValue(0);
  const opacity = useSharedValue(0.5);
  const { t } = useLanguage();

  useEffect(() => {
    rotation.value = withRepeat(
      withTiming(360, { duration: 2000, easing: Easing.linear }),
      -1,
      false
    );
    opacity.value = withRepeat(
      withTiming(1, { duration: 800, easing: Easing.inOut(Easing.ease) }),
      -1,
      true
    );
  }, [rotation, opacity]);

  const spinStyle = useAnimatedStyle(() => ({
    transform: [{ rotateZ: `${rotation.value}deg` }],
  }));

  const pulseStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <View style={styles.container}>
      <Animated.View style={spinStyle}>
        <View style={styles.spinner}>
          <View style={styles.spinnerInner} />
        </View>
      </Animated.View>
      <Text style={styles.icon}>{icon}</Text>
      <Animated.Text style={[styles.message, pulseStyle]}>
        {message || t('loading')}
      </Animated.Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xxl,
    gap: Spacing.base,
  },
  spinner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    borderWidth: 3,
    borderColor: Colors.borderLight,
    borderTopColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinnerInner: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: Colors.borderLight,
    borderTopColor: Colors.primaryLight,
  },
  icon: {
    fontSize: 32,
    marginTop: Spacing.sm,
  },
  message: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: 'center',
    fontWeight: '500',
  },
});
