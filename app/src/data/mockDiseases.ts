/**
 * Mock disease data for 7 tomato diseases + healthy.
 * Tamil names verified for agricultural context.
 */

import { DiseaseCandidate, Symptom } from '@/types/diagnosis';

// ─── Common Symptoms ─────────────────────────────────────────────────────────

export const ALL_SYMPTOMS: Symptom[] = [
  {
    id: 'sym-1',
    name: 'Dark concentric spots on leaves',
    tamilName: 'இலைகளில் கருமையான வட்ட புள்ளிகள்',
    plantPart: 'leaf',
  },
  {
    id: 'sym-2',
    name: 'Yellow halo around spots',
    tamilName: 'புள்ளிகளைச் சுற்றி மஞ்சள் வளையம்',
    plantPart: 'leaf',
  },
  {
    id: 'sym-3',
    name: 'Leaves turning yellow',
    tamilName: 'இலைகள் மஞ்சளாக மாறுதல்',
    plantPart: 'leaf',
  },
  {
    id: 'sym-4',
    name: 'Water-soaked lesions',
    tamilName: 'நீர் ஊறிய புண்கள்',
    plantPart: 'leaf',
  },
  {
    id: 'sym-5',
    name: 'White fuzzy growth on underside',
    tamilName: 'இலையின் அடிப்பகுதியில் வெள்ளை பூஞ்சை வளர்ச்சி',
    plantPart: 'leaf',
  },
  {
    id: 'sym-6',
    name: 'Small dark spots with light centers',
    tamilName: 'ஒளி மையத்துடன் சிறிய கருமையான புள்ளிகள்',
    plantPart: 'leaf',
  },
  {
    id: 'sym-7',
    name: 'Raised scab-like spots on fruit',
    tamilName: 'பழத்தில் உயர்ந்த சொறி போன்ற புள்ளிகள்',
    plantPart: 'fruit',
  },
  {
    id: 'sym-8',
    name: 'Olive-green patches on upper leaves',
    tamilName: 'மேல் இலைகளில் ஆலிவ்-பச்சை திட்டுகள்',
    plantPart: 'leaf',
  },
  {
    id: 'sym-9',
    name: 'Velvety brown growth underneath',
    tamilName: 'அடியில் பட்டு போன்ற பழுப்பு வளர்ச்சி',
    plantPart: 'leaf',
  },
  {
    id: 'sym-10',
    name: 'Leaf curling upward',
    tamilName: 'இலைகள் மேல்நோக்கி சுருளுதல்',
    plantPart: 'leaf',
  },
  {
    id: 'sym-11',
    name: 'Stunted plant growth',
    tamilName: 'தாவர வளர்ச்சி குன்றுதல்',
    plantPart: 'whole',
  },
  {
    id: 'sym-12',
    name: 'Rapid wilting and browning',
    tamilName: 'விரைவான வாடல் மற்றும் பழுப்படைதல்',
    plantPart: 'whole',
  },
  {
    id: 'sym-13',
    name: 'Brown firm rot on fruit',
    tamilName: 'பழத்தில் பழுப்பு நிற கெட்ட அழுகல்',
    plantPart: 'fruit',
  },
  {
    id: 'sym-14',
    name: 'Lower leaves affected first',
    tamilName: 'கீழ் இலைகள் முதலில் பாதிக்கப்படும்',
    plantPart: 'leaf',
  },
];

// ─── Disease Definitions ─────────────────────────────────────────────────────

