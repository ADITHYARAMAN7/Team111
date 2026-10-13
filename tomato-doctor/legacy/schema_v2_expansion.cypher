// =========================================================
// TOMATO DISEASE KG — EXPANSION PACK (v2)
// Run this AFTER schema.cypher, on the SAME Neo4j instance.
// Adds 9 more diseases (fungal/bacterial/viral/pest/physiological),
// their symptoms, Tamil lay-terms, treatments, confirmation images,
// and a new Season/Climate layer (FAVORED_BY edges) for future
// climate-aware scoring.
// =========================================================

// ---- New Diseases ----
CREATE (:Disease {disease_id: 'septoria_leaf_spot', name_en: 'Septoria Leaf Spot', name_ta: 'செப்டோரியா இலை புள்ளி நோய்', type: 'fungal', severity_scale: 3});
CREATE (:Disease {disease_id: 'bacterial_spot', name_en: 'Bacterial Spot', name_ta: 'பாக்டீரியா புள்ளி நோய்', type: 'bacterial', severity_scale: 3});
CREATE (:Disease {disease_id: 'fusarium_wilt', name_en: 'Fusarium Wilt', name_ta: 'ஃபூசேரியம் வாட்டநோய்', type: 'fungal', severity_scale: 4});
CREATE (:Disease {disease_id: 'bacterial_wilt', name_en: 'Bacterial Wilt', name_ta: 'பாக்டீரியா வாட்டநோய்', type: 'bacterial', severity_scale: 5});
CREATE (:Disease {disease_id: 'blossom_end_rot', name_en: 'Blossom End Rot', name_ta: 'பூ முனை அழுகல்', type: 'physiological', severity_scale: 3});
CREATE (:Disease {disease_id: 'mosaic_virus', name_en: 'Tomato Mosaic Virus', name_ta: 'தக்காளி மொசைக் வைரஸ்', type: 'viral', severity_scale: 3});
CREATE (:Disease {disease_id: 'spider_mite', name_en: 'Two-Spotted Spider Mite', name_ta: 'இரட்டை புள்ளி சிலந்தி பூச்சி', type: 'pest', severity_scale: 3});
CREATE (:Disease {disease_id: 'fruit_borer', name_en: 'Fruit Borer', name_ta: 'பழம் துளைப்பான் புழு', type: 'pest', severity_scale: 4});
CREATE (:Disease {disease_id: 'root_knot_nematode', name_en: 'Root-Knot Nematode', name_ta: 'வேர் முடிச்சு நூற்புழு', type: 'pest', severity_scale: 3});

// ---- New Symptoms ----
CREATE (:Symptom {symptom_id: 'small_dark_border_spots', description_en: 'Small circular spots with dark border and gray center on lower leaves', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'water_soaked_yellow_halo', description_en: 'Small water-soaked spots with yellow halo, scabby texture', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'one_sided_wilting', description_en: 'One-sided wilting with yellowing of lower leaves', affected_part: 'whole_plant'});
CREATE (:Symptom {symptom_id: 'vascular_browning', description_en: 'Brown discoloration inside stem when cut open', affected_part: 'stem'});
CREATE (:Symptom {symptom_id: 'sudden_wilting_no_yellowing', description_en: 'Sudden wilting of entire plant without prior yellowing', affected_part: 'whole_plant'});
CREATE (:Symptom {symptom_id: 'dark_sunken_fruit_spot', description_en: 'Dark, sunken, leathery patch at the blossom end of the fruit', affected_part: 'fruit'});
CREATE (:Symptom {symptom_id: 'mottled_leaf_pattern', description_en: 'Mottled light/dark green pattern with leaf distortion', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'fine_speckling_leaf', description_en: 'Tiny yellow/white speckles across leaf surface', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'fine_webbing_underside', description_en: 'Fine spider-web-like webbing on underside of leaves', affected_part: 'leaf'});
CREATE (:Symptom {symptom_id: 'holes_in_fruit', description_en: 'Round bored holes in fruit with larvae visible inside', affected_part: 'fruit'});
CREATE (:Symptom {symptom_id: 'stunted_no_clear_leaf_symptom', description_en: 'Stunted growth with no obvious leaf symptom; roots may show galls', affected_part: 'root'});

