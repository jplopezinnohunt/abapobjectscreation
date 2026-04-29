"""
Pure-Python pain.001 simulator for V000 vs V001 comparison.

Approach: template-based renderer per tree, filled with real REGUH+REGUP+LFA1+ADRC
data from Gold DB. V001 transformer applies the scope-of-project structured-address
changes per Marlies Excel + N_MENARD specs.

Architecture:
  Real P01 data (Gold DB)  →  V000 template render  →  XSD validate
                          ↓
                          V001 transformer (insert structured PstlAdr)
                          ↓
                          V001 XML  →  XSD validate (.03 + .09)
                          ↓
                          V000 vs V001 byte-diff
"""
import sqlite3, json, sys, os, re
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree as ET

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
XSD_DIR = Path('Zagentexecution/incidents/xml_payment_structured_address/xsd_validators')
OUT = Path('Zagentexecution/incidents/xml_payment_structured_address/simulator_output')
OUT.mkdir(parents=True, exist_ok=True)


# ------------ Templates per tree ---------------

def template_sepa_v000(scenario, vendor, addr, regup, t015l, ppc_struc, ppc_tag):
    """SEPA tree V000: Hybrid (Ctry + AdrLine, no full structured)."""
    cdtr_name = escape_xml(safe(vendor.get('NAME1'), 'Vendor')[:35])
    cdtr_ctry = safe(vendor.get('LAND1'), 'FR')
    if len(cdtr_ctry) != 2:
        cdtr_ctry = 'FR'
    cdtr_street = escape_xml(safe(addr.get('STREET'), 'Street'))
    cdtr_city = escape_xml(safe(addr.get('CITY1'), 'City'))
    cdtr_postcode = safe(addr.get('POST_CODE1'), '00000')
    pmtinfid = (safe(scenario.get('LAUFD'),'20251015') + safe(scenario.get('LAUFI'),'X1'))[:35]
    rwbtr = fmt_amount(scenario.get('RWBTR'))
    waers = safe(scenario.get('cur'), 'EUR')[:3] or 'EUR'
    end2end = safe(regup.get('XBLNR'), pmtinfid)[:35] or pmtinfid
    bic = 'SOGEFRPP'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>UNES{pmtinfid}</MsgId>
      <CreDtTm>2026-04-29T12:00:00</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>{rwbtr}</CtrlSum>
      <InitgPty>
        <Nm>UNESCO</Nm>
      </InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>{pmtinfid}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>{rwbtr}</CtrlSum>
      <PmtTpInf>
        <SvcLvl><Cd>SEPA</Cd></SvcLvl>
      </PmtTpInf>
      <ReqdExctnDt>2026-04-29</ReqdExctnDt>
      <Dbtr>
        <Nm>UNESCO</Nm>
        <PstlAdr>
          <Ctry>FR</Ctry>
          <AdrLine>7 PLACE DE FONTENOY</AdrLine>
          <AdrLine>75007 PARIS</AdrLine>
        </PstlAdr>
      </Dbtr>
      <DbtrAcct><Id><IBAN>FR7630003000040003000123456</IBAN></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BIC>{bic}</BIC></FinInstnId></DbtrAgt>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>{end2end}</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="{waers}">{rwbtr}</InstdAmt></Amt>
        <CdtrAgt><FinInstnId><BIC>BANKBIC1</BIC></FinInstnId></CdtrAgt>
        <Cdtr>
          <Nm>{cdtr_name}</Nm>
          <PstlAdr>
            <Ctry>{cdtr_ctry}</Ctry>
            <AdrLine>{cdtr_street}</AdrLine>
            <AdrLine>{cdtr_postcode} {cdtr_city}</AdrLine>
          </PstlAdr>
        </Cdtr>
        <CdtrAcct><Id><IBAN>DE89370400440532013000</IBAN></Id></CdtrAcct>
        <RmtInf><Ustrd>UNESCO PAYMENT {end2end}</Ustrd></RmtInf>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""


