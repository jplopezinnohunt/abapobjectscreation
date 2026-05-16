************************************************************************
*                                                                      *
*  Druckprogramm für Avise zu Zahlungsträgern, die mit dem neuen       *
*  Zahlungsträgerprogramm SAPFPAYM erstelllt wurden                    *
*                                                                      *
*  Voraussetzung: Die Felder des REGUH-Includes IREGUH_FPM müssen      *
*  durch das neue Zahlungsträgertool gefüllt worden sein.              *
*                                                                      *
*  Besonderheit: Die Sortierung soll vollständig von außen vorgegeben  *
*  werden, die beim RFFO-Standard erzwungene Sortierung durch          *
*  SORT BY AVIS   (REGUH-ZBUKR, -RZAWE, -UBNKS, -UBNKY, -UBNKL)        *
*  wird durch einen CLEAR auf diese Felder aufgehoben.                 *
*  Dazu werden die zugehörigen Felder der Struktur SIC_REGUH an den    *
*  Extrakt angehängt.                                                  *
*                                                                      *
************************************************************************


*----------------------------------------------------------------------*
* Das Programm includiert:                                             *
*                                                                      *
* RFFORI0M  Makrodefinition für den Selektionsbildaufbau               *
* RFFORI00  Deklarationsteil der Zahlungsträger-Druckprogramme         *
* RFFORI06  Avis                                                       *
* RFFORI99  Allgemeine Unterroutinen der Zahlungsträger-Druckprogramme *
*----------------------------------------------------------------------*



*----------------------------------------------------------------------*
* Report-Header                                                        *
*----------------------------------------------------------------------*
REPORT rffoavis_fpaym
  LINE-SIZE 132
  MESSAGE-ID f0
  NO STANDARD PAGE HEADING.



*----------------------------------------------------------------------*
*  Segmente                                                            *
*----------------------------------------------------------------------*
TABLES:
  reguh,
  regup.


*----------------------------------------------------------------------*
*  Makrodefinitionen                                                   *
*----------------------------------------------------------------------*
INCLUDE rffori0m.

INITIALIZATION.

*----------------------------------------------------------------------*
*  Parameter und Select-Options                                        *
*----------------------------------------------------------------------*
  block 1.
  SELECT-OPTIONS:
    sel_zawe FOR  reguh-rzawe,         "Zahlwege
    sel_uzaw FOR  reguh-uzawe,         "Zahlwegzusatz
    sel_hbki FOR  reguh-hbkid,         "Hausbank (Kurzschlüssel)
    sel_hkti FOR  reguh-hktid,         "Kontenverbindung (Kurzschlüssel)
    sel_waer FOR  reguh-waers,         "Währungsschlüssel
    sel_pers FOR  reguh-pernr,         "Personalnummer
    sel_lifn FOR  reguh-lifnr,         "Kreditor
    sel_kunn FOR  reguh-kunnr,         "Debitor
    sel_vbln FOR  reguh-vblnr.         "Zahlungsbelegnummer
  SELECTION-SCREEN END OF BLOCK 1.

  block 3.
  PARAMETERS:
    par_anzp LIKE rfpdo-fordanzp,      "Anzahl Probedrucke
    par_pria LIKE rfpdo-fordpria,      "Drucker für die Mitteilungen
    par_srth LIKE t042e-svarh,         "Sortiervariante auf Headerebene
    par_srtp LIKE t042e-svarp,         "Sortiervariante für Positionen
    par_afor LIKE rfpdo1-fordzfor,     "Abweichendes Avisformular
    par_apdf LIKE fpayhx-pdfaf,        "Abweichendes PDF-Avisformular
    par_sofa LIKE rfpdo1-fordsofa,     "Sofortdruck
    par_espr LIKE rfpdo-fordespr,      "Texte in Empfängersprache
    par_isoc LIKE rfpdo-fordisoc.      "Währung in ISO-Code
    SPOOL_AUTHORITY.                   "Spoolberechtigung   1903484
  SELECTION-SCREEN END OF BLOCK 3.

  PARAMETERS:
    par_belp LIKE rfpdo-fordbelp  NO-DISPLAY,
    par_zdru LIKE rfpdo-fordzdru  NO-DISPLAY,
    par_priz LIKE rfpdo-fordpriz  NO-DISPLAY,
    par_sofz LIKE rfpdo1-fordsofz NO-DISPLAY,
    par_xdta LIKE rfpdo-fordxdta  NO-DISPLAY,
    par_priw LIKE rfpdo-fordpriw  NO-DISPLAY,
    par_sofw LIKE rfpdo1-fordsofw NO-DISPLAY,
    par_dtyp LIKE rfpdo-forddtyp  NO-DISPLAY,
    par_unix LIKE rfpdo2-fordnamd NO-DISPLAY,
    par_avis LIKE rfpdo-fordavis  NO-DISPLAY,
    par_begl LIKE rfpdo-fordbegl  NO-DISPLAY,
    par_prib LIKE rfpdo-fordprib  NO-DISPLAY,
    par_sofb LIKE rfpdo1-fordsofb NO-DISPLAY,
    par_maxp LIKE rfpdo-fordmaxp  NO-DISPLAY,
    par_vari(12) TYPE c           NO-DISPLAY,
*    par_sofo(1)  TYPE c           NO-DISPLAY. " 2230408
    par_sofo(1)  TYPE c           NO-DISPLAY, " 2230408
    par_xavi(1) TYPE c           NO-DISPLAY. " 2230408



