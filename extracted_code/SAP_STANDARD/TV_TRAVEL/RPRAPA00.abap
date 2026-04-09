* 6.06
* MAWH1492437   28072010 Erweiterte Programmprüfung im RPRAPA00: Warnung
*                        [note 1492437]

* 6.05
* KCNEB5K026231 05032009 Ergänzung                     [note 1309755]
* KCNEB5K021736 23022009 RPRAPA00: Fehlermeldung 56_CORE 313 bei
*                        Variantenpflege               [note 1309755]
* MAWEB5K015766 02022009 RPRAPA00: Auswahl des Infotyps / Subtyps
*                                                      [note 1300833]

* 6.04
* MAWE4AK022558 10042008 Verhalten bei Fehlern im Testlauf  [1159536]

* 6.03
* MAWE38K063711 07072008 RPRAPA00: Fehlerverhalten in der
*                        Hintergrundverarbeitung       [note 1228103]

* 4.70
* WKUP6BK065240 27022003 kein Abbruch bei PERNR ohne IT 0017 (600444)
* HASP6BK036614          BADIs for file_k exits.
* QIZPL0K032746 02052002 daily run of RPRAPA00...
* QIZPL0K001223 21022002 RPRAPA00 im Core lauffähig gemacht
* QIZAL0K101633 05022002 RPRAPA00 adapted to PS master data
* WKUAL0K039333 02082001 Nachkorrektur zu QIZP9CK053703
* QIZAL0K033506 12072001 Unicode
* 4.6C Support Packages
* QIZP9CK082452 15122000 User-Exit for external vendor numbers created
* QIZP9CK082452 13102000 create company code segments
* QIZP9CK053703 20072000 problems with SY-HOST
* 4.6A
* QIZALRK159176 05121998 BRG00-Data corrected
* 4.5A
* QIZPH4K010807 06071998 server must be available for batch processing
* QIZPH4K000174          Filename improved

*----------------------------------------------------------------------*
* Change history of ALV Development
* Programmer ID : C5056168 (Krunal Nayak)
* Date          : 28.02.2005
*
* Changed Function/flow of the program
* Create/Change/Block Vendor Master Records from HR Master Records
* Develop six ALV lists for File , Log table, errors, Locked PERNRs,
* APAccount and APaccount w/o PERNRs
* Develop application log for statistics and PERNR related messages
*-----------------------------------------------------------------------

*----------------------------------------------------------------------*
* Report  RPRAPA00
*----------------------------------------------------------------------*
* report creates a file based on HR-master-data in order to
* create A/P-accounts by using the Batch-Input programm RFBIKR00
*----------------------------------------------------------------------*
*N740800 Clean up for Selection Screens
* QIZK001223 begin...
* REPORT rprapa00 LINE-SIZE 80 MESSAGE-ID 56 NO STANDARD PAGE HEADING.
REPORT rprapa00 LINE-SIZE 80 MESSAGE-ID 56_core
                NO STANDARD PAGE HEADING.
* QIZK001223 end...

* HASK036614
CLASS cl_exithandler DEFINITION LOAD.
DATA user_exit TYPE REF TO if_ex_badi_exits_rprapa00.
* HASK036614 end

DATA  stringlength TYPE i.
DATA  myname LIKE msxxlist-name.                            "WKUK039333
CONSTANTS: sap_default_btc TYPE bpsrvgrp VALUE 'SAP_DEFAULT_BTC'. "GLW note 1711827
DATA:    default_btc_servers TYPE rsbtc_t_servers,                "GLW note 1711827
         use_default_group   TYPE xfeld.

DATA: w_o_it9 TYPE xfeld.   "GLW note 2063439


DATA subrc_inftyp LIKE sy-subrc.                            "WKUK039333
DATA: m_shown TYPE xfeld.

* Begin of MAWK015766
DATA gv_subtype TYPE c LENGTH 4.
DATA gv_subty      TYPE t591a-subty.
* End of MAWK015766

* Data definition
************* Start commenting C5056168 28/02/2005*****************
*INCLUDE rprapade.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************
INCLUDE rprapade_alv.
************* End ALV Coding C5056168 28/02/2005*****************

* Begin of MAWK015766
* Infotypen
SELECTION-SCREEN BEGIN OF BLOCK 8 WITH FRAME TITLE text-u08.

* U06 Subtyp Infotyp 0006 (Anschriften)
SELECTION-SCREEN BEGIN OF BLOCK 6 WITH FRAME TITLE text-u06.
PARAMETERS p_subty6 TYPE t591a-subty OBLIGATORY DEFAULT '1'.
SELECTION-SCREEN END OF BLOCK 6.

