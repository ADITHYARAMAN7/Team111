"""
lexicon.py - concept lexicon for farmer language (Tamil, English, Tanglish).

Every surface form maps to one or more language-independent CONCEPTS. Lay-term
phrases in the knowledge graph and the farmer's input both go through the same
mapping, so "இலையில் வெள்ளை பொடி", "white powder on leaves" and
"ilai la vellai podi" all become {LEAF, WHITE, POWDER} and can be compared.

Matching rules (see nlu.py):
  * Tamil forms are matched as STEMS: a token matches the longest stem it starts
    with, as long as the leftover suffix is short (Tamil is agglutinative:
    இலை / இலையில் / இலைகளில் / இலையின் are all LEAF).
  * Latin forms of length <= 3 must match exactly ("ver", "kai", "ee").
  * Multi-word forms ("one side", "ஒரு பக்கம்", "no fruit set") are matched
    first, greedily, longest first - this also lets fixed negative idioms like
    "காய் பிடிக்கலை" (fruit not setting) be read as a symptom instead of a
    negation.
"""

# concept -> surface forms
CONCEPTS = {
    # ---- plant parts -------------------------------------------------------
    "LEAF": ["இலை", "எல", "ilai", "ilaigal", "ilaiyil", "ilaila", "elai", "ela", "leaf", "leaves", "leafs", "foliage"],
    "STEM": ["தண்டு", "தண்ட", "தண்டி", "thandu", "thanda", "thandula", "thandil", "stem", "stems", "stalk", "trunk"],
    "BRANCH": ["கிளை", "kilai", "kelai", "branch", "branches", "twig"],
    "ROOT": ["வேர்", "வேரி", "வேர்ல", "ver", "verla", "veru", "veril", "root", "roots"],
    "FRUIT": ["பழம்", "பழத்", "பழங்", "பழக்", "காய்", "காயி", "காய்க", "pazham", "pazhathula", "pazhatha", "palam", "kaai", "kaay", "kai", "kaaila",
              "fruit", "fruits", "tomato", "tomatoes", "தக்காளி", "thakkali", "takkali"],
    "FLOWER": ["பூ", "பூக்க", "பூவு", "poo", "pookkal", "flower", "flowers", "blossom", "blossoms", "bloom"],
    "PLANT": ["செடி", "செடிக", "பயிர்", "chedi", "sedi", "chediyil", "payir", "plant", "plants", "crop", "crops"],
    "FIELD": ["வயல்", "தோட்டம்", "தோட்ட", "vayal", "thottam", "field", "farm", "garden"],
    "VEIN": ["நரம்பு", "narambu", "vein", "veins"],
    "STALK_END": ["காம்பு", "kaambu", "kambu", "stalk end", "stem end"],

    # ---- position ----------------------------------------------------------
    "UNDER": ["அடியில்", "அடியி", "அடிப்பக்க", "அடிப்பகுதி", "அடிப்புற", "அடி", "கீழ்ப்பக்க", "பின்பக்க", "adiyil", "adila", "adi",
              "under", "underside", "beneath", "bottom", "lower side", "back side", "below"],
    "UPPER": ["மேல்", "மேல", "மேற்ப", "மேல்புற", "மேல்நோக்கி", "mel", "mela", "upper", "top", "surface", "above", "upward", "upwards"],
    "INSIDE": ["உள்ளே", "உள்ள", "உள்", "ulle", "ulla", "inside", "inner", "within"],
    "LOWER_OLD": ["கீழ்", "கீழ", "பழைய", "முத்தின", "keezh", "keel", "pazhaya", "lower", "old", "older", "bottom leaves"],
    "YOUNG": ["இளம்", "இள", "புது", "புதிய", "கொழுந்து", "நுனி", "kozhundhu", "kolundhu", "nuni", "pudhu", "young", "new", "tender", "growing tip", "tip"],
    "SIDE": ["பக்கம்", "பக்க", "pakkam", "side", "half", "one side", "ஒரு பக்கம்", "oru pakkam"],
    "WHOLE": ["முழுசா", "முழுவதும்", "முழு", "முழுக்க", "எல்லா", "muzhusa", "muzhukka", "ella", "whole", "entire", "full", "all over", "everywhere"],
    "BETWEEN": ["நடுவில்", "நடுவி", "இடையில்", "இடைய", "நடுவ", "naduvil", "between", "among"],
    "CENTER": ["நடுப்பகுதி", "மையம்", "center", "centre", "middle"],
    "EDGE": ["ஓரம்", "ஓரத்", "ஓரங்", "ஓர", "விளிம்பு", "oram", "edge", "edges", "margin", "margins", "border", "rim"],

    # ---- colours -----------------------------------------------------------
    "WHITE": ["வெள்ளை", "வெள்ள", "வெண்", "vellai", "vella", "vellaya", "white", "whitish"],
    "BLACK": ["கருப்பு", "கறுப்பு", "கருப்ப", "கருத்து", "கருமை", "karuppu", "karupu", "karuppa", "black", "dark", "darker"],
    "BROWN": ["பழுப்பு", "பழுப்ப", "pazhuppu", "pazhupu", "brown", "brownish", "tan", "rusty"],
    "YELLOW": ["மஞ்சள்", "மஞ்ச", "manjal", "manja", "manjala", "yellow", "yellowing", "yellowish", "chlorosis"],
    "PALE": ["வெளிர்", "வெளுத்", "velir", "pale", "light", "faded"],
    "GREEN": ["பச்சை", "பச்ச", "pachai", "pacha", "green"],
    "DARK_GREEN": ["கரும்பச்சை", "dark green"],
    "GREY": ["சாம்பல்", "saambal", "sambal", "grey", "gray", "ash", "ashy"],
    "OLIVE": ["ஆலிவ்", "olive"],
    "BRONZE": ["வெண்கல", "வெள்ளி நிற", "bronze", "bronzing", "silver", "silvery", "copper colour"],

    # ---- shapes / textures -------------------------------------------------
    "SPOT": ["புள்ளி", "பொட்டு", "pulli", "pulligal", "pottu", "spot", "spots", "spotted", "dot", "dots", "speck", "specks", "lesion", "lesions", "fleck"],
    "PATCH": ["திட்டு", "thittu", "patch", "patches", "blotch", "blotches", "blotchy", "area", "areas"],
    "RING": ["வளையம்", "வளைய", "வட்ட", "இலக்கு", "valayam", "valaiyam", "vattam", "vattama", "ring", "rings", "ringed", "circle", "circles",
             "concentric", "target", "bullseye", "halo", "halos"],
    "SMALL": ["சிறிய", "சிறு", "சின்ன", "குண்டூசி", "chinna", "siriya", "small", "tiny", "little", "minute", "pinpoint", "pin head", "pin-head"],
    "MANY": ["நிறைய", "பல", "niraya", "many", "lots", "lot", "numerous", "plenty"],
    "LARGE": ["பெரிய", "periya", "big", "large", "huge"],
    "POWDER": ["தூள்", "தூவின", "பூத்த", "பொடி", "பவுடர்", "மாவு", "thool", "thul", "podi", "maavu", "powder", "powdery", "dust", "dusty", "dusted", "flour"],
    "FUNGUS": ["பூஞ்சை", "பூஞ்ச", "பூசண", "பூசணம்", "பூஞ்சாண", "poonjai", "poonjai", "poosanam", "fungus", "fungal", "fungi", "mold", "mould", "mildew", "moldy", "mouldy"],
    "FUZZY": ["பஞ்சு", "வெல்வெட்", "panju", "velvet", "velvety", "fuzzy", "furry", "cottony", "woolly", "fluffy"],
    "STICKY": ["ஒட்டும்", "ஒட்டு", "பிசுபிசு", "பிசுக்", "ottum", "ottudhu", "pisupisu", "sticky", "gummy", "honeydew"],
    "SHINY": ["பளபள", "palapala", "shiny", "glossy", "glistening"],
    "SOOTY": ["கரி", "soot", "sooty", "black mould"],
    "CURL": ["சுருண்டு", "சுருள்", "சுருட்", "சுருளு", "surundu", "surul", "suruttu", "curl", "curls", "curling", "curled", "curly", "cupped", "cupping", "roll", "rolled", "rolling"],
    "CUP": ["கிண்ணம்", "kinnam", "bowl", "cup", "cups"],
    "SHRIVEL": ["சுருங்கி", "சுருங்கு", "சுருக்க", "surungi", "shrivel", "shriveled", "shrivelled", "wrinkled", "crinkled", "puckered"],
    "DEFORM": ["முறுக்கி", "முறுக்", "கோணல", "கோணல்", "உருமாறி", "ஒடுங்கி", "நூல்", "murukki", "konala", "twist", "twisted", "deformed", "distorted", "misshapen", "narrow", "fern", "shoestring", "malformed"],
    "BENT": ["வளைந்த", "வளைந்து", "வளைஞ்ச", "valaindha", "bent", "winding", "wavy", "serpentine", "zigzag", "squiggly"],
    "LINE": ["கோடு", "கோடுக", "வரி", "கிறுக்க", "kodu", "line", "lines", "streak", "streaks", "stripe", "stripes", "trail", "trails", "scribble"],
    "TUNNEL": ["சுரங்க", "surangam", "tunnel", "tunnels", "mine", "mines", "mining", "miner", "leafminer"],
    "SNAKE": ["பாம்பு", "paambu", "snake"],
    "MOSAIC": ["கலவை", "கலந்த", "தேமல்", "திட்டு திட்டா", "kalavai", "themal", "mosaic", "mottle", "mottled", "mottling", "marbled", "patchy"],
    "WEB": ["வலை", "valai", "web", "webs", "webbing", "cobweb"],
    "MITE": ["சிலந்தி", "பேன்", "silandhi", "mite", "mites", "spider", "spiders", "red spider"],
    "SUNKEN": ["குழி", "குழிந்த", "உள்வாங்கி", "kuzhi", "sunken", "depressed", "pit", "pitted", "hollow"],
    "LEATHER": ["தோல் போல", "leathery", "leather", "hard"],
    "SCAB": ["சொரசொர", "சொறி", "மேடான", "மேடா", "sorasorappa", "scab", "scabby", "raised", "rough", "bumpy", "corky", "warty"],
    "GREASY": ["எண்ணெய்", "ennai", "greasy", "oily"],
    "WET": ["நனைந்து", "நனைஞ்ச", "நனைந்த", "நனைய", "ஈரம்", "நீர் தேங்கிய", "nanainja", "nanaindha", "wet", "watery", "water soaked", "water-soaked", "soggy", "soaked"],
    "WATER": ["தண்ணீர்", "தண்ணி", "நீர்", "thanni", "thanneer", "neer", "water", "glass"],
    "HOLE": ["துளை", "ஓட்டை", "துவார", "thulai", "ottai", "hole", "holes", "bored", "bore", "boring", "burrow"],
    "WORM": ["புழு", "கம்பளி", "pulu", "puzhu", "worm", "worms", "caterpillar", "caterpillars", "larva", "larvae", "grub", "grubs", "maggot", "borer"],
    "INSECT": ["பூச்சி", "poochi", "puchi", "poochigal", "insect", "insects", "bug", "bugs", "pest", "pests"],
    "FLY": ["பறக்கும்", "பறக்கு", "பறக்", "பறந்து", "பறக்கி", "parakkum", "parakkudhu", "parakuthu", "parandhu", "fly", "flies", "flying", "flew"],
    "WHITEFLY": ["வெள்ளை ஈ", "வெள்ளைஈ", "vellai ee", "whitefly", "whiteflies", "white fly", "white flies"],
    "SHAKE": ["ஆட்டினா", "ஆட்டி", "அசைத்தா", "அசைச்சா", "தொட்டா", "aattina", "shake", "shaken", "shaking", "disturb", "disturbed", "touch"],
    "KNOT": ["முடிச்சு", "முடிச்ச", "கட்டி", "கணு", "வீக்க", "mudichu", "katti", "knot", "knots", "gall", "galls", "swelling", "swellings", "lump", "lumps", "nodules"],
    "CUT": ["வெட்டி", "வெட்டின", "வெட்டு", "vetti", "vettina", "cut", "split", "sliced", "slit"],
    "OOZE": ["பால்", "கசிவு", "கசி", "சளி", "paal", "ooze", "oozing", "milky", "slime", "slimy", "exudate", "streaming"],

    "AROUND": ["சுற்றி", "சுத்தி", "suthi", "sutri", "around", "surrounding", "surrounded"],
    "START": ["தொடங்கி", "தொடங்கு", "ஆரம்ப", "முதலில்", "முதல்ல", "mudhalla", "mudhalil", "start", "started", "starts", "starting", "began", "begin", "first", "initially"],
    "ROUND": ["round", "circular", "oval"],
    "COATING": ["படலம்", "படல", "coating", "coat", "coated", "layer", "film", "covering", "covered"],
    "SPECKLE": ["stipple", "stippling", "stippled", "speckle", "speckles", "speckled", "speckling", "freckles", "pinpricks"],

    # ---- dynamics ----------------------------------------------------------
    "WILT": ["வாடு", "வாடி", "வாடல்", "வதங்கு", "சோர்ந்து", "தொங்கு", "சாயுது", "vaadu", "vaadudhu", "vadudhu", "vaadi", "vadi", "wilt", "wilts", "wilting", "wilted",
             "droop", "drooping", "droops", "sag", "sagging", "limp", "collapse", "collapsed", "collapsing"],
    "SUDDEN": ["திடீர்", "திடீரென", "thideer", "thideernu", "sudden", "suddenly", "overnight", "quickly"],
    "RECOVER": ["சரியாகு", "சரியாகி", "தெளிஞ்சு", "மீண்டு", "sariyaagudhu", "recover", "recovers", "recovered", "revive", "revives", "normal again"],
    "NIGHT": ["இரவு", "இரவி", "ராத்திரி", "சாயங்கால", "மாலை", "raathiri", "night", "evening", "nights"],
    "AFTERNOON": ["மதிய", "மதியம்", "வெயில்", "madhiyam", "veyil", "afternoon", "noon", "midday", "heat", "hot sun"],
    "DRY": ["காய்ந்து", "காஞ்சு", "காயுது", "காய்கி", "உலர்", "kaanju", "kaayudhu", "dry", "drying", "dried", "dries", "wither", "withered", "withering"],
    "SCORCH": ["கருகு", "கருகி", "கருகல்", "karugudhu", "karugi", "scorch", "scorched", "burnt", "burned", "burn", "blight", "blighted"],
    "FALL": ["உதிர்", "உதிரு", "கொட்டு", "கொட்டி", "விழுது", "udhirudhu", "udhir", "fall", "falls", "falling", "fell", "drop", "drops", "dropping", "shed", "shedding", "defoliation", "dropped"],
    "ROT": ["அழுகு", "அழுகல்", "அழுகி", "கெட்டு", "azhugudhu", "azhugal", "rot", "rots", "rotten", "rotting", "decay", "decaying", "mushy"],
    "SPREAD": ["பரவு", "பரவி", "paravudhu", "spread", "spreads", "spreading", "spreaded"],
    "FAST": ["வேகமா", "வேகமாக", "vegama", "fast", "rapid", "rapidly", "quick"],
    "DAYS": ["நாள்", "நாளி", "naal", "day", "days", "week"],
    "STUNTED": ["குட்டை", "குள்ள", "புதர்", "வளரலை", "வளரல", "வளர்ச்சி இல்லை", "வளர்ச்சி குறைவு", "kuttai", "kuttaiya", "valaradhu", "valarala", "stunted", "dwarf", "dwarfed",
                "short", "bushy", "not growing", "no growth", "poor growth", "growth stopped"],
    "GROW": ["வளர", "valar", "grow", "growing", "growth"],
    "EAT": ["தின்னு", "தின்கி", "சாப்பிடு", "thinnudhu", "eat", "eating", "eaten", "chewed", "feeding"],
    "FRUIT_SET_FAIL": ["காய் பிடிக்கலை", "காய் பிடிக்கல", "பிஞ்சு பிடிக்கலை", "kaai pidikkala", "no fruit set", "poor fruit set", "fruit set poor", "not setting fruit",
                       "fruits not setting", "no fruits", "fruit set"],
    "RIPEN": ["பழுக்க", "பழுக்கு", "pazhukka", "ripen", "ripens", "ripening", "ripe"],
    "UNEVEN": ["சீரா", "சீராக", "ஒழுங்கா", "seeraa", "uneven", "unevenly", "irregular", "blotchy colour", "blotchy color"],
    "BAD_RIPEN": ["பழுக்கலை", "பழுக்கல", "pazhukkala"],
    "LOW": ["குறைவு", "குறைவா", "குறைஞ்சு", "குறைஞ்சிடு", "கம்மி", "kammiya", "kuraivu", "less", "low", "few", "fewer", "reduced", "dropped"],
    "YIELD": ["மகசூல்", "விளைச்சல்", "magasool", "yield", "harvest", "production"],
    "COLOUR": ["நிறம்", "நிற", "நிறமா", "niram", "colour", "color", "coloured", "colored"],
}

