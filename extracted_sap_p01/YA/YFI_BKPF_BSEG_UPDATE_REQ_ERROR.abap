*&---------------------------------------------------------------------*
*& Report YFI_BKPF_BSEG_UPDATE_REQ_ERROR
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_BKPF_BSEG_UPDATE_REQ_ERROR.

DATA LT_BKP1 TYPE TABLE OF BKP1.
DATA LT_BKPF TYPE TABLE OF BKPF.
DATA LT_BSEC TYPE TABLE OF BSEC.
DATA LT_BSED TYPE TABLE OF BSED.
DATA LT_BSEG TYPE TABLE OF BSEG.
DATA LT_BSET TYPE TABLE OF BSET.
DATA LT_BSEU TYPE TABLE OF BSEU.

DATA LS_BKP1 TYPE BKP1.
DATA LS_BKPF TYPE BKPF.
DATA LS_BSEG TYPE BSEG.
DATA LS_BSEU TYPE BSEU.

DATA LT_GLS0 TYPE TABLE OF GLS0.
DATA LS_GLS0 TYPE GLS0.
DATA LT_GLS0_ADD TYPE TABLE OF RGIAD1.
DATA LS_GLS0_ADD TYPE RGIAD1.

DATA LV_AUGST TYPE NUM1.
DATA LV_KUKEY TYPE FEBEP-KUKEY.
DATA LV_ESNUM TYPE FEBEP-ESNUM.
DATA LV_CSNUM TYPE FEBCL-CSNUM.

PARAMETERS P_COMMIT AS CHECKBOX.
PARAMETERS P_GLT0 AS CHECKBOX.

START-OF-SELECTION.

*******  IF p_glt0 = abap_true.
*******    DELETE FROM glt0 WHERE racct = '1075011'.
*******    DELETE FROM glt0 WHERE racct = '1175011'.
*******    EXIT.
*******  ENDIF.
*******
*******
*******  SELECT SINGLE * FROM bkpf WHERE bukrs = 'UNES'
*******                     AND   belnr = '3500083275'
*******                     AND   gjahr = '2025' INTO @ls_bkpf.
*******  IF sy-subrc = 0.
*******
*******    UPDATE bseg SET hkont = '0001075011'
*******                WHERE bukrs = 'UNES'
*******                AND   belnr = '3500083275'
*******                AND   gjahr = '2025'
*******                AND   buzei = '001'.
*******    UPDATE bseg SET hkont = '0001175011'
*******                WHERE bukrs = 'UNES'
*******                AND   belnr = '3500083275'
*******                AND   gjahr = '2025'
*******                AND   buzei = '002'.
*******
*******  ENDIF.