* U07 Subtyp Infotyp 0009 (Bankverbindung)
SELECTION-SCREEN BEGIN OF BLOCK 7 WITH FRAME TITLE text-u07.
PARAMETERS p_subty9 TYPE t591a-subty OBLIGATORY DEFAULT '2'.
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS: no_9_ok TYPE xfeld AS CHECKBOX USER-COMMAND no_9.    "GLW note
SELECTION-SCREEN POSITION 3.
SELECTION-SCREEN COMMENT (40) text-u09 FOR FIELD no_9_ok.
SELECTION-SCREEN POSITION 44.
PARAMETERS: no_dele TYPE xfeld AS CHECKBOX MODIF ID sc1.
SELECTION-SCREEN POSITION 47.
SELECTION-SCREEN COMMENT (75) text-u10 FOR FIELD no_dele.
SELECTION-SCREEN END OF LINE.
SELECTION-SCREEN END OF BLOCK 7.

SELECTION-SCREEN END OF BLOCK 8.
* End of MAWK015766

SELECTION-SCREEN BEGIN OF BLOCK 3 WITH FRAME TITLE text-u03.
SELECTION-SCREEN BEGIN OF BLOCK 5 WITH FRAME TITLE text-u05.
* QIZKK082452 begin...
*PARAMETERS: CRE_A_P LIKE RPRXXXXX-KR_FELD1 RADIOBUTTON GROUP HINZ,
PARAMETERS: cre_a_p LIKE rprxxxxx-kr_feld1 RADIOBUTTON GROUP hinz.
*
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN COMMENT (3) text-001. " FOR FIELD CREA_CC.
SELECTION-SCREEN POSITION 4.
*PARAMETERS: crea_cc LIKE rprxxxxx-kr_feld8 DEFAULT ' '.
PARAMETERS: crea_cc LIKE ftra_xxxxx-xfeld_01 DEFAULT ' ' AS CHECKBOX.
*SELECTION-SCREEN COMMENT 7(75) text-002.                       "N740800
SELECTION-SCREEN COMMENT 7(75) text-002 FOR FIELD  crea_cc. "N740800
SELECTION-SCREEN END OF LINE.
*           REF_A_P LIKE RPRXXXXX-KR_FELD2 RADIOBUTTON GROUP HINZ,
PARAMETERS: ref_a_p LIKE rprxxxxx-kr_feld2 RADIOBUTTON GROUP hinz.
* QIZKK082452 end...

* GLW note 2099681 begin
SELECTION-SCREEN ULINE .
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN COMMENT 1(75) text-h21.
SELECTION-SCREEN END OF LINE.
* GLW note 2099681 end
PARAMETERS: cha_a_p LIKE rprxxxxx-kr_feld3 RADIOBUTTON GROUP hinz,
* QIZK032746 begin...
*           aedat LIKE prel-aedtm,
            aedat   LIKE prel-aedtm.
PARAMETERS: daily LIKE ftra_xxxxx-xfeld_02 RADIOBUTTON GROUP hinz.
SELECTION-SCREEN BEGIN OF LINE.
SELECTION-SCREEN COMMENT (75) text-003.      " FOR FIELD DAILY.
SELECTION-SCREEN END OF LINE.
PARAMETERS unlock TYPE xfeld.
SELECTION-SCREEN ULINE.   "GLW note 2099681
*           del_a_p LIKE rprxxxxx-kr_feld4 RADIOBUTTON GROUP hinz.
PARAMETERS  del_a_p LIKE rprxxxxx-kr_feld4 RADIOBUTTON GROUP hinz.
PARAMETERS:  no_del  LIKE rprxxxxx-kr_feld4 AS CHECKBOX,  " GLW note 1777015
             no_lock LIKE rprxxxxx-kr_feld4 AS CHECKBOX.
* QIZK032746 end...
SELECTION-SCREEN BEGIN OF LINE.                             "GLW note 1835204
PARAMETERS: inac_too TYPE xfeld AS CHECKBOX.                "GLW note 1835204
SELECTION-SCREEN COMMENT 2(75) text-004 FOR FIELD inac_too. "GLW note 1835204
SELECTION-SCREEN END OF LINE.                               "GLW note 1835204
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS creainac TYPE xfeld AS CHECKBOX. "GLW note 2577011
SELECTION-SCREEN COMMENT 2(75) TEXT-005 FOR FIELD creainac.
SELECTION-SCREEN END OF LINE.
SELECTION-SCREEN END OF BLOCK 5.
SELECTION-SCREEN BEGIN OF BLOCK 1 WITH FRAME TITLE text-u01.
PARAMETERS: temp_a_p LIKE lfb1-lifnr MATCHCODE OBJECT kred.
SELECTION-SCREEN END OF BLOCK 1.
SELECTION-SCREEN END OF BLOCK 3.

SELECTION-SCREEN BEGIN OF BLOCK 2 WITH FRAME TITLE text-u02.
PARAMETERS:
*  file_o   LIKE rprxxxxx-seq_in OBLIGATORY,
  file_o TYPE rfbifile, "GLW note 2162990
  file_pr LIKE rprxxxxx-kr_feld8 DEFAULT ' '.
