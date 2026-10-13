# Setup Guide — Tomato Disease KG Demo

## 1. Create a free Neo4j AuraDB instance (~5 minutes)

1. Go to https://neo4j.com/cloud/aura-free/ and sign up (free, no credit card needed).
2. Click **New Instance** → choose **AuraDB Free**.
3. Give it a name (e.g. `tomato-kg`) and click **Create**.
4. **IMPORTANT**: A popup will show your credentials ONCE — download the `.txt` file it offers.
   It contains:
   - `NEO4J_URI` (looks like `neo4j+s://xxxxxxxx.databases.neo4j.io`)
   - `NEO4J_USERNAME` (usually `neo4j`)
   - `NEO4J_PASSWORD` (auto-generated)
5. Wait ~1-2 minutes for the instance status to turn green ("Running").

## 2. Load the schema + seed data

1. In the AuraDB console, click **Open** on your instance → this opens Neo4j Browser/Query in the cloud (Aura Console UI).
2. Open `schema.cypher` from this project in a text editor, copy its full contents.
3. Paste into the Neo4j query box and run it (it will execute all `CREATE` statements in order).
4. Verify: run `MATCH (n) RETURN count(n);` — you should see ~30+ nodes.
5. Sanity check the ambiguous case: run
   ```cypher
   MATCH (d:Disease)-[r:HAS_SYMPTOM]->(s:Symptom {symptom_id:'white_powdery_coating'})
   RETURN d.name_en, r.weight;
   ```
   You should see both `Powdery Mildew` (0.95) and `Whitefly Infestation` (0.3) — this overlap is intentional, it's what your discriminative-question algorithm resolves.

## 3. Run the backend locally

```bash
cd backend
pip install -r requirements.txt

# set your AuraDB credentials (from step 1)
export NEO4J_URI="neo4j+s://xxxxxxxx.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password-here"

python app.py
```

Open `http://127.0.0.1:5000` in your browser. Click the "Example" button to autofill
the ambiguous "white dust" case and see the disambiguation flow.

## 4. (Optional) Verify the core algorithm without Neo4j

If you just want to demonstrate the scoring/disambiguation logic works, without
setting up AuraDB at all:

```bash
cd backend
python test_logic_standalone.py
```

This runs the exact same algorithm against an in-memory copy of the seed data
and prints the worked "white dust" disambiguation example — useful for your
report and for a fast demo if internet/DB access is unreliable during your viva.

## 5. Add real confirmation images (currently placeholders)

Put tomato disease photos (e.g. from the PlantVillage dataset, or your own
field photos) into `backend/static/images/` named:
`early_blight.jpg`, `late_blight.jpg`, `powdery_mildew.jpg`, `whitefly.jpg`, `leaf_curl_virus.jpg`

## Troubleshooting

- **`ServiceUnavailable` error**: AuraDB free instances pause after inactivity — reopen
  the console to wake it up, wait ~30s, retry.
- **Auth error**: password is only shown once at creation. If lost, reset it from
  the Aura console (instance settings → reset password), then update your env var.
