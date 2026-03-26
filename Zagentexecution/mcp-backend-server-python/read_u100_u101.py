with open("YRGGBS00_SOURCE.txt", mode="r", encoding="utf-16-le") as f:
    lines = f.readlines()
    print("--- U100 & U101 Start ---")
    for i in range(308, 400):
        print(f"{i+1}: {lines[i].strip()}")
        if "ENDFORM" in lines[i] and i > 340:
            # Simple check to stop after U101
            pass