# Generic filler words that carry no symptom meaning (checked before concept lookup).
STOPWORDS = set("""
போல போன்ற மாதிரி இருக்கு இருக்குது இருக்கிறது உள்ளது உள்ளன இருக்கும் இருக்கின்றன ஆகுது ஆகிறது ஆகி போகுது போகிறது போச்சு வருது வருகிறது
ஒரு என் எங்க என்னுடைய எனது நம்ம தான் தான மட்டும் கூட ரொம்ப கொஞ்சம் அதிகம் மேலும் அது இது இந்த அந்த என்ன ஏன் எப்படி
ஆக ஆகும் வந்தது வந்துச்சு தெரியுது தெரிகிறது உண்டு போய் விட்டது விடுது இருந்து வச்சா வெச்சா பிறகு அப்புறம்
பாதிச்சது பாதித்தது பாதிப்பு பட்ட தடவின ரெண்டு மூணு அளவு தன்மையுடன் தன்மை பிடிச்ச மெல்லிய இருக்கும்போதே சரியா காரணமே நிக்குது பிடுங்கினா பிடுங்கி விழுந்திருக்கு
the a an is are was were be been on of in at to my our your and with there have has had some like looks look looking getting get it its this that
very too also just what why how which do does did can could please help me i we they them their plant's tomato's
pola pole maadhiri madhiri mathiri irukku iruku irukudhu aagudhu agudhu pogudhu poguthu varudhu oru en enga ennoda romba konjam la le ula
mattum thaan dhaan than vandhuchu pochu vecha pakkathula
up when off from near while one heavy fine still only their affected pattern end appear
turning turn turns turned becoming become becomes changing change changes appear appears appearing seen see seeing visible my
மாறுது மாறி மாறுகிறது தெரியும் காணப்படுகிறது
""".split())

