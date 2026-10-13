// =========================================================
// TOMATO DISEASE KG - REAL IMAGES (v4)
// Automatically generated to map real dataset images to diseases
// =========================================================

MATCH (d:Disease {disease_id: 'bacterial_spot'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_bacterial_spot_1', disease_id: 'bacterial_spot', url: '/static/images/real/bacterial_spot_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'bacterial_spot'}), (i:ConfirmationImage {image_id: 'img_bacterial_spot_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_bacterial_spot_2', disease_id: 'bacterial_spot', url: '/static/images/real/bacterial_spot_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'bacterial_spot'}), (i:ConfirmationImage {image_id: 'img_bacterial_spot_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_bacterial_spot_3', disease_id: 'bacterial_spot', url: '/static/images/real/bacterial_spot_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'bacterial_spot'}), (i:ConfirmationImage {image_id: 'img_bacterial_spot_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'early_blight'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_early_blight_1', disease_id: 'early_blight', url: '/static/images/real/early_blight_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'early_blight'}), (i:ConfirmationImage {image_id: 'img_early_blight_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_early_blight_2', disease_id: 'early_blight', url: '/static/images/real/early_blight_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'early_blight'}), (i:ConfirmationImage {image_id: 'img_early_blight_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_early_blight_3', disease_id: 'early_blight', url: '/static/images/real/early_blight_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'early_blight'}), (i:ConfirmationImage {image_id: 'img_early_blight_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'late_blight'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_late_blight_1', disease_id: 'late_blight', url: '/static/images/real/late_blight_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'late_blight'}), (i:ConfirmationImage {image_id: 'img_late_blight_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_late_blight_2', disease_id: 'late_blight', url: '/static/images/real/late_blight_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'late_blight'}), (i:ConfirmationImage {image_id: 'img_late_blight_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_late_blight_3', disease_id: 'late_blight', url: '/static/images/real/late_blight_3.jpg', verified_count: 0});
MATCH (d:Disease {disease_id: 'late_blight'}), (i:ConfirmationImage {image_id: 'img_late_blight_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'leaf_mold'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_leaf_mold_1', disease_id: 'leaf_mold', url: '/static/images/real/leaf_mold_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'leaf_mold'}), (i:ConfirmationImage {image_id: 'img_leaf_mold_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_leaf_mold_2', disease_id: 'leaf_mold', url: '/static/images/real/leaf_mold_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'leaf_mold'}), (i:ConfirmationImage {image_id: 'img_leaf_mold_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_leaf_mold_3', disease_id: 'leaf_mold', url: '/static/images/real/leaf_mold_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'leaf_mold'}), (i:ConfirmationImage {image_id: 'img_leaf_mold_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'septoria_leaf_spot'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_septoria_leaf_spot_1', disease_id: 'septoria_leaf_spot', url: '/static/images/real/septoria_leaf_spot_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'septoria_leaf_spot'}), (i:ConfirmationImage {image_id: 'img_septoria_leaf_spot_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_septoria_leaf_spot_2', disease_id: 'septoria_leaf_spot', url: '/static/images/real/septoria_leaf_spot_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'septoria_leaf_spot'}), (i:ConfirmationImage {image_id: 'img_septoria_leaf_spot_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_septoria_leaf_spot_3', disease_id: 'septoria_leaf_spot', url: '/static/images/real/septoria_leaf_spot_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'septoria_leaf_spot'}), (i:ConfirmationImage {image_id: 'img_septoria_leaf_spot_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'spider_mite'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_spider_mite_1', disease_id: 'spider_mite', url: '/static/images/real/spider_mite_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'spider_mite'}), (i:ConfirmationImage {image_id: 'img_spider_mite_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_spider_mite_2', disease_id: 'spider_mite', url: '/static/images/real/spider_mite_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'spider_mite'}), (i:ConfirmationImage {image_id: 'img_spider_mite_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_spider_mite_3', disease_id: 'spider_mite', url: '/static/images/real/spider_mite_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'spider_mite'}), (i:ConfirmationImage {image_id: 'img_spider_mite_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'target_spot'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_target_spot_1', disease_id: 'target_spot', url: '/static/images/real/target_spot_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'target_spot'}), (i:ConfirmationImage {image_id: 'img_target_spot_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_target_spot_2', disease_id: 'target_spot', url: '/static/images/real/target_spot_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'target_spot'}), (i:ConfirmationImage {image_id: 'img_target_spot_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_target_spot_3', disease_id: 'target_spot', url: '/static/images/real/target_spot_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'target_spot'}), (i:ConfirmationImage {image_id: 'img_target_spot_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'leaf_curl_virus'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_leaf_curl_virus_1', disease_id: 'leaf_curl_virus', url: '/static/images/real/leaf_curl_virus_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'leaf_curl_virus'}), (i:ConfirmationImage {image_id: 'img_leaf_curl_virus_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_leaf_curl_virus_2', disease_id: 'leaf_curl_virus', url: '/static/images/real/leaf_curl_virus_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'leaf_curl_virus'}), (i:ConfirmationImage {image_id: 'img_leaf_curl_virus_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_leaf_curl_virus_3', disease_id: 'leaf_curl_virus', url: '/static/images/real/leaf_curl_virus_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'leaf_curl_virus'}), (i:ConfirmationImage {image_id: 'img_leaf_curl_virus_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);

MATCH (d:Disease {disease_id: 'mosaic_virus'})-[r:CONFIRMED_BY]->(i:ConfirmationImage)
DELETE r, i;

CREATE (:ConfirmationImage {image_id: 'img_mosaic_virus_1', disease_id: 'mosaic_virus', url: '/static/images/real/mosaic_virus_1.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'mosaic_virus'}), (i:ConfirmationImage {image_id: 'img_mosaic_virus_1'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_mosaic_virus_2', disease_id: 'mosaic_virus', url: '/static/images/real/mosaic_virus_2.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'mosaic_virus'}), (i:ConfirmationImage {image_id: 'img_mosaic_virus_2'})
CREATE (d)-[:CONFIRMED_BY]->(i);

CREATE (:ConfirmationImage {image_id: 'img_mosaic_virus_3', disease_id: 'mosaic_virus', url: '/static/images/real/mosaic_virus_3.JPG', verified_count: 0});
MATCH (d:Disease {disease_id: 'mosaic_virus'}), (i:ConfirmationImage {image_id: 'img_mosaic_virus_3'})
CREATE (d)-[:CONFIRMED_BY]->(i);