SELECTION-SCREEN END OF BLOCK 2.

SELECTION-SCREEN BEGIN OF BLOCK 0 WITH FRAME TITLE text-u00.
PARAMETERS:
  testrun  LIKE rprxxxxx-kr_feld5 RADIOBUTTON GROUP binp,
  actmode  LIKE rprxxxxx-kr_feld6 RADIOBUTTON GROUP binp,
  back_job TYPE xfeld AS CHECKBOX,              "KCNK021736
  jobname  LIKE tbtco-jobname DEFAULT 'A/P_ACCOUNTS',
  m_name   LIKE rprxxxxx-map_name DEFAULT 'A/P_ACCOUNTS',
* QIZK010807 begin...
* fileonly like rprxxxxx-kr_feld7 radiobutton group binp default 'X'.
  fileonly LIKE rprxxxxx-kr_feld7 RADIOBUTTON GROUP binp DEFAULT 'X',
  uname    LIKE rprxxxxx-uname,
  mandant  LIKE rprxxxxx-mandt.
* QIZK010807 end...
SELECTION-SCREEN END OF BLOCK 0.

SELECTION-SCREEN BEGIN OF BLOCK 4 WITH FRAME TITLE text-u04.
PARAMETERS: adr_kana LIKE rprxxxxx-kr_feld9 NO-DISPLAY.
SELECTION-SCREEN END OF BLOCK 4.

AT SELECTION-SCREEN OUTPUT.
  IF no_9_ok IS INITIAL.
    CLEAR no_dele.
    LOOP AT SCREEN.
      CASE screen-name.
        WHEN 'NO_DELE'.
          screen-input = 0.
          MODIFY SCREEN.
          CLEAR no_dele.
          EXIT.
      ENDCASE.
    ENDLOOP.
  ELSE.
    LOOP AT SCREEN.
      CASE screen-name.
        WHEN 'NO_DELE'.
          screen-input = 1.
          MODIFY SCREEN.
          EXIT.
      ENDCASE.
    ENDLOOP.
  ENDIF.

INITIALIZATION.

  LOOP AT SCREEN.
    CASE screen-name.
      WHEN 'NO_DELE'.
        IF no_9_ok = ' '.
          screen-input = 0.
          MODIFY SCREEN.
          CLEAR no_dele.
        ENDIF.
        EXIT.
    ENDCASE.
  ENDLOOP.

  pnptimed = 'D'.
*  aedat(6) = sy-datum(6).
*  aedat+6(2) = '01'.

  aedat = sy-datum - 31. "GLW note 2560276

  repname = sy-repid.
  CALL FUNCTION 'HR_MAPNAME_VERIFY'
    EXPORTING
      mapname    = m_name
      reportname = repname
    IMPORTING
      mapname    = m_name.
* prepare the filename
  CALL 'C_SAPGPARAM' ID 'NAME'  FIELD 'DIR_GLOBAL'        "#EC CI_CCALL
                     ID 'VALUE' FIELD file_o.
  stringlength = strlen( file_o ).
* if stringlength > 33.                                     "QIZK000174
  IF stringlength > 124.                                    "QIZK000174 "GLW note 2248550
    CLEAR file_o.
* elseif file_o ca '/'.                                     "QIZK000174
  ELSE.                                                     "QIZK000174
    IF file_o CA '/'.                                       "QIZK000174
*    file_o+33 = '/APACCT'.                                 "QIZK000174
      file_o+stringlength = '/'.                            "QIZK000174
    ELSE.
*    file_o+33 = '\APACCT'.                                 "QIZK000174
      file_o+stringlength = '\'.                            "QIZK000174
    ENDIF.                                                  "QIZK000174
    CASE stringlength.                                      "QIZK000174
      WHEN '123'.                                            "QIZK000174"GLW note 2248550
        file_o+35 = 'APACT'.                                "QIZK000174
      WHEN '124'.                                            "QIZK000174 "GLW note 2248550
        file_o+36 = 'APAC'.                                 "QIZK000174
      WHEN '125'.                                            "QIZK000174
        file_o+37 = 'APA'.                                  "QIZK000174   "GLW note 2248550
      WHEN OTHERS.                                          "QIZK000174
        file_o+34 = 'APACT'.                                "QIZK000174
    ENDCASE.                                                "QIZK000174
  ENDIF.
  CONDENSE file_o NO-GAPS.

  uname = sy-uname.
  mandant = sy-mandt.

* FORM-routines
************* Start commenting C5056168 28/02/2005*****************
*  INCLUDE rprapafo.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************
  INCLUDE rprapafo_alv.
************* End ALV Coding C5056168 28/02/2005*******************

* to process features
  INCLUDE rpumkc00.
