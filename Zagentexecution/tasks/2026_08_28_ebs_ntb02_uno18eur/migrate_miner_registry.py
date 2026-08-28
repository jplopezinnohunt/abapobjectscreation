# -*- coding: utf-8 -*-
"""Mete los siete mineros de banca DENTRO del registro, con claves que no colisionan.

Defecto mio de s108: registre D1-D6 en la RAIZ de algorithms.json, fuera de `algorithms`,
que es donde vive el registro de verdad (98 entradas). El agente que registro D7 heredo el
error. Dos consecuencias:

  1. Estaban fuera del registro, asi que ninguna puerta que recorra `algorithms` los veia --
     y `algorithm_landing_check` daba PASS sin haberlos mirado nunca. Un verde por no mirar.
  2. Los prefijos D1/D4/D5/D6 YA existen dentro y significan otra cosa: estrategias de delta,
     troceado de campos, sonda acotada, agregar-antes-de-resolver. Dos cosas distintas con el
     mismo nombre en el mismo store es como se pierde la trazabilidad.

Se renumeran a A72-A78, continuando la serie real. Los ficheros y su contenido no cambian.
"""
import json, io, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

P = "brain_v2/methods/algorithms.json"
d = json.load(io.open(P, encoding="utf-8"))
reg = d["algorithms"]

VIEJAS = ["D1_house_bank_ebs_wiring", "D2_bank_statement_channel_census",
          "D3_bank_account_nature_model", "D4_bank_config_profile_by_nature",
          "D5_bank_account_behaviour_signature", "D6_ebs_format_consolidation",
          "D7_bank_statement_sod_check"]
NUEVAS = ["A72_house_bank_ebs_wiring", "A73_bank_statement_channel_census",
          "A74_bank_account_nature_model", "A75_bank_config_profile_by_nature",
          "A76_bank_account_behaviour_signature", "A77_ebs_format_consolidation",
          "A78_bank_statement_sod_check"]

movidas = 0
for vieja, nueva in zip(VIEJAS, NUEVAS):
    if nueva in reg:
        print("  %-38s ya estaba dentro" % nueva)
        continue
    if vieja not in d:
        print("  %-38s NO esta en la raiz" % vieja)
        continue
    ent = d.pop(vieja)
    ent["_renombrado_de"] = vieja
    ent["_por_que"] = ("s108: estaba en la RAIZ de algorithms.json, fuera del registro, y su "
                       "prefijo D chocaba con una entrada distinta que ya existia dentro "
                       "(D4=troceado de campos, D5=sonda acotada). Fuera del registro ninguna "
                       "puerta lo veia: algorithm_landing_check daba PASS sin mirarlo.")
    reg[nueva] = ent
    movidas += 1
    print("  %-38s <- %s" % (nueva, vieja))

json.dump(d, io.open(P, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\nregistro: %d entradas (%d movidas desde la raiz)" % (len(reg), movidas))
print("raiz: %s" % [k for k in d if k != "algorithms"])
