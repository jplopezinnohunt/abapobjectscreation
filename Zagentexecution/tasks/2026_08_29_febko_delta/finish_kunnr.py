# -*- coding: utf-8 -*-
"""Termina lo que dejo a medias add_kunnr_to_reguh: el UPDATE y el indice unico.

POR QUE EXISTE ESTE SEGUNDO FICHERO
    El primero leyo bien -- 3.739.106 filas de P01 en 174 s -- y se quedo colgado en el UPDATE.
    La causa: escribi el join envuelto en `IFNULL(...)` en LOS DOS LADOS, y eso ANULA el indice
    de la tabla temporal. SQLite pasaba a escanear 3,7 M filas por cada una de las 3,7 M.

    Comprobado con EXPLAIN QUERY PLAN, que es lo que habria que haber hecho ANTES:
        con IFNULL   -> SCAN t
        sin IFNULL   -> SEARCH t USING COVERING INDEX _ix_kunnr

    Y quitar el IFNULL es seguro porque esta MEDIDO: 0 filas con NULL en la firma, ni en el
    Golden ni en la temporal. La temporal sobrevivio, asi que no se vuelve a leer P01.

    Es la tercera vez hoy que estimo la lectura y no la escritura. Aqui el plan se mira antes.
"""
import sqlite3, sys, time
DB="Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
F=["LAUFD","LAUFI","XVORL","ZBUKR","LIFNR","EMPFG","VBLNR","NAME1","RWBTR"]
K=["LAUFD","LAUFI","XVORL","ZBUKR","LIFNR","KUNNR","EMPFG","VBLNR"]
c=sqlite3.connect(DB)
join=" AND ".join("t.[%s]=REGUH.[%s]"%(f,f) for f in F)
t=time.time()
c.execute("UPDATE REGUH SET KUNNR=(SELECT t.KUNNR FROM _tmp_kunnr t WHERE %s) "
          "WHERE EXISTS (SELECT 1 FROM _tmp_kunnr t WHERE %s)"%(join,join))
c.commit()
n=c.execute("SELECT COUNT(*) FROM REGUH WHERE KUNNR IS NOT NULL").fetchone()[0]
print("UPDATE en %.0f s -> %s de 3.707.737 filas con KUNNR"%(time.time()-t,"{:,}".format(n)))
c.execute("DROP TABLE _tmp_kunnr"); c.commit()
try:
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_reguh_delta ON REGUH (%s)"
              % ", ".join('"%s"'%x for x in K))
    c.commit(); print("INDICE UNICO creado sobre %s -> delta DESBLOQUEADO"%"+".join(K))
except sqlite3.IntegrityError:
    kk=" || '|' || ".join("IFNULL(\"%s\",'')"%x for x in K)
    a,b=c.execute("SELECT COUNT(*),COUNT(DISTINCT %s) FROM REGUH"%kk).fetchone()
    print("el indice SIGUE sin crearse: %s filas / %s claves"%("{:,}".format(a),"{:,}".format(b)))
    sys.exit(2)
c.close()
