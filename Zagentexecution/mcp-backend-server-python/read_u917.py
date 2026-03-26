with open("YRGGBS00_SOURCE.txt", mode="r", encoding="utf-16-le") as f:
    lines = f.readlines()
    print("--- U917 Start ---")
    for i in range(1542, 1600):
        print(f"{i+1}: {lines[i].strip()}")
        if "ENDFORM" in lines[i]:
            break
