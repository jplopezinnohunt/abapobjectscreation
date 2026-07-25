"""
SM21 syslog CENTDATA decoder + channel classifier (H74/H78).

The raw SM21 record (CENTDATA, fixed format) is:
  [0]    length-class (l/m/p/h)
  [1:3]  AREA            (Q0, R2, E0, BY, R4, R5 ...)
  [3]    SUBID
  [4:18] timestamp       YYYYMMDDHHMMSS
  [18:21]'000'           (millis/pad)
  [21:30]9 digits        (counter/pid-ish)
  [30:32]WP code         (DP=dispatcher, Dn=dialog WP n, Bn=batch WP n, RD ...)
  [32:]  body            (padded fields; layout depends on message type)

KEY DISCRIMINATOR (proven 2026-06-22, H74): a `10054` ("connection forcibly closed by
remote host", WSAECONNRESET) is NOT one thing. The CHANNEL is decided by area/subid/WP:
  Q0/I  recv|WSASend nixxi  +WP=DP  -> frontend DIAG reset (SAP GUI native, end-user PC)
  Q0/4  dpTermin            +WP=DP  -> frontend session terminate (names the workstation)
  R2/G  SAPMHTTP auto logout        -> HTTP/Fiori idle auto-logout (EXPECTED, names user IP)
  R4/9,R5/A RfcHand CPIC-Er         -> RFC/CPIC channel error (the integration RFC channel)
  BY/M  dbsh                        -> DB library connection reset (SAP<->SQL Server)
  E0/A  HQ-ORION ...                -> ORION EAI app error (integration, app-level not TCP)
  E0/A  DBSQL_*_ERROR               -> batch SQL error (e.g. RFFMAVC_OVERALL_VIEW)

So a 10054 in Q0/DP is a benign end-user GUI disconnect; a 10054 in BY/dbsh is a real
SAP<->SQL Server reset. Counting raw "10054" conflates them. This decoder separates them.

Run:  python process_mining/parse_syslog.py
"""
import sqlite3, re, json, datetime
from collections import Counter, defaultdict

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gold_ref import GOLD  # T5: resolved via golden_manifest.json, not a hardcoded path


def _grp(pat, s, g=1):
    m = re.search(pat, s)
    return m.group(g) if m else ""


def decode(cd):
    """Decode one CENTDATA string into structured fields."""
    b = cd[32:]
    return {
        "len_class": cd[0:1], "area": cd[1:3], "subid": cd[3:4],
        "ts": cd[4:18], "wp": cd[30:32].strip(), "body": b,
        # error number (recv<errno>, WSASend<errno>, or bare 1005x in dbsh)
        "errno": _grp(r"(?:recv|WSASend)(\d{3,5})", b) or _grp(r"(10054|10053|10060)", b),
        # user (ABAP user token), program (SAPM*/RFFM*/RS*), client IP
        "user": _grp(r"([A-Z](?:_[A-Z]+|[A-Z0-9])[A-Z0-9_\-]{2,11})", b),
        "program": _grp(r"((?:SAPM|RFFM|RS|RE_)[A-Z0-9_]+)", b),
        "ip": _grp(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\d{1,3}\.\d{1,3}\.\d)", b),
    }


def classify(area, subid, wp, body):
    bl = body
    if area == "Q0" and subid == "I" and ("recv" in bl or "WSASend" in bl):
        return "frontend_DIAG_reset"        # SAP GUI native socket reset (end-user PC)
    if area == "Q0" and subid == "4" and "dpTermin" in bl:
        return "frontend_session_term"      # dispatcher terminates a GUI session
    if area == "R2" and "HTTP plugin auto logout" in bl:
        return "http_idle_logout"           # Fiori/WebGUI idle auto-logout (expected)
    if area in ("R4", "R5") and "CPIC" in bl:
        return "rfc_cpic_error"             # RFC/CPIC channel error (integration RFC)
    if area == "BY" and "dbsh" in bl:
        return "db_connection_reset"        # SAP<->SQL Server DB library reset
    if "HQ-ORION" in bl:
        return "orion_app_error"            # ORION EAI app-level error
    if "DBSQL" in bl:
        return "batch_sql_error"            # SQL error inside a batch program
    if area == "E0":
        return "app_error"
    return "other"


def main():
    db = sqlite3.connect(GOLD)
    rows = db.execute("SELECT TS, AREA, SUBID, CENTDATA FROM sm21_syslog_history").fetchall()
    by_chan = Counter()
    chan_hour = defaultdict(Counter)
    chan_dow = defaultdict(Counter)
    chan_host = defaultdict(Counter)
    err_by_chan = defaultdict(Counter)
    for ts, area, subid, cd in rows:
        d = decode(cd)
        chan = classify(area, subid, d["wp"], d["body"])
        by_chan[chan] += 1
        try:
            dt = datetime.date(int(ts[:4]), int(ts[4:6]), int(ts[6:8]))
            chan_hour[chan][int(ts[8:10])] += 1
            chan_dow[chan][dt.strftime("%a")] += 1
        except Exception:
            pass
        if d["errno"]:
            err_by_chan[chan][d["errno"]] += 1
        host = d["ip"] or d["user"]
        if host:
            chan_host[chan][host] += 1

    print(f"=== {len(rows):,} syslog rows -> channel classification ===")
    for chan, n in by_chan.most_common():
        errs = ",".join(f"{e}x{c}" for e, c in err_by_chan[chan].most_common(3))
        print(f"  {n:>5}  {chan:<22} {('['+errs+']') if errs else ''}")

    # where 10054 actually lands
    print("\n=== '10054' by channel (the headline correction) ===")
    for chan, ec in err_by_chan.items():
        if ec.get("10054"):
            print(f"  {ec['10054']:>4}  {chan}")

    # business-hours / weekday signature per frontend channel
    for chan in ("frontend_DIAG_reset", "db_connection_reset", "rfc_cpic_error"):
        h = chan_hour.get(chan, {})
        tot = sum(h.values())
        if not tot:
            continue
        biz = sum(h.get(x, 0) for x in range(6, 20))
        wk = chan_dow.get(chan, {})
        wend = wk.get("Sat", 0) + wk.get("Sun", 0)
        print(f"\n=== {chan}: n={tot} | business 06-19h={100*biz/tot:.0f}% | "
              f"weekend share={100*wend/tot:.0f}% (Sat={wk.get('Sat',0)},Sun={wk.get('Sun',0)}) ===")

    summary = {"generated": None, "total_rows": len(rows),
               "by_channel": dict(by_chan),
               "10054_by_channel": {c: ec["10054"] for c, ec in err_by_chan.items() if ec.get("10054")}}
    with open("process_mining/syslog_parsed_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\nwrote process_mining/syslog_parsed_summary.json")
    db.close()


if __name__ == "__main__":
    main()