* User-exits
  INCLUDE rprapaex.
  INCLUDE rprapaex_001.                                     "QIZK082452

* Begin of MAWK015766
AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_subty6.
* Subtyp Infotyp 0006 (Anschriften)
  gv_subtype = '0006'.
  CALL SCREEN 100 STARTING AT 10 5
                  ENDING   AT 50 20.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_subty9.
* Subtyp Infotyp 0009 (Bankverbindung)
  gv_subtype = '0009'.
  CALL SCREEN 100 STARTING AT 10 5
                  ENDING   AT 50 20.

AT LINE-SELECTION.
  CHECK NOT gv_subty IS INITIAL.

  CASE gv_subtype.
    WHEN '0006'.
*     U06 Subtyp Infotyp 0006 (Anschriften)
      p_subty6 = gv_subty.
    WHEN '0009'.
*     U07 Subtyp Infotyp 0009 (Bankverbindung)
      p_subty9 = gv_subty.
  ENDCASE.

  LEAVE TO SCREEN 0.
* End of MAWK015766

AT SELECTION-SCREEN ON jobname.
  IF NOT actmode IS INITIAL AND jobname IS INITIAL.
    IF back_job IS NOT INITIAL.                             "KCNK021736
      MESSAGE e032.                      "Please define the jobname
      sw_stop = 'X'.
      STOP.
    ENDIF.                                                  "KCNK021736
  ENDIF.

AT SELECTION-SCREEN ON m_name.
  IF NOT actmode IS INITIAL AND m_name IS INITIAL.
    MESSAGE e033.
    sw_stop = 'X'.
    STOP.
  ENDIF.

  CALL FUNCTION 'HR_MAPNAME_VERIFY'
    EXPORTING
      mapname    = m_name
      reportname = repname
    IMPORTING
      mapname    = m_name.

AT SELECTION-SCREEN ON file_o.
  IF file_o IS INITIAL.
    MESSAGE e033.                      "Please define the filename
    sw_stop = 'X'.
    STOP.
  ENDIF.

AT SELECTION-SCREEN ON BLOCK 0.                             "QIZK010807
  IF fileonly IS INITIAL AND                                "QIZK010807
    ( uname NE sy-uname OR mandant NE sy-mandt ).           "QIZK010807

    IF ( m_shown IS INITIAL AND sy-batch IS INITIAL ).
      IF NOT ( sy-ucomm = 'ONLI' OR sy-ucomm = 'PRIN' OR sy-ucomm = 'SJOB' ).
        MESSAGE i016 WITH                                   "QIZK010807
      'Ein abweichender Username/Mandant'(us0)              "QIZK010807
      'ist nur bei "Nur Arbeitsdatei erzeugen" erlaubt'(us1).
*    sw_stop = 'X'.                                          "QIZK010807
*    STOP.                                                   "QIZK010807
*    uname = sy-uname.  "GLW note 3137774
*    mandant = sy-mandt.
        m_shown = abap_true.
      ENDIF.
    ENDIF.
    IF sy-ucomm = 'ONLI' OR sy-ucomm = 'PRIN' OR sy-ucomm = 'SJOB'.
      MESSAGE w016 WITH                                     "QIZK010807
    'Ein abweichender Username/Mandant'(us0)                "QIZK010807
    'ist nur bei "Nur Arbeitsdatei erzeugen" erlaubt'(us1).
    ENDIF.
  ENDIF.                                                    "QIZK010807

* IF NOT actmode IS INITIAL.                     "QIZK010807"KCNK026231
  IF NOT actmode  IS INITIAL AND                            "KCNK026231
     NOT back_job IS INITIAL.                               "KCNK026231
    INCLUDE tskhincl.                                       "QIZK010807
    DATA: BEGIN OF server_list OCCURS 10.                   "QIZK010807
            INCLUDE STRUCTURE msxxlist.                     "QIZK010807
    DATA: END OF server_list.                               "QIZK010807

*   DATA:  myname LIKE msxxlist-name.           "QIZK053703 "WKUK039333

    CALL 'C_SAPGPARAM' ID 'NAME'  FIELD 'rdisp/myname'    "#EC CI_CCALL
                       ID 'VALUE' FIELD myname.             "QIZK053703

    CALL FUNCTION 'TH_SERVER_LIST'                          "QIZK010807
      EXPORTING                                          "QIZK010807
        services = ms_btc                       "QIZK010807
      TABLES                                             "QIZK010807
        list     = server_list.                 "QIZK010807

*   LOOP AT SERVER_LIST WHERE HOST EQ SY-HOST.  "QIZK010807 "QIZK053703
    LOOP AT server_list WHERE name EQ myname.               "QIZK053703
    ENDLOOP.                                                "QIZK010807
    IF sy-subrc NE 0.                                       "QIZK010807
