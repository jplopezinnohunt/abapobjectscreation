with open("YRGGBS00_SOURCE.txt", mode="r", encoding="utf-16-le") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "FORM u910" in line:
            print("--- U910 Start ---")
            for j in range(i, i+50):
                if j < len(lines):
                    print(f"{j+1}: {lines[j].strip()}")
                if "ENDFORM" in lines[j]:
                    break
