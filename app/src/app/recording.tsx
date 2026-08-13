/**
 * Recording Screen — Voice recording interface.
 * Simulates a 3-second recording process.
 */

import React, { useState, useCallback } from 'react';
import { StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';

import { RecordingPanel } from '@/components/RecordingPanel';
import { ProgressIndicator } from '@/components/ProgressIndicator';
import { Colors } from '@/constants/theme';

export default function RecordingScreen() {
  const router = useRouter();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingComplete, setRecordingComplete] = useState(false);

  const handleStartRecording = useCallback(() => {
    setIsRecording(true);
    setRecordingComplete(false);
    setTimeout(() => {
      setIsRecording(false);
      setRecordingComplete(true);
    }, 3000);
  }, []);

  const handleStopRecording = useCallback(() => {
    setIsRecording(false);
    setRecordingComplete(true);
  }, []);

  const handleContinue = useCallback(() => {
    router.push('/symptoms');
  }, [router]);

  return (
    <View style={styles.container}>
      <ProgressIndicator currentStep="voice" />
      <RecordingPanel
        isRecording={isRecording}
        onStartRecording={handleStartRecording}
        onStopRecording={handleStopRecording}
        onContinue={handleContinue}
        recordingComplete={recordingComplete}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
});
