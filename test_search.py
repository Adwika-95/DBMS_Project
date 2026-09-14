from backend.search_engine import search_medicines

tokens = ['PHIXDST', 'LPL', 'SOO', 'LEVIPII', 'SUO', 'LEVIEH', 'SUD', 'LEVETIRACETAM', 'IAPLE', 'LRVIPIL', '500', 'OO', 'HEDKA', 'VU', 'IINI', 'LEVIPI', 'LAVIPU', 'EVETIRACETAMM', 'ABLETS']

res = search_medicines(tokens)
print(f"Total candidates matched: {len(res)}")
for i, r in enumerate(res[:3]):
    print(f"\n#{i+1}: {r['brand_name']} ({r['strength']}) - {r['manufacturer_name']}")
    print(f"   Score: {r['score']} | Confidence: {r['confidence_pct']}% ({r['confidence_label']})")
    print("   Clues:")
    for c in r['matched_clues']:
        print(f"     - {c['label']} (+{c['pts']} pts)")
