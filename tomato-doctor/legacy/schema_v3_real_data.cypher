// =========================================================
// TOMATO DISEASE KG — REAL DATA UPDATE (v3)
// Source: Jagtap, Shinde, Marade, Sawant, Sable, Mahalle (2025).
// "A Comprehensive Dataset of Tomato Plant Diseases for National
// Predictive Analytics and Crop Health Management." Mendeley Data.
// DOI: 10.17632/ztncd79yhk.1
//
// Run this AFTER schema.cypher and schema_v2_expansion.cypher.
//
// What this does:
//  1. Tags existing overlapping diseases (Early Blight, Late Blight,
//     Septoria, Spider Mite, Mosaic Virus, Yellow Leaf Curl Virus) with
//     a source_citation, and adds REAL treatment products + dosages
//     from the dataset (replacing earlier estimated ones as your
//     primary cited treatments).
//  2. Adds 3 brand-new diseases fully sourced from the dataset:
//     Leaf Miner, Leaf Mold, Target Spot.
//  3. Tamil lay-terms are still author-written (the dataset is English-
//     only) - this is expected and matches the project's documented
//     methodology: technical layer sourced, colloquial layer authored/
//     survey-driven.
// =========================================================

// ---- Tag existing diseases with real-data citation ----
MATCH (d:Disease) WHERE d.disease_id IN
  ['early_blight','late_blight','septoria_leaf_spot','spider_mite','mosaic_virus','leaf_curl_virus']
SET d.source_citation = 'Jagtap et al. 2025, Mendeley Data, DOI:10.17632/ztncd79yhk.1';

// =========================================================
// REAL TREATMENTS for existing diseases (actual products + dosages
// from the dataset, replacing estimated ones as primary citations)
// =========================================================

