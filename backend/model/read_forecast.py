import pandas as pd

print("🌊 SWELL APPROACH REPORT (East -> West)")
print("-" * 65)
print(f"{'Location':<10} {'Depth (m)':<10} {'Hs (m)':<10} {'Dir (deg)':<10} {'Status':<15}")
print("-" * 65)

try:
    cols = ["X", "Y", "Hs", "Tp", "Dir", "Depth", "QB"]
    # SWAN outputs multiple points in one file.
    df = pd.read_csv("arugam_forecast.tbl", skiprows=7, delim_whitespace=True, names=cols)
    
    # Map rows to names (Order matches INPUT file)
    names = ["DEEP OCEAN", "MID SHELF", "SURF ZONE"]
    
    for i, row in df.iterrows():
        name = names[i] if i < 3 else f"POINT {i}"
        depth = row['Depth']
        hs = row['Hs']
        qb = row['QB']
        
        status = "Swell"
        if depth < 5.0: status = "Shallows"
        if qb > 0.1: status = "BREAKING 🌊"
        
        print(f"{name:<10} {depth:<10.1f} {hs:<10.2f} {row['Dir']:<10.1f} {status:<15}")

    print("-" * 65)
    
    # Final Verdict
    surf_hs = df.iloc[2]['Hs']
    if surf_hs > 0.5:
        print(f"🏄 FINAL VERDICT: {surf_hs:.1f}m waves at Arugam Bay!")
    else:
        print(f"🧘 FINAL VERDICT: Flat/Small ({surf_hs:.1f}m). Try moving point closer.")

except Exception as e:
    print(f"Error: {e}")