*     MESSAGE E313 WITH SY-HOST.                "QIZK010807 "QIZK053703
      MESSAGE e313 WITH myname.                             "QIZK053703
    ENDIF.                                                  "QIZK010807
  ENDIF.                                                    "QIZK010807

** GLW note 1711827 begin
*  IF sy-batch IS INITIAL.
** if program is started in dialogue, we must respect the servergroup SAP_DEFAULT_BTC for the RFBIKR00 job. All jobs
** without explicit target server(group) shall be started in this server group if defined in SM61. If RPRAPA00 is processed
** in background itselfe, we don't need to respect this servergroup; myname contains anyhow a server of SAP_DEFAULT_BTC or a
** target server(group) was entered explicitely.
*    CALL FUNCTION 'RSBATCH_GET_SERVER_AND_GROUP'
*      EXPORTING
*        i_group     = sap_default_btc
*      IMPORTING
*        e_t_servers = default_btc_servers.
*
*    IF default_btc_servers[] IS NOT INITIAL.
*      use_default_group = 'X'.
*    ENDIF.
*  ENDIF.
** GLW note 1711827 end

START-OF-SELECTION.

  IF fileonly IS INITIAL AND                                "QIZK010807
      ( uname NE sy-uname OR mandant NE sy-mandt ).         "QIZK010807
    MESSAGE e016 WITH                                       "QIZK010807
      'Ein abweichender Username/Mandant'(us0)              "QIZK010807
      'ist nur bei "Nur Arbeitsdatei erzeugen" erlaubt'(us1).
    sw_stop = 'X'.                                          "QIZK010807
    STOP.                                                   "QIZK010807
  ENDIF.

* HASK036614
  CALL METHOD cl_exithandler=>get_instance "#EC CI_BADI_OLD "#EC CI_BADI_GETINST
    CHANGING
      instance = user_exit.
* HASK036614 end


* QIZK101633 begin...
  CALL FUNCTION 'FUNCTION_EXISTS'
    EXPORTING
      funcname           = 'FM_PSO43_PSOSD_READ'
    EXCEPTIONS
      function_not_exist = 1
      OTHERS             = 2.

  IF sy-subrc EQ 0.
    CALL FUNCTION 'FM_PSO43_PSOSD_READ'                     "#EC *
      IMPORTING                                             "#EC *
        e_active = ps_master_data_active.                   "#EC *
  ENDIF.
* QIZK101633 end...

  IF NOT cre_a_p IS INITIAL.
* create A/P account
    t_code = 'XK01'.
  ENDIF.
* QIZK032746 begin...
* IF NOT cha_a_p IS INITIAL OR NOT ref_a_p IS INITIAL.
  IF NOT cha_a_p IS INITIAL OR NOT ref_a_p IS INITIAL
                            OR NOT daily IS INITIAL.
* QIZK032746 end...
* change A/P account / refresh A/P accounts
    t_code = 'XK02'.
  ENDIF.
  IF NOT del_a_p IS INITIAL.
* lock A/P account
    t_code = 'XK05'.
  ENDIF.

* Read the template A/P-account.
  PERFORM read_a_p_account USING temp_a_p.
* open dataset to create file
* QIZK033506 Unicode begin...
* OPEN DATASET file_o IN TEXT MODE FOR OUTPUT MESSAGE msg.

* Begin of HZIH1517930
  CONSTANTS gc_fname TYPE fileintern VALUE 'FI_TV_RPRAPA00'.

  CALL FUNCTION 'FILE_VALIDATE_NAME'
    EXPORTING
      logical_filename           = gc_fname
    CHANGING
      physical_filename          = file_o
    EXCEPTIONS
      logical_filename_not_found = 1
      validation_failed          = 2
      OTHERS                     = 3.

  IF sy-subrc <> 0.
    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
      WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
  ENDIF.
* End of HZIH1517930

  OPEN DATASET file_o IN TEXT MODE FOR OUTPUT
                         ENCODING DEFAULT
                         MESSAGE msg.
* QIZK033506 Unicode end...
  IF sy-subrc NE 0 OR msg IS NOT INITIAL.
************* Start commenting C5056168 28/02/2005*****************
*    FORMAT COLOR 6.
*    WRITE:/1(80) sy-uline.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE: 2(78) msg.
*    WRITE: 80 sy-vline, /1(80) sy-uline.
************* End commenting C5056168 28/02/2005*******************

    sw_stop = 'X'.
    IF msg IS NOT INITIAL.
      PERFORM message_os.
    ENDIF.
    STOP.
  ENDIF.
* Mappenvorsatz
* perform nodata_in_structure using 'BGR00' nodata.         "QIZK159176
  PERFORM nodata_in_structure USING 'BGR00' space.          "QIZK159176
  bgr00-stype = '0'.
  bgr00-group = m_name.