export const DISEASES: DiseaseCandidate[] = [
  {
    id: 'early-blight',
    name: 'Early Blight',
    tamilName: 'ஆரம்ப கருகல் நோய்',
    scientificName: 'Alternaria solani',
    matchLevel: 'high',
    matchedSymptoms: [ALL_SYMPTOMS[0], ALL_SYMPTOMS[1], ALL_SYMPTOMS[13]],
    description: 'Fungal disease causing concentric ring-shaped spots on lower leaves first, spreading upward.',
    tamilDescription: 'கீழ் இலைகளில் முதலில் தொடங்கி மேல்நோக்கி பரவும் வட்ட வடிவ புள்ளிகளை ஏற்படுத்தும் பூஞ்சை நோய்.',
  },
  {
    id: 'late-blight',
    name: 'Late Blight',
    tamilName: 'பிந்தைய கருகல் நோய்',
    scientificName: 'Phytophthora infestans',
    matchLevel: 'high',
    matchedSymptoms: [ALL_SYMPTOMS[3], ALL_SYMPTOMS[4], ALL_SYMPTOMS[11], ALL_SYMPTOMS[12]],
    description: 'Devastating oomycete disease causing water-soaked lesions and rapid plant death.',
    tamilDescription: 'நீர் ஊறிய புண்கள் மற்றும் விரைவான தாவர இறப்பை ஏற்படுத்தும் பேரழிவு நோய்.',
  },
  {
    id: 'septoria',
    name: 'Septoria Leaf Spot',
    tamilName: 'செப்டோரியா இலைப்புள்ளி நோய்',
    scientificName: 'Septoria lycopersici',
    matchLevel: 'medium',
    matchedSymptoms: [ALL_SYMPTOMS[5], ALL_SYMPTOMS[2], ALL_SYMPTOMS[13]],
    description: 'Fungal disease producing small dark spots with light gray centers on lower leaves.',
    tamilDescription: 'கீழ் இலைகளில் ஒளி சாம்பல் மையத்துடன் சிறிய கருமையான புள்ளிகளை உருவாக்கும் பூஞ்சை நோய்.',
  },
  {
    id: 'bacterial-spot',
    name: 'Bacterial Spot',
    tamilName: 'பாக்டீரியா புள்ளி நோய்',
    scientificName: 'Xanthomonas campestris pv. vesicatoria',
    matchLevel: 'medium',
    matchedSymptoms: [ALL_SYMPTOMS[6], ALL_SYMPTOMS[3]],
    description: 'Bacterial disease causing water-soaked spots on leaves and scab-like lesions on fruit.',
    tamilDescription: 'இலைகளில் நீர் ஊறிய புள்ளிகள் மற்றும் பழத்தில் சொறி போன்ற புண்களை ஏற்படுத்தும் பாக்டீரியா நோய்.',
  },
  {
    id: 'leaf-mold',
    name: 'Leaf Mold',
    tamilName: 'இலை பூஞ்சை நோய்',
    scientificName: 'Passalora fulva',
    matchLevel: 'medium',
    matchedSymptoms: [ALL_SYMPTOMS[7], ALL_SYMPTOMS[8]],
    description: 'Fungal disease causing olive-green to brown velvety patches on leaf undersides.',
    tamilDescription: 'இலையின் அடிப்புறத்தில் ஆலிவ்-பச்சை முதல் பழுப்பு நிற பட்டு போன்ற திட்டுகளை ஏற்படுத்தும் பூஞ்சை நோய்.',
  },
  {
    id: 'yellow-leaf-curl',
    name: 'Yellow Leaf Curl Virus',
    tamilName: 'மஞ்சள் இலை சுருட்டு வைரஸ்',
    scientificName: 'TYLCV',
    matchLevel: 'high',
    matchedSymptoms: [ALL_SYMPTOMS[9], ALL_SYMPTOMS[2], ALL_SYMPTOMS[10]],
    description: 'Viral disease transmitted by whiteflies causing upward leaf curling, yellowing, and stunted growth.',
    tamilDescription: 'வெள்ளை ஈக்களால் பரவும், இலைகள் மேல்நோக்கி சுருளுதல், மஞ்சளாதல் மற்றும் வளர்ச்சி குன்றுதலை ஏற்படுத்தும் வைரஸ் நோய்.',
  },
  {
    id: 'healthy',
    name: 'Healthy',
    tamilName: 'ஆரோக்கியமான',
    matchLevel: 'low',
    matchedSymptoms: [],
    description: 'No disease symptoms detected. Plant appears healthy.',
    tamilDescription: 'எந்த நோய் அறிகுறிகளும் கண்டறியப்படவில்லை. தாவரம் ஆரோக்கியமாக உள்ளது.',
  },
];

// ─── Helper: Get disease by ID ───────────────────────────────────────────────

export function getDiseaseById(id: string): DiseaseCandidate | undefined {
  return DISEASES.find((d) => d.id === id);
}

// ─── Mock transcript for demo ────────────────────────────────────────────────

export const MOCK_TRANSCRIPT =
  'என் தக்காளி செடியின் இலைகளில் கருமையான வட்ட புள்ளிகள் தெரிகின்றன. கீழ் இலைகள் முதலில் மஞ்சளாக மாறுகின்றன. புள்ளிகளைச் சுற்றி மஞ்சள் வளையம் உள்ளது.';

export const MOCK_SYMPTOMS_RESULT = {
  crop: 'Tomato',
  tamilCrop: 'தக்காளி',
  affectedPart: 'leaf' as const,
  tamilAffectedPart: 'இலை',
  symptoms: [ALL_SYMPTOMS[0], ALL_SYMPTOMS[1], ALL_SYMPTOMS[2], ALL_SYMPTOMS[13]],
};