CREATE (:Treatment {treatment_id: 'real_mancozeb_75wp', name_en: 'Mancozeb 75% WP', type: 'chemical', dosage: '3 g/litre of water', cost_tier: 'low', source: 'Jagtap et al. 2025'});
CREATE (:Treatment {treatment_id: 'real_copper_hydroxide_eb', name_en: 'Copper Hydroxide', type: 'chemical', dosage: '10-day schedule, starting pre-bloom or at first sign of blight spots', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'early_blight'}), (t:Treatment {treatment_id:'real_mancozeb_75wp'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);
MATCH (d:Disease {disease_id:'early_blight'}), (t:Treatment {treatment_id:'real_copper_hydroxide_eb'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);

CREATE (:Treatment {treatment_id: 'real_copper_oxychloride_lb', name_en: 'Copper Oxychloride 50% WP', type: 'chemical', dosage: '1-2 g/litre of water', cost_tier: 'low', source: 'Jagtap et al. 2025'});
CREATE (:Treatment {treatment_id: 'real_trichoderma_lb', name_en: 'Trichoderma asperellum (soil application)', type: 'organic', dosage: '1.0 kg/acre', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'late_blight'}), (t:Treatment {treatment_id:'real_copper_oxychloride_lb'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'late_blight'}), (t:Treatment {treatment_id:'real_trichoderma_lb'})
CREATE (d)-[:TREATED_BY {efficacy: 0.7}]->(t);

CREATE (:Treatment {treatment_id: 'real_copper_oxychloride_septoria', name_en: 'Copper Oxychloride 50% WP', type: 'chemical', dosage: 'Apply at 7-10 day intervals through the late season', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'septoria_leaf_spot'}), (t:Treatment {treatment_id:'real_copper_oxychloride_septoria'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'septoria_leaf_spot'}), (t:Treatment {treatment_id:'real_mancozeb_75wp'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);

CREATE (:Treatment {treatment_id: 'real_insecticidal_soap', name_en: 'Insecticidal Soap', type: 'organic', dosage: 'Standard foliar spray dilution per label', cost_tier: 'low', source: 'Jagtap et al. 2025'});
CREATE (:Treatment {treatment_id: 'real_sulfur_mite', name_en: 'Sulfur (miticide)', type: 'organic', dosage: 'Standard foliar spray dilution per label', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'spider_mite'}), (t:Treatment {treatment_id:'real_insecticidal_soap'})
CREATE (d)-[:TREATED_BY {efficacy: 0.75}]->(t);
MATCH (d:Disease {disease_id:'spider_mite'}), (t:Treatment {treatment_id:'real_sulfur_mite'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);

CREATE (:Treatment {treatment_id: 'real_sodium_hypochlorite_seed', name_en: 'Sodium Hypochlorite Seed Treatment', type: 'cultural', dosage: 'Immerse seeds in 1% solution for 10 minutes before planting', cost_tier: 'free', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'mosaic_virus'}), (t:Treatment {treatment_id:'real_sodium_hypochlorite_seed'})
CREATE (d)-[:TREATED_BY {efficacy: 0.7}]->(t);
// NOTE: dataset explicitly states "Fungicides will NOT treat this viral disease" -
// worth keeping in your report as a real example of a treatment-type constraint
// your KG's `type` field on Treatment can encode/filter on.

CREATE (:Treatment {treatment_id: 'real_neonicotinoid_ylcv', name_en: 'Neonicotinoid (targets whitefly vector)', type: 'chemical', dosage: 'Per product label - controls the whitefly vector, not the virus directly', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'leaf_curl_virus'}), (t:Treatment {treatment_id:'real_neonicotinoid_ylcv'})
CREATE (d)-[:TREATED_BY {efficacy: 0.65}]->(t);

// =========================================================
// NEW DISEASE: Leaf Miner (pest, not in your KG yet)
// =========================================================
CREATE (:Disease {disease_id: 'leaf_miner', name_en: 'Leaf Miner', name_ta: 'இலை சுரங்கப் புழு', type: 'pest', severity_scale: 3, source_citation: 'Jagtap et al. 2025, Mendeley Data, DOI:10.17632/ztncd79yhk.1'});
MATCH (c:Crop {crop_id:'tomato'}), (d:Disease {disease_id:'leaf_miner'})
CREATE (c)-[:SUSCEPTIBLE_TO]->(d);

CREATE (:Symptom {symptom_id: 'serpentine_leaf_tunnels', description_en: 'Irregular winding tunnels (mines) visible on the leaf surface from larval feeding', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'leaf_distortion_shriveling', description_en: 'Leaves become distorted, shriveled, and may curl from mining damage', affected_part: 'leaf'});
MATCH (d:Disease {disease_id:'leaf_miner'}), (s:Symptom {symptom_id:'serpentine_leaf_tunnels'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.95}]->(s);
MATCH (d:Disease {disease_id:'leaf_miner'}), (s:Symptom {symptom_id:'leaf_distortion_shriveling'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.6}]->(s);

CREATE (:LayTerm {term_id: 'lt_leaf_tunnels', raw_text: 'இலையில் சுரங்கம் போல வளைந்த கோடுகள்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_leaf_shrivel', raw_text: 'இலை சுருங்கி வளைந்து போகுது', region_tag: 'general'});
MATCH (l:LayTerm {term_id:'lt_leaf_tunnels'}), (s:Symptom {symptom_id:'serpentine_leaf_tunnels'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_leaf_shrivel'}), (s:Symptom {symptom_id:'leaf_distortion_shriveling'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.75}]->(s);

CREATE (:Treatment {treatment_id: 'real_bt_leafminer', name_en: 'Bacillus thuringiensis (Bt)', type: 'organic', dosage: 'Effective against early larval stages; standard foliar spray', cost_tier: 'low', source: 'Jagtap et al. 2025'});
CREATE (:Treatment {treatment_id: 'real_pheromone_leafminer', name_en: 'Pheromone Traps', type: 'organic', dosage: '45-50 traps per hectare', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'leaf_miner'}), (t:Treatment {treatment_id:'real_bt_leafminer'})
CREATE (d)-[:TREATED_BY {efficacy: 0.75}]->(t);
MATCH (d:Disease {disease_id:'leaf_miner'}), (t:Treatment {treatment_id:'real_pheromone_leafminer'})
CREATE (d)-[:TREATED_BY {efficacy: 0.7}]->(t);
// NOTE: no ConfirmationImage seeded for leaf_miner - PlantVillage does not
// have a leaf-miner class (it's a pest damage pattern, not a standard
// classification target). Flagged as a gap for your report / future work.

// =========================================================
// NEW DISEASE: Leaf Mold
// =========================================================
CREATE (:Disease {disease_id: 'leaf_mold', name_en: 'Leaf Mold', name_ta: 'இலை பூஞ்சை நோய்', type: 'fungal', severity_scale: 3, source_citation: 'Jagtap et al. 2025, Mendeley Data, DOI:10.17632/ztncd79yhk.1'});
MATCH (c:Crop {crop_id:'tomato'}), (d:Disease {disease_id:'leaf_mold'})
CREATE (c)-[:SUSCEPTIBLE_TO]->(d);

CREATE (:Symptom {symptom_id: 'olive_velvety_mold_underside', description_en: 'Olive-green to brown velvety mold on the lower leaf surface below pale yellow leaf spots', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'pale_yellow_upper_spots', description_en: 'Pale greenish-yellow spots with no definite margins on upper leaf surface', affected_part: 'leaf'});
MATCH (d:Disease {disease_id:'leaf_mold'}), (s:Symptom {symptom_id:'olive_velvety_mold_underside'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'leaf_mold'}), (s:Symptom {symptom_id:'pale_yellow_upper_spots'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.6}]->(s);

CREATE (:LayTerm {term_id: 'lt_velvety_mold_under', raw_text: 'இலையின் அடியில் பச்சை பழுப்பு பூஞ்சை', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_pale_yellow_spots', raw_text: 'இலை மேல் வெளிர் மஞ்சள் புள்ளிகள்', region_tag: 'general'});
MATCH (l:LayTerm {term_id:'lt_velvety_mold_under'}), (s:Symptom {symptom_id:'olive_velvety_mold_underside'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_pale_yellow_spots'}), (s:Symptom {symptom_id:'pale_yellow_upper_spots'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.55}]->(s);
// NOTE: pale_yellow_upper_spots deliberately has modest lay-term confidence -
// "pale yellow spots" is a common, low-specificity descriptor shared with
// several other diseases in this KG; it should rarely drive a diagnosis
// alone and is a good real example of low-DISCRIMINATES-value symptom.

CREATE (:Treatment {treatment_id: 'real_azoxy_difeno_leafmold', name_en: 'Azoxystrobin + Difenoconazole', type: 'chemical', dosage: 'Per product label', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'leaf_mold'}), (t:Treatment {treatment_id:'real_azoxy_difeno_leafmold'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'leaf_mold'}), (t:Treatment {treatment_id:'real_mancozeb_75wp'})
CREATE (d)-[:TREATED_BY {efficacy: 0.75}]->(t);

CREATE (:ConfirmationImage {image_id: 'img_leaf_mold', disease_id: 'leaf_mold', url: '/static/images/leaf_mold.jpg', verified_count: 0});
MATCH (d:Disease {disease_id:'leaf_mold'}), (i:ConfirmationImage {image_id:'img_leaf_mold'})
CREATE (d)-[:CONFIRMED_BY]->(i);

// =========================================================
// NEW DISEASE: Target Spot
// =========================================================
CREATE (:Disease {disease_id: 'target_spot', name_en: 'Target Spot', name_ta: 'இலக்கு புள்ளி நோய்', type: 'fungal', severity_scale: 4, source_citation: 'Jagtap et al. 2025, Mendeley Data, DOI:10.17632/ztncd79yhk.1'});
MATCH (c:Crop {crop_id:'tomato'}), (d:Disease {disease_id:'target_spot'})
CREATE (c)-[:SUSCEPTIBLE_TO]->(d);

CREATE (:Symptom {symptom_id: 'target_ring_lesions', description_en: 'Circular spots with gray to pale brown centers and dark concentric rings, target-like appearance', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'water_soaked_pinpoint_spots', description_en: 'Pinpoint-sized, water-soaked spots on the upper leaf surface, progressing to necrotic lesions', affected_part: 'leaf'});
MATCH (d:Disease {disease_id:'target_spot'}), (s:Symptom {symptom_id:'target_ring_lesions'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'target_spot'}), (s:Symptom {symptom_id:'water_soaked_pinpoint_spots'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.6}]->(s);
// NOTE: target_ring_lesions deliberately overlaps in wording/concept with
// early_blight's dark_ring_spots and small_dark_border_spots (septoria) -
// this is a REAL three-way ambiguous case straight from the literature
// (all three genuinely produce ring-like leaf lesions), a strong example
// for your paper's disambiguation section.
MATCH (d:Disease {disease_id:'target_spot'}), (s:Symptom {symptom_id:'dark_ring_spots'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.35}]->(s);

CREATE (:LayTerm {term_id: 'lt_target_ring', raw_text: 'இலக்கு வளையம் போன்ற புள்ளிகள் இலையில்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_pinpoint_water_spots', raw_text: 'இலையில் சிறிய நீர் தேங்கிய புள்ளிகள்', region_tag: 'general'});
MATCH (l:LayTerm {term_id:'lt_target_ring'}), (s:Symptom {symptom_id:'target_ring_lesions'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.85}]->(s);
MATCH (l:LayTerm {term_id:'lt_pinpoint_water_spots'}), (s:Symptom {symptom_id:'water_soaked_pinpoint_spots'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.8}]->(s);

CREATE (:Treatment {treatment_id: 'real_azoxystrobin_targetspot', name_en: 'Azoxystrobin 250g/L SC', type: 'chemical', dosage: '10 ml/10L water', cost_tier: 'low', source: 'Jagtap et al. 2025'});
CREATE (:Treatment {treatment_id: 'real_bacillus_subtilis_targetspot', name_en: 'Bacillus subtilis (strain QST 713)', type: 'organic', dosage: '4.5 kg/ha', cost_tier: 'low', source: 'Jagtap et al. 2025'});
MATCH (d:Disease {disease_id:'target_spot'}), (t:Treatment {treatment_id:'real_azoxystrobin_targetspot'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'target_spot'}), (t:Treatment {treatment_id:'real_bacillus_subtilis_targetspot'})
CREATE (d)-[:TREATED_BY {efficacy: 0.65}]->(t);

CREATE (:ConfirmationImage {image_id: 'img_target_spot', disease_id: 'target_spot', url: '/static/images/target_spot.jpg', verified_count: 0});
MATCH (d:Disease {disease_id:'target_spot'}), (i:ConfirmationImage {image_id:'img_target_spot'})
CREATE (d)-[:CONFIRMED_BY]->(i);

// =========================================================
// Climate context from real favourable_condition data (FAVORED_BY)
// =========================================================
MATCH (d:Disease {disease_id:'leaf_miner'}), (sc:SeasonCondition {condition_id:'humid_monsoon'})
CREATE (d)-[:FAVORED_BY {boost: 0.75}]->(sc);
MATCH (d:Disease {disease_id:'leaf_mold'}), (sc:SeasonCondition {condition_id:'humid_monsoon'})
CREATE (d)-[:FAVORED_BY {boost: 0.85}]->(sc);
MATCH (d:Disease {disease_id:'target_spot'}), (sc:SeasonCondition {condition_id:'humid_monsoon'})
CREATE (d)-[:FAVORED_BY {boost: 0.8}]->(sc);
