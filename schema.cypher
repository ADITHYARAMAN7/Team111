// =========================================================
// TOMATO DISEASE KNOWLEDGE GRAPH - Schema + Seed Data
// Run this entire file in Neo4j Browser / AuraDB Query tab
// =========================================================

// ---- Constraints (uniqueness) ----
CREATE CONSTRAINT crop_id IF NOT EXISTS FOR (c:Crop) REQUIRE c.crop_id IS UNIQUE;
CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (d:Disease) REQUIRE d.disease_id IS UNIQUE;
CREATE CONSTRAINT symptom_id IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE;
CREATE CONSTRAINT layterm_id IF NOT EXISTS FOR (l:LayTerm) REQUIRE l.term_id IS UNIQUE;
CREATE CONSTRAINT treatment_id IF NOT EXISTS FOR (t:Treatment) REQUIRE t.treatment_id IS UNIQUE;
CREATE CONSTRAINT image_id IF NOT EXISTS FOR (i:ConfirmationImage) REQUIRE i.image_id IS UNIQUE;

// ---- Crop ----
CREATE (:Crop {crop_id: 'tomato', name_en: 'Tomato', name_ta: 'தக்காளி'});

// ---- Diseases ----
CREATE (:Disease {disease_id: 'early_blight', name_en: 'Early Blight', name_ta: 'ஆரம்பகால கருகல் நோய்', type: 'fungal', severity_scale: 3});
CREATE (:Disease {disease_id: 'late_blight', name_en: 'Late Blight', name_ta: 'பிற்பகுதி கருகல் நோய்', type: 'fungal', severity_scale: 5});
CREATE (:Disease {disease_id: 'powdery_mildew', name_en: 'Powdery Mildew', name_ta: 'வெள்ளை பூஞ்சை நோய்', type: 'fungal', severity_scale: 2});
CREATE (:Disease {disease_id: 'whitefly', name_en: 'Whitefly Infestation', name_ta: 'வெள்ளை ஈ தாக்குதல்', type: 'pest', severity_scale: 3});
CREATE (:Disease {disease_id: 'leaf_curl_virus', name_en: 'Tomato Leaf Curl Virus', name_ta: 'இலை சுருள் நோய்', type: 'viral', severity_scale: 4});

// ---- Symptoms (technical) ----
CREATE (:Symptom {symptom_id: 'dark_ring_spots', description_en: 'Dark concentric ring spots on lower leaves', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'water_soaked_patches', description_en: 'Water-soaked patches turning black rapidly', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'white_fungal_underside', description_en: 'White fungal growth on underside of leaf', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'white_powdery_coating', description_en: 'White powdery/dust-like coating on leaf surface', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'tiny_flying_white_insects', description_en: 'Tiny white insects that fly up when leaf is disturbed', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'sticky_honeydew', description_en: 'Sticky/shiny residue on leaves, sooty mould', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'leaf_curling_upward', description_en: 'Leaves curling upward, stunted plant growth', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'yellowing_margins', description_en: 'Yellowing at leaf margins', affected_part: 'leaf'});

// ---- Lay Terms (Tamil, farmer-facing descriptions) ----
CREATE (:LayTerm {term_id: 'lt_black_spots', raw_text: 'இலையில் கருப்பு புள்ளிகள்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_ring_spot', raw_text: 'வளையம் போன்ற புள்ளி இலையில்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_water_black', raw_text: 'இலை நனைந்து கருகுதல்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_white_fungus_under', raw_text: 'இலையின் அடியில் வெள்ளை பூஞ்சை', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_white_dust', raw_text: 'வெள்ளை தூள் போல இலையில்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_white_powder', raw_text: 'இலையில் வெள்ளை பொடி', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_white_flying_insects', raw_text: 'வெள்ளை சிறு பூச்சிகள் பறக்கும்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_white_dot_insects', raw_text: 'இலையில் வெள்ளை புள்ளி பூச்சி', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_sticky_leaf', raw_text: 'இலை ஒட்டும் தன்மையுடன் இருக்கும்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_leaf_curl', raw_text: 'இலை சுருண்டு போகுது', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_stunted', raw_text: 'செடி சரியா வளரலை குட்டையா இருக்கு', region_tag: 'general'});

// ---- Treatments ----
CREATE (:Treatment {treatment_id: 'mancozeb_spray', name_en: 'Mancozeb Fungicide Spray', type: 'chemical', dosage: '2.5g/litre water, every 7-10 days', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'copper_oxychloride', name_en: 'Copper Oxychloride Spray', type: 'chemical', dosage: '3g/litre water, every 7 days', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'sulfur_dust', name_en: 'Sulfur Dust / Wettable Sulfur Spray', type: 'organic', dosage: '2g/litre water, weekly', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'neem_oil', name_en: 'Neem Oil Spray', type: 'organic', dosage: '5ml/litre water, every 5-7 days', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'yellow_sticky_traps', name_en: 'Yellow Sticky Traps', type: 'organic', dosage: '10-15 traps/acre', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'remove_infected', name_en: 'Rogue Out & Destroy Infected Plants', type: 'cultural', dosage: 'Immediate removal + burn/bury away from field', cost_tier: 'free'});

// ---- Confirmation Images (placeholders - replace url with real hosted image paths) ----
CREATE (:ConfirmationImage {image_id: 'img_early_blight', disease_id: 'early_blight', url: '/static/images/early_blight.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_late_blight', disease_id: 'late_blight', url: '/static/images/late_blight.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_powdery_mildew', disease_id: 'powdery_mildew', url: '/static/images/powdery_mildew.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_whitefly', disease_id: 'whitefly', url: '/static/images/whitefly.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_leaf_curl_virus', disease_id: 'leaf_curl_virus', url: '/static/images/leaf_curl_virus.jpg', verified_count: 0});