*  ls_bkp1-currj = '2026'.
*  APPEND ls_bkp1 TO lt_bkp1.
*
*  ls_bkpf-mandt = '350'.
*  ls_bkpf-bukrs = 'UNES'.
*  ls_bkpf-belnr = '3500083275'.
*  ls_bkpf-gjahr = '2025'.
*  ls_bkpf-blart = 'Z1'.
*  ls_bkpf-bldat = ls_bkpf-budat = ls_bkpf-wwert = '20251222'.
*  ls_bkpf-monat = '12'.
*  ls_bkpf-cpudt = ls_bkpf-psobt = '20260106'.
*  ls_bkpf-cputm = '155907'.
*  ls_bkpf-usnam = 'I_BIDAULT'.
*  ls_bkpf-tcode = 'FB05'.
*  ls_bkpf-xblnr = 'SOG01USDD125251'.
*  ls_bkpf-bktxt = '0074391700001'.
*  ls_bkpf-waers = 'USD'.
*  ls_bkpf-xrueb = 'X'.
*  ls_bkpf-glvor = 'RFBU'.
*  ls_bkpf-awtyp = 'BKPF'.
*  ls_bkpf-awkey = '3500083275UNES2025'.
*  ls_bkpf-fikrs = 'UNES'.
*  ls_bkpf-hwaer = 'USD'.
*  ls_bkpf-xmwst = 'X'.
*  ls_bkpf-kurst = 'M'.
*  ls_bkpf-psozl = 'X'.
*  APPEND ls_bkpf TO lt_bkpf.
*
*  ls_bseu-waers = 'USD'.
*  APPEND ls_bseu TO lt_bseu.
*  APPEND ls_bseu TO lt_bseu.
*
*  CLEAR ls_bseg.
*  ls_bseg-mandt = '350'.
*  ls_bseg-bukrs = 'UNES'.
*  ls_bseg-belnr = '3500083275'.
*  ls_bseg-gjahr = '2025'.
*  ls_bseg-buzei = '001'.
*  ls_bseg-bschl = '40'.
*  ls_bseg-koart = 'S'.
*  ls_bseg-shkzg = 'S'.
*  ls_bseg-gsber = 'GEF'.
*  ls_bseg-dmbtr = ls_bseg-wrbtr = ls_bseg-pswbt = '57240.01'.
*  ls_bseg-pswsl = 'USD'.
*  ls_bseg-valut = '20251222'.
*  ls_bseg-zuonr = '0074391700001'.
*  ls_bseg-sgtxt = '/FR045/TRANSFERTS RECUSRTR 12/11/25/REMI/RTR 12/11'.
*  ls_bseg-vorgn = 'RFBU'.
*  ls_bseg-fdlev = 'B0'.
*  ls_bseg-fdwbt = '57240.01'.
*  ls_bseg-fdtag = '20251222'.
*  ls_bseg-kokrs = 'UNES'.
*  ls_bseg-xkres = 'X'.
*  ls_bseg-hkont = '1075011'.
*  ls_bseg-xbilk = 'X'.
*  ls_bseg-fipos = 'BANK'.
*  ls_bseg-xref1 = 'HQ'.
*  ls_bseg-xref2 = 'HQ'.
*  APPEND ls_bseg TO lt_bseg.
*
*  CLEAR ls_bseg.
*  ls_bseg-mandt = '350'.
*  ls_bseg-bukrs = 'UNES'.
*  ls_bseg-belnr = '3500083275'.
*  ls_bseg-gjahr = '2025'.
*  ls_bseg-buzei = '002'.
*  ls_bseg-bschl = '50'.
*  ls_bseg-koart = 'S'.
*  ls_bseg-shkzg = 'H'.
*  ls_bseg-gsber = 'GEF'.
*  ls_bseg-dmbtr = ls_bseg-wrbtr = ls_bseg-pswbt = '57240.01'.
*  ls_bseg-pswsl = 'USD'.
*  ls_bseg-valut = '20251222'.
*  ls_bseg-zuonr = '0083275'.
*  ls_bseg-sgtxt = 'ROF AFGHANISTAN KOMITEEN'.
*  ls_bseg-vorgn = 'RFBU'.
*  ls_bseg-fdlev = 'B1'.
*  ls_bseg-fdwbt = '57240.01-'.
*  ls_bseg-fdtag = '20251222'.
*  ls_bseg-kokrs = 'UNES'.
*  ls_bseg-xkres = 'X'.
*  ls_bseg-xopvw = 'X'.
*  ls_bseg-hkont = '1175011'.
*  ls_bseg-xbilk = 'X'.
*  ls_bseg-fipos = 'BANK'.
*  ls_bseg-xref1 = 'HQ'.
*  ls_bseg-xref2 = 'HQ'.
*  APPEND ls_bseg TO lt_bseg.
*
*  CALL FUNCTION 'POST_DOCUMENT' IN UPDATE TASK
** EXPORTING
**   I_BKDF           =
**   I_UF05A          =
**   XBKPU            =
**   I_GENER          =
**   SPLIT_DATA       =
*    TABLES
**     T_AUSZ1          =
**     T_AUSZ2          =
**     T_AUSZ3          =
**     T_AUSZ4          =
*      t_bkp1 = lt_bkp1
*      t_bkpf = lt_bkpf
*      t_bsec = lt_bsec
*      t_bsed = lt_bsed
*      t_bseg = lt_bseg
*      t_bset = lt_bset
*      t_bseu = lt_bseu
**     T_BSEGC          =
**     T_CCARDEC        =
**     T_PYORDKEY       =
**     T_VBSIP          =
  .