*----------------------------------------------------------------------*
*  Vorbelegung der Parameter und Select-Options                        *
*----------------------------------------------------------------------*
  PERFORM init.
  par_belp = space.
  par_zdru = space.
  par_xdta = space.
  par_dtyp = space.
  par_avis = 'X'.
  par_begl = space.
  par_anzp = 0.
  par_espr = space.
  par_isoc = space.



*----------------------------------------------------------------------*
*  Tabellen / Felder / Field-Groups / At Selection-Screen              *
*----------------------------------------------------------------------*
  INCLUDE rffori00.



*----------------------------------------------------------------------*
*  Abweichendes Avis-Formular                                          *
*----------------------------------------------------------------------*
AT SELECTION-SCREEN ON VALUE-REQUEST FOR par_afor.
  PERFORM f4_formular USING par_afor.

AT SELECTION-SCREEN ON par_afor.
  IF par_afor NE space.
    SET CURSOR FIELD 'PAR_AFOR'.
    CALL FUNCTION 'FORM_CHECK'
      EXPORTING
        i_pzfor = par_afor.
  ENDIF.

AT SELECTION-SCREEN  ON par_apdf.
  IF par_apdf NE space.
    SET CURSOR FIELD 'PAR_APDF'.
    CALL FUNCTION 'PDF_FORM_CHECK'
      EXPORTING
        i_formname = par_apdf.
  ENDIF.
  IF  par_afor NE space
  AND par_apdf NE space.
*--- only one form allowed
    MESSAGE e271(bfibl02).
  ENDIF.


*----------------------------------------------------------------------*
*  Felder vorbelegen                                                   *
*----------------------------------------------------------------------*
START-OF-SELECTION.

  HLP_AUTH  = PAR_AUTH.  "spool authority  1903484
  PERFORM vorbereitung.
  flg_avis = 1.
  hlp_svarh = par_srth.
  hlp_svarp = par_srtp.
  zw_edisl = '*'.

  INSERT sic_reguh-rzawe
         sic_reguh-zbukr
         sic_reguh-ubnks
         sic_reguh-ubnky
         sic_reguh-ubnkl INTO daten.



*----------------------------------------------------------------------*
*  Daten prüfen und extrahieren                                        *
*----------------------------------------------------------------------*
GET reguh.

* überprüfen der Abgrenzungen für diesen Zahllauf
  CHECK sel_zawe.
  CHECK sel_uzaw.
  CHECK sel_hbki.
  CHECK sel_hkti.
  CHECK sel_waer.
  CHECK sel_pers.
  CHECK sel_lifn.
  CHECK sel_kunn.
  CHECK sel_vbln.

* nur Avise ausgeben, nachdem das neue Zahlungsträgertool entschieden
* hat, daß der Avisdruck notwendig ist (Prüfung für Online-Zahlen liegt
* im PAYMENT_MEDIUM_ONLINE)
  CHECK reguh-xavis NE space OR hlp_laufk EQ '*'
        OR par_xavi = 'X' " call from FM PAYMENT_MEDIUM_ONLINE, 2230408
        OR REGUH-RZAWE EQ space.   " note 1043111

* Simulation von Saldo-Null-Mitteilungen (RZAWE = SPACE, AVISG <> 'V')
  sic_reguh-rzawe = reguh-rzawe. CLEAR reguh-rzawe.
  PERFORM pruefung.
  reguh-rzawe = sic_reguh-rzawe.
  IF reguh-rzawe NE space.                                     "n1962009
  CALL FUNCTION 'FI_PAYMENT_METHOD_PROPERTIES'
    EXPORTING
      i_zlsch = reguh-rzawe
      i_land1 = t001-land1
    IMPORTING
      e_t042z = t042z.
  ELSE.                                                        "n1962009
    CLEAR t042z.
  ENDIF.
  regud-xeinz = t042z-xeinz.
  hlp_xeuro   = t042z-xeuro.

  clear reguh-srtf2. " note 967803

  PERFORM extract_vorbereitung.


GET regup.

* Sortierfelder initialisieren, aber in Struktur SIC_REGUH merken
  IF NOT ( reguh-rzawe IS INITIAL AND  "Sortierfelder nur
           reguh-zbukr IS INITIAL AND  "beim ersten Durchlauf
           reguh-ubnks IS INITIAL ).   "initialisieren !
    sic_reguh-rzawe = reguh-rzawe. CLEAR reguh-rzawe.
    sic_reguh-zbukr = reguh-zbukr. CLEAR reguh-zbukr.
    sic_reguh-ubnks = reguh-ubnks. CLEAR reguh-ubnks.
    sic_reguh-ubnky = reguh-ubnky. CLEAR reguh-ubnky.
    sic_reguh-ubnkl = reguh-ubnkl. CLEAR reguh-ubnkl.
  ENDIF.
  PERFORM extract.



*----------------------------------------------------------------------*
*  Bearbeitung der extrahierten Daten                                  *
*----------------------------------------------------------------------*
END-OF-SELECTION.

  IF flg_selektiert NE 0.

    IF par_avis EQ 'X'.
      hlp_aforn  = par_afor.           "abweichendes SAPscript Formular
      hlp_apdfaf = par_apdf.           "abweichendes Adobe PDF Formular
      PERFORM avis.                                         "RFFORI06
    ENDIF.

  ENDIF.

  PERFORM fehlermeldungen.

  PERFORM information_2.



*----------------------------------------------------------------------*
*  Unterprogramm Avis ohne Allongeteil                                 *
*----------------------------------------------------------------------*
  INCLUDE rffori06.



*----------------------------------------------------------------------*
*  Allgemeine Unterroutinen                                            *
*----------------------------------------------------------------------*
  INCLUDE rffori99.