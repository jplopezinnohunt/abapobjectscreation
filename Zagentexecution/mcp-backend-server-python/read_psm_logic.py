with open("YRGGBS00_SOURCE.txt", mode="r", encoding="utf-16-le") as f:
    lines = f.readlines()
    
    # Section 1: around 1135
    print("--- Section 1 (around 1135) ---")
    for i in range(1120, 1200):
        print(f"{i+1}: {lines[i].strip()}")
        
    # Section 2: around 1321
    print("\n--- Section 2 (around 1321) ---")
    for i in range(1310, 1400):
        print(f"{i+1}: {lines[i].strip()}")

    # Section 3: around 1427
    print("\n--- Section 3 (around 1427) ---")
    for i in range(1410, 1500):
        print(f"{i+1}: {lines[i].strip()}")
