/**
 * Mock disease image data with source attribution.
 * Uses placeholder colors since real dataset images will be integrated later.
 */

import { DiseaseImage } from '@/types/diagnosis';

export const MOCK_IMAGES: DiseaseImage[] = [
  // Early Blight
  {
    id: 'img-eb-1',
    diseaseId: 'early-blight',
    imageUrl: 'https://via.placeholder.com/400x300/8B4513/FFFFFF?text=Early+Blight+1',
    description: 'Concentric ring pattern on tomato leaf (target-board appearance)',
    tamilDescription: 'தக்காளி இலையில் வட்ட வடிவ வளைய அமைப்பு (இலக்கு பலகை தோற்றம்)',
    source: 'PlantVillage Dataset',
    sourceUrl: 'https://plantvillage.psu.edu/',
  },
  {
    id: 'img-eb-2',
    diseaseId: 'early-blight',
    imageUrl: 'https://via.placeholder.com/400x300/A0522D/FFFFFF?text=Early+Blight+2',
    description: 'Brown lesions with characteristic concentric rings on lower leaf',
    tamilDescription: 'கீழ் இலையில் சிறப்பான செறிவு வளையங்களுடன் பழுப்பு புண்கள்',
    source: 'PlantDoc Dataset',
    sourceUrl: 'https://github.com/pratikkayal/PlantDoc-Dataset',
  },
  // Late Blight
  {
    id: 'img-lb-1',
    diseaseId: 'late-blight',
    imageUrl: 'https://via.placeholder.com/400x300/2F4F4F/FFFFFF?text=Late+Blight+1',
    description: 'Large water-soaked lesions with white fuzzy growth',
    tamilDescription: 'வெள்ளை பூஞ்சை வளர்ச்சியுடன் பெரிய நீர் ஊறிய புண்கள்',
    source: 'PlantVillage Dataset',
    sourceUrl: 'https://plantvillage.psu.edu/',
  },
  {
    id: 'img-lb-2',
    diseaseId: 'late-blight',
    imageUrl: 'https://via.placeholder.com/400x300/556B2F/FFFFFF?text=Late+Blight+2',
    description: 'Darkened, water-soaked area spreading rapidly across leaf',
    tamilDescription: 'இலை முழுவதும் வேகமாகப் பரவும் கருமையான, நீர் ஊறிய பகுதி',
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
  // Septoria Leaf Spot
  {
    id: 'img-sl-1',
    diseaseId: 'septoria',
    imageUrl: 'https://via.placeholder.com/400x300/696969/FFFFFF?text=Septoria+1',
    description: 'Numerous small circular spots with gray centers and dark borders',
    tamilDescription: 'சாம்பல் மையம் மற்றும் கருமையான எல்லைகளுடன் பல சிறிய வட்ட புள்ளிகள்',
    source: 'PlantVillage Dataset',
    sourceUrl: 'https://plantvillage.psu.edu/',
  },
  // Bacterial Spot
  {
    id: 'img-bs-1',
    diseaseId: 'bacterial-spot',
    imageUrl: 'https://via.placeholder.com/400x300/8B0000/FFFFFF?text=Bacterial+Spot+1',
    description: 'Small raised spots on green tomato fruit surface',
    tamilDescription: 'பச்சை தக்காளி பழ மேற்பரப்பில் சிறிய உயர்ந்த புள்ளிகள்',
    source: 'PlantVillage Dataset',
    sourceUrl: 'https://plantvillage.psu.edu/',
  },
  // Leaf Mold
  {
    id: 'img-lm-1',
    diseaseId: 'leaf-mold',
    imageUrl: 'https://via.placeholder.com/400x300/6B8E23/FFFFFF?text=Leaf+Mold+1',
    description: 'Olive-green patches on upper leaf surface with velvety brown underneath',
    tamilDescription: 'மேல் இலை மேற்பரப்பில் ஆலிவ்-பச்சை திட்டுகள், அடியில் பட்டு போன்ற பழுப்பு',
    source: 'PlantVillage Dataset',
    sourceUrl: 'https://plantvillage.psu.edu/',
  },
  // Yellow Leaf Curl
  {
    id: 'img-ylc-1',
    diseaseId: 'yellow-leaf-curl',
    imageUrl: 'https://via.placeholder.com/400x300/DAA520/FFFFFF?text=Yellow+Leaf+Curl+1',
    description: 'Upward curling, yellowed leaves with stunted growth',
    tamilDescription: 'மேல்நோக்கி சுருண்ட, மஞ்சளான இலைகள் மற்றும் வளர்ச்சி குன்றிய நிலை',
    source: 'PlantVillage Dataset',
    sourceUrl: 'https://plantvillage.psu.edu/',
  },
  {
    id: 'img-ylc-2',
    diseaseId: 'yellow-leaf-curl',
    imageUrl: 'https://via.placeholder.com/400x300/BDB76B/FFFFFF?text=Yellow+Leaf+Curl+2',
    description: 'Stunted tomato plant with severely curled and yellowed leaves',
    tamilDescription: 'கடுமையாக சுருண்ட மற்றும் மஞ்சளான இலைகளுடன் வளர்ச்சி குன்றிய தக்காளி செடி',
    source: 'TNAU Agritech Portal',
    sourceUrl: 'https://agritech.tnau.ac.in/',
  },
];

export function getImagesByDiseaseId(diseaseId: string): DiseaseImage[] {
  return MOCK_IMAGES.filter((img) => img.diseaseId === diseaseId);
}