// ---- New Lay Terms (Tamil) ----
CREATE (:LayTerm {term_id: 'lt_small_spots_grey', raw_text: 'இலையில் சிறிய சாம்பல் நிற புள்ளிகள்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_scabby_spots', raw_text: 'இலையில் மஞ்சள் வளையத்துடன் புள்ளி', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_one_side_wilt', raw_text: 'செடியின் ஒரு பக்கம் மட்டும் வாடுது', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_stem_brown_inside', raw_text: 'தண்டை வெட்டினா உள்ளே பழுப்பு நிறம்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_sudden_wilt', raw_text: 'செடி திடீரென்று முழுசா வாடுது', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_fruit_bottom_black', raw_text: 'தக்காளி பழத்தின் அடிப்பகுதி கருப்பா கெட்டுப்போகுது', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_mottled_leaf', raw_text: 'இலையில் வெளிர் பச்சை கரும்பச்சை கலவை மாதிரி', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_tiny_yellow_dots', raw_text: 'இலையில் சிறிய மஞ்சள் புள்ளிகள்', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_web_under_leaf', raw_text: 'இலையின் அடியில் சிலந்தி வலை போல', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_fruit_holes', raw_text: 'தக்காளி பழத்தில் துளைகள் புழு இருக்கு', region_tag: 'general'});
CREATE (:LayTerm {term_id: 'lt_stunted_no_reason', raw_text: 'செடி காரணமே இல்லாம குட்டையா இருக்கு', region_tag: 'general'});

// ---- New Treatments ----
CREATE (:Treatment {treatment_id: 'copper_bactericide', name_en: 'Copper-based Bactericide Spray', type: 'chemical', dosage: '3g/litre water, every 7 days', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'crop_rotation', name_en: 'Crop Rotation & Resistant Varieties', type: 'cultural', dosage: 'Rotate with non-solanaceous crop for 2-3 seasons', cost_tier: 'free'});
CREATE (:Treatment {treatment_id: 'calcium_spray', name_en: 'Calcium Chloride Foliar Spray', type: 'chemical', dosage: '5g/litre water, every 10 days during fruiting', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'consistent_watering', name_en: 'Consistent Watering Schedule + Mulching', type: 'cultural', dosage: 'Even soil moisture; avoid wet-dry cycles', cost_tier: 'free'});
CREATE (:Treatment {treatment_id: 'remove_and_disinfect', name_en: 'Remove Infected Plant & Disinfect Tools', type: 'cultural', dosage: 'Uproot and destroy; wash hands/tools with soap before touching healthy plants', cost_tier: 'free'});
CREATE (:Treatment {treatment_id: 'miticide_spray', name_en: 'Miticide / Wettable Sulfur Spray', type: 'organic', dosage: '2g/litre water, every 5-7 days', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'pheromone_traps', name_en: 'Pheromone Traps', type: 'organic', dosage: '5 traps/acre, replace lure monthly', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'bt_spray', name_en: 'Bacillus thuringiensis (Bt) Spray', type: 'organic', dosage: '2g/litre water, every 5-7 days, evening application', cost_tier: 'low'});
CREATE (:Treatment {treatment_id: 'soil_solarization', name_en: 'Soil Solarization Before Planting', type: 'cultural', dosage: 'Cover moist soil with clear plastic for 4-6 weeks in peak summer', cost_tier: 'free'});

// ---- New Confirmation Images (placeholders) ----
CREATE (:ConfirmationImage {image_id: 'img_septoria_leaf_spot', disease_id: 'septoria_leaf_spot', url: '/static/images/septoria_leaf_spot.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_bacterial_spot', disease_id: 'bacterial_spot', url: '/static/images/bacterial_spot.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_fusarium_wilt', disease_id: 'fusarium_wilt', url: '/static/images/fusarium_wilt.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_bacterial_wilt', disease_id: 'bacterial_wilt', url: '/static/images/bacterial_wilt.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_blossom_end_rot', disease_id: 'blossom_end_rot', url: '/static/images/blossom_end_rot.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_mosaic_virus', disease_id: 'mosaic_virus', url: '/static/images/mosaic_virus.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_spider_mite', disease_id: 'spider_mite', url: '/static/images/spider_mite.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_fruit_borer', disease_id: 'fruit_borer', url: '/static/images/fruit_borer.jpg', verified_count: 0});
CREATE (:ConfirmationImage {image_id: 'img_root_knot_nematode', disease_id: 'root_knot_nematode', url: '/static/images/root_knot_nematode.jpg', verified_count: 0});

// ---- New Season/Climate nodes (for future climate-aware scoring) ----
CREATE (:SeasonCondition {condition_id: 'humid_monsoon', name_en: 'Humid / Monsoon', temp_range: '22-30C', humidity_range: '80-100%'});
CREATE (:SeasonCondition {condition_id: 'hot_dry', name_en: 'Hot & Dry', temp_range: '30-40C', humidity_range: '20-40%'});
CREATE (:SeasonCondition {condition_id: 'cool_moist', name_en: 'Cool & Moist', temp_range: '15-22C', humidity_range: '60-80%'});

// =========================================================
// RELATIONSHIPS FOR NEW DISEASES
// =========================================================

// ---- Crop -> new Diseases ----
MATCH (c:Crop {crop_id:'tomato'}), (d:Disease)
WHERE d.disease_id IN ['septoria_leaf_spot','bacterial_spot','fusarium_wilt','bacterial_wilt',
                        'blossom_end_rot','mosaic_virus','spider_mite','fruit_borer','root_knot_nematode']
CREATE (c)-[:SUSCEPTIBLE_TO]->(d);

// ---- LayTerm -> Symptom ----
MATCH (l:LayTerm {term_id:'lt_small_spots_grey'}), (s:Symptom {symptom_id:'small_dark_border_spots'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.85}]->(s);
MATCH (l:LayTerm {term_id:'lt_scabby_spots'}), (s:Symptom {symptom_id:'water_soaked_yellow_halo'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.85}]->(s);
MATCH (l:LayTerm {term_id:'lt_one_side_wilt'}), (s:Symptom {symptom_id:'one_sided_wilting'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_stem_brown_inside'}), (s:Symptom {symptom_id:'vascular_browning'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_sudden_wilt'}), (s:Symptom {symptom_id:'sudden_wilting_no_yellowing'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.85}]->(s);
MATCH (l:LayTerm {term_id:'lt_fruit_bottom_black'}), (s:Symptom {symptom_id:'dark_sunken_fruit_spot'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_mottled_leaf'}), (s:Symptom {symptom_id:'mottled_leaf_pattern'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.85}]->(s);
MATCH (l:LayTerm {term_id:'lt_tiny_yellow_dots'}), (s:Symptom {symptom_id:'fine_speckling_leaf'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.75}]->(s);
MATCH (l:LayTerm {term_id:'lt_web_under_leaf'}), (s:Symptom {symptom_id:'fine_webbing_underside'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_fruit_holes'}), (s:Symptom {symptom_id:'holes_in_fruit'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.9}]->(s);
MATCH (l:LayTerm {term_id:'lt_stunted_no_reason'}), (s:Symptom {symptom_id:'stunted_no_clear_leaf_symptom'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.7}]->(s);
// NOTE: lt_stunted_no_reason also plausibly overlaps with leaf_curl_virus's
// stunted growth (leaf_curling_upward symptom) — intentional ambiguity,
// same disambiguation mechanism from v1 resolves it via other symptoms present.
MATCH (l:LayTerm {term_id:'lt_stunted_no_reason'}), (s:Symptom {symptom_id:'leaf_curling_upward'})
CREATE (l)-[:LAYTERM_MAPS_TO {weight: 0.3}]->(s);

// ---- Disease -> Symptom ----
MATCH (d:Disease {disease_id:'septoria_leaf_spot'}), (s:Symptom {symptom_id:'small_dark_border_spots'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);

MATCH (d:Disease {disease_id:'bacterial_spot'}), (s:Symptom {symptom_id:'water_soaked_yellow_halo'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'bacterial_spot'}), (s:Symptom {symptom_id:'small_dark_border_spots'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.35}]->(s);
// NOTE: intentional overlap with septoria_leaf_spot on small_dark_border_spots —
// water_soaked_yellow_halo is the discriminator between the two.

MATCH (d:Disease {disease_id:'fusarium_wilt'}), (s:Symptom {symptom_id:'one_sided_wilting'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'fusarium_wilt'}), (s:Symptom {symptom_id:'vascular_browning'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.85}]->(s);

MATCH (d:Disease {disease_id:'bacterial_wilt'}), (s:Symptom {symptom_id:'sudden_wilting_no_yellowing'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'bacterial_wilt'}), (s:Symptom {symptom_id:'vascular_browning'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.6}]->(s);
// NOTE: intentional overlap with fusarium_wilt on vascular_browning —
// sudden_wilting_no_yellowing vs one_sided_wilting is the discriminator.

MATCH (d:Disease {disease_id:'blossom_end_rot'}), (s:Symptom {symptom_id:'dark_sunken_fruit_spot'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.95}]->(s);

MATCH (d:Disease {disease_id:'mosaic_virus'}), (s:Symptom {symptom_id:'mottled_leaf_pattern'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);
MATCH (d:Disease {disease_id:'mosaic_virus'}), (s:Symptom {symptom_id:'leaf_curling_upward'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.25}]->(s);

MATCH (d:Disease {disease_id:'spider_mite'}), (s:Symptom {symptom_id:'fine_speckling_leaf'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.85}]->(s);
MATCH (d:Disease {disease_id:'spider_mite'}), (s:Symptom {symptom_id:'fine_webbing_underside'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.9}]->(s);

MATCH (d:Disease {disease_id:'fruit_borer'}), (s:Symptom {symptom_id:'holes_in_fruit'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.95}]->(s);

MATCH (d:Disease {disease_id:'root_knot_nematode'}), (s:Symptom {symptom_id:'stunted_no_clear_leaf_symptom'})
CREATE (d)-[:HAS_SYMPTOM {weight: 0.8}]->(s);

// ---- Disease -> Treatment ----
MATCH (d:Disease {disease_id:'septoria_leaf_spot'}), (t:Treatment {treatment_id:'mancozeb_spray'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'bacterial_spot'}), (t:Treatment {treatment_id:'copper_bactericide'})
CREATE (d)-[:TREATED_BY {efficacy: 0.75}]->(t);
MATCH (d:Disease {disease_id:'fusarium_wilt'}), (t:Treatment {treatment_id:'crop_rotation'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'fusarium_wilt'}), (t:Treatment {treatment_id:'remove_infected'})
CREATE (d)-[:TREATED_BY {efficacy: 0.7}]->(t);
MATCH (d:Disease {disease_id:'bacterial_wilt'}), (t:Treatment {treatment_id:'crop_rotation'})
CREATE (d)-[:TREATED_BY {efficacy: 0.75}]->(t);
MATCH (d:Disease {disease_id:'bacterial_wilt'}), (t:Treatment {treatment_id:'remove_infected'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);
MATCH (d:Disease {disease_id:'blossom_end_rot'}), (t:Treatment {treatment_id:'calcium_spray'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'blossom_end_rot'}), (t:Treatment {treatment_id:'consistent_watering'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);
MATCH (d:Disease {disease_id:'mosaic_virus'}), (t:Treatment {treatment_id:'remove_and_disinfect'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);
MATCH (d:Disease {disease_id:'spider_mite'}), (t:Treatment {treatment_id:'miticide_spray'})
CREATE (d)-[:TREATED_BY {efficacy: 0.85}]->(t);
MATCH (d:Disease {disease_id:'spider_mite'}), (t:Treatment {treatment_id:'neem_oil'})
CREATE (d)-[:TREATED_BY {efficacy: 0.65}]->(t);
MATCH (d:Disease {disease_id:'fruit_borer'}), (t:Treatment {treatment_id:'pheromone_traps'})
CREATE (d)-[:TREATED_BY {efficacy: 0.7}]->(t);
MATCH (d:Disease {disease_id:'fruit_borer'}), (t:Treatment {treatment_id:'bt_spray'})
CREATE (d)-[:TREATED_BY {efficacy: 0.8}]->(t);
MATCH (d:Disease {disease_id:'root_knot_nematode'}), (t:Treatment {treatment_id:'soil_solarization'})
CREATE (d)-[:TREATED_BY {efficacy: 0.75}]->(t);
MATCH (d:Disease {disease_id:'root_knot_nematode'}), (t:Treatment {treatment_id:'crop_rotation'})
CREATE (d)-[:TREATED_BY {efficacy: 0.7}]->(t);

// ---- Disease -> ConfirmationImage ----
MATCH (d:Disease {disease_id:'septoria_leaf_spot'}), (i:ConfirmationImage {image_id:'img_septoria_leaf_spot'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'bacterial_spot'}), (i:ConfirmationImage {image_id:'img_bacterial_spot'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'fusarium_wilt'}), (i:ConfirmationImage {image_id:'img_fusarium_wilt'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'bacterial_wilt'}), (i:ConfirmationImage {image_id:'img_bacterial_wilt'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'blossom_end_rot'}), (i:ConfirmationImage {image_id:'img_blossom_end_rot'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'mosaic_virus'}), (i:ConfirmationImage {image_id:'img_mosaic_virus'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'spider_mite'}), (i:ConfirmationImage {image_id:'img_spider_mite'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'fruit_borer'}), (i:ConfirmationImage {image_id:'img_fruit_borer'})
CREATE (d)-[:CONFIRMED_BY]->(i);
MATCH (d:Disease {disease_id:'root_knot_nematode'}), (i:ConfirmationImage {image_id:'img_root_knot_nematode'})
CREATE (d)-[:CONFIRMED_BY]->(i);

// ---- Disease -> SeasonCondition (FAVORED_BY) ----
// This layer isn't used by the current Python scoring yet — it's seeded now
// so climate-aware scoring can be added as a later enhancement (multiply
// score by season_boost when the farmer's local season is known).
MATCH (d:Disease {disease_id:'late_blight'}), (sc:SeasonCondition {condition_id:'humid_monsoon'})
CREATE (d)-[:FAVORED_BY {boost: 0.9}]->(sc);
MATCH (d:Disease {disease_id:'early_blight'}), (sc:SeasonCondition {condition_id:'humid_monsoon'})
CREATE (d)-[:FAVORED_BY {boost: 0.7}]->(sc);
MATCH (d:Disease {disease_id:'bacterial_wilt'}), (sc:SeasonCondition {condition_id:'humid_monsoon'})
CREATE (d)-[:FAVORED_BY {boost: 0.8}]->(sc);
MATCH (d:Disease {disease_id:'septoria_leaf_spot'}), (sc:SeasonCondition {condition_id:'cool_moist'})
CREATE (d)-[:FAVORED_BY {boost: 0.8}]->(sc);
MATCH (d:Disease {disease_id:'whitefly'}), (sc:SeasonCondition {condition_id:'hot_dry'})
CREATE (d)-[:FAVORED_BY {boost: 0.8}]->(sc);
MATCH (d:Disease {disease_id:'spider_mite'}), (sc:SeasonCondition {condition_id:'hot_dry'})
CREATE (d)-[:FAVORED_BY {boost: 0.9}]->(sc);
MATCH (d:Disease {disease_id:'powdery_mildew'}), (sc:SeasonCondition {condition_id:'cool_moist'})
CREATE (d)-[:FAVORED_BY {boost: 0.7}]->(sc);