* bgr00-mandt = sy-mandt.                                   "QIZK010807
  bgr00-mandt = mandant.                                    "QIZK010807
* bgr00-usnam = sy-uname.                                   "QIZK010807
  bgr00-usnam = uname.                                      "QIZK010807
  bgr00-nodata = nodata.                                    "QIZK159176

  CALL METHOD user_exit->set_values_for_bgr00               "HASK036614
    CHANGING                                          "HASK036614
      c_bgr00 = bgr00.                                "HASK036614

* file_k = bgr00.                                           "MAWH1492437
  PERFORM move_struct_to_file USING bgr00                   "MAWH1492437
                                    'BGR00'                 "MAWH1492437
                           CHANGING file_k.                 "MAWH1492437
  PERFORM write_file USING '0' file_k 'X' space.

  TRANSFER file_k TO file_o.

  GET pernr.
  sel_pernr = sel_pernr + 1.
  CLEAR w_o_it9.   "GLW note 2063439
* Check whether the personnel number is locked or not.
  PERFORM check_locked.
* Read infotype P0001 in order to know P0001-BUKRS -> existence....
  CALL FUNCTION 'HR_READ_INFOTYPE_AUTHC_DISABLE'.
  CLEAR p0017_help. REFRESH p0017_help.                     "WKUK039334

  CALL FUNCTION 'HR_READ_INFOTYPE'                          "WKUK039334
    EXPORTING                                            "WKUK039334
      tclas           = 'A'                           "WKUK039334
      pernr           = pernr-pernr                   "WKUK039334
      infty           = '0017'                        "WKUK039334
      begda           = pn-begda                      "WKUK039334
      endda           = pn-endda                      "WKUK039334
    IMPORTING                                            "WKUK039334
      subrc           = subrc_inftyp                  "WKUK039334
    TABLES                                               "WKUK039334
      infty_tab       = p0017_help                    "WKUK039334
    EXCEPTIONS                                           "WKUK039334
      infty_not_found = 1                             "WKUK039334
      OTHERS          = 2.                            "WKUK039334
* keine Reaktion nötig, wenn IT 0017 nicht vorhanden        "WKUK065240
* IF subrc_inftyp <> 0 OR sy-subrc <> 0.        "WKUK039334 "WKUK065240
*   CALL FUNCTION 'TRAVEL_EXISTS'               "QIZK001223 "WKUK065240
*     EXCEPTIONS                                "QIZK001223 "WKUK065240
*       travel_not_existing       = 1           "QIZK001223 "WKUK065240
*       others                    = 2.          "QIZK001223 "WKUK065240
*   IF sy-subrc EQ 0.                           "QIZK001223 "WKUK065240
*     MESSAGE s701 WITH '0017' sy-datum.        "WKUK039334 "WKUK065240
*     LEAVE TO SCREEN 0.                        "WKUK039334 "WKUK065240
*   ENDIF.                                      "QIZK001223 "WKUK065240
* ENDIF.                                        "WKUK039334 "WKUK065240

  rp_provide_from_last p0000 space pn-begda pn-endda.
  rp_provide_from_last p0001 space pn-begda pn-endda.
  PERFORM err-table USING '0001' pn-begda pn-endda pnp-sw-found.
*  IF p0000-stat2 NE '3' AND t_code NE 'XK05'.
  IF  p0000-stat2 NE '3' AND ( ( t_code EQ 'XK01' AND creainac IS INITIAL ) OR ( inac_too NE abap_true AND t_code EQ 'XK02' ) ). "GLW note 1835204  "GLW note 2577011
* employee is not active
    PERFORM err-table USING '0001' pn-begda pn-endda 'A'.
  ENDIF.
* BEGIN WKUK039334
* rp_provide_from_last p0017 space pn-begda pn-endda.
* IF NOT p0017-bukrs IS INITIAL.
*   p0001-bukrs = p0017-bukrs.
* ENDIF.
  rp_provide_from_last p0017_help space pn-begda pn-endda.
  IF NOT p0017_help-bukrs IS INITIAL.
    p0001-bukrs = p0017_help-bukrs.
  ENDIF.
* END WKUK039334
  PERFORM re001 USING p0001-bukrs t001_ort01
                      t001_ktopl  t001_land1
                      t001_waers  t001_periv
                      t001_spras.
  PERFORM re500p USING p0001-werks.
