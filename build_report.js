const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, PageBreak
} = require("docx");

const GREEN = "2E7D32";
const LIGHTGREEN = "E3EFE2";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 150 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } });
}
function p(text, opts = {}) {
  return new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 120 } });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 60 } });
}
function code(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Consolas", size: 20 })],
    shading: { type: ShadingType.CLEAR, fill: "F4F7F2" },
    spacing: { before: 80, after: 80 },
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: GREEN } },
    indent: { left: 200 }
  });
}

function cell(text, opts = {}) {
  return new TableCell({
    width: opts.width || { size: 25, type: WidthType.PERCENTAGE },
    shading: opts.header ? { type: ShadingType.CLEAR, fill: LIGHTGREEN } : undefined,
    children: [new Paragraph({
      children: [new TextRun({ text, bold: !!opts.header, size: 20 })]
    })],
  });
}

function table(headerRow, rows, widths) {
  const w = widths || headerRow.map(() => Math.floor(100 / headerRow.length));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: w.map(x => x * 90),
    rows: [
      new TableRow({ children: headerRow.map((t, i) => cell(t, { header: true, width: { size: w[i], type: WidthType.PERCENTAGE } })) }),
      ...rows.map(r => new TableRow({ children: r.map((t, i) => cell(t, { width: { size: w[i], type: WidthType.PERCENTAGE } })) }))
    ]
  });
}

