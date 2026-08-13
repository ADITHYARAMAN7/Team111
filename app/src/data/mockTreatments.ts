/**
 * Mock treatment data with source-backed recommendations.
 * Data structured for TNAU (Tamil Nadu Agricultural University) and general agricultural sources.
 */

import { Treatment } from '@/types/diagnosis';

export const MOCK_TREATMENTS: Treatment[] = [
  {
    diseaseId: 'early-blight',
    diseaseName: 'Early Blight',
    tamilDiseaseName: 'ஆரம்ப கருகல் நோய்',
    management: [
      {
        text: 'Apply Mancozeb 75% WP at 2.5g/L water as foliar spray',
        tamilText: 'மான்கோசெப் 75% WP ஐ 2.5 கிராம்/லிட்டர் நீரில் கரைத்து இலைகளில் தெளிக்கவும்',
        icon: '💊',
      },
      {
        text: 'Remove and destroy infected lower leaves',
        tamilText: 'பாதிக்கப்பட்ட கீழ் இலைகளை அகற்றி அழிக்கவும்',
        icon: '✂️',
      },
      {
        text: 'Apply Copper Oxychloride 50% WP at 3g/L as spray',
        tamilText: 'காப்பர் ஆக்சிக்ளோரைடு 50% WP ஐ 3 கிராம்/லிட்டர் தெளிக்கவும்',
        icon: '💊',
      },
    ],
    prevention: [
      {
        text: 'Use disease-free certified seeds',
        tamilText: 'நோயற்ற சான்றிதழ் பெற்ற விதைகளை பயன்படுத்தவும்',
        icon: '🌱',
      },
      {
        text: 'Practice 3-year crop rotation',
        tamilText: '3 ஆண்டு பயிர் சுழற்சி கடைப்பிடிக்கவும்',
        icon: '🔄',
      },
      {
        text: 'Ensure proper plant spacing for air circulation',
        tamilText: 'காற்றோட்டத்திற்கு சரியான செடி இடைவெளியை உறுதி செய்யவும்',
        icon: '🌿',
      },
      {
        text: 'Apply mulch to prevent soil splash',
        tamilText: 'மண் தெறிப்பை தடுக்க தழைக்கூளம் பயன்படுத்தவும்',
        icon: '🏞️',
      },
    ],
    warnings: [
      {
        text: 'Do not overhead irrigate — use drip irrigation',
        tamilText: 'மேலிருந்து நீர் பாய்ச்ச வேண்டாம் — சொட்டு நீர் பாசனம் பயன்படுத்தவும்',
        icon: '⚠️',
      },
      {
        text: 'Follow recommended dosage — excess fungicide can harm plants',
        tamilText: 'பரிந்துரைக்கப்பட்ட அளவை பின்பற்றவும் — அதிக பூஞ்சைக் கொல்லி செடிகளுக்கு தீங்கு விளைவிக்கும்',
        icon: '⚠️',
      },
    ],
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
  {
    diseaseId: 'late-blight',
    diseaseName: 'Late Blight',
    tamilDiseaseName: 'பிந்தைய கருகல் நோய்',
    management: [
      {
        text: 'Apply Metalaxyl + Mancozeb (Ridomil Gold) at 2g/L immediately',
        tamilText: 'உடனடியாக மெட்டாலாக்சில் + மான்கோசெப் (ரிடோமில் கோல்டு) 2 கிராம்/லிட்டர் தெளிக்கவும்',
        icon: '💊',
      },
      {
        text: 'Remove and destroy all infected plant parts',
        tamilText: 'பாதிக்கப்பட்ட அனைத்து தாவர பாகங்களையும் அகற்றி அழிக்கவும்',
        icon: '✂️',
      },
      {
        text: 'Improve drainage around plants',
        tamilText: 'செடிகளைச் சுற்றி வடிகால் வசதியை மேம்படுத்தவும்',
        icon: '💧',
      },
    ],
    prevention: [
      {
        text: 'Use resistant varieties like Arka Rakshak',
        tamilText: 'அர்க்கா ரக்ஷக் போன்ற எதிர்ப்பு இரகங்களை பயன்படுத்தவும்',
        icon: '🌱',
      },
      {
        text: 'Avoid planting in low-lying waterlogged areas',
        tamilText: 'பள்ளமான நீர் தேங்கும் பகுதிகளில் நடவு செய்ய வேண்டாம்',
        icon: '🏞️',
      },
      {
        text: 'Spray preventive fungicide before rainy season',
        tamilText: 'மழைக்காலத்திற்கு முன் தடுப்பு பூஞ்சைக் கொல்லி தெளிக்கவும்',
        icon: '☔',
      },
    ],
    warnings: [
      {
        text: 'Late blight spreads extremely fast — act immediately',
        tamilText: 'பிந்தைய கருகல் மிக வேகமாக பரவும் — உடனடியாக நடவடிக்கை எடுக்கவும்',
        icon: '🚨',
      },
      {
        text: 'Do not compost infected material — burn or bury deep',
        tamilText: 'பாதிக்கப்பட்ட பொருட்களை உரமாக்க வேண்டாம் — எரிக்கவும் அல்லது ஆழமாக புதைக்கவும்',
        icon: '⚠️',
      },
    ],
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
  {
    diseaseId: 'septoria',
    diseaseName: 'Septoria Leaf Spot',
    tamilDiseaseName: 'செப்டோரியா இலைப்புள்ளி நோய்',
    management: [
      {
        text: 'Apply Chlorothalonil 75% WP at 2g/L water',
        tamilText: 'குளோரோதலோனில் 75% WP ஐ 2 கிராம்/லிட்டர் நீரில் தெளிக்கவும்',
        icon: '💊',
      },
      {
        text: 'Remove heavily infected leaves from lower canopy',
        tamilText: 'கீழ் பகுதியில் கடுமையாக பாதிக்கப்பட்ட இலைகளை அகற்றவும்',
        icon: '✂️',
      },
    ],
    prevention: [
      {
        text: 'Maintain adequate spacing between plants',
        tamilText: 'செடிகளுக்கு இடையே போதுமான இடைவெளி பராமரிக்கவும்',
        icon: '🌿',
      },
      {
        text: 'Avoid working in wet fields',
        tamilText: 'ஈரமான வயலில் வேலை செய்வதை தவிர்க்கவும்',
        icon: '💧',
      },
    ],
    warnings: [
      {
        text: 'Disease thrives in warm, wet conditions',
        tamilText: 'வெதுவெதுப்பான, ஈரமான சூழலில் நோய் செழிக்கும்',
        icon: '⚠️',
      },
    ],
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
  {
    diseaseId: 'bacterial-spot',
    diseaseName: 'Bacterial Spot',
    tamilDiseaseName: 'பாக்டீரியா புள்ளி நோய்',
    management: [
      {
        text: 'Apply Copper Hydroxide 77% WP at 2g/L',
        tamilText: 'காப்பர் ஹைட்ராக்சைடு 77% WP ஐ 2 கிராம்/லிட்டர் தெளிக்கவும்',
        icon: '💊',
      },
      {
        text: 'Apply Streptomycin sulphate 500ppm as foliar spray',
        tamilText: 'ஸ்ட்ரெப்டோமைசின் சல்ஃபேட் 500ppm இலைகளில் தெளிக்கவும்',
        icon: '💊',
      },
    ],
    prevention: [
      {
        text: 'Treat seeds with hot water (50°C for 25 minutes)',
        tamilText: 'விதைகளை சூடான நீரில் (50°C, 25 நிமிடங்கள்) நேர்த்தி செய்யவும்',
        icon: '🌡️',
      },
      {
        text: 'Avoid overhead irrigation',
        tamilText: 'மேலிருந்து நீர் பாய்ச்சுவதை தவிர்க்கவும்',
        icon: '💧',
      },
    ],
    warnings: [
      {
        text: 'No cure once severely infected — focus on prevention',
        tamilText: 'கடுமையாக பாதிக்கப்பட்டால் குணப்படுத்த முடியாது — தடுப்பில் கவனம் செலுத்தவும்',
        icon: '🚨',
      },
    ],
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
  {
    diseaseId: 'leaf-mold',
    diseaseName: 'Leaf Mold',
    tamilDiseaseName: 'இலை பூஞ்சை நோய்',
    management: [
      {
        text: 'Apply Mancozeb 75% WP at 2.5g/L as spray',
        tamilText: 'மான்கோசெப் 75% WP ஐ 2.5 கிராம்/லிட்டர் தெளிக்கவும்',
        icon: '💊',
      },
      {
        text: 'Improve ventilation in greenhouse/polyhouse',
        tamilText: 'பசுமைக் குடிலில் காற்றோட்டத்தை மேம்படுத்தவும்',
        icon: '🌬️',
      },
    ],
    prevention: [
      {
        text: 'Reduce humidity below 85%',
        tamilText: 'ஈரப்பதத்தை 85% க்கு கீழ் குறைக்கவும்',
        icon: '💨',
      },
      {
        text: 'Use resistant varieties',
        tamilText: 'எதிர்ப்பு இரகங்களை பயன்படுத்தவும்',
        icon: '🌱',
      },
    ],
    warnings: [
      {
        text: 'Common in poorly ventilated greenhouses',
        tamilText: 'மோசமான காற்றோட்டம் உள்ள பசுமைக் குடில்களில் பொதுவானது',
        icon: '⚠️',
      },
    ],
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
  {
    diseaseId: 'yellow-leaf-curl',
    diseaseName: 'Yellow Leaf Curl Virus',
    tamilDiseaseName: 'மஞ்சள் இலை சுருட்டு வைரஸ்',
    management: [
      {
        text: 'Remove and destroy infected plants immediately',
        tamilText: 'பாதிக்கப்பட்ட செடிகளை உடனடியாக அகற்றி அழிக்கவும்',
        icon: '🗑️',
      },
      {
        text: 'Control whiteflies using yellow sticky traps',
        tamilText: 'மஞ்சள் ஒட்டும் பொறிகள் பயன்படுத்தி வெள்ளை ஈக்களை கட்டுப்படுத்தவும்',
        icon: '🪤',
      },
      {
        text: 'Apply Imidacloprid 17.8% SL at 0.5ml/L for whitefly control',
        tamilText: 'வெள்ளை ஈ கட்டுப்பாட்டிற்கு இமிடாகுளோபிரிட் 17.8% SL ஐ 0.5 மில்லி/லிட்டர் தெளிக்கவும்',
        icon: '💊',
      },
    ],
    prevention: [
      {
        text: 'Use virus-resistant varieties like TH-328',
        tamilText: 'TH-328 போன்ற வைரஸ் எதிர்ப்பு இரகங்களை பயன்படுத்தவும்',
        icon: '🌱',
      },
      {
        text: 'Use 40-mesh nylon net as barrier against whiteflies',
        tamilText: 'வெள்ளை ஈக்களுக்கு எதிராக 40-மெஷ் நைலான் வலை பயன்படுத்தவும்',
        icon: '🪢',
      },
      {
        text: 'Raise seedlings in insect-proof nursery',
        tamilText: 'பூச்சி தடுப்பு நாற்றங்காலில் நாற்றுகளை வளர்க்கவும்',
        icon: '🏠',
      },
    ],
    warnings: [
      {
        text: 'No cure for viral diseases — prevention is the only strategy',
        tamilText: 'வைரஸ் நோய்களுக்கு மருந்து இல்லை — தடுப்பு மட்டுமே வழி',
        icon: '🚨',
      },
      {
        text: 'Infected plants will not recover — remove to prevent spread',
        tamilText: 'பாதிக்கப்பட்ட செடிகள் குணமடையாது — பரவலைத் தடுக்க அகற்றவும்',
        icon: '⚠️',
      },
    ],
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
];

export function getTreatmentByDiseaseId(diseaseId: string): Treatment | undefined {
  return MOCK_TREATMENTS.find((t) => t.diseaseId === diseaseId);
}
