"""
scripts/seed_rich_dataset.py
----------------------------
Populates medicine_system.db with comprehensive, high-quality data
for real Indian medicines across all major therapeutic classes,
including anti-epileptics (Levipil / Levetiracetam), cardiology,
gastroenterology, anti-diabetics, antibiotics, analgesics, and vitamins.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medicine_system.db")

# Comprehensive List of Manufacturers
MANUFACTURERS = [
    ("Sun Pharmaceutical Industries Ltd.", "Sun Pharma", "Goregaon East, Mumbai", "Mumbai", "Maharashtra", "https://sunpharma.com"),
    ("Torrent Pharmaceuticals Ltd.", "Torrent", "Off S.G. Highway, Ahmedabad", "Ahmedabad", "Gujarat", "https://torrentpharma.com"),
    ("Cipla Ltd.", "Cipla", "Mumbai Central, Mumbai", "Mumbai", "Maharashtra", "https://cipla.com"),
    ("Dr. Reddy's Laboratories Ltd.", "Dr. Reddy's", "Banjara Hills, Hyderabad", "Hyderabad", "Telangana", "https://drreddys.com"),
    ("Glenmark Pharmaceuticals Ltd.", "Glenmark", "Andheri East, Mumbai", "Mumbai", "Maharashtra", "https://glenmarkpharma.com"),
    ("Lupin Ltd.", "Lupin", "Santacruz East, Mumbai", "Mumbai", "Maharashtra", "https://lupin.com"),
    ("Alkem Laboratories Ltd.", "Alkem", "Lower Parel, Mumbai", "Mumbai", "Maharashtra", "https://alkemlabs.com"),
    ("Mankind Pharma Ltd.", "Mankind", "Okhla Phase III, New Delhi", "New Delhi", "Delhi", "https://mankindpharma.com"),
    ("Zydus Lifesciences Ltd.", "Zydus", "Satellite Cross Roads, Ahmedabad", "Ahmedabad", "Gujarat", "https://zyduslife.com"),
    ("Intas Pharmaceuticals Ltd.", "Intas", "Thaltej, Ahmedabad", "Ahmedabad", "Gujarat", "https://intaspharma.com"),
    ("Abbott India Ltd.", "Abbott", "BKC, Bandra East, Mumbai", "Mumbai", "Maharashtra", "https://abbott.co.in"),
    ("GlaxoSmithKline Pharmaceuticals Ltd.", "GSK", "Dr. Annie Besant Rd, Mumbai", "Mumbai", "Maharashtra", "https://gsk.com"),
    ("Sanofi India Ltd.", "Sanofi", "Powai, Mumbai", "Mumbai", "Maharashtra", "https://sanofi.in"),
    ("Micro Labs Ltd.", "Micro Labs", "Race Course Rd, Bengaluru", "Bengaluru", "Karnataka", "https://microlabsltd.com"),
    ("IPCA Laboratories Ltd.", "IPCA", "Kandivli West, Mumbai", "Mumbai", "Maharashtra", "https://ipca.com"),
    ("USV Pvt. Ltd.", "USV", "Govandi, Mumbai", "Mumbai", "Maharashtra", "https://usvindia.com"),
    ("Alembic Pharmaceuticals Ltd.", "Alembic", "Alembic Rd, Vadodara", "Vadodara", "Gujarat", "https://alembicpharmaceuticals.com"),
    ("Macleods Pharmaceuticals Ltd.", "Macleods", "Andheri East, Mumbai", "Mumbai", "Maharashtra", "https://macleodspharma.com"),
    ("FDC Ltd.", "FDC", "Jogeshwari West, Mumbai", "Mumbai", "Maharashtra", "https://fdcindia.com"),
    ("AstraZeneca Pharma India Ltd.", "AstraZeneca", "Hebbal, Bengaluru", "Bengaluru", "Karnataka", "https://astrazeneca.com"),
    ("Novartis India Ltd.", "Novartis", "Sandoz Baug, Kolshet Rd, Thane", "Thane", "Maharashtra", "https://novartis.in"),
    ("Pfizer Ltd.", "Pfizer", "Jogeshwari West, Mumbai", "Mumbai", "Maharashtra", "https://pfizer.co.in"),
    ("Blue Cross Laboratories Ltd.", "Blue Cross", "Worli, Mumbai", "Mumbai", "Maharashtra", "https://bluecrosslabs.com"),
    ("Emcure Pharmaceuticals Ltd.", "Emcure", "Hinjawadi, Pune", "Pune", "Maharashtra", "https://emcure.com"),
    ("Apex Laboratories Pvt. Ltd.", "Apex", "Guindy, Chennai", "Chennai", "Tamil Nadu", "https://apexlabs.co.in"),
    ("Procter & Gamble Health Ltd.", "P&G", "Bandra Kurla Complex, Mumbai", "Mumbai", "Maharashtra", "https://pghealth.com"),
]

# Categories
CATEGORIES = [
    ("Anticonvulsant / Anti-epileptic", "Medicines used to treat epileptic seizures and neuropathic conditions."),
    ("Antihypertensive & Cardiac", "Medicines for high blood pressure, heart failure, and coronary heart disease."),
    ("Gastroenterology & Antacids", "Medicines for acid reflux, ulcers, nausea, and gastrointestinal disorders."),
    ("Analgesic & Anti-inflammatory", "Pain relief, antipyretic fever reduction, and anti-inflammatory therapy."),
    ("Anti-diabetic", "Oral hypoglycemic agents for management of Type 2 diabetes mellitus."),
    ("Antibiotics & Antimicrobials", "Antibacterial and antimicrobial drugs for systemic bacterial infections."),
    ("Respiratory & Antiallergic", "Antihistamines, bronchodilators, and anti-allergy agents."),
    ("Vitamins & Mineral Supplements", "Nutritional supplementation, hematinics, calcium, and vitamin compounds."),
    ("Psychiatric & Neurotropic", "Anxiolytics, antidepressants, and central nervous system modulators."),
    ("Endocrine & Thyroid", "Hormone replacement and endocrine regulator therapies."),
]

# Salts
SALTS = [
    ("Levetiracetam", "(2S)-2-(2-oxopyrrolidin-1-yl)butanamide", "Anticonvulsant (SV2A ligand)"),
    ("Phenytoin Sodium", "Sodium 5,5-diphenylimidazolidine-2,4-dione", "Hydantoin Anticonvulsant"),
    ("Carbamazepine", "5H-dibenzo[b,f]azepine-5-carboxamide", "Sodium Channel Blocker Anticonvulsant"),
    ("Sodium Valproate", "Sodium 2-propylpentanoate", "GABAergic Anticonvulsant"),
    ("Valproic Acid", "2-propylpentanoic acid", "Anticonvulsant / Mood Stabilizer"),
    ("Pantoprazole Sodium", "Sodium 5-(difluoromethoxy)-2-[(3,4-dimethoxypyridin-2-yl)methylsulfinyl]benzimidazole", "Proton Pump Inhibitor"),
    ("Omeprazole", "6-methoxy-2-[(4-methoxy-3,5-dimethylpyridin-2-yl)methylsulfinyl]benzimidazole", "Proton Pump Inhibitor"),
    ("Rabeprazole Sodium", "Sodium 2-(((4-(3-methoxypropoxy)-3-methylpyridin-2-yl)methyl)sulfinyl)benzimidazole", "Proton Pump Inhibitor"),
    ("Esomeprazole Magnesium", "(S)-5-methoxy-2-[(4-methoxy-3,5-dimethylpyridin-2-yl)methylsulfinyl]benzimidazole magnesium", "Proton Pump Inhibitor"),
    ("Domperidone", "5-chloro-1-[1-[3-(2-oxo-2,3-dihydrobenzimidazol-1-yl)propyl]piperidin-4-yl]benzimidazol-2-one", "Dopamine D2 Antagonist / Prokinetic"),
    ("Paracetamol", "N-(4-hydroxyphenyl)acetamide", "Analgesic & Antipyretic"),
    ("Ibuprofen", "2-(4-isobutylphenyl)propanoic acid", "NSAID"),
    ("Diclofenac Sodium", "Sodium 2-(2-(2,6-dichlorophenylamino)phenyl)acetate", "NSAID"),
    ("Aceclofenac", "2-(2-(2,6-Dichlorophenylamino)phenylacetyloxy)acetic acid", "NSAID"),
    ("Nimesulide", "N-(4-nitro-2-phenoxyphenyl)methanesulfonamide", "COX-2 Selective NSAID"),
    ("Tramadol Hydrochloride", "(1R,2R)-2-(dimethylaminomethyl)-1-(3-methoxyphenyl)cyclohexanol hydrochloride", "Opioid Analgesic"),
    ("Telmisartan", "4'-[(1,4'-dimethyl-2'-propyl-[2,6'-bi-1H-benzimidazol]-1'-yl)methyl]biphenyl-2-carboxylic acid", "Angiotensin II Receptor Blocker (ARB)"),
    ("Losartan Potassium", "Potassium 2-butyl-4-chloro-1-[[4-[2-(1H-tetrazol-5-yl)phenyl]phenyl]methyl]imidazole-5-methanol", "ARB Antihypertensive"),
    ("Amlodipine Besylate", "3-ethyl 5-methyl 2-(2-aminoethoxymethyl)-4-(2-chlorophenyl)-6-methyl-1,4-dihydropyridine-3,5-dicarboxylate benzenesulfonate", "Calcium Channel Blocker (Dihydropyridine)"),
    ("Atenolol", "2-[4-[2-hydroxy-3-(propan-2-ylamino)propoxy]phenyl]acetamide", "Beta-1 Selective Adrenergic Blocker"),
    ("Metoprolol Succinate", "bis[1-(isopropylamino)-3-[4-(2-methoxyethyl)phenoxy]propan-2-ol] butanedioate", "Beta-1 Selective Adrenergic Blocker"),
    ("Metformin Hydrochloride", "3-(diaminomethylidene)-1,1-dimethylguanidine hydrochloride", "Biguanide Antidiabetic"),
    ("Glimepiride", "3-ethyl-4-methyl-N-[2-[4-[(4-methylcyclohexyl)carbamoylsulfamoyl]phenyl]ethyl]-2-oxo-5H-pyrrole-1-carboxamide", "Sulfonylurea Antidiabetic"),
    ("Sitagliptin Phosphate", "(3R)-3-amino-1-[3-(trifluoromethyl)-6,8-dihydro-5H-[1,2,4]triazolo[4,3-a]pyrazin-7-yl]-4-(2,4,5-trifluorophenyl)butan-1-one phosphate", "DPP-4 Inhibitor"),
    ("Vildagliptin", "(2S)-1-[(3-hydroxyadamantan-1-yl)amino]acetylpyrrolidine-2-carbonitrile", "DPP-4 Inhibitor"),
    ("Dapagliflozin", "(1S)-1,5-anhydro-1-C-[4-chloro-3-[(4-ethoxyphenyl)methyl]phenyl]-D-glucitol", "SGLT2 Inhibitor"),
    ("Atorvastatin Calcium", "calcium (3R,5R)-7-[2-(4-fluorophenyl)-3-phenyl-4-(phenylcarbamoyl)-5-propan-2-ylpyrrol-1-yl]-3,5-dihydroxyheptanoate", "HMG-CoA Reductase Inhibitor (Statin)"),
    ("Rosuvastatin Calcium", "calcium bis[(3R,5S,6E)-7-[4-(4-fluorophenyl)-2-[methyl(methylsulfonyl)amino]-6-propan-2-ylpyrimidin-5-yl]-3,5-dihydroxyhept-6-enoate]", "HMG-CoA Reductase Inhibitor (Statin)"),
    ("Clopidogrel Bisulfate", "(S)-2-(2-chlorophenyl)-2-(4,5,6,7-tetrahydrothieno[3,2-c]pyridin-5-yl)acetic acid hydrogen sulfate", "P2Y12 Antiplatelet"),
    ("Aspirin", "2-acetoxybenzoic acid", "Antiplatelet / Salicylate"),
    ("Amoxicillin", "6-[amino(4-hydroxyphenyl)acetyl]amino-3,3-dimethyl-7-oxo-4-thia-1-azabicyclo[3.2.0]heptane-2-carboxylic acid", "Penicillin Antibiotic"),
    ("Potassium Clavulanate", "potassium (Z)-(2R,5R)-3-(2-hydroxyethylidene)-7-oxo-4-oxa-1-azabicyclo[3.2.0]heptane-2-carboxylate", "Beta-lactamase Inhibitor"),
    ("Azithromycin", "9-deoxo-9a-aza-9a-methyl-9a-homoerythromycin A", "Macrolide Antibiotic"),
    ("Ciprofloxacin", "1-cyclopropyl-6-fluoro-4-oxo-7-piperazin-1-ylquinoline-3-carboxylic acid", "Fluoroquinolone Antibiotic"),
    ("Cefixime", "(6R,7R)-7-[[(2Z)-2-(2-amino-1,3-thiazol-4-yl)-2-(carboxymethoxyimino)acetyl]amino]-3-ethenyl-8-oxo-5-thia-1-azabicyclo[4.2.0]oct-2-ene-2-carboxylic acid", "Third-generation Cephalosporin"),
    ("Cefpodoxime Proxetil", "1-(isopropoxycarbonyloxy)ethyl (6R,7R)-7-[[(2Z)-2-(2-amino-1,3-thiazol-4-yl)-2-methoxyiminoacetyl]amino]-3-(methoxymethyl)-8-oxo-5-thia-1-azabicyclo[4.2.0]oct-2-ene-2-carboxylate", "Cephalosporin Antibiotic"),
    ("Cetirizine Hydrochloride", "2-(4-((4-chlorophenyl)(phenyl)methyl)piperazin-1-yl)acetic acid dihydrochloride", "Second-generation Antihistamine"),
    ("Levocetirizine Dihydrochloride", "(R)-2-(4-((4-chlorophenyl)(phenyl)methyl)piperazin-1-yl)acetic acid dihydrochloride", "Second-generation Antihistamine"),
    ("Montelukast Sodium", "Sodium 2-[1-[[(1R)-1-[3-[(E)-2-(7-chloroquinolin-2-yl)ethenyl]phenyl]-3-[2-(2-hydroxypropan-2-yl)phenyl]propyl]sulfanylmethyl]cyclopropyl]acetate", "Leukotriene Receptor Antagonist"),
    ("Fexofenadine Hydrochloride", "4-[1-hydroxy-4-[4-(hydroxydiphenylmethyl)piperidin-1-yl]butyl]-2,2-dimethylphenylacetic acid hydrochloride", "Second-generation Antihistamine"),
    ("Thyroxine Sodium", "sodium 4-(4-hydroxy-3,5-diiodophenoxy)-3,5-diiodophenylalanine", "Thyroid Hormone"),
    ("Calcium Carbonate", "calcium carbonate", "Mineral Supplement"),
    ("Cholecalciferol (Vitamin D3)", "(1S,3Z)-3-[(2E)-2-[(1R,3aS,7aR)-1-[(2R)-6-methylheptan-2-yl]-7a-methyl-2,3,3a,5,6,7-hexahydro-1H-inden-4-ylidene]ethylidene]-4-methylidenecyclohexan-1-ol", "Vitamin D Analog"),
    ("Alprazolam", "8-chloro-1-methyl-6-phenyl-4H-[1,2,4]triazolo[4,3-a][1,4]benzodiazepine", "Benzodiazepine Anxiolytic"),
    ("Clonazepam", "5-(2-chlorophenyl)-7-nitro-1,3-dihydro-1,4-benzodiazepin-2-one", "Benzodiazepine Anticonvulsant / Anxiolytic"),
    ("Escitalopram Oxalate", "(1S)-1-[3-(dimethylamino)propyl]-1-(4-fluorophenyl)-1,3-dihydro-2-benzofuran-5-carbonitrile oxalate", "Selective Serotonin Reuptake Inhibitor (SSRI)"),
]

# Core Medicines Data
MEDICINES_DATA = [
    # Anti-epileptic / Neurological
    {
        "brand_name": "Levipil 500",
        "generic_name": "Levetiracetam IP 500 mg",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White to off-white",
        "tablet_shape": "Oval, biconvex",
        "strip_size": "15 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Anticonvulsant / Anti-epileptic",
        "salts": [("Levetiracetam", "500 mg")],
        "uses": "Monotherapy and adjunctive therapy in the treatment of partial onset seizures, myoclonic seizures, and primary generalized tonic-clonic seizures in adults and adolescents with epilepsy.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Do not discontinue abruptly as it may increase seizure frequency. Monitor for behavioral changes or depression. Avoid alcohol.",
        "storage_info": "Store below 25°C in a dry place. Protect from light and moisture.",
        "dominant_color": "Silver foil with blue & red lettering",
        "packaging_keywords": "LEVIPIL, 500, LEVETIRACETAM, SUN PHARMA, LRVIPIL, LEVIPI, LEVIPII, TABLET",
        "ocr_hints": ["LEVIPIL", "LRVIPIL", "LEVIPI", "LEVETIRACETAM", "500", "SUN PHARMA", "SUN", "TABLETS"]
    },
    {
        "brand_name": "Levipil 250",
        "generic_name": "Levetiracetam IP 250 mg",
        "strength": "250 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Blue",
        "tablet_shape": "Oval, biconvex",
        "strip_size": "15 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Anticonvulsant / Anti-epileptic",
        "salts": [("Levetiracetam", "250 mg")],
        "uses": "Treatment of partial-onset seizures with or without secondary generalization in patients with epilepsy.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Take regularly at the same time every day.",
        "storage_info": "Store below 25°C. Keep out of reach of children.",
        "dominant_color": "Silver foil with blue print",
        "packaging_keywords": "LEVIPIL, 250, LEVETIRACETAM, SUN PHARMA",
        "ocr_hints": ["LEVIPIL", "250", "LEVETIRACETAM", "SUN"]
    },
    {
        "brand_name": "Levipil 750",
        "generic_name": "Levetiracetam IP 750 mg",
        "strength": "750 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Orange",
        "tablet_shape": "Oblong",
        "strip_size": "10 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Anticonvulsant / Anti-epileptic",
        "salts": [("Levetiracetam", "750 mg")],
        "uses": "Treatment of generalized and refractory epileptic seizures.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Strictly under neurological supervision.",
        "storage_info": "Store below 25°C in dry place.",
        "dominant_color": "Silver foil with orange markings",
        "packaging_keywords": "LEVIPIL, 750, LEVETIRACETAM, SUN PHARMA",
        "ocr_hints": ["LEVIPIL", "750", "LEVETIRACETAM"]
    },
    {
        "brand_name": "Torleva 500",
        "generic_name": "Levetiracetam IP 500 mg",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow",
        "tablet_shape": "Capsule-shaped",
        "strip_size": "10 Tablets",
        "manufacturer": "Torrent Pharmaceuticals Ltd.",
        "category": "Anticonvulsant / Anti-epileptic",
        "salts": [("Levetiracetam", "500 mg")],
        "uses": "Adjunctive therapy in management of partial and juvenile myoclonic epilepsy.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Do not chew or crush. Swallow whole with water.",
        "storage_info": "Store in a cool dry place below 30°C.",
        "dominant_color": "Silver aluminum blister with red Torrent logo",
        "packaging_keywords": "TORLEVA, 500, TORRENT, LEVETIRACETAM",
        "ocr_hints": ["TORLEVA", "500", "TORRENT", "LEVETIRACETAM"]
    },
    {
        "brand_name": "Eptoin 100",
        "generic_name": "Phenytoin Sodium IP 100 mg",
        "strength": "100 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "120 Tablets",
        "manufacturer": "Abbott India Ltd.",
        "category": "Anticonvulsant / Anti-epileptic",
        "salts": [("Phenytoin Sodium", "100 mg")],
        "uses": "Control of generalized tonic-clonic (grand mal) and psychomotor (temporal lobe) seizures.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Narrow therapeutic index drug. Monitor serum levels.",
        "storage_info": "Store protected from moisture and light.",
        "dominant_color": "Amber bottle / Silver blister",
        "packaging_keywords": "EPTOIN, 100, ABBOTT, PHENYTOIN",
        "ocr_hints": ["EPTOIN", "100", "ABBOTT", "PHENYTOIN"]
    },
    {
        "brand_name": "Tegretol 200",
        "generic_name": "Carbamazepine IP 200 mg",
        "strength": "200 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round, scored",
        "strip_size": "10 Tablets",
        "manufacturer": "Novartis India Ltd.",
        "category": "Anticonvulsant / Anti-epileptic",
        "salts": [("Carbamazepine", "200 mg")],
        "uses": "Epilepsy, trigeminal neuralgia, and bipolar affective disorder.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Periodic blood counts and liver function tests recommended.",
        "storage_info": "Store below 30°C in moisture-proof packaging.",
        "dominant_color": "White blister with Novartis logo",
        "packaging_keywords": "TEGRETOL, 200, NOVARTIS, CARBAMAZEPINE",
        "ocr_hints": ["TEGRETOL", "200", "NOVARTIS", "CARBAMAZEPINE"]
    },

    # Antacids & Gastroenterology
    {
        "brand_name": "Pan 40",
        "generic_name": "Pantoprazole Gastro-resistant Tablets IP 40 mg",
        "strength": "40 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow",
        "tablet_shape": "Round, biconvex",
        "strip_size": "15 Tablets",
        "manufacturer": "Dr. Reddy's Laboratories Ltd.",
        "category": "Gastroenterology & Antacids",
        "salts": [("Pantoprazole Sodium", "40 mg")],
        "uses": "Treatment of gastroesophageal reflux disease (GERD), erosive esophagitis, gastric and duodenal ulcers.",
        "warnings": "Swallow whole 30-60 minutes before meals. Do not chew or crush.",
        "storage_info": "Store below 30°C. Protect from light and moisture.",
        "dominant_color": "Silver foil with purple Pan logo",
        "packaging_keywords": "PAN, 40, DR REDDY, PANTOPRAZOLE",
        "ocr_hints": ["PAN", "40", "DR REDDY", "PANTOPRAZOLE"]
    },
    {
        "brand_name": "Pantop 40",
        "generic_name": "Pantoprazole Sodium Tablets IP 40 mg",
        "strength": "40 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow",
        "tablet_shape": "Oblong",
        "strip_size": "15 Tablets",
        "manufacturer": "Torrent Pharmaceuticals Ltd.",
        "category": "Gastroenterology & Antacids",
        "salts": [("Pantoprazole Sodium", "40 mg")],
        "uses": "Acid peptic disease, Zollinger-Ellison syndrome, GERD.",
        "warnings": "Take on an empty stomach in the morning.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver foil with blue Torrent text",
        "packaging_keywords": "PANTOP, 40, TORRENT, PANTOPRAZOLE",
        "ocr_hints": ["PANTOP", "40", "TORRENT", "PANTOPRAZOLE"]
    },
    {
        "brand_name": "Pantocid 40",
        "generic_name": "Pantoprazole Sodium Gastro-resistant Tablets 40 mg",
        "strength": "40 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow",
        "tablet_shape": "Oval",
        "strip_size": "15 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Gastroenterology & Antacids",
        "salts": [("Pantoprazole Sodium", "40 mg")],
        "uses": "Heartburn, hyperacidity, and peptic ulcer disease.",
        "warnings": "Swallow whole before breakfast.",
        "storage_info": "Store below 30°C in dry place.",
        "dominant_color": "Silver blister pack with red Sun Pharma emblem",
        "packaging_keywords": "PANTOCID, 40, SUN, PANTOPRAZOLE",
        "ocr_hints": ["PANTOCID", "40", "SUN", "PANTOPRAZOLE"]
    },
    {
        "brand_name": "Pan-D",
        "generic_name": "Pantoprazole 40 mg + Domperidone 30 mg SR Capsules",
        "strength": "40 mg + 30 mg",
        "dosage_form": "Capsule",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow / White cap",
        "tablet_shape": "Hard gelatin capsule",
        "strip_size": "15 Capsules",
        "manufacturer": "Alkem Laboratories Ltd.",
        "category": "Gastroenterology & Antacids",
        "salts": [("Pantoprazole Sodium", "40 mg"), ("Domperidone", "30 mg")],
        "uses": "Gastroesophageal reflux disease associated with nausea, dyspepsia, and delayed gastric emptying.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Not recommended for long-term unmonitored use.",
        "storage_info": "Store in a cool, dry place.",
        "dominant_color": "Silver blister with blue & orange accents",
        "packaging_keywords": "PAN-D, PAN D, ALKEM, PANTOPRAZOLE, DOMPERIDONE",
        "ocr_hints": ["PAN-D", "PAN D", "ALKEM", "PANTOPRAZOLE", "DOMPERIDONE"]
    },
    {
        "brand_name": "Omez 20",
        "generic_name": "Omeprazole Capsules IP 20 mg",
        "strength": "20 mg",
        "dosage_form": "Capsule",
        "prescription_status": "Schedule H",
        "tablet_color": "Pink / Lavender",
        "tablet_shape": "Capsule",
        "strip_size": "20 Capsules",
        "manufacturer": "Dr. Reddy's Laboratories Ltd.",
        "category": "Gastroenterology & Antacids",
        "salts": [("Omeprazole", "20 mg")],
        "uses": "Short-term treatment of active duodenal ulcers, gastric ulcers, and severe GERD.",
        "warnings": "Take 30 minutes before food.",
        "storage_info": "Store below 30°C protected from moisture.",
        "dominant_color": "Silver strip with red Omez brandmark",
        "packaging_keywords": "OMEZ, 20, DR REDDY, OMEPRAZOLE",
        "ocr_hints": ["OMEZ", "20", "DR REDDY", "OMEPRAZOLE"]
    },
    {
        "brand_name": "Razo 20",
        "generic_name": "Rabeprazole Sodium Tablets IP 20 mg",
        "strength": "20 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow",
        "tablet_shape": "Round",
        "strip_size": "15 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Gastroenterology & Antacids",
        "salts": [("Rabeprazole Sodium", "20 mg")],
        "uses": "Healing of erosive or ulcerative GERD and maintenance of healing of GERD.",
        "warnings": "Swallow whole. Do not crush or split.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver strip with yellow blister cups",
        "packaging_keywords": "RAZO, 20, SUN, RABEPRAZOLE",
        "ocr_hints": ["RAZO", "20", "SUN", "RABEPRAZOLE"]
    },
    {
        "brand_name": "Rablet 20",
        "generic_name": "Rabeprazole Sodium Tablets 20 mg",
        "strength": "20 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow",
        "tablet_shape": "Oval",
        "strip_size": "10 Tablets",
        "manufacturer": "Lupin Ltd.",
        "category": "Gastroenterology & Antacids",
        "salts": [("Rabeprazole Sodium", "20 mg")],
        "uses": "Acid reflux, peptic ulcers, and dyspepsia.",
        "warnings": "Take on an empty stomach.",
        "storage_info": "Store below 25°C in a dry place.",
        "dominant_color": "Silver foil with blue Lupin insignia",
        "packaging_keywords": "RABLET, 20, LUPIN, RABEPRAZOLE",
        "ocr_hints": ["RABLET", "20", "LUPIN", "RABEPRAZOLE"]
    },

    # Antihypertensive & Cardiology
    {
        "brand_name": "Telma 40",
        "generic_name": "Telmisartan Tablets IP 40 mg",
        "strength": "40 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Oval",
        "strip_size": "15 Tablets",
        "manufacturer": "Glenmark Pharmaceuticals Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Telmisartan", "40 mg")],
        "uses": "Essential hypertension and reduction of cardiovascular morbidity in high-risk patients.",
        "warnings": "DO NOT USE IN PREGNANCY. Risk of fetal toxicity. Monitor blood pressure and serum potassium.",
        "storage_info": "Store below 30°C in dry place.",
        "dominant_color": "Silver foil with blue Telma banner",
        "packaging_keywords": "TELMA, 40, GLENMARK, TELMISARTAN",
        "ocr_hints": ["TELMA", "40", "GLENMARK", "TELMISARTAN", "TEL"]
    },
    {
        "brand_name": "Telma 80",
        "generic_name": "Telmisartan Tablets IP 80 mg",
        "strength": "80 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Capsule-shaped",
        "strip_size": "15 Tablets",
        "manufacturer": "Glenmark Pharmaceuticals Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Telmisartan", "80 mg")],
        "uses": "Moderate to severe hypertension.",
        "warnings": "Contraindicated in pregnancy. Regular renal profiling recommended.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver foil with red & blue print",
        "packaging_keywords": "TELMA, 80, GLENMARK, TELMISARTAN",
        "ocr_hints": ["TELMA", "80", "GLENMARK", "TELMISARTAN"]
    },
    {
        "brand_name": "Telmikind 40",
        "generic_name": "Telmisartan Tablets 40 mg",
        "strength": "40 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "10 Tablets",
        "manufacturer": "Mankind Pharma Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Telmisartan", "40 mg")],
        "uses": "Management of high blood pressure.",
        "warnings": "Schedule H drug. Take at the same time each day.",
        "storage_info": "Store in dry place below 30°C.",
        "dominant_color": "Silver blister pack with red Mankind box",
        "packaging_keywords": "TELMIKIND, 40, MANKIND, TELMISARTAN",
        "ocr_hints": ["TELMIKIND", "40", "MANKIND", "TELMISARTAN"]
    },
    {
        "brand_name": "Tozam 50",
        "generic_name": "Losartan Potassium Tablets IP 50 mg",
        "strength": "50 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round, film coated",
        "strip_size": "15 Tablets",
        "manufacturer": "Torrent Pharmaceuticals Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Losartan Potassium", "50 mg")],
        "uses": "Hypertension, diabetic nephropathy in type 2 diabetes, stroke reduction in patients with LVH.",
        "warnings": "Contraindicated in second and third trimesters of pregnancy. Monitor renal function.",
        "storage_info": "Store below 30°C in dry place.",
        "dominant_color": "Silver foil with Torrent emblem",
        "packaging_keywords": "TOZAM, 50, TORRENT, LOSARTAN, TORR, ZAM",
        "ocr_hints": ["TOZAM", "50", "TORRENT", "LOSARTAN", "TORR", "ZAM"]
    },
    {
        "brand_name": "Losacar 50",
        "generic_name": "Losartan Potassium IP 50 mg",
        "strength": "50 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "15 Tablets",
        "manufacturer": "Zydus Lifesciences Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Losartan Potassium", "50 mg")],
        "uses": "Hypertension and heart failure management.",
        "warnings": "Schedule H drug. Avoid potassium supplements unless advised.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver foil with green Zydus band",
        "packaging_keywords": "LOSACAR, 50, ZYDUS, LOSARTAN",
        "ocr_hints": ["LOSACAR", "50", "ZYDUS", "LOSARTAN"]
    },
    {
        "brand_name": "Stamlo 5",
        "generic_name": "Amlodipine Besylate Tablets IP 5 mg",
        "strength": "5 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "15 Tablets",
        "manufacturer": "Dr. Reddy's Laboratories Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Amlodipine Besylate", "5 mg")],
        "uses": "Treatment of hypertension and coronary artery disease (chronic stable angina).",
        "warnings": "Peripheral edema (swelling of ankles) may occur. Do not stop abruptly.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver blister with blue Stamlo logo",
        "packaging_keywords": "STAMLO, 5, DR REDDY, AMLODIPINE",
        "ocr_hints": ["STAMLO", "5", "DR REDDY", "AMLODIPINE"]
    },
    {
        "brand_name": "Atorva 10",
        "generic_name": "Atorvastatin Calcium Tablets IP 10 mg",
        "strength": "10 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Oval, film coated",
        "strip_size": "15 Tablets",
        "manufacturer": "Zydus Lifesciences Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Atorvastatin Calcium", "10 mg")],
        "uses": "Hypercholesterolemia, hypertriglyceridemia, and prevention of cardiovascular events.",
        "warnings": "Avoid excessive alcohol. Report unexplained muscle aches or fatigue immediately.",
        "storage_info": "Store below 25°C protected from moisture.",
        "dominant_color": "Silver blister pack with green Zydus logo",
        "packaging_keywords": "ATORVA, 10, ZYDUS, ATORVASTATIN",
        "ocr_hints": ["ATORVA", "10", "ZYDUS", "ATORVASTATIN"]
    },
    {
        "brand_name": "Atorva 20",
        "generic_name": "Atorvastatin Calcium Tablets IP 20 mg",
        "strength": "20 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Oval",
        "strip_size": "15 Tablets",
        "manufacturer": "Zydus Lifesciences Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Atorvastatin Calcium", "20 mg")],
        "uses": "Intensive lipid lowering in cardiovascular disease.",
        "warnings": "SCHEDULE H PRESCRIPTION DRUG. Periodic liver function tests recommended.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver foil with green markings",
        "packaging_keywords": "ATORVA, 20, ZYDUS, ATORVASTATIN",
        "ocr_hints": ["ATORVA", "20", "ZYDUS", "ATORVASTATIN"]
    },
    {
        "brand_name": "Rozavel 10",
        "generic_name": "Rosuvastatin Calcium Tablets IP 10 mg",
        "strength": "10 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Pink",
        "tablet_shape": "Round",
        "strip_size": "10 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Rosuvastatin Calcium", "10 mg")],
        "uses": "Primary hyperlipidemia and mixed dyslipidemia.",
        "warnings": "Schedule H. Take once daily at bedtime.",
        "storage_info": "Store below 30°C in a dry place.",
        "dominant_color": "Silver foil with pink band",
        "packaging_keywords": "ROZAVEL, 10, SUN, ROSUVASTATIN",
        "ocr_hints": ["ROZAVEL", "10", "SUN", "ROSUVASTATIN"]
    },
    {
        "brand_name": "Ecosprin 75",
        "generic_name": "Aspirin Gastro-resistant Tablets IP 75 mg",
        "strength": "75 mg",
        "dosage_form": "Tablet",
        "prescription_status": "OTC",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "14 Tablets",
        "manufacturer": "USV Pvt. Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Aspirin", "75 mg")],
        "uses": "Prophylaxis of stroke, myocardial infarction, and transient ischemic attacks.",
        "warnings": "Avoid in patients with active peptic ulcers or bleeding disorders.",
        "storage_info": "Store below 25°C in a dry place.",
        "dominant_color": "Silver foil with blue USV logo",
        "packaging_keywords": "ECOSPRIN, 75, USV, ASPIRIN",
        "ocr_hints": ["ECOSPRIN", "75", "USV", "ASPIRIN"]
    },
    {
        "brand_name": "Clopilet 75",
        "generic_name": "Clopidogrel Tablets IP 75 mg",
        "strength": "75 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Pink",
        "tablet_shape": "Round",
        "strip_size": "15 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Antihypertensive & Cardiac",
        "salts": [("Clopidogrel Bisulfate", "75 mg")],
        "uses": "Prevention of atherothrombotic events in patients with acute coronary syndrome.",
        "warnings": "Increased risk of bleeding. Inform surgeon/dentist before any procedure.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver blister pack with red lettering",
        "packaging_keywords": "CLOPILET, 75, SUN, CLOPIDOGREL",
        "ocr_hints": ["CLOPILET", "75", "SUN", "CLOPIDOGREL"]
    },

    # Analgesic & Anti-inflammatory
    {
        "brand_name": "Dolo 650",
        "generic_name": "Paracetamol Tablets IP 650 mg",
        "strength": "650 mg",
        "dosage_form": "Tablet",
        "prescription_status": "OTC",
        "tablet_color": "White",
        "tablet_shape": "Oval, scored",
        "strip_size": "15 Tablets",
        "manufacturer": "Micro Labs Ltd.",
        "category": "Analgesic & Anti-inflammatory",
        "salts": [("Paracetamol", "650 mg")],
        "uses": "Relief of mild to moderate pain (headache, body ache) and high fever.",
        "warnings": "Do not exceed 4 tablets (2600 mg) in 24 hours. Hepatotoxic risk in liver disease.",
        "storage_info": "Store below 30°C in dry place.",
        "dominant_color": "Silver strip with red & green Dolo logo",
        "packaging_keywords": "DOLO, 650, MICRO LABS, PARACETAMOL",
        "ocr_hints": ["DOLO", "650", "MICRO LABS", "PARACETAMOL"]
    },
    {
        "brand_name": "Calpol 500",
        "generic_name": "Paracetamol Tablets IP 500 mg",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "prescription_status": "OTC",
        "tablet_color": "White",
        "tablet_shape": "Capsule-shaped",
        "strip_size": "15 Tablets",
        "manufacturer": "GlaxoSmithKline Pharmaceuticals Ltd.",
        "category": "Analgesic & Anti-inflammatory",
        "salts": [("Paracetamol", "500 mg")],
        "uses": "Fever, mild pain relief in adults and children above 12 years.",
        "warnings": "Do not take with other paracetamol-containing formulations.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "White blister pack with blue & red Calpol emblem",
        "packaging_keywords": "CALPOL, 500, GSK, PARACETAMOL",
        "ocr_hints": ["CALPOL", "500", "GSK", "PARACETAMOL"]
    },
    {
        "brand_name": "Combiflam",
        "generic_name": "Ibuprofen 400 mg + Paracetamol 325 mg Tablets",
        "strength": "400 mg + 325 mg",
        "dosage_form": "Tablet",
        "prescription_status": "OTC",
        "tablet_color": "White",
        "tablet_shape": "Round, biconvex",
        "strip_size": "20 Tablets",
        "manufacturer": "Sanofi India Ltd.",
        "category": "Analgesic & Anti-inflammatory",
        "salts": [("Ibuprofen", "400 mg"), ("Paracetamol", "325 mg")],
        "uses": "Dental pain, musculoskeletal pain, osteoarthritis, fever with inflammatory symptoms.",
        "warnings": "Always take after meals with plenty of water. Avoid in active stomach ulcer.",
        "storage_info": "Store below 25°C in dry place.",
        "dominant_color": "Silver foil with blue Combiflam typography",
        "packaging_keywords": "COMBIFLAM, SANOFI, IBUPROFEN, PARACETAMOL",
        "ocr_hints": ["COMBIFLAM", "SANOFI", "IBUPROFEN", "PARACETAMOL"]
    },
    {
        "brand_name": "Zerodol P",
        "generic_name": "Aceclofenac 100 mg + Paracetamol 325 mg",
        "strength": "100 mg + 325 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Oblong",
        "strip_size": "10 Tablets",
        "manufacturer": "IPCA Laboratories Ltd.",
        "category": "Analgesic & Anti-inflammatory",
        "salts": [("Aceclofenac", "100 mg"), ("Paracetamol", "325 mg")],
        "uses": "Relief of pain and inflammation in rheumatoid arthritis, ankylosing spondylitis, and osteoarthritis.",
        "warnings": "SCHEDULE H. Take with or after food. Caution in renal or cardiac impairment.",
        "storage_info": "Store below 30°C in dry place.",
        "dominant_color": "Silver strip with dark blue IPCA banner",
        "packaging_keywords": "ZERODOL, ZERODOL-P, IPCA, ACECLOFENAC, PARACETAMOL",
        "ocr_hints": ["ZERODOL", "ZERODOL-P", "IPCA", "ACECLOFENAC", "PARACETAMOL"]
    },
    {
        "brand_name": "Voveran 50",
        "generic_name": "Diclofenac Sodium Gastro-resistant Tablets 50 mg",
        "strength": "50 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Yellow",
        "tablet_shape": "Round",
        "strip_size": "15 Tablets",
        "manufacturer": "Novartis India Ltd.",
        "category": "Analgesic & Anti-inflammatory",
        "salts": [("Diclofenac Sodium", "50 mg")],
        "uses": "Acute musculoskeletal trauma, post-operative inflammation, acute gout.",
        "warnings": "SCHEDULE H. Take with food. High cardiovascular and gastrointestinal risk on chronic use.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver blister pack with Novartis logo",
        "packaging_keywords": "VOVERAN, 50, NOVARTIS, DICLOFENAC",
        "ocr_hints": ["VOVERAN", "50", "NOVARTIS", "DICLOFENAC"]
    },

    # Anti-diabetic
    {
        "brand_name": "Glycomet 500",
        "generic_name": "Metformin Hydrochloride Tablets IP 500 mg",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "20 Tablets",
        "manufacturer": "USV Pvt. Ltd.",
        "category": "Anti-diabetic",
        "salts": [("Metformin Hydrochloride", "500 mg")],
        "uses": "First-line pharmacological management of Type 2 Diabetes Mellitus.",
        "warnings": "SCHEDULE H. Take with meals to reduce gastrointestinal side effects. Monitor kidney function.",
        "storage_info": "Store below 25°C in dry place.",
        "dominant_color": "Silver foil with blue USV lettering",
        "packaging_keywords": "GLYCOMET, 500, USV, METFORMIN",
        "ocr_hints": ["GLYCOMET", "500", "USV", "METFORMIN"]
    },
    {
        "brand_name": "Januvia 100",
        "generic_name": "Sitagliptin Tablets 100 mg",
        "strength": "100 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Beige",
        "tablet_shape": "Round",
        "strip_size": "14 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Anti-diabetic",
        "salts": [("Sitagliptin Phosphate", "100 mg")],
        "uses": "Glycemic control in Type 2 Diabetes Mellitus as monotherapy or combination therapy.",
        "warnings": "Risk of pancreatitis. Discontinue immediately if severe persistent abdominal pain occurs.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver blister pack with white backing",
        "packaging_keywords": "JANUVIA, 100, SITAGLIPTIN",
        "ocr_hints": ["JANUVIA", "100", "SITAGLIPTIN"]
    },
    {
        "brand_name": "Galvus 50",
        "generic_name": "Vildagliptin Tablets 50 mg",
        "strength": "50 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White to light yellowish",
        "tablet_shape": "Round",
        "strip_size": "14 Tablets",
        "manufacturer": "Novartis India Ltd.",
        "category": "Anti-diabetic",
        "salts": [("Vildagliptin", "50 mg")],
        "uses": "Type 2 diabetes in adult patients.",
        "warnings": "Schedule H. Liver enzymes monitoring recommended prior to and during treatment.",
        "storage_info": "Store below 30°C in original package.",
        "dominant_color": "Silver foil with Novartis trade emblem",
        "packaging_keywords": "GALVUS, 50, NOVARTIS, VILDAGLIPTIN",
        "ocr_hints": ["GALVUS", "50", "NOVARTIS", "VILDAGLIPTIN"]
    },

    # Antibiotics
    {
        "brand_name": "Augmentin 625 Duo",
        "generic_name": "Amoxicillin 500 mg + Potassium Clavulanate 125 mg Tablets IP",
        "strength": "625 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H1",
        "tablet_color": "White",
        "tablet_shape": "Capsule-shaped",
        "strip_size": "10 Tablets",
        "manufacturer": "GlaxoSmithKline Pharmaceuticals Ltd.",
        "category": "Antibiotics & Antimicrobials",
        "salts": [("Amoxicillin", "500 mg"), ("Potassium Clavulanate", "125 mg")],
        "uses": "Community-acquired pneumonia, otitis media, sinusitis, skin and soft tissue infections.",
        "warnings": "SCHEDULE H1 PRESCRIPTION DRUG. Warning: It is dangerous to take this preparation except in accordance with medical advice. Complete the full prescribed course.",
        "storage_info": "Store below 25°C in a dry place. Foil pack must remain sealed until use.",
        "dominant_color": "Silver foil with bold red Schedule H1 warning band",
        "packaging_keywords": "AUGMENTIN, 625, DUO, GSK, AMOXICILLIN, CLAVULANATE",
        "ocr_hints": ["AUGMENTIN", "625", "DUO", "GSK", "AMOXICILLIN", "CLAVULANATE"]
    },
    {
        "brand_name": "Azithral 500",
        "generic_name": "Azithromycin Tablets IP 500 mg",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H1",
        "tablet_color": "White",
        "tablet_shape": "Oblong",
        "strip_size": "5 Tablets",
        "manufacturer": "Alembic Pharmaceuticals Ltd.",
        "category": "Antibiotics & Antimicrobials",
        "salts": [("Azithromycin", "500 mg")],
        "uses": "Upper and lower respiratory tract infections, typhoid fever, and genital ulcer diseases.",
        "warnings": "SCHEDULE H1. Take 1 hour before or 2 hours after meals. Complete full 3 or 5 day regimen.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver blister pack with blue Alembic logo",
        "packaging_keywords": "AZITHRAL, 500, ALEMBIC, AZITHROMYCIN",
        "ocr_hints": ["AZITHRAL", "500", "ALEMBIC", "AZITHROMYCIN"]
    },
    {
        "brand_name": "Azee 500",
        "generic_name": "Azithromycin Tablets IP 500 mg",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H1",
        "tablet_color": "White",
        "tablet_shape": "Oval",
        "strip_size": "5 Tablets",
        "manufacturer": "Cipla Ltd.",
        "category": "Antibiotics & Antimicrobials",
        "salts": [("Azithromycin", "500 mg")],
        "uses": "Bacterial pharyngitis, tonsillitis, and bronchitis.",
        "warnings": "SCHEDULE H1 PRESCRIPTION DRUG. Not for viral infections like common cold.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver foil with blue Cipla banner",
        "packaging_keywords": "AZEE, 500, CIPLA, AZITHROMYCIN",
        "ocr_hints": ["AZEE", "500", "CIPLA", "AZITHROMYCIN"]
    },
    {
        "brand_name": "Ciplox 500",
        "generic_name": "Ciprofloxacin Tablets IP 500 mg",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H1",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "10 Tablets",
        "manufacturer": "Cipla Ltd.",
        "category": "Antibiotics & Antimicrobials",
        "salts": [("Ciprofloxacin", "500 mg")],
        "uses": "Urinary tract infections, infectious diarrhea, and bone/joint infections.",
        "warnings": "SCHEDULE H1. Avoid taking simultaneously with calcium/iron/antacids. Risk of tendonitis.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver strip with blue Cipla branding",
        "packaging_keywords": "CIPLOX, 500, CIPLA, CIPROFLOXACIN",
        "ocr_hints": ["CIPLOX", "500", "CIPLA", "CIPROFLOXACIN"]
    },
    {
        "brand_name": "Taxim-O 200",
        "generic_name": "Cefixime Tablets IP 200 mg",
        "strength": "200 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H1",
        "tablet_color": "White",
        "tablet_shape": "Capsule-shaped",
        "strip_size": "10 Tablets",
        "manufacturer": "Alkem Laboratories Ltd.",
        "category": "Antibiotics & Antimicrobials",
        "salts": [("Cefixime", "200 mg")],
        "uses": "Uncomplicated UTI, otitis media, pharyngitis, and enteric fever.",
        "warnings": "SCHEDULE H1. Caution in patients with penicillin allergy.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver foil with red Schedule H1 box",
        "packaging_keywords": "TAXIM-O, 200, ALKEM, CEFIXIME",
        "ocr_hints": ["TAXIM-O", "TAXIM", "200", "ALKEM", "CEFIXIME"]
    },

    # Respiratory & Antiallergic
    {
        "brand_name": "Montair LC",
        "generic_name": "Montelukast 10 mg + Levocetirizine 5 mg Tablets",
        "strength": "10 mg + 5 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Orange",
        "tablet_shape": "Round, biconvex",
        "strip_size": "15 Tablets",
        "manufacturer": "Cipla Ltd.",
        "category": "Respiratory & Antiallergic",
        "salts": [("Montelukast Sodium", "10 mg"), ("Levocetirizine Dihydrochloride", "5 mg")],
        "uses": "Allergic rhinitis with comorbid asthma, chronic allergic symptoms, urticaria.",
        "warnings": "Take at night. May cause mild drowsiness. Monitor for neuropsychiatric changes.",
        "storage_info": "Store below 30°C in dry place.",
        "dominant_color": "Silver blister pack with orange print",
        "packaging_keywords": "MONTAIR, MONTAIR-LC, CIPLA, MONTELUKAST, LEVOCETIRIZINE",
        "ocr_hints": ["MONTAIR", "MONTAIR-LC", "CIPLA", "MONTELUKAST", "LEVOCETIRIZINE"]
    },
    {
        "brand_name": "Allegra 120",
        "generic_name": "Fexofenadine Hydrochloride Tablets IP 120 mg",
        "strength": "120 mg",
        "dosage_form": "Tablet",
        "prescription_status": "OTC",
        "tablet_color": "Peach",
        "tablet_shape": "Capsule-shaped",
        "strip_size": "10 Tablets",
        "manufacturer": "Sanofi India Ltd.",
        "category": "Respiratory & Antiallergic",
        "salts": [("Fexofenadine Hydrochloride", "120 mg")],
        "uses": "Seasonal allergic rhinitis and chronic idiopathic urticaria.",
        "warnings": "Non-sedating antihistamine. Do not take with fruit juice as it reduces bioavailability.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver foil with purple Allegra logo",
        "packaging_keywords": "ALLEGRA, 120, SANOFI, FEXOFENADINE",
        "ocr_hints": ["ALLEGRA", "120", "SANOFI", "FEXOFENADINE"]
    },
    {
        "brand_name": "Cetzine 10",
        "generic_name": "Cetirizine Hydrochloride Tablets IP 10 mg",
        "strength": "10 mg",
        "dosage_form": "Tablet",
        "prescription_status": "OTC",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "10 Tablets",
        "manufacturer": "Cipla Ltd.",
        "category": "Respiratory & Antiallergic",
        "salts": [("Cetirizine Hydrochloride", "10 mg")],
        "uses": "Runny nose, sneezing, allergic conjunctivitis, itching.",
        "warnings": "May cause drowsiness. Avoid driving or operating machinery.",
        "storage_info": "Store below 30°C.",
        "dominant_color": "Silver foil with blue Cipla text",
        "packaging_keywords": "CETZINE, 10, CIPLA, CETIRIZINE",
        "ocr_hints": ["CETZINE", "10", "CIPLA", "CETIRIZINE"]
    },

    # Thyroid & Supplements
    {
        "brand_name": "Thyronorm 50",
        "generic_name": "Thyroxine Sodium Tablets IP 50 mcg",
        "strength": "50 mcg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round, small",
        "strip_size": "100 Tablets bottle",
        "manufacturer": "Abbott India Ltd.",
        "category": "Endocrine & Thyroid",
        "salts": [("Thyroxine Sodium", "50 mcg")],
        "uses": "Hypothyroidism (thyroid hormone replacement) and goiter management.",
        "warnings": "Take on an empty stomach in the morning 30-60 minutes before breakfast with plain water.",
        "storage_info": "Store in a cool dry place below 25°C. Keep bottle tightly closed.",
        "dominant_color": "White bottle with blue cap and Abbott logo",
        "packaging_keywords": "THYRONORM, 50, ABBOTT, THYROXINE",
        "ocr_hints": ["THYRONORM", "50", "ABBOTT", "THYROXINE"]
    },
    {
        "brand_name": "Shelcal 500",
        "generic_name": "Calcium 500 mg + Vitamin D3 250 IU Tablets",
        "strength": "500 mg + 250 IU",
        "dosage_form": "Tablet",
        "prescription_status": "OTC",
        "tablet_color": "White",
        "tablet_shape": "Oblong",
        "strip_size": "15 Tablets",
        "manufacturer": "Torrent Pharmaceuticals Ltd.",
        "category": "Vitamins & Mineral Supplements",
        "salts": [("Calcium Carbonate", "500 mg"), ("Cholecalciferol (Vitamin D3)", "250 IU")],
        "uses": "Osteoporosis prevention, osteomalacia, pregnancy, lactation, and calcium deficiency.",
        "warnings": "Take after meals. Maintain adequate fluid intake.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "White blister pack with blue & green Shelcal logo",
        "packaging_keywords": "SHELCAL, 500, TORRENT, CALCIUM, VITAMIN D3",
        "ocr_hints": ["SHELCAL", "500", "TORRENT", "CALCIUM"]
    },

    # Psychiatric / Neuro
    {
        "brand_name": "Alprax 0.5",
        "generic_name": "Alprazolam Tablets IP 0.5 mg",
        "strength": "0.5 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "Pink",
        "tablet_shape": "Round, scored",
        "strip_size": "15 Tablets",
        "manufacturer": "Torrent Pharmaceuticals Ltd.",
        "category": "Psychiatric & Neurotropic",
        "salts": [("Alprazolam", "0.5 mg")],
        "uses": "Short-term management of generalized anxiety disorder and panic disorder.",
        "warnings": "HABIT FORMING DRUG. High dependency potential. Do not stop abruptly.",
        "storage_info": "Store below 25°C protected from light.",
        "dominant_color": "Silver foil with red Schedule H warning",
        "packaging_keywords": "ALPRAX, 0.5, TORRENT, ALPRAZOLAM",
        "ocr_hints": ["ALPRAX", "0.5", "TORRENT", "ALPRAZOLAM"]
    },
    {
        "brand_name": "Nexito 10",
        "generic_name": "Escitalopram Oxalate Tablets IP 10 mg",
        "strength": "10 mg",
        "dosage_form": "Tablet",
        "prescription_status": "Schedule H",
        "tablet_color": "White",
        "tablet_shape": "Round",
        "strip_size": "10 Tablets",
        "manufacturer": "Sun Pharmaceutical Industries Ltd.",
        "category": "Psychiatric & Neurotropic",
        "salts": [("Escitalopram Oxalate", "10 mg")],
        "uses": "Major depressive episodes and generalized anxiety disorder.",
        "warnings": "SCHEDULE H. Takes 2-4 weeks for therapeutic effect. Do not discontinue without medical supervision.",
        "storage_info": "Store below 25°C.",
        "dominant_color": "Silver foil with blue Sun Pharma mark",
        "packaging_keywords": "NEXITO, 10, SUN, ESCITALOPRAM",
        "ocr_hints": ["NEXITO", "10", "SUN", "ESCITALOPRAM"]
    }
]

def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    print(f"Connecting to {DB_PATH}...")

    # Insert Manufacturers
    mfg_id_map = {}
    for name, short, addr, city, state, web in MANUFACTURERS:
        cur.execute("""
            INSERT INTO Manufacturers (name, short_name, address, city, state, website)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET short_name=excluded.short_name, website=excluded.website
        """, (name, short, addr, city, state, web))
        row = cur.execute("SELECT manufacturer_id FROM Manufacturers WHERE name = ?", (name,)).fetchone()
        mfg_id_map[name] = row[0]
    print(f"Loaded {len(mfg_id_map)} manufacturers.")

    # Insert Categories
    cat_id_map = {}
    for name, desc in CATEGORIES:
        cur.execute("""
            INSERT INTO Categories (category_name, description)
            VALUES (?, ?)
            ON CONFLICT(category_name) DO UPDATE SET description=excluded.description
        """, (name, desc))
        row = cur.execute("SELECT category_id FROM Categories WHERE category_name = ?", (name,)).fetchone()
        cat_id_map[name] = row[0]
    print(f"Loaded {len(cat_id_map)} categories.")

    # Insert Salts
    salt_id_map = {}
    for name, iupac, drug_class in SALTS:
        cur.execute("""
            INSERT INTO Salts (salt_name, iupac_name, drug_class)
            VALUES (?, ?, ?)
            ON CONFLICT(salt_name) DO UPDATE SET drug_class=excluded.drug_class, iupac_name=excluded.iupac_name
        """, (name, iupac, drug_class))
        row = cur.execute("SELECT salt_id FROM Salts WHERE salt_name = ?", (name,)).fetchone()
        salt_id_map[name] = row[0]
    print(f"Loaded {len(salt_id_map)} active salts.")

    # Insert Medicines
    med_count = 0
    for med in MEDICINES_DATA:
        mfg_id = mfg_id_map[med["manufacturer"]]
        cat_id = cat_id_map[med["category"]]

        cur.execute("""
            INSERT INTO Medicines (
                brand_name, generic_name, strength, dosage_form, prescription_status,
                tablet_color, tablet_shape, strip_size, uses, warnings, storage_info,
                manufacturer_id, category_id, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(brand_name, strength, manufacturer_id) DO UPDATE SET
                generic_name=excluded.generic_name,
                dosage_form=excluded.dosage_form,
                prescription_status=excluded.prescription_status,
                tablet_color=excluded.tablet_color,
                tablet_shape=excluded.tablet_shape,
                strip_size=excluded.strip_size,
                uses=excluded.uses,
                warnings=excluded.warnings,
                storage_info=excluded.storage_info,
                category_id=excluded.category_id,
                is_active=1
        """, (
            med["brand_name"], med["generic_name"], med["strength"], med["dosage_form"],
            med["prescription_status"], med["tablet_color"], med["tablet_shape"],
            med["strip_size"], med["uses"], med["warnings"], med["storage_info"],
            mfg_id, cat_id
        ))

        row = cur.execute(
            "SELECT medicine_id FROM Medicines WHERE brand_name = ? AND strength = ? AND manufacturer_id = ?",
            (med["brand_name"], med["strength"], mfg_id)
        ).fetchone()
        med_id = row[0]
        med_count += 1

        # Link Salts
        for salt_name, comp_strength in med["salts"]:
            if salt_name in salt_id_map:
                s_id = salt_id_map[salt_name]
                cur.execute("""
                    INSERT OR REPLACE INTO Medicine_Salt_Mapping (medicine_id, salt_id, composition_strength)
                    VALUES (?, ?, ?)
                """, (med_id, s_id, comp_strength))

        # Packaging Details
        cur.execute("""
            INSERT INTO Packaging_Details (medicine_id, dominant_color, packaging_type, packaging_keywords)
            VALUES (?, ?, 'Blister strip', ?)
            ON CONFLICT(medicine_id) DO UPDATE SET
                dominant_color=excluded.dominant_color,
                packaging_keywords=excluded.packaging_keywords
        """, (med_id, med["dominant_color"], med["packaging_keywords"]))

        # OCR Keywords
        for kw in med["ocr_hints"]:
            cur.execute("""
                INSERT OR IGNORE INTO OCR_Keywords (medicine_id, keyword, keyword_type)
                VALUES (?, ?, 'brand_fragment')
            """, (med_id, kw.upper()))

    conn.commit()

    total_meds = cur.execute("SELECT COUNT(*) FROM Medicines").fetchone()[0]
    total_salts = cur.execute("SELECT COUNT(*) FROM Salts").fetchone()[0]
    total_mfgs = cur.execute("SELECT COUNT(*) FROM Manufacturers").fetchone()[0]
    print(f"Seeding complete!")
    print(f"Total Medicines in DB: {total_meds}")
    print(f"Total Salts: {total_salts}")
    print(f"Total Manufacturers: {total_mfgs}")

    # Verify Levipil
    cur.execute("""
        SELECT m.medicine_id, m.brand_name, m.strength, man.name, GROUP_CONCAT(s.salt_name)
        FROM Medicines m
        JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
        LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
        LEFT JOIN Salts s ON msm.salt_id = s.salt_id
        WHERE m.brand_name LIKE '%Levipil%'
        GROUP BY m.medicine_id
    """)
    for r in cur.fetchall():
        print("  Verified Levipil:", r)

    conn.close()

if __name__ == "__main__":
    seed()