*  lv_kukey = '00743917'.
*  lv_esnum = '00001'.
*  lv_csnum = '000'.
*
*  CALL FUNCTION 'UPDATE_FEBEP_VB_STATUS' IN UPDATE TASK
*    EXPORTING
*      i_awtyp        = 'BKPF'
*      i_awref        = '3500083275'
*      i_awkey        = '3500083275UNES2025'
*      i_aworg        = 'UNES2025'
*      i_posting_area = '1'
*      i_kukey        = lv_kukey
*      i_esnum        = lv_esnum
*      i_komk         = space
*      i_xakon        = space
*      i_rcsnum       = lv_csnum
*      i_augst_avis   = lv_augst
**     I_ML_STATUS    =
**   TABLES
**     I_VBKEP        =
**     I_XFEBCL       =
*    .

*  CLEAR ls_gls0.
*  ls_gls0-rclnt = '350'.
*  ls_gls0-rldnr = '00'.
*  ls_gls0-rrcty = '0'.
*  ls_gls0-rvers = '001'.
*  ls_gls0-bukrs = 'UNES'.
*  ls_gls0-ryear = '2025'.
*  ls_gls0-racct = '0001075011'.
*  ls_gls0-rbusa = 'GEF'.
*  ls_gls0-rtcur = 'USD'.
*  ls_gls0-drcrk = 'S'.
*  ls_gls0-poper = '012'.
*  ls_gls0-docct = 'B'.
*  ls_gls0-docnr = '$1'.
*  ls_gls0-docln = '001'.
*  ls_gls0-cpudt = '20260106'.
*  ls_gls0-cputm = '155907'.
*  ls_gls0-usnam = 'I_BIDAULT'.
*  ls_gls0-tsl = ls_gls0-hsl = '57240.01'.
*  ls_gls0-docty = 'Z1'.
*  ls_gls0-activ = 'RFBU'.
*  APPEND ls_gls0 TO lt_gls0.
*
*  ls_gls0-ryear = '2026'.
*  ls_gls0-poper = '000'.
*  APPEND ls_gls0 TO lt_gls0.
*
*  ls_gls0-ryear = '2025'.
*  ls_gls0-racct = '0001175011'.
*  ls_gls0-drcrk = 'H'.
*  ls_gls0-poper = '012'.
*  ls_gls0-docln = '002'.
*  ls_gls0-tsl = ls_gls0-hsl = '57240.01-'.
*  APPEND ls_gls0 TO lt_gls0.
*
*  ls_gls0-ryear = '2026'.
*  ls_gls0-poper = '000'.
*  APPEND ls_gls0 TO lt_gls0.
*
*  ls_gls0_add-rpmax = '016'.
*  ls_gls0_add-buchkreis = 'UNES'.
*  ls_gls0_add-offset = '012'.
*  ls_gls0_add-post = 'X'.
*  APPEND ls_gls0_add TO lt_gls0_add.
*
*  ls_gls0_add-offset = '000'.
*  APPEND ls_gls0_add TO lt_gls0_add.
*
*  ls_gls0_add-offset = '012'.
*  APPEND ls_gls0_add TO lt_gls0_add.
*
*  ls_gls0_add-offset = '000'.
*  APPEND ls_gls0_add TO lt_gls0_add.
*
*  CALL FUNCTION 'G_FI_POSTING' IN UPDATE TASK
*    TABLES
*      int_gls0     = lt_gls0
*      int_gls0_add = lt_gls0_add.
*
*  IF p_commit = abap_false.
*    ROLLBACK WORK.
*    WRITE: 'Done with Rollback'.
*  ELSE.
*    COMMIT WORK.
*    WRITE: 'Done with Commit'.
*  ENDIF.