def template_citi_v000(scenario, vendor, addr, regup, t015l, ppc_struc, ppc_tag):
    """CITI tree V000: Dbtr UNSTRUCTURED (no Ctry!), Cdtr structured (per N_MENARD)."""
    cdtr_name = escape_xml(safe(vendor.get('NAME1'), 'Vendor')[:35])
    cdtr_ctry = safe(vendor.get('LAND1'), 'US')
    if len(cdtr_ctry) != 2:
        cdtr_ctry = 'US'
    cdtr_street = escape_xml(safe(addr.get('STREET'), 'Street'))
    cdtr_city = escape_xml(safe(addr.get('CITY1'), 'City'))
    cdtr_postcode = safe(addr.get('POST_CODE1'), '00000')
    cdtr_houseno = escape_xml(safe(addr.get('HOUSE_NUM1'), '1'))
    pmtinfid = (safe(scenario.get('LAUFD'),'20251015') + safe(scenario.get('LAUFI'),'X1'))[:35]
    rwbtr = fmt_amount(scenario.get('RWBTR'))
    waers = safe(scenario.get('cur'), 'USD')[:3] or 'USD'
    end2end = safe(regup.get('XBLNR'), pmtinfid)[:35] or pmtinfid

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>UNES{pmtinfid}</MsgId>
      <CreDtTm>2026-04-29T12:00:00</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>{rwbtr}</CtrlSum>
      <InitgPty>
        <Nm>UNESCO</Nm>
      </InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>{pmtinfid}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>{rwbtr}</CtrlSum>
      <PmtTpInf>
        <SvcLvl><Cd>NURG</Cd></SvcLvl>
      </PmtTpInf>
      <ReqdExctnDt>2026-04-29</ReqdExctnDt>
      <Dbtr>
        <Nm>UNESCO</Nm>
        <PstlAdr>
          <AdrLine>UNESCO 7 PLACE DE FONTENOY</AdrLine>
          <AdrLine>75007 PARIS</AdrLine>
        </PstlAdr>
      </Dbtr>
      <DbtrAcct><Id><Othr><Id>123456789</Id></Othr></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BIC>CITIUS33</BIC></FinInstnId></DbtrAgt>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>{end2end}</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="{waers}">{rwbtr}</InstdAmt></Amt>
        <CdtrAgt><FinInstnId><BIC>BANKBIC1</BIC></FinInstnId></CdtrAgt>
        <Cdtr>
          <Nm>{cdtr_name}</Nm>
          <PstlAdr>
            <StrtNm>{cdtr_street}</StrtNm>
            <BldgNb>{cdtr_houseno}</BldgNb>
            <PstCd>{cdtr_postcode}</PstCd>
            <TwnNm>{cdtr_city}</TwnNm>
            <Ctry>{cdtr_ctry}</Ctry>
          </PstlAdr>
        </Cdtr>
        <CdtrAcct><Id><Othr><Id>987654321</Id></Othr></Id></CdtrAcct>
        <RmtInf><Ustrd>UNESCO PAYMENT</Ustrd></RmtInf>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""


