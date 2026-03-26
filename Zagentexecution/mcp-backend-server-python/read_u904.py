with open("YRGGBS00_SOURCE.txt", mode="r", encoding="utf-16-le") as f:
    lines = f.readlines()
    print("--- U904 Start ---")
    for i in range(572, 650):
        print(f"{i+1}: {lines[i].strip()}")
        if "ENDFORM" in lines[i]:
            break