const doc = new Document({
  sections: [{
    properties: {},
    children: [
      new Paragraph({
        children: [new TextRun({ text: "Knowledge Graph–Based Diagnosis System for Tomato Crop Diseases", bold: true, size: 32, color: GREEN })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "30% Implementation Checkpoint Report", size: 24, italics: true })],
        spacing: { after: 300 }
      }),

      h1("1. Problem Statement"),
      p("Farmers, particularly in Tamil Nadu, often struggle to identify crop diseases early and accurately. Existing digital tools largely rely on image classification alone, which requires the farmer to already have a clear photo and does not handle the initial natural-language description of a problem — spoken or typed in Tamil, often in colloquial or regional terms. This project proposes a conversational diagnosis system for tomato crop diseases (extensible to other crops) that accepts a Tamil description of the problem, reasons over a Knowledge Graph (KG) to identify the most likely disease, and confirms the diagnosis visually before recommending treatment."),

      h1("2. Objectives for this Checkpoint (30%)"),
      bullet("Design and implement the core Knowledge Graph schema (Crop, Symptom, LayTerm, Disease, Treatment, ConfirmationImage nodes and weighted relationships)."),
      bullet("Seed the graph with real tomato disease data covering 5 diseases spanning fungal, viral, and pest categories."),
      bullet("Implement the weighted lay-term matching and disease scoring algorithm."),
      bullet("Implement the Discriminative Question Selection algorithm — the project's primary novelty — and validate it against an intentionally ambiguous test case."),
      bullet("Build a minimal working UI (Tamil text input → ranked diagnosis → treatment) to demonstrate the end-to-end flow."),
      bullet("Voice input, the online-learning feedback loop's long-term evaluation, and multi-crop support are scoped for later milestones (see Section 7)."),

      h1("3. System Architecture"),
      p("The system is composed of four layers:"),
      table(
        ["Layer", "Technology", "Status"],
        [
          ["Knowledge Graph store", "Neo4j (AuraDB Free — cloud, no local server needed)", "Implemented"],
          ["Backend / reasoning engine", "Python (Flask, neo4j driver, RapidFuzz for lay-term matching)", "Implemented"],
          ["Frontend", "HTML/JS minimal web UI (Tamil text input)", "Implemented (text only)"],
          ["Voice input (Tamil ASR)", "Planned — Google Speech-to-Text / IndicASR", "Not yet started"],
        ],
        [30, 45, 25]
      ),

      h1("4. Knowledge Graph Schema"),
      h2("4.1 Node Types"),
      table(
        ["Node Type", "Purpose", "Example"],
        [
          ["Crop", "Root entity", "Tomato / தக்காளி"],
          ["Symptom", "Technical/pathology-level symptom description", "White powdery coating on leaf"],
          ["LayTerm", "Farmer's colloquial Tamil description of a symptom", "வெள்ளை தூள் போல இலையில்"],
          ["Disease", "Fungal / viral / pest condition", "Powdery Mildew, Whitefly Infestation"],
          ["Treatment", "Recommended remedy with dosage", "Sulfur dust spray, 2g/litre weekly"],
          ["ConfirmationImage", "Reference photo shown for visual confirmation", "img_powdery_mildew.jpg"],
        ],
        [20, 40, 40]
      ),

      h2("4.2 Relationship Types (weighted, not boolean)"),
      p("The key design decision in this schema is that relationships carry numeric weights rather than being simple boolean links. This is what allows probabilistic ranking of candidate diseases instead of a single deterministic lookup, and is the foundation the novelty algorithms (Section 5) are built on."),
      table(
        ["Relationship", "Direction", "Weight meaning"],
        [
          ["LAYTERM_MAPS_TO", "LayTerm → Symptom", "Confidence that this colloquial phrase refers to this technical symptom"],
          ["HAS_SYMPTOM", "Disease → Symptom", "P(symptom present | this disease) — seeded from agricultural literature"],
          ["TREATED_BY", "Disease → Treatment", "Efficacy of this treatment for this disease"],
          ["CONFIRMED_BY", "Disease → ConfirmationImage", "Links to reference photo; tracks verified_count from farmer confirmations"],
        ],
        [25, 25, 50]
      ),
      p("Seed data currently covers 5 diseases (Early Blight, Late Blight, Powdery Mildew, Whitefly Infestation, Tomato Leaf Curl Virus), 8 technical symptoms, 11 Tamil lay-terms, and 6 treatments — sourced from TNAU (Tamil Nadu Agricultural University) extension material and standard plant pathology references, then cross-checked for the weight estimates.", { italics: true, size: 20 }),

      h1("5. Core Algorithms (Novelty)"),
      h2("5.1 Weighted Candidate Scoring"),
      p("Given a farmer's free-text input, the system fuzzy-matches it against known LayTerm nodes, then propagates confidence through the graph:"),
      code("score(disease) = Σ [ layterm_weight × match_score × has_symptom_weight ]"),
      p("This produces a ranked list of candidate diseases rather than a single answer, which is necessary because Tamil symptom descriptions are frequently ambiguous (e.g. \"white dust\" could describe either Powdery Mildew or a Whitefly infestation)."),

      h2("5.2 Discriminative Question Selection — primary novelty"),
      p("When the top two (or more) candidate diseases have scores within 20% of each other, the system does not guess. Instead, it identifies the single best follow-up question to ask the farmer — the symptom that most sharply separates the remaining candidates. This mirrors information-gain-based splitting in a decision tree, but is computed by walking the weighted KG rather than over a flat feature table:"),
      bullet("For each unasked symptom shared context among the top candidates, compute the variance of its HAS_SYMPTOM weight across those candidates."),
      bullet("A symptom completely absent for at least one candidate (not just low-weight, but no edge at all) is treated as maximally discriminating, since absence is itself informative."),
      bullet("The symptom with the highest resulting split-score is asked next."),
      p("This is, to our knowledge, not commonly implemented in existing agricultural chatbot / KG systems, which typically either guess the top match directly or ask a fixed, non-adaptive sequence of questions."),

      h2("5.3 Confirmation-Driven Feedback Loop"),
      p("When the farmer visually confirms or rejects the top diagnosis against the sample image, the system nudges the HAS_SYMPTOM and LAYTERM_MAPS_TO edge weights along the path that produced that diagnosis (small learning rate, bounded between 0.05 and 1.0). Over many interactions this allows the graph to self-correct for how the actual farmer population describes symptoms in Tamil, rather than remaining fixed at its initial expert-seeded values. This closes the loop between the KG and real usage — the graph is designed to improve over time rather than being static."),

      h1("6. Worked Example — Validating the Disambiguation Algorithm"),
      p("To verify Section 5.2 concretely, the algorithm was run against the exact ambiguous case motivating this project: a farmer describing \"white dust-like\" material on tomato leaves, which genuinely could indicate either Powdery Mildew or Whitefly Infestation."),
      code('Input (Tamil): "இலையில் வெள்ளை தூள் போல இருக்கு"'),
      code('  1. Matched lay-terms: lt_white_dust, lt_white_powder -> symptom "white_powdery_coating"\n                          lt_white_flying_insects, lt_white_dot_insects -> symptom "tiny_flying_white_insects"'),
      code('  2. Ranked candidates: Powdery Mildew (score=0.7125)   Whitefly Infestation (score=0.6670)'),
      code('  3. Scores within 20% of each other -> AMBIGUOUS, do not guess'),
      code('  4. Discriminative question selected: "tiny_flying_white_insects"\n     (present strongly for Whitefly [0.95], entirely absent for Powdery Mildew)'),
      p("The algorithm correctly avoided a premature guess and selected the symptom that actually distinguishes the two diseases — asking the farmer \"do you also see tiny white insects flying up?\" resolves the ambiguity in a single follow-up, rather than guessing wrong or asking an arbitrary question. Full output is reproducible via test_logic_standalone.py in the submitted code.", {}),

      h1("7. Implementation Status"),
      table(
        ["Component", "Status"],
        [
          ["KG schema design (nodes, weighted relationships)", "Done"],
          ["Seed data (5 diseases, 8 symptoms, 11 lay-terms, 6 treatments)", "Done"],
          ["Weighted scoring algorithm", "Done, validated"],
          ["Discriminative question selection algorithm", "Done, validated"],
          ["Confirmation feedback loop (weight update)", "Implemented, long-run evaluation pending"],
          ["Minimal web UI (Tamil text input)", "Done"],
          ["Tamil voice input (ASR)", "Not started"],
          ["Proper Tamil NLU (currently fuzzy string matching only)", "Not started — planned upgrade"],
          ["Real confirmation photo dataset (currently placeholders)", "Not started"],
          ["Multi-crop extension", "Not started (future work)"],
          ["Regional outbreak-clustering analysis", "Not started (future work)"],
        ],
        [65, 35]
      ),
      p("This represents the core reasoning engine of the system — the part with genuine algorithmic novelty — working end-to-end on a realistic seeded dataset. The remaining 70% is largely input-layer expansion (voice, better NLU) and breadth (more crops, real image dataset, live feedback evaluation) rather than architectural rework.", { italics: true }),

      h1("8. Tech Stack Summary"),
      table(
        ["Layer", "Choice", "Why"],
        [
          ["Graph database", "Neo4j AuraDB (Free tier)", "Cypher makes weighted traversal easy to write & explain; no server maintenance"],
          ["Backend", "Python + Flask", "Fast to iterate; clean neo4j driver integration"],
          ["Text matching (interim)", "RapidFuzz", "Lightweight placeholder until a proper Tamil NLU model is integrated"],
          ["Frontend", "HTML/CSS/JS", "Minimal, framework-free for this checkpoint's demo needs"],
        ],
        [25, 35, 40]
      ),

      h1("9. Next Steps (Remaining 70%)"),
      bullet("Integrate a proper Tamil NLU/ASR pipeline (e.g. Whisper for speech-to-text, fine-tuned embedding model for symptom extraction) to replace the current fuzzy-matching placeholder."),
      bullet("Expand the lay-term layer via a structured farmer survey — this is the primary data-collection task and forms the low-resource-language NLP contribution of the paper."),
      bullet("Source or capture a labeled confirmation-image dataset for each disease (e.g. PlantVillage for bootstrap, supplemented with field photos)."),
      bullet("Run the confirmation feedback loop over simulated/pilot usage and evaluate how lay-term weights converge — this produces the online-learning evaluation results for the paper."),
      bullet("Extend the schema to a second crop to validate the KG design generalizes."),
      bullet("(Stretch) Aggregate confirmed diagnoses with farmer location to explore regional disease-outbreak clustering as an early-warning feature."),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  require("fs").writeFileSync("/home/claude/project/Tomato_KG_30pct_Report.docx", buf);
  console.log("Report written.");
});