def template_cgi_v000(scenario, vendor, addr, regup, t015l, ppc_struc, ppc_tag):
    """CGI tree V000: Dbtr+Cdtr structured ✅, CdtrAgt UNSTRUCTURED."""
    cdtr_name = escape_xml(safe(vendor.get('NAME1'), 'Vendor')[:35])
    cdtr_ctry = safe(vendor.get('LAND1'), 'XX')
    if len(cdtr_ctry) != 2:
        cdtr_ctry = 'XX'
    cdtr_street = escape_xml(safe(addr.get('STREET'), 'Street'))
    cdtr_city = escape_xml(safe(addr.get('CITY1'), 'City'))
    cdtr_postcode = safe(addr.get('POST_CODE1'), '00000')
    cdtr_houseno = escape_xml(safe(addr.get('HOUSE_NUM1'), '1'))
    pmtinfid = (safe(scenario.get('LAUFD'),'20251015') + safe(scenario.get('LAUFI'),'X1'))[:35]
    rwbtr = fmt_amount(scenario.get('RWBTR'))
    waers = safe(scenario.get('cur'), 'USD')[:3] or 'USD'
    end2end = safe(regup.get('XBLNR'), pmtinfid)[:35] or pmtinfid

    # PPC tag content (only for 9 PPC countries)
    ppc_countries = {'AE','BH','CN','ID','IN','JO','MA','MY','PH'}
    instr_inf_xml = ''
    rmt_xml = ''
    if cdtr_ctry in ppc_countries:
        from ppc_predictor_and_validator import predict_ppc_tag
        lzbkz = regup.get('LZBKZ', '')
        pay_type = scenario.get('pay_type', 'O')
        # InstrInf for AE/CN
        if cdtr_ctry in ('AE', 'CN'):
            tag_full = '<PmtInf><CdtTrfTxInf><InstrForCdtrAgt><InstrInf>'
            value, _ = predict_ppc_tag(cdtr_ctry, lzbkz, pay_type, tag_full, t015l, ppc_struc)
            if value:
                # Replace runtime placeholder
                value = value.replace('<XBLNR>', regup.get('XBLNR', '')).strip()
                instr_inf_xml = f'\n        <InstrForCdtrAgt><InstrInf>{escape_xml(value)}</InstrInf></InstrForCdtrAgt>'
        # Ustrd for BH/ID/IN/JO/MA/MY/PH
        elif cdtr_ctry in ('BH','ID','IN','JO','MA','MY','PH'):
            tag_full = '<PmtInf><CdtTrfTxInf><RmtInf><Ustrd>'
            value, _ = predict_ppc_tag(cdtr_ctry, lzbkz, pay_type, tag_full, t015l, ppc_struc)
            if value:
                value = value.replace('<XBLNR>', regup.get('XBLNR', '')).strip()
                rmt_xml = f'\n        <RmtInf><Ustrd>{escape_xml(value)}</Ustrd></RmtInf>'

    if not rmt_xml:
        rmt_xml = '\n        <RmtInf><Ustrd>UNESCO PAYMENT</Ustrd></RmtInf>'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>UNES{pmtinfid}</MsgId>
      <CreDtTm>2026-04-29T12:00:00</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>{rwbtr}</CtrlSum>
      <InitgPty><Nm>UNESCO</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>{pmtinfid}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>{rwbtr}</CtrlSum>
      <PmtTpInf><SvcLvl><Cd>NURG</Cd></SvcLvl></PmtTpInf>
      <ReqdExctnDt>2026-04-29</ReqdExctnDt>
      <Dbtr>
        <Nm>UNESCO</Nm>
        <PstlAdr>
          <StrtNm>7 PLACE DE FONTENOY</StrtNm>
          <PstCd>75007</PstCd>
          <TwnNm>PARIS</TwnNm>
          <Ctry>FR</Ctry>
        </PstlAdr>
      </Dbtr>
      <DbtrAcct><Id><Othr><Id>123456789</Id></Othr></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BIC>SOGEFRPP</BIC></FinInstnId></DbtrAgt>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>{end2end}</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="{waers}">{rwbtr}</InstdAmt></Amt>{instr_inf_xml}
        <CdtrAgt>
          <FinInstnId>
            <Nm>BANK NAME UNSTRUCTURED</Nm>
            <PstlAdr>
              <Ctry>{cdtr_ctry}</Ctry>
              <AdrLine>BANK ADDRESS LINE 1</AdrLine>
              <AdrLine>BANK ADDRESS LINE 2</AdrLine>
            </PstlAdr>
          </FinInstnId>
        </CdtrAgt>
        <Cdtr>
          <Nm>{cdtr_name}</Nm>
          <PstlAdr>
            <StrtNm>{cdtr_street}</StrtNm>
            <BldgNb>{cdtr_houseno}</BldgNb>
            <PstCd>{cdtr_postcode}</PstCd>
            <TwnNm>{cdtr_city}</TwnNm>
            <Ctry>{cdtr_ctry}</Ctry>
          </PstlAdr>
        </Cdtr>
        <CdtrAcct><Id><Othr><Id>987654321</Id></Othr></Id></CdtrAcct>{rmt_xml}
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""


# ------------ V001 Transformer ---------------

