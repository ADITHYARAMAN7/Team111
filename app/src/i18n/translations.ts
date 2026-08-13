export type Language = 'en' | 'ta';

export const translations = {
  en: {
    // General
    appTitle: 'Tomato Disease Diagnosis',
    loading: 'Processing...',
    error: 'Error',
    retry: 'Retry',
    continueBtn: 'Continue →',
    goBack: 'Go Back',
    confirmBtn: 'Confirm ✓',
    
    // Tabs
    tabHome: 'Home',
    tabHistory: 'History',
    tabAbout: 'About',

    // Home Screen
    homeWelcomeTitle: 'Tomato Disease\nDiagnosis',
    homeSubtitle: 'Speak about your tomato plant symptoms in Tamil or English.\nWe will diagnose the disease and suggest treatments.',
    tapToSpeak: '🎙️ Tap to speak',
    examplesTitle: '💡 Examples:',
    example1: 'My tomato leaves have dark concentric spots',
    example2: 'Leaves are turning yellow and curling',
    example3: 'Scab-like lesions on the fruit',
    howToUse: '📖 How to use?',
    step1: 'Speak your symptoms',
    step2: 'AI diagnoses the disease',
    step3: 'Confirm with reference images',
    step4: 'Get treatment recommendations',
    disclaimer: 'This is an assistive tool only. Consult agricultural experts for critical decisions.',

    // Recording Screen
    recordingInstruction: 'Describe your plant symptoms...',
    recordingComplete: 'Recording Complete ✓',
    recordingHintButton: 'Press button below to record',
    hintsTitle: '📋 What you can say:',
    hint1: '• Is the leaf color changing?',
    hint2: '• Are there spots or lesions?',
    hint3: '• Which part is affected?',
    reRecord: '🔄 Re-record',
    recordingStatus: '🔴 Recording...',

    // Symptoms Screen
    transcriptHeader: 'You said:',
    extractedInfo: 'Extracted Information',
    crop: 'Crop',
    affectedPart: 'Affected Part',
    symptoms: 'Symptoms',
    diagnoseBtn: 'Diagnose Disease →',

    // Diagnosis Screen
    possibleDiseasesTitle: 'Possible Diseases',
    possibleDiseasesSubtitle: 'Based on your symptoms, it could be:',
    matchHigh: 'High Match',
    matchMedium: 'Medium Match',
    matchLow: 'Low Match',
    matchedSymptomsLabel: 'Matched Symptoms:',
    confirmWithImagesBtn: 'Confirm with Images →',
    noMatchTitle: 'No Match',
    noMatchMessage: 'Could not find any diseases matching these symptoms.',

    // Confirmation Screen
    confirmImagesTitle: 'Confirm Disease with Images',
    confirmImagesSubtitle: 'Check if these reference images match your plant.',
    thisMatches: 'This Matches',
    selected: '✓ Selected',
    noImageMatches: 'No images match?',
    viewOtherDisease: 'View other diseases',
    confirmModalTitle: 'Confirm Disease',
    confirmModalMessage: 'You have selected:',
    confirmModalQuestion: 'Do you confirm this disease matches your plant condition?',

    // Result Screen
    diseaseConfirmed: 'Disease Confirmed',
    verificationBadge: '✓ Symptom + Image Verification',
    keySymptomsTitle: 'Key Symptoms:',
    viewTreatmentsBtn: 'View Treatment Plans 🌱',
    missingDataTitle: 'Error',
    missingDataMessage: 'Disease data not found.',
    goToHome: 'Go to Home',

    // Treatment Screen
    whatToDo: 'What to do?',
    prevention: 'Prevention Measures',
    warnings: 'Warnings to note',
    dataSource: 'Data Source',
    listenInTamil: '🔊 Listen in Tamil',

    // Voice Response Screen
    preparingAudio: 'Preparing voice response...',
    listenAgain: '🔊 Listen Again',
    returnHome: 'Return to Home 🏠',

    // History Screen
    historyTitle: 'Diagnosis History',
    noHistoryTitle: 'No past diagnoses found',
    statusIncomplete: 'Incomplete',
    statusHighMatch: 'High Match',
    statusMediumMatch: 'Medium Match',
    statusLowMatch: 'Low Match',
    noDiseaseDetected: 'No disease detected',

    // About Screen
    versionInfo: 'Version 1.0 (Prototype)',
    aboutTitle: 'About',
    aboutDescription: 'This app is built for tomato farmers. It helps diagnose plant diseases by speaking symptoms and provides tailored treatment plans.',
    dataSourcesTitle: 'Data Sources',
    sourceTreatments: 'Treatment Methods',
    sourceImages: 'Disease Images',
    settingsTitle: 'Settings',
    languageLabel: 'Language',
    disclaimerTitle: 'Disclaimer',
    disclaimerFullText: 'The information provided in this app is for general guidance only. Consult local agricultural authorities or experts before confirming diseases or using chemical treatments.'
  },
  ta: {
    // General
    appTitle: 'தக்காளி நோய் கண்டறிதல்',
    loading: 'செயல்படுத்தப்படுகிறது...',
    error: 'பிழை',
    retry: 'மீண்டும் முயற்சிக்கவும்',
    continueBtn: 'தொடரவும் →',
    goBack: 'திரும்பு',
    confirmBtn: 'உறுதிப்படுத்து ✓',
    
    // Tabs
    tabHome: 'முகப்பு',
    tabHistory: 'வரலாறு',
    tabAbout: 'பற்றி',

    // Home Screen
    homeWelcomeTitle: 'தக்காளி நோய்\nகண்டறிதல்',
    homeSubtitle: 'உங்கள் தக்காளி செடியின் அறிகுறிகளை தமிழில் பேசுங்கள்.\nநாங்கள் நோயை கண்டறிந்து சிகிச்சை பரிந்துரைப்போம்.',
    tapToSpeak: '🎙️ பேச தொடங்க அழுத்தவும்',
    examplesTitle: '💡 உதாரணங்கள்:',
    example1: 'என் தக்காளி இலைகளில் கருமையான புள்ளிகள் உள்ளன',
    example2: 'இலைகள் மஞ்சளாக மாறி சுருங்குகின்றன',
    example3: 'பழத்தில் புண்கள் தெரிகின்றன',
    howToUse: '📖 எப்படி பயன்படுத்துவது?',
    step1: 'அறிகுறிகளை தமிழில் பேசுங்கள்',
    step2: 'செயற்கை நுண்ணறிவு நோயை கண்டறியும்',
    step3: 'படங்களை பார்த்து உறுதிப்படுத்துங்கள்',
    step4: 'சிகிச்சை பரிந்துரையை பெறுங்கள்',
    disclaimer: 'இது ஒரு உதவி கருவி மட்டுமே. முக்கிய முடிவுகளுக்கு விவசாய நிபுணர்களை அணுகவும்.',

    // Recording Screen
    recordingInstruction: 'உங்கள் செடியின் அறிகுறிகளை தமிழில் விவரிக்கவும்...',
    recordingComplete: 'பதிவு முடிந்தது ✓',
    recordingHintButton: 'பதிவு செய்ய கீழே உள்ள பொத்தானை அழுத்தவும்',
    hintsTitle: '📋 என்ன சொல்லலாம்:',
    hint1: '• இலையின் நிறம் மாறுகிறதா?',
    hint2: '• புள்ளிகள் அல்லது புண்கள் உள்ளதா?',
    hint3: '• எந்த பகுதி பாதிக்கப்பட்டுள்ளது?',
    reRecord: '🔄 மீண்டும் பதிவு',
    recordingStatus: '🔴 பதிவு செய்கிறது...',

    // Symptoms Screen
    transcriptHeader: 'நீங்கள் கூறியது:',
    extractedInfo: 'கண்டறியப்பட்ட தகவல்கள்',
    crop: 'பயிர்',
    affectedPart: 'பாதிக்கப்பட்ட பகுதி',
    symptoms: 'அறிகுறிகள்',
    diagnoseBtn: 'நோயை கண்டறியவும் →',

    // Diagnosis Screen
    possibleDiseasesTitle: 'சாத்தியமான நோய்கள்',
    possibleDiseasesSubtitle: 'அறிகுறிகளின் அடிப்படையில் பின்வரும் நோய்கள் இருக்கலாம்:',
    matchHigh: 'உயர் பொருத்தம்',
    matchMedium: 'நடுத்தர பொருத்தம்',
    matchLow: 'குறைந்த பொருத்தம்',
    matchedSymptomsLabel: 'பொருந்தும் அறிகுறிகள்:',
    confirmWithImagesBtn: 'படங்களை வைத்து உறுதிப்படுத்தவும் →',
    noMatchTitle: 'பொருத்தம் இல்லை',
    noMatchMessage: 'அறிகுறிகளுடன் பொருந்தும் நோய்கள் கிடைக்கவில்லை.',

    // Confirmation Screen
    confirmImagesTitle: 'படங்களை ஒப்பிட்டு நோயை உறுதிப்படுத்துங்கள்',
    confirmImagesSubtitle: 'இந்த படங்கள் உங்கள் செடியின் அறிகுறிகளுடன் பொருந்துகிறதா என பார்க்கவும்.',
    thisMatches: 'இது பொருந்துகிறது',
    selected: '✓ தேர்வு செய்யப்பட்டது',
    noImageMatches: 'எந்த படமும் பொருந்தவில்லையா?',
    viewOtherDisease: 'வேறு நோயை பார்க்கவும்',
    confirmModalTitle: 'நோயை உறுதிப்படுத்துங்கள்',
    confirmModalMessage: 'நீங்கள் தேர்வு செய்த நோய்:',
    confirmModalQuestion: 'இந்த நோய் உங்கள் செடியின் நிலையுடன் பொருந்துகிறது என்று உறுதிப்படுத்துகிறீர்களா?',

    // Result Screen
    diseaseConfirmed: 'நோய் உறுதிப்படுத்தப்பட்டது',
    verificationBadge: '✓ அறிகுறி + பட உறுதிப்படுத்தல்',
    keySymptomsTitle: 'முக்கிய அறிகுறிகள்:',
    viewTreatmentsBtn: 'சிகிச்சை முறைகளை காண்க 🌱',
    missingDataTitle: 'பிழை',
    missingDataMessage: 'நோய் தரவுகளை காணவில்லை.',
    goToHome: 'முகப்புக்கு செல்லவும்',

    // Treatment Screen
    whatToDo: 'என்ன செய்ய வேண்டும்?',
    prevention: 'தடுப்பு நடவடிக்கைகள்',
    warnings: 'கவனிக்க வேண்டியது',
    dataSource: 'தரவு மூலம்',
    listenInTamil: '🔊 தமிழில் கேட்க',

    // Voice Response Screen
    preparingAudio: 'குரல் பதிலை தயார் செய்கிறது...',
    listenAgain: '🔊 மீண்டும் கேட்க',
    returnHome: 'முகப்புக்கு திரும்பவும் 🏠',

    // History Screen
    historyTitle: 'கண்டறிதல் வரலாறு',
    noHistoryTitle: 'முந்தைய கண்டறிதல்கள் எதுவும் இல்லை',
    statusIncomplete: 'முடிவடையவில்லை',
    statusHighMatch: 'உயர் பொருத்தம்',
    statusMediumMatch: 'நடுத்தர பொருத்தம்',
    statusLowMatch: 'குறைந்த பொருத்தம்',
    noDiseaseDetected: 'நோய் கண்டறியப்படவில்லை',

    // About Screen
    versionInfo: 'பதிப்பு 1.0 (மாதிரி)',
    aboutTitle: 'பற்றி',
    aboutDescription: 'இந்த செயலி தக்காளி விவசாயிகளுக்காக உருவாக்கப்பட்டது. உங்கள் செடியின் அறிகுறிகளை பேசி நோய்களை கண்டறியவும், தகுந்த சிகிச்சை முறைகளை பெறவும் இது உதவும்.',
    dataSourcesTitle: 'தரவு மூலங்கள்',
    sourceTreatments: 'சிகிச்சை முறைகள்',
    sourceImages: 'நோய் படங்கள்',
    settingsTitle: 'அமைப்பு',
    languageLabel: 'மொழி (Language)',
    disclaimerTitle: 'பொறுப்புத் துறப்பு (Disclaimer)',
    disclaimerFullText: 'இந்த செயலியில் வழங்கப்படும் தகவல்கள் பொதுவான வழிகாட்டுதலுக்காக மட்டுமே. நோய்களை உறுதிப்படுத்தவும், இரசாயன மருந்துகளை பயன்படுத்தும் முன்பும் அருகிலுள்ள வேளாண் துறை அதிகாரிகளையோ அல்லது விவசாய நிபுணர்களையோ அணுகவும்.'
  }
};
