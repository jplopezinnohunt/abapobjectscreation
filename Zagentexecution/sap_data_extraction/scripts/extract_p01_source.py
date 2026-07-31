"""extract_p01_source.py — read the source that is ACTUALLY VALID, from production (s097).

**The rule said "data from P01, code from D01", and that was answering a different
question.** D01 is where code is *developed*; it is not evidence of what *runs*. Package
ZPBC holds 114 objects in D01 and 77 in P01 — a third of it never reached production,
including sixteen transactions. Any conclusion about production behaviour drawn from D01
source is an inference, and it would have overstated the footprint by 32%.

The user put it plainly: *"deberíamos leer entonces el código directo de P01 para saber qué
está válido"*. Correct — so the question became whether P01 *can* be read, and it can:

    RFC_READ_REPORT     FU_NOT_FOUND        not RFC-enabled here
    RPY_CLASS_READ      FU_NOT_FOUND        not RFC-enabled here
    SEO_CLASS_READ      NOT_FOUND           callable, but class source is not here
    RPY_PROGRAM_READ    WORKS               <- this one

**This is a READ.** It calls nothing that modifies anything, and it does not touch ADT. The
write discipline (no ADT against production, no transports in P01, own Z*/Y* objects only)
is about CHANGES; reading what is active is how you check a claim rather than assume it.

**Classes need the pool trick.** A class has no program of its own: its source lives in the
generated pool `<CLASSNAME>` padded to 30 characters with `=` then `CP`, whose include list
carries one `...CM<xx>` include per method. Reading the pool alone returns 25 lines of
skeleton; the implementations are in the includes — 1,004 lines for
`ZCL_IM__UNESCO_ENCUMB`, which the skeleton would have reported as almost empty.

Writes into `extracted_sap_p01/` — kept SEPARATE from the D01 corpus on purpose. Merging
them would destroy the only distinction that matters here: what is deployed versus what
merely exists.

Run: python Zagentexecution/sap_data_extraction/scripts/extract_p01_source.py [PACKAGE]
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

OUT = REPO / "extracted_sap_p01"


def pool_name(cls):
    """The generated class pool: name padded to 30 with '=', then CP."""
    return cls.ljust(30, "=") + "CP"


def read_program(conn, name):
    """Source lines of a program, or []. Never raises."""
    try:
        r = conn.call("RPY_PROGRAM_READ", PROGRAM_NAME=name, ONLY_SOURCE="X")
        return [x.get("LINE", "") for x in (r.get("SOURCE_EXTENDED") or [])]
    except Exception:                                             # noqa: BLE001
        return []


def read_class(conn, cls):
    """Full class source: the pool skeleton PLUS every method include.

    The pool alone is ~25 lines of declaration. Reporting that as the class would make a
    1,000-line implementation look empty — which is exactly the kind of confident-and-wrong
    this repository keeps paying for.
    """
    try:
        r = conn.call("RPY_PROGRAM_READ", PROGRAM_NAME=pool_name(cls),
                      WITH_INCLUDELIST="X", ONLY_SOURCE="")
    except Exception:                                             # noqa: BLE001
        return None
    parts = [f"* ==== CLASS POOL {cls} ===="]
    parts += [x.get("LINE", "") for x in (r.get("SOURCE_EXTENDED") or [])]
    for inc in (r.get("INCLUDE_TAB") or []):
        name = inc.get("INCLNAME", "")
        if name[30:32] not in ("CM", "CU", "CO", "CI"):   # methods, macros, definitions
            continue
        lines = read_program(conn, name)
        if lines:
            parts.append(f"\n* ---- {name} ----")
            parts += lines
    return "\n".join(parts)


def main():
    package = sys.argv[1] if len(sys.argv) > 1 else "ZPBC"
    conn = get_connection("P01")
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
                  FIELDS=[{"FIELDNAME": "OBJECT"}, {"FIELDNAME": "OBJ_NAME"}],
                  OPTIONS=[{"TEXT": f"DEVCLASS = '{package}'"}], ROWCOUNT=500)
    objs = [tuple(x["WA"].split("|")) for x in r["DATA"]]
    objs = [(a.strip(), b.strip()) for a, b in objs]

    dest = OUT / package
    dest.mkdir(parents=True, exist_ok=True)
    got, empty = 0, []
    for kind, name in objs:
        if kind == "CLAS":
            src = read_class(conn, name)
        elif kind in ("PROG", "FUGR"):
            src = "\n".join(read_program(conn, name)) or None
        else:
            continue
        if not src or len(src.splitlines()) < 3:
            empty.append(f"{kind}:{name}")
            continue
        (dest / f"{name}.abap").write_text(src, encoding="utf-8")
        got += 1
        print(f"  {kind} {name:38s} {len(src.splitlines()):>5} lines")

    conn.close()
    print(f"\n{got} objects written to {dest}")
    if empty:
        # Say what came back empty. Silence here would read as "the package is small".
        print(f"  {len(empty)} returned no readable source: {', '.join(empty[:8])}")
    print("  SOURCE OF TRUTH: this is what is ACTIVE IN PRODUCTION. The D01 corpus is what "
          "exists in development — they are different questions and are stored apart.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