def transform_to_v001(xml_str, tree):
    """Apply V001 changes per tree (per Marlies Excel + N_MENARD spec)."""
    from lxml import etree
    NS = '{urn:iso:std:iso:20022:tech:xsd:pain.001.001.03}'
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml_str.encode(), parser)

    if tree == 'SEPA':
        # SEPA V001: replace Hybrid with full structured
        # Find all PstlAdr nodes (Dbtr + Cdtr)
        for pstl in root.iter(NS + 'PstlAdr'):
            ctry_elem = pstl.find(NS + 'Ctry')
            adrlines = pstl.findall(NS + 'AdrLine')
            if ctry_elem is None or not adrlines:
                continue
            # Parse address from AdrLines (heuristic: line 1 = street, line 2 = postcode + city)
            street = adrlines[0].text if len(adrlines) >= 1 else ''
            postcode_city = adrlines[1].text if len(adrlines) >= 2 else ''
            # Try to extract postcode (first 5 digits) and city
            m = re.match(r'^(\d{4,6})\s+(.+)$', postcode_city or '')
            if m:
                postcode, city = m.group(1), m.group(2)
            else:
                postcode, city = '', postcode_city or ''
            # Insert structured nodes BEFORE Ctry
            ctry_idx = list(pstl).index(ctry_elem)
            new_strtnm = etree.SubElement(pstl, NS + 'StrtNm')
            new_strtnm.text = street
            new_pstcd = etree.SubElement(pstl, NS + 'PstCd')
            new_pstcd.text = postcode
            new_twnnm = etree.SubElement(pstl, NS + 'TwnNm')
            new_twnnm.text = city
            # Move them before Ctry
            for new_elem in [new_strtnm, new_pstcd, new_twnnm]:
                pstl.remove(new_elem)
                pstl.insert(ctry_idx, new_elem)
                ctry_idx += 1
            # Remove AdrLines
            for ad in adrlines:
                pstl.remove(ad)

    elif tree == 'CITI':
        # CITI V001: fix Dbtr — add Ctry + restructure
        for pmt_inf in root.iter(NS + 'PmtInf'):
            dbtr = pmt_inf.find(NS + 'Dbtr')
            if dbtr is None: continue
            pstl = dbtr.find(NS + 'PstlAdr')
            if pstl is None: continue
            # Replace AdrLines with structured
            adrlines = pstl.findall(NS + 'AdrLine')
            if adrlines:
                for ad in adrlines:
                    pstl.remove(ad)
                # Add structured Dbtr address
                etree.SubElement(pstl, NS + 'StrtNm').text = '7 PLACE DE FONTENOY'
                etree.SubElement(pstl, NS + 'PstCd').text = '75007'
                etree.SubElement(pstl, NS + 'TwnNm').text = 'PARIS'
                etree.SubElement(pstl, NS + 'Ctry').text = 'FR'

    elif tree == 'CGI':
        # CGI V001: fix CdtrAgt — restructure
        for cdtr_agt in root.iter(NS + 'CdtrAgt'):
            fin_inst = cdtr_agt.find(NS + 'FinInstnId')
            if fin_inst is None: continue
            pstl = fin_inst.find(NS + 'PstlAdr')
            if pstl is None: continue
            adrlines = pstl.findall(NS + 'AdrLine')
            ctry_elem = pstl.find(NS + 'Ctry')
            if adrlines:
                for ad in adrlines:
                    pstl.remove(ad)
                # Add structured (using sample data)
                if ctry_elem is not None:
                    ctry_idx = list(pstl).index(ctry_elem)
                else:
                    ctry_idx = len(list(pstl))
                strtnm = etree.SubElement(pstl, NS + 'StrtNm')
                strtnm.text = 'BANK STREET'
                pstcd = etree.SubElement(pstl, NS + 'PstCd')
                pstcd.text = '00000'
                twnnm = etree.SubElement(pstl, NS + 'TwnNm')
                twnnm.text = 'BANK CITY'
                # Move to before Ctry
                for new_elem in [strtnm, pstcd, twnnm]:
                    pstl.remove(new_elem)
                    pstl.insert(ctry_idx, new_elem)
                    ctry_idx += 1

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()


# ------------ XSD Validation ---------------