// =========================================================
// RELATIONSHIPS
// =========================================================

// ---- Crop grown -> Disease can affect ----
MATCH (c:Crop {crop_id:'tomato'}), (d:Disease)
CREATE (c)-[:SUSCEPTIBLE_TO]->(d);

// ---- LayTerm -> Symptom (confidence weight, seeded manually, refined by feedback loop) ----
MATCH (l:LayTerm {term_id:'lt_black_spots'}), (s:Symptom {symptom_id:'dark_ring_spots'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.7}]->(s);
MATCH (l:LayTerm {term_id:'lt_ring_spot'}), (s:Symptom {symptom_id:'dark_ring_spots'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.95}]->(s);
MATCH (l:LayTerm {term_id:'lt_water_black'}), (s:Symptom {symptom_id:'water_soaked_patches'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.85}]->(s);
MATCH (l:LayTerm {term_id:'lt_white_fungus_under'}), (s:Symptom {symptom_id:'white_fungal_underside'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_white_dust'}), (s:Symptom {symptom_id:'white_powdery_coating'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.8}]->(s);
MATCH (l:LayTerm {term_id:'lt_white_powder'}), (s:Symptom {symptom_id:'white_powdery_coating'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.85}]->(s);
MATCH (l:LayTerm {term_id:'lt_white_flying_insects'}), (s:Symptom {symptom_id:'tiny_flying_white_insects'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.95}]->(s);
MATCH (l:LayTerm {term_id:'lt_white_dot_insects'}), (s:Symptom {symptom_id:'tiny_flying_white_insects'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.6}]->(s);
MATCH (l:LayTerm {term_id:'lt_sticky_leaf'}), (s:Symptom {symptom_id:'sticky_honeydew'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_leaf_curl'}), (s:Symptom {symptom_id:'leaf_curling_upward'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_stunted'}), (s:Symptom {symptom_id:'leaf_curling_upward'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.5}]->(s);

// ---- Disease -> Symptom (P(symptom | disease)) ----
MATCH (d:Disease {disease_id:'early_blight'}), (s:Symptom {symptom_id:'dark_ring_spots'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'early_blight'}), (s:Symptom {symptom_id:'yellowing_margins'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.4}]->(s);

MATCH (d:Disease {disease_id:'late_blight'}), (s:Symptom {symptom_id:'water_soaked_patches'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'late_blight'}), (s:Symptom {symptom_id:'white_fungal_underside'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.85}]->(s);

MATCH (d:Disease {disease_id:'powdery_mildew'}), (s:Symptom {symptom_id:'white_powdery_coating'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.95}]->(s);
MATCH (d:Disease {disease_id:'powdery_mildew'}), (s:Symptom {symptom_id:'yellowing_margins'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.3}]->(s);

MATCH (d:Disease {disease_id:'whitefly'}), (s:Symptom {symptom_id:'tiny_flying_white_insects'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.95}]->(s);
MATCH (d:Disease {disease_id:'whitefly'}), (s:Symptom {symptom_id:'sticky_honeydew'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.8}]->(s);
MATCH (d:Disease {disease_id:'whitefly'}), (s:Symptom {symptom_id:'white_powdery_coating'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.3}]->(s);
// NOTE: whitefly and powdery_mildew intentionally overlap on white_powdery_coating
// (farmers describe both as "white dust") - this is the ambiguity the
// discriminative-question algorithm is designed to resolve.

MATCH (d:Disease {disease_id:'leaf_curl_virus'}), (s:Symptom {symptom_id:'leaf_curling_upward'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'leaf_curl_virus'}), (s:Symptom {symptom_id:'yellowing_margins'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.5}]->(s);

// ---- Disease -> Treatment (efficacy weight) ----
MATCH (d:Disease {disease_id:'early_blight'}), (t:Treatment {treatment_id:'mancozeb_spray'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);
MATCH (d:Disease {disease_id:'late_blight'}), (t:Treatment {treatment_id:'copper_oxychloride'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'late_blight'}), (t:Treatment {treatment_id:'remove_infected'})
CREATE (d)-[:TREATED_BY {efficacy: 0.9}]->(t);
MATCH (d:Disease {disease_id:'powdery_mildew'}), (t:Treatment {treatment_id:'sulfur_dust'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);
MATCH (d:Disease {disease_id:'powdery_mildew'}), (t:Treatment {treatment_id:'neem_oil'})
CREATE (d)-[:TREATED_BY {efficacy: 0.7}]->(t);
MATCH (d:Disease {disease_id:'whitefly'}), (t:Treatment {treatment_id:'yellow_sticky_traps'})
CREATE (d)-[:TREATED_BY {efficacy: 0.75}]->(t);
MATCH (d:Disease {disease_id:'whitefly'}), (t:Treatment {treatment_id:'neem_oil'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'leaf_curl_virus'}), (t:Treatment {treatment_id:'remove_infected'})
CREATE (d)-[:TREATED_BY {efficacy: 0.9}]->(t);

// ---- Disease -> ConfirmationImage ----
MATCH (d:Disease {disease_id:'early_blight'}), (i:ConfirmationImage {image_id:'img_early_blight'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'late_blight'}), (i:ConfirmationImage {image_id:'img_late_blight'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'powdery_mildew'}), (i:ConfirmationImage {image_id:'img_powdery_mildew'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'whitefly'}), (i:ConfirmationImage {image_id:'img_whitefly'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'leaf_curl_virus'}), (i:ConfirmationImage {image_id:'img_leaf_curl_virus'})
CREATE (d)-[:CONFIRMED_BY]->(i);
