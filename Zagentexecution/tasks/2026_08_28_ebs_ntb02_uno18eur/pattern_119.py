# -*- coding: utf-8 -*-
"""Las 119 sin señal: ¿que PATRONES hay de verdad?

No se inventan etiquetas. Se miran las señales que ya existen y se cuenta cuantas cuentas
cubre cada una, en orden de fuerza de evidencia:

  1. pertenencia a un set YBANK  -> HQ vs FO ya esta declarado en configuracion (grado CONFIG)
  2. si la cuenta PAGA (T042I)   -> hecho operativo, no una opinion
  3. el canal del extracto       -> hecho operativo
  4. forma del TEXTO             -> convencion humana (grado TEXTO)
  5. la divisa frente al pais del banco -> local vs divisa fuerte

Lo que quede sin cubrir por ninguna es el residuo REAL que hay que preguntar.

SOLO LECTURA.
"""
import sys, os, json, collections, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "config_profile.json")
filas = json.load(open(P, encoding="utf-8"))
sin = [f for f in filas if f["naturaleza"] == "SIN_CLASIFICAR"]
print("cuentas vivas: %d | sin clasificar: %d" % (len(filas), len(sin)))

# ---- 1. ¿que dice YBANK de ellas? -------------------------------------------
print("\n==== 1. pertenencia a set YBANK (grado CONFIG — ya esta declarado) ====")
fam = collections.Counter()
for f in sin:
    s = f.get("ybank_set", "")
    if not s:
        fam["(en NINGUN set)"] += 1
    elif "_FO_" in s:
        fam["FO — oficina de terreno"] += 1
    elif "_SIGHT" in s:
        fam["SIGHT — a la vista"] += 1
    elif "_HQ_" in s:
        fam["HQ — sede"] += 1
    else:
        fam[s] += 1
for k, v in fam.most_common():
    print("   %-28s %3d  (%.0f%%)" % (k, v, 100.0*v/len(sin)))

# ---- 2. hechos operativos ---------------------------------------------------
print("\n==== 2. hechos operativos ====")
print("   pagan (T042I):", sum(1 for f in sin if f["PAGA_T042I"]))
print("   canal:", dict(collections.Counter(f["canal"] for f in sin)))

# ---- 3. forma del texto -----------------------------------------------------
print("\n==== 3. forma del TEXTO — palabras que aparecen en 2+ cuentas ====")
STOP = {"UNESCO", "-", "", "BK", "DE", "THE", "AND", "OF"}
CCY = {"USD","EUR","XOF","XAF","GBP","CHF","JPY","AUD","CAD","DKK","SEK","NOK","BRL","INR",
       "IRR","ETB","GHS","KES","MZN","NAD","NPR","VND","CNY","KHR","UZS","MXN","CLP","ARS",
       "WST","ZWG","ILS","JOD","LBP","THB","TZS","ZMW","HTG","CUP","BIF","SDD","RUB","QAR",
       "AFN","GNF","VES","KZT","IDR","PEN","MAD","TND","RON","UYU","COP","BOB","PYG","DOP"}
tok = collections.Counter()
for f in sin:
    for w in re.split(r"[\s\-,/()]+", (f["texto"] or "").upper()):
        w = w.strip()
        if w and w not in STOP and w not in CCY and not w.isdigit() and len(w) > 2:
            tok[w] += 1
for w, n in tok.most_common(22):
    if n >= 2:
        print("   %-22s %d" % (w, n))

# ---- 4. ¿el texto es "UNESCO <SITIO> - <DIVISA>"? ---------------------------
pat = re.compile(r"^\s*UNESCO\s+[A-Z\.\'\s]+[-–]\s*[A-Z]{3}\s*$")
enc = [f for f in sin if pat.match((f["texto"] or "").upper())]
print("\n==== 4. texto con la forma 'UNESCO <SITIO> - <DIVISA>' : %d de %d ====" % (len(enc), len(sin)))
for f in enc[:12]:
    print("   %-22s %s" % (f["cuenta"], f["texto"]))

# ---- 5. propuesta de clasificacion en cascada -------------------------------
print("\n==== 5. CASCADA propuesta — cada cuenta cae en la PRIMERA que aplica ====")
reglas = []
def clasifica(f):
    s = f.get("ybank_set", "") or ""
    t = (f["texto"] or "").upper()
    if f["PAGA_T042I"]:
        return ("OPERATIVA", "HECHO", "esta en determinacion de banco de pagos")
    if "IMPREST" in t or "CAISSE" in t or "PETTY" in t:
        return ("CAJA_IMPREST", "TEXTO", "texto dice imprest/caisse")
    if "DONATION" in t or "UPO" in t or "SHOP" in t or "SALES" in t:
        return ("RECAUDACION", "TEXTO", "texto dice donaciones/ventas")
    if "_FO_" in s:
        return ("TERRENO", "CONFIG", "esta en un set YBANK de oficina de terreno")
    if "_SIGHT" in s:
        return ("A_LA_VISTA", "CONFIG", "set YBANK _SIGHT")
    if "_HQ_" in s:
        return ("SEDE_sin_uso_declarado", "CONFIG-PARCIAL", "set YBANK de sede, uso sin declarar")
    return ("RESIDUO", "NINGUNA", "ni set ni texto reconocible")

out = collections.Counter()
det = collections.defaultdict(list)
for f in sin:
    nat, grado, por = clasifica(f)
    out[(nat, grado)] += 1
    det[nat].append(f)
for (nat, grado), n in sorted(out.items(), key=lambda x: -x[1]):
    print("   %-26s %-14s %3d" % (nat, grado, n))

print("\n==== 6. EL RESIDUO — lo unico que hay que preguntar ====")
for f in det["RESIDUO"]:
    print("   %-22s %-8s canal=%-13s %s"
          % (f["cuenta"], f["waers"], f["canal"], (f["texto"] or "")[:44]))
print("\n==== 7. SEDE sin uso declarado ====")
for f in det["SEDE_sin_uso_declarado"]:
    print("   %-22s %-8s canal=%-13s %s"
          % (f["cuenta"], f["waers"], f["canal"], (f["texto"] or "")[:44]))