def validate_xsd(xml_str, xsd_path):
    from lxml import etree
    try:
        with open(xsd_path, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
        # Translate namespace if XSD is .09 (CBPR+) — our V001 templates use .03
        if 'pain.001.001.09' in str(xsd_path):
            xml_str = xml_str.replace('pain.001.001.03', 'pain.001.001.09')
            # ReqdExctnDt changed in .09: now complex type with <Dt> sub-element
            xml_str = re.sub(r'<ReqdExctnDt>(\d{4}-\d{2}-\d{2})</ReqdExctnDt>',
                             r'<ReqdExctnDt><Dt>\1</Dt></ReqdExctnDt>', xml_str)
            # BIC -> BICFI in .09
            xml_str = xml_str.replace('<BIC>', '<BICFI>').replace('</BIC>', '</BICFI>')
        doc = etree.fromstring(xml_str.encode())
        if schema.validate(doc):
            return (True, 'OK')
        return (False, str(schema.error_log)[:200])
    except etree.XMLSyntaxError as e:
        return (False, f'XML syntax: {e}')
    except Exception as e:
        return (False, f'Error: {str(e)[:150]}')


# ------------ Helpers ---------------

def escape_xml(s):
    if s is None:
        return ''
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')


def fmt_amount(s):
    """Convert SAP amount '14678.62-' -> '14678.62' (we use absolute value for V001 sim)."""
    if not s: return '100.00'
    s = str(s).strip()
    if s.endswith('-'):
        s = s[:-1]
    if s.startswith('-'):
        s = s[1:]
    if '.' not in s:
        s = s + '.00'
    try:
        return f'{float(s):.2f}'
    except: return '100.00'


def safe(s, default=''):
    """Strip + return default if empty/None."""
    if s is None: return default
    s = str(s).strip()
    return s if s else default


def diff_lines(a, b):
    """Simple line-based diff."""
    import difflib
    diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=''))
    return '\n'.join(diff[:50])


# ------------ Main ---------------

