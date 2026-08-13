/**
 * VoiceButton — Large circular microphone button, the primary CTA.
 * 80dp+ touch target with pulse animation and agricultural green accent.
 */

import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from 'react-native-reanimated';

import { Colors, Shadows, TouchTargets } from '@/constants/theme';

interface VoiceButtonProps {
  onPress: () => void;
  isRecording?: boolean;
  size?: number;
}

export function VoiceButton({ onPress, isRecording = false, size = TouchTargets.primaryCTA }: VoiceButtonProps) {
  const pulseScale = useSharedValue(1);

  React.useEffect(() => {
    if (isRecording) {
      pulseScale.value = withRepeat(
        withSequence(
          withTiming(1.3, { duration: 800, easing: Easing.inOut(Easing.ease) }),
          withTiming(1, { duration: 800, easing: Easing.inOut(Easing.ease) })
        ),
        -1,
        false
      );
    } else {
      pulseScale.value = withTiming(1, { duration: 300 });
    }
  }, [isRecording, pulseScale]);

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulseScale.value }],
    opacity: isRecording ? 0.4 : 0,
  }));

  return (
    <View style={styles.container}>
      <Animated.View
        style={[
          styles.pulse,
          {
            width: size * 1.6,
            height: size * 1.6,
            borderRadius: size * 0.8,
            backgroundColor: isRecording ? Colors.recordingRed : Colors.primary,
          },
          pulseStyle,
        ]}
      />
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          styles.button,
          {
            width: size,
            height: size,
            borderRadius: size / 2,
            backgroundColor: isRecording ? Colors.recordingRed : Colors.primary,
            transform: [{ scale: pressed ? 0.92 : 1 }],
          },
        ]}
        accessibilityLabel={isRecording ? 'பதிவை நிறுத்து' : 'குரல் பதிவு தொடங்கு'}
        accessibilityRole="button"
      >
        <MicIcon size={size * 0.4} color={Colors.white} isRecording={isRecording} />
      </Pressable>
    </View>
  );
}

function MicIcon({ size, color, isRecording }: { size: number; color: string; isRecording: boolean }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      {isRecording ? (
        // Stop icon (square)
        <View
          style={{
            width: size * 0.5,
            height: size * 0.5,
            backgroundColor: color,
            borderRadius: 3,
          }}
        />
      ) : (
        // Mic icon (simplified SVG-like)
        <View style={{ alignItems: 'center' }}>
          <View
            style={{
              width: size * 0.35,
              height: size * 0.55,
              backgroundColor: color,
              borderRadius: size * 0.175,
            }}
          />
          <View
            style={{
              width: size * 0.55,
              height: size * 0.08,
              borderColor: color,
              borderWidth: 2,
              borderTopWidth: 0,
              borderBottomLeftRadius: size * 0.275,
              borderBottomRightRadius: size * 0.275,
              marginTop: -size * 0.08,
            }}
          />
          <View
            style={{
              width: 2,
              height: size * 0.15,
              backgroundColor: color,
            }}
          />
          <View
            style={{
              width: size * 0.3,
              height: 2,
              backgroundColor: color,
            }}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulse: {
    position: 'absolute',
  },
  button: {
    alignItems: 'center',
    justifyContent: 'center',
    ...Shadows.lg,
  },
});