* Does the template company code exist? (create-mode and refresh-mode)
  IF t_code EQ 'XK01' OR
   ( t_code EQ 'XK02' AND NOT ref_a_p IS INITIAL ) OR ( ( t_code = 'XK01' OR t_code = 'XK02' ) AND no_9_ok IS NOT INITIAL ). "GLW ntoe 2063439
    SELECT SINGLE * FROM lfb1
                WHERE lifnr EQ temp_a_p AND bukrs EQ p0001-bukrs.
    IF sy-subrc EQ 0.
      *lfb1 = lfb1.
      SELECT * FROM lfb5 WHERE lifnr EQ temp_a_p            "QIZK003419
                         AND bukrs   EQ p0001-bukrs         "QIZK003419
                         AND maber   EQ space.              "QIZK003419
        *lfb5 = lfb5.                                       "QIZK003419
      ENDSELECT.                                            "QIZK003419
    ELSE.
      PERFORM fill_error_int USING pernr-pernr
                                   '56_CORE'                "QIZK001223
                                   'E'
                                   '040'
                                   temp_a_p
                                   p0001-bukrs
                                   space
                                   space.
*      sw_stop = 'X'.   "GLW note 1989485
*     STOP.                                                 "MAWK022558
      PERFORM stop_or_reject.                               "MAWK022558
    ENDIF.
*   *lfb5-mahna = '0001'.                                "QIZTestcoding
*   *lfb5-gmvdt = '19980228'.                            "QIZTestcoding
    PERFORM auth_a_p_account_lfb1.
  ENDIF.
* Check whether the employee exists as an vendor or not.
  PERFORM check_existence USING pernr-pernr p0001-bukrs subrc.
* QIZK082452 begin...
* search for PERNR independent of company code...
  CLEAR vendor_no.
  CASE t_code.
    WHEN 'XK01'.
* create mode
      IF NOT ( subrc IS INITIAL ) AND NOT ( crea_cc IS INITIAL ).
* There is no vendor for PERNR and BUKRS;
* Is there a vendor for PERNR independent of BUKRS?
        PERFORM check_existence_without_bukrs USING pernr-pernr
                                                    vendor_no.
        IF NOT vendor_no IS INITIAL.
* There is a vendor for PERNR independent of BUKRS;
* Does a LFB1-segment exist for VENDOR_NO and BUKRS (w/o PERNR)?
          PERFORM check_existence_with_bukrs USING vendor_no
                                                   p0001-bukrs.
        ENDIF.
      ENDIF.
    WHEN 'XK02'.
* change mode
      IF NOT ( subrc IS INITIAL ).
* There is no vendor for PERNR and BUKRS;
* Is there a vendor for PERNR independent of BUKRS?
        PERFORM check_existence_without_bukrs USING pernr-pernr
                                                    vendor_no.
        IF NOT vendor_no IS INITIAL.
* There is a vendor for PERNR independent of BUKRS;
* Does a LFB1-segment exist for VENDOR_NO and BUKRS (w/o PERNR)?
          PERFORM check_existence_with_bukrs USING vendor_no
                                                   p0001-bukrs.
        ENDIF.
      ENDIF.
      CLEAR vendor_no.
    WHEN OTHERS.
  ENDCASE.
* QIZK082452 end...
  CASE t_code.
    WHEN 'XK01'.
* create A/P account
      IF subrc IS INITIAL.
* there is an A/P account
        LOOP AT errortable WHERE pernr EQ pernr-pernr.
          EXIT.
        ENDLOOP.
* is the employee already in errortable?
        IF NOT sy-subrc IS INITIAL.
          sel_ex_vendors = sel_ex_vendors + 1.
          apaccounttable-pernr = pernr-pernr.
          apaccounttable-name  = p0001-ename.
          APPEND apaccounttable.
          REJECT.
        ENDIF.
      ENDIF.
    WHEN 'XK02'.
* change A/P account
      IF NOT subrc IS INITIAL.
* there is no A/P account
        LOOP AT errortable WHERE pernr EQ pernr-pernr.
          EXIT.
        ENDLOOP.
* is the employee already in errortable?
        IF NOT sy-subrc IS INITIAL.
          sel_no_vendors = sel_no_vendors + 1.
          apaccounttable-pernr = pernr-pernr.
          apaccounttable-name  = p0001-ename.
          APPEND apaccounttable.
          REJECT.
        ENDIF.
      ENDIF.
    WHEN 'XK05'.
* lock A/P account
      IF subrc IS INITIAL AND old_vendor_lfb1-sperr IS NOT INITIAL. "GLW note 2110208
* there is a vendor and it is already locked
        REJECT. "reject. No reason for error
      ENDIF.
      IF NOT subrc IS INITIAL.
* there is no A/P account
        LOOP AT errortable WHERE pernr EQ pernr-pernr.
          EXIT.
        ENDLOOP.
* is the employee already in errortable?
        IF NOT sy-subrc IS INITIAL.
          sel_no_vendors = sel_no_vendors + 1.
          apaccounttable-pernr = pernr-pernr.
          apaccounttable-name  = p0001-ename.
          APPEND apaccounttable.
          REJECT.
        ENDIF.
      ENDIF.
  ENDCASE.
* Read HR-master-data
  PERFORM hr_master_data USING pn-begda pn-endda.
* fill list of all accepted employees
  PERFORM log_table.