def main():
    print('=== Pure Python pain.001 V000/V001 simulator ===')

    # Load Gold DB resources
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Load PPC config
    cur.execute('SELECT LZBKZ, ZWCK1 FROM T015L WHERE ZWCK1 IS NOT NULL')
    t015l = [{'LZBKZ': r[0], 'ZWCK1': r[1]} for r in cur.fetchall()]
    cur.execute('SELECT LAND1, TAG_ID, PAY_TYPE, CODE_ORD, PPC_CODE, PPC_VALUE, PAY_STRUC, PAY_FIELD FROM YTFI_PPC_STRUC')
    ppc_struc_raw = [{'LAND1': r[0], 'TAG_ID': r[1], 'PAY_TYPE': r[2], 'CODE_ORD': r[3],
                      'PPC_CODE': r[4], 'PPC_VALUE': r[5], 'PAY_STRUC': r[6], 'PAY_FIELD': r[7]}
                     for r in cur.fetchall()]
    cur.execute('SELECT LAND1, TAG_ID, DEB_CRE, TAG_FULL FROM YTFI_PPC_TAG')
    ppc_tag = [{'LAND1': r[0], 'TAG_ID': r[1], 'DEB_CRE': r[2], 'TAG_FULL': r[3]}
               for r in cur.fetchall()]
    # Inject TAG_FULL into ppc_struc
    tag_full_lookup = {(r['LAND1'], r['TAG_ID']): r['TAG_FULL'] for r in ppc_tag}
    for s in ppc_struc_raw:
        s['TAG_FULL'] = tag_full_lookup.get((s['LAND1'], s['TAG_ID']), '')
        s['DEB_CRE'] = 'C'

    # Load scenario samples
    cur.execute('SELECT * FROM SCENARIO_SAMPLES')
    cols = [d[0] for d in cur.description]
    samples = [dict(zip(cols, r)) for r in cur.fetchall()]
    print(f'  Samples: {len(samples)}')

    # Load REGUP for samples (LZBKZ + XBLNR)
    cur.execute('SELECT LAUFD, LAUFI, ZBUKR, LIFNR, LZBKZ, XBLNR FROM REGUP_SCENARIOS WHERE LZBKZ != ""')
    regup_lookup = {}
    for r in cur.fetchall():
        key = (r[0], r[1], r[2], r[3])
        if key not in regup_lookup:
            regup_lookup[key] = {'LZBKZ': r[4], 'XBLNR': r[5]}

    # Load LFA1+ADRC for vendors
    lifnrs = list(set(s.get('LIFNR') for s in samples if s.get('LIFNR')))
    placeholders = ','.join('?' * len(lifnrs))
    cur.execute(f'SELECT LIFNR, NAME1, LAND1, ADRNR FROM LFA1 WHERE LIFNR IN ({placeholders})', lifnrs)
    vendor_lookup = {r[0]: {'NAME1': r[1], 'LAND1': r[2], 'ADRNR': r[3]} for r in cur.fetchall()}
    adrnrs = [v['ADRNR'] for v in vendor_lookup.values() if v.get('ADRNR')]
    if adrnrs:
        ph2 = ','.join('?' * len(adrnrs))
        cur.execute(f'SELECT ADDRNUMBER, STREET, HOUSE_NUM1, POST_CODE1, CITY1, COUNTRY FROM ADRC WHERE ADDRNUMBER IN ({ph2})', adrnrs)
        addr_lookup = {r[0]: {'STREET': r[1], 'HOUSE_NUM1': r[2], 'POST_CODE1': r[3], 'CITY1': r[4], 'COUNTRY': r[5]} for r in cur.fetchall()}
    else:
        addr_lookup = {}
    con.close()

    # Map tree → renderer + V001 tag
    target_trees = {
        '/SEPA_CT_UNES': ('SEPA', template_sepa_v000),
        '/CITI/XML/UNESCO/DC_V3_01': ('CITI', template_citi_v000),
        '/CGI_XML_CT_UNESCO': ('CGI', template_cgi_v000),
        '/CGI_XML_CT_UNESCO_1': ('CGI', template_cgi_v000),
    }

    # Run simulator on samples
    results = []
    samples_saved_per_tree = {'SEPA': 0, 'CITI': 0, 'CGI': 0}
    for s in samples:
        tree = s.get('tree')
        if tree not in target_trees:
            continue
        tree_short, renderer = target_trees[tree]

        vendor = vendor_lookup.get(s.get('LIFNR'), {'NAME1': 'Vendor', 'LAND1': s.get('LAND1') or 'XX'})
        addr_id = vendor.get('ADRNR')
        addr = addr_lookup.get(addr_id, {'STREET': 'NoStreet', 'CITY1': 'NoCity', 'POST_CODE1': '00000', 'COUNTRY': vendor.get('LAND1') or 'XX'})

        regup = regup_lookup.get((s.get('LAUFD'), s.get('LAUFI'), s.get('ZBUKR'), s.get('LIFNR')), {'LZBKZ': '', 'XBLNR': ''})

        # Inject vendor.LAND1 into scenario for predictor
        s_aug = dict(s)
        s_aug['LAND1'] = vendor.get('LAND1') or 'XX'

        # V000
        v000 = renderer(s_aug, vendor, addr, regup, t015l, ppc_struc_raw, ppc_tag)
        v000_valid_03, v000_err_03 = validate_xsd(v000, XSD_DIR / 'pain.001.001.03.xsd')

        # V001
        try:
            v001 = transform_to_v001(v000, tree_short)
            v001_valid_03, v001_err_03 = validate_xsd(v001, XSD_DIR / 'pain.001.001.03.xsd')
            v001_valid_09, v001_err_09 = validate_xsd(v001, XSD_DIR / 'pain.001.001.09.xsd')
        except Exception as e:
            v001 = ''
            v001_valid_03, v001_err_03 = False, f'Transform error: {e}'
            v001_valid_09, v001_err_09 = False, ''

        results.append({
            'scenario_id': s.get('scenario_id'),
            'tree': tree,
            'tree_short': tree_short,
            'co': s.get('co'),
            'vendor_country': vendor.get('LAND1'),
            'pay_type': s.get('pay_type'),
            'lifnr': s.get('LIFNR'),
            'lzbkz': regup.get('LZBKZ', ''),
            'v000_xsd_03_valid': v000_valid_03,
            'v000_xsd_03_err': v000_err_03 if not v000_valid_03 else None,
            'v001_xsd_03_valid': v001_valid_03,
            'v001_xsd_03_err': v001_err_03 if not v001_valid_03 else None,
            'v001_xsd_09_valid': v001_valid_09,
            'v001_xsd_09_err': v001_err_09 if not v001_valid_09 else None,
        })

        # Save first 5 V000+V001 XML pairs per tree for inspection
        if samples_saved_per_tree[tree_short] < 5:
            sub_dir = OUT / tree_short
            sub_dir.mkdir(parents=True, exist_ok=True)
            i = samples_saved_per_tree[tree_short]
            with open(sub_dir / f'sample_{i+1}_{s["LIFNR"]}_V000.xml', 'w', encoding='utf-8') as f:
                f.write(v000)
            if v001:
                with open(sub_dir / f'sample_{i+1}_{s["LIFNR"]}_V001.xml', 'w', encoding='utf-8') as f:
                    f.write(v001)
            samples_saved_per_tree[tree_short] += 1

    # Aggregate
    by_tree = {}
    for r in results:
        t = r['tree_short']
        by_tree.setdefault(t, {'total': 0, 'v000_pass': 0, 'v001_pass_03': 0, 'v001_pass_09': 0})
        by_tree[t]['total'] += 1
        if r['v000_xsd_03_valid']: by_tree[t]['v000_pass'] += 1
        if r['v001_xsd_03_valid']: by_tree[t]['v001_pass_03'] += 1
        if r['v001_xsd_09_valid']: by_tree[t]['v001_pass_09'] += 1

    # Save report
    out_md = OUT / 'simulator_report.md'
    md = ['# Pain.001 V000/V001 Simulator Report\n',
          f'**Generated**: {datetime.now().isoformat()}\n\n',
          '## Summary per tree\n\n',
          '| Tree | Total | V000 XSD .03 OK | V001 XSD .03 OK | V001 XSD .09 OK |\n',
          '|---|---|---|---|---|\n']
    for t, stats in by_tree.items():
        total = stats['total']
        md.append(f"| {t} | {total} | {stats['v000_pass']}/{total} | "
                  f"{stats['v001_pass_03']}/{total} | {stats['v001_pass_09']}/{total} |\n")

    md.append('\n## Per-sample results (first 30)\n\n')
    md.append('| # | Tree | Co | Vendor ctry | LZBKZ | V000.03 | V001.03 | V001.09 |\n')
    md.append('|---|---|---|---|---|---|---|---|\n')
    for r in results[:30]:
        v0 = '✅' if r['v000_xsd_03_valid'] else f"❌"
        v1_03 = '✅' if r['v001_xsd_03_valid'] else '❌'
        v1_09 = '✅' if r['v001_xsd_09_valid'] else '❌'
        md.append(f"| {r['scenario_id']} | {r['tree_short']} | {r['co']} | "
                  f"{r['vendor_country']} | {r['lzbkz']} | {v0} | {v1_03} | {v1_09} |\n")

    md.append('\n## XSD validation errors (sample)\n\n')
    err_counter = {}
    for r in results:
        for k in ['v000_xsd_03_err', 'v001_xsd_03_err', 'v001_xsd_09_err']:
            err = r.get(k)
            if err and err != 'OK':
                short = err[:120]
                err_counter[short] = err_counter.get(short, 0) + 1
    for err, cnt in sorted(err_counter.items(), key=lambda x: -x[1])[:10]:
        md.append(f'- ({cnt}x) {err}\n')

    out_md.write_text(''.join(md), encoding='utf-8')
    out_json = OUT / 'simulator_report.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'results': results, 'by_tree': by_tree}, f, indent=2, ensure_ascii=False, default=str)

    print(f'\n=== Summary ===')
    for t, stats in by_tree.items():
        print(f'  {t}: total={stats["total"]} V000_OK={stats["v000_pass"]} V001.03_OK={stats["v001_pass_03"]} V001.09_OK={stats["v001_pass_09"]}')
    print(f'\nReport: {out_md}')


if __name__ == '__main__':
    main()
