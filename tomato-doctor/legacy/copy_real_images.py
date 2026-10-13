import os
import shutil
import random

def main():
    source_dir = r"d:\AA sem 7\P2\tomato-new - ui\tomato-kg-project\tomato\train"
    dest_dir = r"d:\AA sem 7\P2\tomato-new - ui\tomato-kg-project\backend\static\images\real"
    cypher_file = r"d:\AA sem 7\P2\tomato-new - ui\tomato-kg-project\schema_v4_real_images.cypher"

    disease_map = {
        "bacterial_spot": "Tomato___Bacterial_spot",
        "early_blight": "Tomato___Early_blight",
        "late_blight": "Tomato___Late_blight",
        "leaf_mold": "Tomato___Leaf_Mold",
        "septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
        "spider_mite": "Tomato___Spider_mites Two-spotted_spider_mite",
        "target_spot": "Tomato___Target_Spot",
        "leaf_curl_virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
        "mosaic_virus": "Tomato___Tomato_mosaic_virus"
    }

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    cypher_statements = [
        "// =========================================================",
        "// TOMATO DISEASE KG - REAL IMAGES (v4)",
        "// Automatically generated to map real dataset images to diseases",
        "// =========================================================\n"
    ]

    for disease_id, folder_name in disease_map.items():
        folder_path = os.path.join(source_dir, folder_name)
        if not os.path.exists(folder_path):
            print(f"Warning: Folder not found for {disease_id} at {folder_path}")
            continue

        images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            print(f"Warning: No images found for {disease_id} in {folder_path}")
            continue

        # Select up to 3 random images
        selected_images = random.sample(images, min(3, len(images)))

        # Cypher: delete existing ConfirmationImages for this disease
        cypher_statements.append(f"MATCH (d:Disease {{disease_id: '{disease_id}'}})-[r:CONFIRMED_BY]->(i:ConfirmationImage)")
        cypher_statements.append("DELETE r, i;\n")

        for idx, img_name in enumerate(selected_images):
            # We rename the file to make it clean: {disease_id}_{idx}.jpg
            ext = os.path.splitext(img_name)[1]
            new_img_name = f"{disease_id}_{idx+1}{ext}"
            src_path = os.path.join(folder_path, img_name)
            dst_path = os.path.join(dest_dir, new_img_name)

            shutil.copy2(src_path, dst_path)

            img_id = f"img_{disease_id}_{idx+1}"
            url = f"/static/images/real/{new_img_name}"

            cypher_statements.append(f"CREATE (:ConfirmationImage {{image_id: '{img_id}', disease_id: '{disease_id}', url: '{url}', verified_count: 0}});")
            cypher_statements.append(f"MATCH (d:Disease {{disease_id: '{disease_id}'}}), (i:ConfirmationImage {{image_id: '{img_id}'}})")
            cypher_statements.append("CREATE (d)-[:CONFIRMED_BY]->(i);\n")

    with open(cypher_file, "w", encoding="utf-8") as f:
        f.write("\n".join(cypher_statements))

    print(f"Successfully processed {len(disease_map)} diseases and generated {cypher_file}")

if __name__ == "__main__":
    main()
