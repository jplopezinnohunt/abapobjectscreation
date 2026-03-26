import sqlite3

conn = sqlite3.connect('c:/Users/jp_lopez/projects/abapobjectscreation/Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
cur = conn.cursor()

unes_hq = ['WHC','DCE','BIO','ESD','ESC','EDP','IEO','CEO','OPC','FMS','EDU','RPF',
           'E30','IPD','PCB','CPD','FLI','SPR','ITH','IOC','IPS','EME','IOS','GEM',
           'SEO','HED','PBS','FMD','MCO','EPR','CPE','UAI','PSU','BES','YOU','GCP',
           'KSD','MTD','TAI','YLS']
hq_str = ','.join("'%s'" % x for x in unes_hq)

desc = {
    'PDK': 'IIEP Paris', 'ADM': 'IIEP Administration', 'TEC': 'IIEP Technical Cooperation',
    'IBA': 'IIEP Buenos Aires', 'KMM': 'IIEP Kathmandu', 'TRA': 'IIEP Training',
    'RND': 'IIEP Research',
    'WHC': 'World Heritage Centre', 'DCE': 'Diversity Cultural Expressions',
    'BIO': 'Bioethics & Ethics of S&T', 'ESD': 'Education Sustainable Dev.',
    'ESC': 'Natural Sciences Sector', 'EDP': 'Education Policy',
    'IEO': 'Evaluation Office', 'CEO': 'Chief Executive Office',
    'OPC': 'Office of DG', 'FMS': 'Financial Mgmt',
    'EDU': 'Education Sector', 'RPF': 'Results & Performance',
    'E30': 'Education Division', 'IPD': 'Intersectoral Platform',
    'PCB': 'Participation & Cooperation', 'CPD': 'Capacity Development',
    'FLI': 'Field Liaison', 'SPR': 'Strategic Planning',
    'ITH': 'Intangible Heritage', 'IOC': 'Oceanographic Commission',
    'IPS': 'Information & Promotion', 'EME': 'Emergency Response',
    'IOS': 'Internal Oversight', 'GEM': 'Global Ed. Monitoring',
    'SEO': 'Social & Human Sciences', 'HED': 'Higher Education',
    'PBS': 'Programme & Budget', 'FMD': 'Field Management',
    'MCO': 'Media & Communication', 'EPR': 'Emergency Preparedness',
    'CPE': 'Culture & Emergencies', 'UAI': 'Archives & Info Mgmt',
    'PSU': 'Programme Support', 'BES': 'Basic Education',
    'YOU': 'Youth Section', 'GCP': 'Gender & Culture',
    'KSD': 'Knowledge Systems', 'MTD': 'Media & Tech Dev',
    'TAI': 'Technology & AI', 'YLS': 'Youth Leadership',
    'YAO': 'Yaounde (Cameroon)', 'BGK': 'Bangkok (Thailand)', 'NAI': 'Nairobi (Kenya)',
    'HAV': 'Havana (Cuba)', 'AMN': 'Amman (Jordan)', 'HAR': 'Harare (Zimbabwe)',
    'BEI': 'Beirut (Lebanon)', 'ABJ': 'Abidjan (Ivory Coast)', 'BAG': 'Baghdad (Iraq)',
    'DAK': 'Dakar (Senegal)', 'BRV': 'Montevideo (Uruguay)', 'VNI': 'Venice (Italy)',
    'LIM': 'Lima (Peru)', 'LHE': 'Islamabad (Pakistan)', 'KAB': 'Kabul (Afghanistan)',
    'DHE': 'Doha (Qatar)', 'JAK': 'Jakarta (Indonesia)', 'PNP': 'Phnom Penh (Cambodia)',
    'NDL': 'New Delhi (India)', 'KHA': 'Khartoum (Sudan)', 'FEJ': 'Rabat (Morocco)',
    'STG': 'Santiago (Chile)', 'API': 'Apia (Samoa)', 'POP': 'Port-au-Prince (Haiti)',
    'RAB': 'Rabat (Morocco)', 'SJO': 'San Jose (Costa Rica)', 'CAI': 'Cairo (Egypt)',
    'ACR': 'Accra (Ghana)', 'KNS': 'Kinshasa (DRC)', 'ISB': 'Islamabad (Pakistan)',
    'DOH': 'Doha (Qatar)', 'IGE': 'Abuja (Nigeria)', 'LBV': 'Libreville (Gabon)',
    'PLS': 'Ramallah (Palestine)', 'RAM': 'Ramallah (Palestine)', 'HAN': 'Hanoi (Vietnam)',
    'BAM': 'Bamako (Mali)', 'JUB': 'Juba (South Sudan)', 'TEH': 'Tehran (Iran)',
    'ABU': 'Abuja (Nigeria)', 'BRU': 'Brussels (Belgium)', 'MTF': 'Windhoek (Namibia)',
    'EES': 'Almaty (Kazakhstan)', 'MXC': 'Mexico City', 'DHA': 'Dhaka (Bangladesh)',
    'HAE': 'Port-au-Prince', 'HYD': 'Hyderabad (India)', 'SHS': 'Shanghai (China)',
    'TAS': 'Tashkent (Uzbekistan)', 'ATA': 'Antananarivo (Madagascar)', 'TED': 'Tegucigalpa (Honduras)',
    'BEJ': 'Beijing (China)', 'GUC': 'Guatemala City', 'ATD': 'Addis Ababa (Ethiopia)',
    'DAR': 'Dar es Salaam (Tanzania)', 'ADI': 'Addis Ababa (Ethiopia)', 'KAT': 'Kathmandu (Nepal)',
    'UNE': 'UNESCO General', 'WIN': 'Windhoek (Namibia)', 'KNG': 'Kingston (Jamaica)',
    'EEO': 'Eastern Europe Office', 'IRD': 'Irbid (Jordan)', 'IDT': 'Programme Office',
    'MHM': 'Myanmar', 'MIL': 'Milan (Italy)',
}

CR = "(b.BKTXT LIKE '%%cost recov%%' OR b.BKTXT LIKE '%%COST RECOV%%')"

segments = [
    ('IIEP (all)', "b.BUKRS = 'IIEP'"),
    ('UNES HQ Sectors', "b.BUKRS = 'UNES' AND f.FISTL IN (%s)" % hq_str),
    ('UNES Field', "b.BUKRS = 'UNES' AND f.FISTL NOT IN (%s)" % hq_str),
]

# GRAND SUMMARY
print('=' * 100)
print('  2025 COST RECOVERY - GRAND SUMMARY BY SEGMENT')
print('=' * 100)
print()
fmt = "  %-18s | %5s | %10s | %10s | %8s | %7s | %5s"
print(fmt % ('Segment','Docs','Staff(11)','Conslt(13)','Rev(CR)','Offices','Funds'))
print("  " + "-"*85)
for label, where in segments:
    cur.execute("""
    SELECT COUNT(DISTINCT b.BELNR),
      SUM(CASE WHEN f.FIPEX = '11' THEN 1 ELSE 0 END),
      SUM(CASE WHEN f.FIPEX = '13' THEN 1 ELSE 0 END),
      SUM(CASE WHEN f.FIPEX = 'REVENUE' THEN 1 ELSE 0 END),
      COUNT(DISTINCT f.FISTL), COUNT(DISTINCT f.FONDS)
    FROM fmifiit_full f
    JOIN bkpf b ON f.KNBELNR = b.BELNR AND f.KNGJAHR = b.GJAHR AND f.BUKRS = b.BUKRS
    WHERE b.GJAHR = '2025' AND %s AND %s
    """ % (CR, where))
    r = cur.fetchone()
    dr = r[1]+r[2]
    ps = "(%2.0f%%)" % (r[1]*100/dr) if dr else ""
    pc = "(%2.0f%%)" % (r[2]*100/dr) if dr else ""
    print("  %-18s | %5d | %5d %4s | %5d %4s | %8d | %7d | %5d" % (
        label, r[0], r[1], ps, r[2], pc, r[3], r[4], r[5]))

print()
print()

# 1. IIEP
print('=' * 100)
print('  1. IIEP (Company Code IIEP)')
print('=' * 100)
print()
cur.execute("""
SELECT f.FISTL,
  SUM(CASE WHEN f.FIPEX = '11' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.FIPEX = '13' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.FIPEX = '30' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.FIPEX = 'REVENUE' THEN 1 ELSE 0 END),
  COUNT(DISTINCT f.FONDS), COUNT(*)
FROM fmifiit_full f
JOIN bkpf b ON f.KNBELNR = b.BELNR AND f.KNGJAHR = b.GJAHR AND f.BUKRS = b.BUKRS
WHERE b.GJAHR = '2025' AND b.BUKRS = 'IIEP' AND %s
GROUP BY f.FISTL ORDER BY COUNT(*) DESC
""" % CR)
print("  %-6s %-28s %8s %10s %7s %8s %5s %5s" % (
    'FISTL','Description','Staff(11)','Conslt(13)','Oth(30)','Rev(CR)','Funds','Total'))
print("  " + "-"*90)
for r in cur.fetchall():
    print("  %-6s %-28s %8d %10d %7d %8d %5d %5d" % (
        r[0], desc.get(r[0],'?'), r[1], r[2], r[3], r[4], r[5], r[6]))

print()
print()

# 2. UNES HQ
print('=' * 100)
print('  2. UNESCO HQ Sectors (Company Code UNES, Paris-based)')
print('=' * 100)
print()
cur.execute("""
SELECT f.FISTL,
  SUM(CASE WHEN f.FIPEX = '11' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.FIPEX = '13' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.FIPEX = 'REVENUE' THEN 1 ELSE 0 END),
  COUNT(DISTINCT f.FONDS), COUNT(*)
FROM fmifiit_full f
JOIN bkpf b ON f.KNBELNR = b.BELNR AND f.KNGJAHR = b.GJAHR AND f.BUKRS = b.BUKRS
WHERE b.GJAHR = '2025' AND b.BUKRS = 'UNES' AND %s AND f.FISTL IN (%s)
GROUP BY f.FISTL ORDER BY COUNT(*) DESC
""" % (CR, hq_str))
print("  %-6s %-35s %8s %10s %8s %5s %5s" % (
    'FISTL','Description','Staff(11)','Conslt(13)','Rev(CR)','Funds','Total'))
print("  " + "-"*90)
for r in cur.fetchall():
    print("  %-6s %-35s %8d %10d %8d %5d %5d" % (
        r[0], desc.get(r[0],'?'), r[1], r[2], r[3], r[4], r[5]))

print()
print()

# 3. UNES Field
print('=' * 100)
print('  3. UNESCO Field Offices (Company Code UNES)')
print('=' * 100)
print()
cur.execute("""
SELECT f.FISTL,
  SUM(CASE WHEN f.FIPEX = '11' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.FIPEX = '13' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.FIPEX = 'REVENUE' THEN 1 ELSE 0 END),
  COUNT(DISTINCT f.FONDS), COUNT(*)
FROM fmifiit_full f
JOIN bkpf b ON f.KNBELNR = b.BELNR AND f.KNGJAHR = b.GJAHR AND f.BUKRS = b.BUKRS
WHERE b.GJAHR = '2025' AND b.BUKRS = 'UNES' AND %s AND f.FISTL NOT IN (%s)
GROUP BY f.FISTL ORDER BY COUNT(*) DESC
""" % (CR, hq_str))
print("  %-6s %-30s %8s %10s %8s %5s %5s" % (
    'FISTL','Description','Staff(11)','Conslt(13)','Rev(CR)','Funds','Total'))
print("  " + "-"*85)
for r in cur.fetchall():
    print("  %-6s %-30s %8d %10d %8d %5d %5d" % (
        r[0], desc.get(r[0],'?'), r[1], r[2], r[3], r[4], r[5]))

print()
print()

# Monthly for each segment
for label, where in segments:
    print('--- %s BY MONTH ---' % label)
    cur.execute("""
    SELECT b.MONAT,
      SUM(CASE WHEN f.FIPEX = '11' THEN 1 ELSE 0 END),
      SUM(CASE WHEN f.FIPEX = '13' THEN 1 ELSE 0 END),
      SUM(CASE WHEN f.FIPEX = 'REVENUE' THEN 1 ELSE 0 END),
      COUNT(DISTINCT b.BELNR), COUNT(DISTINCT f.FISTL)
    FROM fmifiit_full f
    JOIN bkpf b ON f.KNBELNR = b.BELNR AND f.KNGJAHR = b.GJAHR AND f.BUKRS = b.BUKRS
    WHERE b.GJAHR = '2025' AND %s AND %s
    GROUP BY b.MONAT ORDER BY b.MONAT
    """ % (CR, where))
    print("  %-6s %8s %10s %8s %5s %7s" % ('Month','Staff(11)','Conslt(13)','Rev(CR)','Docs','Offices'))
    ts = tc = tr = td = 0
    for r in cur.fetchall():
        print("  %-6s %8d %10d %8d %5d %7d" % r)
        ts += r[1]; tc += r[2]; tr += r[3]; td += r[4]
    print("  %-6s %8d %10d %8d %5d" % ('TOTAL', ts, tc, tr, td))
    print()

conn.close()