* fill file
  PERFORM create_file_a_p.

END-OF-SELECTION.
* close dataset
  CLOSE DATASET file_o.
* For Testing: read file, which was created as a UNIX-File
* perform read_file_k.
  IF sw_stop IS INITIAL.
* Print logtable of all employees who were transfered to file.
    PERFORM display_log_table.
* Print the lists with all rejected employees
    PERFORM display_err_table.
* Submit RFBIKR00
    PERFORM sub_rfbikr00.
  ENDIF.
* Print messages and statistics
************* Start commenting C5056168 08/03/2005*****************
*  PERFORM display_messages.
************* End commenting C5056168 08/03/2005*******************
  IF sw_stop IS INITIAL.
    PERFORM statistics.
  ENDIF.

************* Start ALV Coding C5056168 28/02/2005*****************

  PERFORM display_alv_list USING '1'. "Output FILE ALV table

************* End ALV Coding C5056168 28/02/2005*******************

************* Start commenting C5056168 28/02/2005*****************
*TOP-OF-PAGE.
*  SKIP TO LINE 1.
*  CLEAR h_line.
*  CASE t_code.
*    WHEN 'XK01'.
*      WRITE text-h20 TO h_line CENTERED.
*    WHEN 'XK02'.
*      IF ref_a_p IS INITIAL.
*        WRITE text-h21 TO h_line CENTERED.
*      ELSE.
*        WRITE text-h23 TO h_line CENTERED.
*      ENDIF.
*    WHEN 'XK05'.
*      WRITE text-h22 TO h_line CENTERED.
*  ENDCASE.
*  WRITE sy-datum DD/MM/YYYY TO h_line(10).
*  WRITE: sy-pagno TO h_line+78(2).
*  WRITE: h_line COLOR 1 INTENSIFIED INVERSE.
*  ULINE.
*  SKIP TO LINE 3.
************* End commenting C5056168 28/02/2005*******************

* begin of MAWK063711
  IF NOT sw_stop IS INITIAL.                 "MAWK500244 / note 1228103
    IF sy-batch = 'X'.
*
      IF testrun IS INITIAL.
*     text-e14: Produktivlauf:
*     text-e10: Fehler bei der Verarbeitung der Daten
        MESSAGE i016 WITH text-e14 text-e10.
*     text-e14: Produktivlauf:
*     text-e11: Lesen Sie das Fehlerprotokoll in der Spool-Datei
        MESSAGE i016 WITH text-e14 text-e11.
*     text-e14: Produktivlauf:
*     text-e12: Die Hintergrundverarbeitung wird abgebrochen
        MESSAGE e016 WITH text-e14 text-e12.
      ELSE.
*     text-e13: Testlauf:
*     text-e10: Fehler bei der Verarbeitung der Daten
        MESSAGE i016 WITH text-e13 text-e10.
*     text-e13: Testlauf:
*     text-e11: Lesen Sie das Fehlerprotokoll in der Spool-Datei
        MESSAGE i016 WITH text-e13 text-e11.
*     text-e13: Testlauf:
*     text-e12: Die Hintergrundverarbeitung wird abgebrochen
        MESSAGE e016 WITH text-e13 text-e12.
      ENDIF.
    ENDIF.
  ENDIF.                                     "MAWK500244 / note 1228103
* end of MAWK063711

  INCLUDE rprapa00_pbo.

FORM message_os.
  DATA mt TYPE c LENGTH 200.
  TYPES c50 TYPE c LENGTH 50.
  DATA lt_mt TYPE TABLE OF c50.
  DATA wa50 TYPE c50.
  CONCATENATE 'OPEN DATASET' file_o 'FOR OUTPUT:' 'Message =' msg INTO mt SEPARATED BY space.
* whatever error text is in msg: this comes directly from OS.
  CALL FUNCTION 'RKD_WORD_WRAP'
    EXPORTING
      textline            = mt
      outputlen           = 50
    TABLES
      out_lines           = lt_mt
    EXCEPTIONS
      outputlen_too_large = 1
      OTHERS              = 2.
  IF sy-subrc <> 0.
* Implement suitable error handling here
  ENDIF.

  CLEAR: sy-msgv1, sy-msgv2, sy-msgv3, sy-msgv4.

  LOOP AT lt_mt INTO wa50.
    CASE sy-tabix.
      WHEN 1.
        sy-msgv1 = wa50.
      WHEN 2.
        sy-msgv2 = wa50.
      WHEN 3.
        sy-msgv3 = wa50.
      WHEN 4.
        sy-msgv4 = wa50.
    ENDCASE.
  ENDLOOP.

  MESSAGE ID 'F1' TYPE 'E' NUMBER 600 WITH  sy-msgv1  sy-msgv2 sy-msgv3  sy-msgv4. "GLW note 2767908
ENDFORM.