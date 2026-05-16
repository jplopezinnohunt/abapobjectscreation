"""Locate the UltmtCdtr/Nm node in D01 /CITI/XML/UNESCO/DC_V3_01 tree
and identify the exit FM / BAdI handler wired to it.
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

TREE = '/CITI/XML/UNESCO/DC_V3_01'

# 1. Find UltmtCdtr parent + Nm child nodes
print(f"\n=== Tree: {TREE} ===")
print("\n--- Search for nodes named 'UltmtCdtr' or 'Nm' under UltmtCdtr ---")

# DMEE_TREE_NODE narrow read
try:
    # All nodes with TECH_NAME = 'UltmtCdtr' or 'Nm'
    a = rd("DMEE_TREE_NODE",
           [f"TREE_ID = '{TREE}'", "AND VERSION = '000'"],
           ["NODE_ID","NODE_TYPE","TECH_NAME","REF_ID","PARENT","NEXT_NODE"], n=2000)
    print(f"  Total nodes: {len(a)}")

    # Find UltmtCdtr parent + Nm children
    ultmt_nodes = [n for n in a if n['TECH_NAME'].strip() == 'UltmtCdtr']
    nm_nodes = [n for n in a if n['TECH_NAME'].strip() == 'Nm']
    print(f"  UltmtCdtr nodes: {len(ultmt_nodes)}")
    for u in ultmt_nodes:
        print(f"    UltmtCdtr NODE_ID={u['NODE_ID']} NODE_TYPE={u['NODE_TYPE']}")
    print(f"  Nm nodes total: {len(nm_nodes)}")

    # For each Nm node, walk up parents to determine which is under UltmtCdtr
    node_by_id = {n['NODE_ID'].strip(): n for n in a}

    def ancestors(nid, depth=10):
        result = []
        for _ in range(depth):
            n = node_by_id.get(nid)
            if not n: break
            parent = n.get('PARENT','').strip()
            if not parent or parent == nid: break
            p = node_by_id.get(parent)
            if p:
                result.append(p['TECH_NAME'].strip())
            nid = parent
        return result

    for n in nm_nodes:
        anc = ancestors(n['NODE_ID'].strip())
        if 'UltmtCdtr' in anc:
            print(f"\n  ★ Nm under UltmtCdtr: NODE_ID={n['NODE_ID']} TECH={n['TECH_NAME']} REF_ID={n['REF_ID']}")
            print(f"      ancestor chain: {anc}")
except Exception as e:
    print(f"  err1: {e}")

# 2. Get MP_EXIT_FUNC for those Nm nodes
print(f"\n--- Get MP_EXIT_FUNC for candidate Nm nodes ---")
try:
    b = rd("DMEE_TREE_NODE",
           [f"TREE_ID = '{TREE}'", "AND VERSION = '000'"],
           ["NODE_ID","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD","MP_OFFSET","MP_LENGTH"], n=2000)
    by_id = {r['NODE_ID'].strip(): r for r in b}
    # For Nm nodes under UltmtCdtr (found above)
    for n in nm_nodes:
        anc = ancestors(n['NODE_ID'].strip())
        if 'UltmtCdtr' in anc:
            m = by_id.get(n['NODE_ID'].strip(), {})
            print(f"  NODE_ID={n['NODE_ID']} EXIT_FUNC='{m.get('MP_EXIT_FUNC','').strip()}' MP_SC_TAB={m.get('MP_SC_TAB','').strip()} MP_SC_FLD={m.get('MP_SC_FLD','').strip()} OFF={m.get('MP_OFFSET','').strip()} LEN={m.get('MP_LENGTH','').strip()}")
except Exception as e:
    print(f"  err2: {e}")

# 3. Also: Cdtr/Nm and InitgPty/Nm for completeness (other Nm nodes in tree)
print(f"\n--- All Nm nodes in {TREE} (for context) ---")
try:
    for n in nm_nodes:
        anc = ancestors(n['NODE_ID'].strip())
        m = by_id.get(n['NODE_ID'].strip(), {})
        parent_name = anc[0] if anc else '?'
        chain = ' / '.join(reversed(anc))
        ef = m.get('MP_EXIT_FUNC','').strip()
        tab = m.get('MP_SC_TAB','').strip()
        fld = m.get('MP_SC_FLD','').strip()
        print(f"  NODE_ID={n['NODE_ID']} parent={parent_name:15s} chain=[{chain}]  EXIT='{ef}' TAB={tab} FLD={fld}")
except Exception as e:
    print(f"  err3: {e}")
