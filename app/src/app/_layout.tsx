/**
 * Root Layout — Stack navigator wrapping tab navigator + workflow screens.
 */

import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { Colors } from '@/constants/theme';
import { LanguageProvider, useLanguage } from '@/contexts/LanguageContext';

function RootStack() {
  const { t } = useLanguage();

  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: Colors.background,
        },
        headerTintColor: Colors.primary,
        headerTitleStyle: {
          fontWeight: '600',
          fontSize: 18,
        },
        headerShadowVisible: false,
        contentStyle: {
          backgroundColor: Colors.background,
        },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen
        name="(tabs)"
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="recording"
        options={{
          title: `🎙️ ${t('recordingStatus').replace('...', '')}`,
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="symptoms"
        options={{
          title: `📝 ${t('symptoms')}`,
        }}
      />
      <Stack.Screen
        name="diagnosis"
        options={{
          title: `🧠 ${t('possibleDiseasesTitle')}`,
        }}
      />
      <Stack.Screen
        name="confirmation"
        options={{
          title: `📷 ${t('confirmImagesTitle')}`,
        }}
      />
      <Stack.Screen
        name="result"
        options={{
          title: `✅ ${t('diseaseConfirmed')}`,
          headerBackVisible: false,
        }}
      />
      <Stack.Screen
        name="treatment"
        options={{
          title: `🌱 ${t('whatToDo').replace('?', '')}`,
        }}
      />
      <Stack.Screen
        name="voice-response"
        options={{
          title: `🔊 ${t('listenInTamil')}`,
          headerBackVisible: false,
        }}
      />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <LanguageProvider>
      <StatusBar style="dark" />
      <RootStack />
    </LanguageProvider>
  );
}
