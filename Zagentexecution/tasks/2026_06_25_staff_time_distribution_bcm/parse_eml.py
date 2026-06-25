#!/usr/bin/env python3
"""Parse the staff-time-distribution .eml: headers, body text, attachments."""
import email, email.policy, os, sys, hashlib

EML = r"C:\Users\jp_lopez\Downloads\RE_ Template of update staff work time distribution .eml"
OUT = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\tasks\2026_06_25_staff_time_distribution_bcm\attachments"

with open(EML, "rb") as f:
    msg = email.message_from_binary_file(f, policy=email.policy.default)

print("="*80)
print("HEADERS")
print("="*80)
for h in ("From", "To", "Cc", "Subject", "Date"):
    print(f"{h}: {msg.get(h)}")

print("\n" + "="*80)
print("BODY (text/plain, first 12000 chars)")
print("="*80)
body = msg.get_body(preferencelist=("plain", "html"))
if body is not None:
    content = body.get_content()
    print(content[:12000])
else:
    print("(no simple body found)")

print("\n" + "="*80)
print("ATTACHMENTS / PARTS")
print("="*80)
idx = 0
for part in msg.walk():
    ctype = part.get_content_type()
    disp = part.get_content_disposition()
    fname = part.get_filename()
    if fname or (disp == "attachment") or ctype.startswith("image/") or ctype.startswith("application/"):
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        idx += 1
        safe = fname if fname else f"part_{idx}_{ctype.replace('/','_')}"
        # sanitize
        safe = "".join(c for c in safe if c.isalnum() or c in " ._-()").strip()
        if not safe:
            safe = f"part_{idx}"
        path = os.path.join(OUT, safe)
        with open(path, "wb") as o:
            o.write(payload)
        h = hashlib.md5(payload).hexdigest()[:8]
        print(f"[{idx}] type={ctype} disp={disp} name={fname!r} bytes={len(payload)} md5={h}")
        print(f"     -> saved: {safe}")

print(f"\nTotal saved: {idx}")