# Words that negate (Tamil negators come AFTER what they negate, English BEFORE).
NEGATORS_POST = {"இல்லை", "இல்ல", "இல்லே", "இல்லியே", "கிடையாது", "இல்லாம", "இல்லாமல்", "இல்லாத", "illa", "illai", "ille", "illaye", "kidaiyadhu", "kidayathu", "illama"}
NEGATORS_PRE = {"no", "not", "never", "without", "dont", "don't", "didnt", "didn't", "doesnt", "doesn't", "isnt", "isn't", "arent", "aren't", "nothing", "none", "neither", "nor", "cannot", "cant", "can't"}
# Tamil negative verb endings (e.g. பறக்கலை = "doesn't fly", தெரியலை = "can't see")
NEG_SUFFIXES = ("க்கலை", "க்கல", "யலை", "யல", "ரலை", "டலை", "றலை", "ணலை", "சலை")

# Clause boundaries (contrast words reset negation scope)
CLAUSE_BREAKS = {"ஆனா", "ஆனால்", "ஆனாலும்", "but", "however", "although", "though", "aana", "aanaa", "anal"}

# Partial similarity between related concepts (symmetric)
RELATED = {
    ("SPOT", "PATCH"): 0.6, ("BLACK", "BROWN"): 0.6, ("YELLOW", "PALE"): 0.4, ("CURL", "SHRIVEL"): 0.5, ("CURL", "DEFORM"): 0.5,
    ("SHRIVEL", "DEFORM"): 0.6, ("DRY", "SCORCH"): 0.7, ("DRY", "FALL"): 0.3, ("WORM", "INSECT"): 0.4, ("WHITEFLY", "INSECT"): 0.7,
    ("WHITEFLY", "FLY"): 0.7, ("FUNGUS", "FUZZY"): 0.5, ("WET", "WATER"): 0.6, ("SPREAD", "FAST"): 0.4, ("TUNNEL", "LINE"): 0.6,
    ("BENT", "LINE"): 0.3, ("ROT", "SUNKEN"): 0.4, ("SCORCH", "BLACK"): 0.4, ("MOSAIC", "PATCH"): 0.4, ("CUP", "CURL"): 0.7,
    ("STUNTED", "GROW"): 0.5, ("LOW", "SMALL"): 0.5, ("GREY", "WHITE"): 0.3, ("OLIVE", "GREEN"): 0.6, ("DARK_GREEN", "GREEN"): 0.6,
    ("SOOTY", "BLACK"): 0.6, ("MITE", "INSECT"): 0.5, ("FRUIT_SET_FAIL", "FLOWER"): 0.4, ("BAD_RIPEN", "RIPEN"): 0.6, ("BAD_RIPEN", "UNEVEN"): 0.8,
    ("AROUND", "RING"): 0.4, ("ROUND", "RING"): 0.6, ("COATING", "POWDER"): 0.6, ("COATING", "SOOTY"): 0.4,
    ("SPECKLE", "SPOT"): 0.4, ("SPECKLE", "SMALL"): 0.3, ("SHINY", "STICKY"): 0.5, ("SHINY", "BRONZE"): 0.5, ("START", "LOWER_OLD"): 0.0,
}
