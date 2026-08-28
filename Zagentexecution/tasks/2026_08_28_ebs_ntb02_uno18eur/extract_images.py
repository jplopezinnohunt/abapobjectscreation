# -*- coding: utf-8 -*-
import email, email.policy, os, sys

P = r"C:\Users\jp_lopez\Downloads\RE_ Request to change account for NORTHERN TRUST UNESCO ASHI-EUR account.eml"
OUT = os.path.dirname(os.path.abspath(__file__))
m = email.message_from_file(open(P, "r", encoding="utf-8", errors="replace"), policy=email.policy.default)
for part in m.walk():
    fn = part.get_filename()
    if fn and fn.lower().endswith(".png"):
        data = part.get_payload(decode=True)
        p = os.path.join(OUT, fn)
        open(p, "wb").write(data)
        print(p, len(data))
