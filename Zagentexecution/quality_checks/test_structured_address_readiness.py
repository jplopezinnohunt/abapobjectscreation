#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_structured_address_readiness.py -- las trampas que ya nos costaron una vez.

Corre SIN CONEXION a SAP. Cada caso de aqui es un error real de 2026-08-19, no un
ejemplo inventado: si alguien vuelve a romper una de estas, el test lo dice antes
de que llegue a un fichero que va al banco.

    python Zagentexecution/quality_checks/test_structured_address_readiness.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "sar", os.path.join(AQUI, "structured_address_readiness.py"))
sar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sar)

OK = FALLO = 0


def check(nombre, obtenido, esperado):
    global OK, FALLO
    if obtenido == esperado:
        OK += 1
    else:
        FALLO += 1
        print("  FALLA  %s\n         obtuve   %r\n         esperaba %r"
              % (nombre, obtenido, esperado))


print("1. receptor_key -- el bug que colapso 8.894 proveedores en 1 receptor")
# En FI-AP el PERNR viene relleno de ceros: es un string NO VACIO, asi que
# `PERNR or LIFNR` devolvia el PERNR para todos y los agrupaba en uno solo.
check("nomina usa PERNR",
      sar.receptor_key({"DORIGIN": "HR-PY", "PERNR": "10154618", "LIFNR": "10154618"}),
      "10154618")
check("proveedor usa LIFNR aunque el PERNR sea '00000000'",
      sar.receptor_key({"DORIGIN": "FI-AP", "PERNR": "00000000", "LIFNR": "0000351714"}),
      "0000351714")

print("2. es_placeholder -- el bug que habria cargado New York como Alaska")
# '99999' cae en el rango de ZIP de Alaska. La primera version del detector
# anclaba al final y NO reconocia '99999-9999' ni 'Z9Z 9Z9', que son 64 de los
# 68 casos reales.
for pc, esperado in (("99999-9999", True), ("99999", True), ("Z9Z 9Z9", True),
                     ("Z9Z9Z9", True), ("00000", True), ("0000000", True),
                     ("XXXXX", True), ("12345", True),
                     ("10017", False), ("H3Z 3B8", False), ("75007", False),
                     ("80011", False), ("98122", False), ("M5B 2H1", False),
                     ("", False)):
    check("es_placeholder(%r)" % pc, sar.es_placeholder(pc), esperado)

print("3. classify -- la region solo se exige si el rail la pide")
# Citi documenta CtrySubDvsn como obligatorio en su Linea 2; SocGen no. Tratarlos
# igual dimensiona mal el trabajo en un factor 9.
d = sar.classify("Main St", "NEW YORK", "10017", "US", "", True, "US")
check("sin region y el rail la exige -> REGION",
      any(x[0] == "REGION" for x in d), True)
d = sar.classify("Main St", "NEW YORK", "10017", "US", "", False, "US")
check("sin region y el rail NO la exige -> sin hallazgo",
      any(x[0] == "REGION" for x in d), False)
d = sar.classify("Main St", "NEW YORK", "99999-9999", "US", "NY", True, "US")
check("CP comodin -> COMODIN, y NO 'sin codigo postal'",
      (any(x[0] == "COMODIN" for x in d),
       any("sin codigo postal" in x[1] for x in d)), (True, False))
d = sar.classify("", "", "", "", "", True, "US")
check("sin ciudad y sin pais -> dos bloqueantes",
      sum(1 for x in d if x[0] == "BLOQUEANTE"), 2)
d = sar.classify("Main", "WIEN A-1010", "1010", "AT", "", False, "AT")
check("ciudad con el postal pegado -> SUCIO",
      any(x[0] == "SUCIO" for x in d), True)
d = sar.classify("Main", "PARIS", "75007", "FR", "", False, "FR")
check("direccion completa y rail que no exige region -> sin hallazgos", d, [])

print("4. worst -- manda el defecto mas grave")
check("BLOQUEANTE gana a REGION",
      sar.worst([("REGION", "x"), ("BLOQUEANTE", "y")]), "BLOQUEANTE")
check("REGION gana a SUCIO", sar.worst([("SUCIO", "x"), ("REGION", "y")]), "REGION")
check("sin defectos -> OK", sar.worst([]), "OK")

print("\n>>> %d OK, %d fallos" % (OK, FALLO))
sys.exit(1 if FALLO else 0)
