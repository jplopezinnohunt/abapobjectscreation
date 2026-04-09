* ZFJN1506975 08092010 Country missing in case ptrv_vatdetail is empty

FUNCTION get_travel_vat_refund_data.
*"----------------------------------------------------------------------
*"*"Lokale Schnittstelle:
*"  IMPORTING
*"     VALUE(IV_STARTDATE) TYPE  DATS
*"     VALUE(IV_ENDDATE) TYPE  DATS
*"  TABLES
*"      ET_VAT_REFUND_DATA STRUCTURE  PTK_VAT_REFUND_DATA
*"      IT_COMPCODE STRUCTURE  PTK_BUKRS
*"      IT_INTCA STRUCTURE  PTK_INTCA
*"      RETURN STRUCTURE  BAPIRET2
*"      IT_COMPCODE_GLOB STRUCTURE  PTK_BUKRS_GLOB OPTIONAL
*"----------------------------------------------------------------------

  TYPES: BEGIN OF ts_t001,
           bukrs TYPE bukrs,
           land1 TYPE land1,
         END OF  ts_t001.
  TYPES: BEGIN OF ts_t500p,
           persa TYPE persa,
           bukrs TYPE bukrs,
           land1 TYPE land1,
         END OF  ts_t500p.
  TYPES: BEGIN OF ts_pernr,
           pernr TYPE pernr_d,
           persa TYPE persa,
           bukrs TYPE bukrs,
           land1 TYPE land1,
         END OF   ts_pernr.
  TYPES: BEGIN OF ts_head,
           pernr TYPE pernr_d,
           reinr TYPE reinr,
           hdvrs TYPE ptrv_hdvrs,
           morei TYPE morei,                             "MAWH1497299
         END OF ts_head.
  TYPES: BEGIN OF ts_perio,
           pernr TYPE pernr_d,
           reinr TYPE reinr,
           perio TYPE ptrv_perod,
           pdvrs TYPE ptrv_pdvrs,
           hdvrs TYPE ptrv_hdvrs,                        "MAWH1497299
           morei TYPE morei,                             "MAWH1497299
         END OF ts_perio.

* Begin of MAWH1497299
  TYPES: BEGIN OF ts_land1_region,
           land1 TYPE t702o-land1,
           rgion TYPE t702o-rgion,
           intca TYPE t702o-intca,
         END OF ts_land1_region.
* End of MAWH1497299

  DATA: lit_t001         TYPE TABLE OF ts_t001 WITH KEY bukrs,
        lit_t500p        TYPE TABLE OF ts_t500p WITH KEY persa,
        lit_pernr        TYPE TABLE OF ts_pernr WITH KEY pernr,
        lit_head         TYPE TABLE OF ts_head WITH NON-UNIQUE KEY pernr reinr,
        lit_perio        TYPE TABLE OF ts_perio WITH NON-UNIQUE KEY pernr reinr perio,
        lit_beleg        TYPE TABLE OF ptk03 WITH NON-UNIQUE KEY bldat,
        lit_land1_region TYPE TABLE OF ts_land1_region,     "MAWH1497299
        lit_temp_data    TYPE TABLE OF recdata.

  DATA: lv_startdate    TYPE dats,
        lv_enddate      TYPE dats,
        lv_trip_start   TYPE dats,
        lv_trip_end     TYPE dats,
        lv_logsys       TYPE logsys,
        lv_tekey        TYPE ptp00,
        lv_count        TYPE i,
        lv_index        TYPE i,

        ls_t001         TYPE ts_t001,
        ls_pernr        TYPE ts_pernr,
        ls_perio        TYPE ts_perio,
        ls_temp_data    TYPE recdata,
        ls_vat_details  TYPE ty_s_data,
        ls_land1_region TYPE ts_land1_region,              "MAWH1497299
        ls_t702o        TYPE t702o,                        "MAWH1497299
        ls_vat_ref_data TYPE ptk_vat_refund_data.

  DATA: l_msgty      TYPE symsgty,
        l_msgid      LIKE sy-msgid,
        l_msgno      LIKE sy-msgno,
        l_msgv1      LIKE sy-msgv1,
        l_msgv2      LIKE sy-msgv2,
        l_msgv3      LIKE sy-msgv3,
        lv_morei_old TYPE morei,                        "MAWH1497299
        l_msgv4      LIKE sy-msgv4.

  INFOTYPES: 0017 OCCURS 2.

  FIELD-SYMBOLS:
    <fs_temp_data>    TYPE recdata,
    <fs_land1_region> TYPE ts_land1_region,             "MAWH1497299
    <fs_perio>        TYPE ts_perio,                    "MAWH1497299
    <fs_head>         TYPE ts_head,                     "MAWH1497299
    <fs_intca>        TYPE ptk_intca.

  CONSTANTS: c_bufferdays TYPE i       VALUE 90,
             c_msg_err    TYPE symsgty VALUE 'E',
             c_msg_id     TYPE symsgid VALUE 'PTRA_WEB_INTERFACE'.

  lv_startdate = iv_startdate.
  lv_enddate = iv_enddate.

* Initialize the message class and type
  l_msgty = c_msg_err.
  l_msgid = c_msg_id.

* Change the date range so that it can accomodate the Trips with dates outside the receipt date range.
  lv_trip_start = lv_startdate - c_bufferdays.
  lv_trip_end = lv_enddate + c_bufferdays.

  SORT it_compcode BY bukrs.
  DELETE ADJACENT DUPLICATES FROM it_compcode COMPARING bukrs.

********************************************************
* Check that the input compamy codes table is not empty
********************************************************
  DESCRIBE TABLE it_compcode LINES lv_count.
  IF lv_count LE 0.
    "return error.
    CLEAR return.
    l_msgno = '275'.
    CALL FUNCTION 'BALW_BAPIRETURN_GET2'
      EXPORTING
        type   = l_msgty
        cl     = l_msgid
        number = l_msgno
        par1   = l_msgv1
        par2   = l_msgv2
        par3   = l_msgv3
        par4   = l_msgv4
      IMPORTING
        return = return.

    APPEND return.
    EXIT.
    IF 1 = 2.
      MESSAGE e275(ptra_web_interface).
    ENDIF.
  ENDIF.


********************************************************
*  Get the logical system
********************************************************
  SELECT SINGLE logsys FROM t000
    INTO lv_logsys
    WHERE mandt EQ sy-mandt.
*  IF sy-subrc NE 0.
*    In case of local call, the logsys need not to be maintained -> no error message
*  ENDIF.


********************************************************
* Get the state of establishment (country) using the company code
********************************************************
  SELECT bukrs land1 FROM t001
    INTO TABLE lit_t001
    FOR ALL ENTRIES IN it_compcode WHERE bukrs EQ it_compcode-bukrs.

  IF sy-subrc NE 0.
    "return error.
    CLEAR return.
    l_msgno = '276'.
    CALL FUNCTION 'BALW_BAPIRETURN_GET2'
      EXPORTING
        type   = l_msgty
        cl     = l_msgid
        number = l_msgno
        par1   = l_msgv1
        par2   = l_msgv2
        par3   = l_msgv3
        par4   = l_msgv4
      IMPORTING
        return = return.

    APPEND return.
    EXIT.
    IF 1 = 2.
      MESSAGE e276(ptra_web_interface).
    ENDIF.
  ENDIF.

  SORT lit_t001 BY bukrs.
  DELETE ADJACENT DUPLICATES FROM lit_t001 COMPARING bukrs.

********************************************************
* Select the personal area according to the company code
********************************************************
  SELECT persa bukrs land1 FROM t500p
    INTO TABLE lit_t500p
    FOR ALL ENTRIES IN lit_t001
    WHERE bukrs EQ lit_t001-bukrs.

  IF sy-subrc NE 0.
    "return error.
    l_msgno = '277'.
    CLEAR return.

    CALL FUNCTION 'BALW_BAPIRETURN_GET2'
      EXPORTING
        type   = l_msgty
        cl     = l_msgid
        number = l_msgno
        par1   = l_msgv1
        par2   = l_msgv2
        par3   = l_msgv3
        par4   = l_msgv4
      IMPORTING
        return = return.

    APPEND return.
    EXIT.
    IF 1 = 2.
      MESSAGE e277(ptra_web_interface).
    ENDIF.
  ENDIF.

  SORT lit_t500p BY persa.
  DELETE ADJACENT DUPLICATES FROM lit_t500p COMPARING persa.

********************************************************
* Select the personal numbers which are assigned
* to the correct personal area in info type 0001
* use iv_enddate for the selection
********************************************************
  SELECT pernr werks bukrs FROM pa0001
    INTO TABLE lit_pernr
    FOR ALL ENTRIES IN lit_t500p
    WHERE werks = lit_t500p-persa
    AND begda LE iv_enddate
    AND endda GE iv_enddate ##too_many_itab_fields .

  IF sy-subrc NE 0.
    "return error.
    CLEAR return.
    l_msgno = '274'.
    CALL FUNCTION 'BALW_BAPIRETURN_GET2'
      EXPORTING
        type   = l_msgty
        cl     = l_msgid
        number = l_msgno
        par1   = l_msgv1
        par2   = l_msgv2
        par3   = l_msgv3
        par4   = l_msgv4
      IMPORTING
        return = return.

    APPEND return.
    EXIT.
    IF 1 = 2.
      MESSAGE e274(ptra_web_interface).
    ENDIF.
  ENDIF.

********************************************************
* remove useless data / decrease data volume in lit_pernr
* sort by pernr
* delete adjacent duplicates comparing pernr
********************************************************
  SORT lit_pernr BY pernr.
  DELETE ADJACENT DUPLICATES FROM lit_pernr COMPARING pernr.


********************************************************
* Read company code in info type 0017
* If this exists use this instead of company code from info type 0001
* If this company code is not part of the selected values remove the personal number
********************************************************
  LOOP AT lit_pernr INTO ls_pernr.

    CLEAR p0017.
    REFRESH p0017.
    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
*       TCLAS           = 'A'
        pernr           = ls_pernr-pernr
        infty           = '0017'
        begda           = iv_enddate
        endda           = iv_enddate
*       BYPASS_BUFFER   = ' '
*       LEGACY_MODE     = ' '
*     IMPORTING
*       SUBRC           =
      TABLES
        infty_tab       = p0017
      EXCEPTIONS
        infty_not_found = 1
        OTHERS          = 2.
    IF sy-subrc = 0.

      IF p0017-bukrs IS NOT INITIAL AND p0017-bukrs NE ls_pernr-bukrs.

        READ TABLE lit_t001 WITH KEY bukrs = p0017-bukrs TRANSPORTING NO FIELDS BINARY SEARCH.
        IF sy-subrc NE 0.
          DELETE lit_pernr.
          CONTINUE.
        ELSE.
          ls_pernr-bukrs = p0017-bukrs.
          MODIFY lit_pernr FROM ls_pernr TRANSPORTING bukrs.
        ENDIF.
      ENDIF.
    ENDIF.

* fill state of establishment
    READ TABLE lit_t001 INTO ls_t001 WITH KEY bukrs = ls_pernr-bukrs BINARY SEARCH.
    IF sy-subrc = 0.
      ls_pernr-land1 = ls_t001-land1.
      MODIFY lit_pernr FROM ls_pernr TRANSPORTING land1.
    ENDIF.


  ENDLOOP.

********************************************************
* Select all the trips for the selected personal numbers
********************************************************
* SELECT pernr reinr hdvrs                                  "MAWH1497299
  SELECT pernr reinr hdvrs morei                            "MAWH1497299
    FROM ptrv_head
    INTO TABLE lit_head
    FOR ALL ENTRIES IN lit_pernr
    WHERE pernr EQ lit_pernr-pernr
    AND datv1 GE lv_trip_start
    AND datb1 LE lv_trip_end .

  IF sy-subrc NE 0.
    "return error.
    CLEAR return.
    l_msgno = '278'.
    CALL FUNCTION 'BALW_BAPIRETURN_GET2'
      EXPORTING
        type   = l_msgty
        cl     = l_msgid
        number = l_msgno
        par1   = l_msgv1
        par2   = l_msgv2
        par3   = l_msgv3
        par4   = l_msgv4
      IMPORTING
        return = return.

    APPEND return.
    EXIT.
    IF 1 = 2.
      MESSAGE e278(ptra_web_interface).
    ENDIF.
  ENDIF.


********************************************************
* remove useless data / decrease data volume in lit_head
* sort by pernr reinr hdvrs
* delete adjacent duplicates comparing pernr reinr
********************************************************
  SORT lit_head BY pernr reinr hdvrs.
  DELETE ADJACENT DUPLICATES FROM lit_head COMPARING pernr reinr.


********************************************************
* Select the trip periods from table ptrv_perio which fall in the given date range.
********************************************************
* SELECT pernr reinr perio pdvrs                            "MAWH1497299
  SELECT pernr reinr perio pdvrs hdvrs                      "MAWH1497299
    FROM ptrv_perio
    INTO TABLE lit_perio
    FOR ALL ENTRIES IN lit_head
    WHERE uebrf EQ '1'          " Posted to FI
    AND vat_status NE space     " VAT relevant
    AND  pdatv GE lv_trip_start " Date Range
    AND  pdatb LE lv_trip_end
    AND pernr EQ lit_head-pernr
    AND reinr EQ lit_head-reinr. " Only trips selected in header table

  IF sy-subrc NE 0.
    "return error.
    CLEAR return.
    l_msgno = '274'.
    CALL FUNCTION 'BALW_BAPIRETURN_GET2'
      EXPORTING
        type   = l_msgty
        cl     = l_msgid
        number = l_msgno
        par1   = l_msgv1
        par2   = l_msgv2
        par3   = l_msgv3
        par4   = l_msgv4
      IMPORTING
        return = return.

    APPEND return.
    EXIT.
    IF 1 = 2.
      MESSAGE e274(ptra_web_interface).
    ENDIF.
  ENDIF.


********************************************************
* only keep the latest version (lowest pdvrs)
* sort by pernr reinr perio pdvrs
* delete adjacent duplicates comparing pernr reinr perio
********************************************************
  SORT lit_perio ASCENDING BY pernr reinr perio pdvrs.
  DELETE ADJACENT DUPLICATES FROM lit_perio COMPARING pernr reinr perio.


* Begin of MAWH1497299
* fill the field MOREI in table LIT_PERIO
  LOOP AT lit_perio ASSIGNING <fs_perio>.
    READ TABLE lit_head ASSIGNING <fs_head> WITH KEY pernr = <fs_perio>-pernr
                                                     reinr = <fs_perio>-reinr
                                                     hdvrs = <fs_perio>-hdvrs.
    IF sy-subrc = 0.
      <fs_perio>-morei = <fs_head>-morei.
    ENDIF.
  ENDLOOP.
* End of MAWH1497299

********************************************************
* Select the Receipt data from cluster table for each trip period
********************************************************
  LOOP AT lit_perio INTO ls_perio.

* Form the key to read from the cluster table
    lv_tekey-pernr = ls_perio-pernr.
    lv_tekey-reinr = ls_perio-reinr.
    lv_tekey-perio = ls_perio-perio.
    lv_tekey-pdvrs = ls_perio-pdvrs.

* Read from the cluster table with the key
    CLEAR lit_beleg.
    REFRESH lit_beleg.
    IMPORT beleg TO lit_beleg
    FROM   DATABASE pcl1(te)
    ID     lv_tekey.

    CLEAR ls_temp_data.
    ls_temp_data-key = lv_tekey.

* determine starting point by read table binary search (sort table before) and loop only over the relevant part of the table

    DELETE lit_beleg WHERE vat_status EQ space.
    SORT lit_beleg BY bldat.
    READ TABLE lit_beleg INTO ls_temp_data-data  WITH KEY bldat = lv_startdate BINARY SEARCH.
    lv_index = sy-index.

*   Begin of MAWH1497299
    IF ls_perio-morei <> lv_morei_old.
      CLEAR lit_land1_region.
      LOOP AT it_intca ASSIGNING <fs_intca>.
        CLEAR ls_t702o.
        CLEAR ls_land1_region.
        SELECT * FROM t702o INTO ls_t702o WHERE morei = ls_perio-morei
                                            AND intca = <fs_intca>-intca.
          MOVE-CORRESPONDING ls_t702o TO ls_land1_region.
          APPEND ls_land1_region TO lit_land1_region.
        ENDSELECT.
        IF sy-subrc <> 0.
          MOVE <fs_intca>-intca TO ls_land1_region-land1.
          APPEND ls_land1_region TO lit_land1_region.
        ENDIF.
      ENDLOOP.
      SORT lit_land1_region BY land1 rgion.
      DELETE ADJACENT DUPLICATES FROM lit_land1_region COMPARING land1 rgion.
      lv_morei_old = ls_perio-morei.
    ENDIF.
*   End of MAWH1497299

* Choose the receipts with relevant VAT status, matching date and from the matching country where expenses have occurred
*   IF it_intca[] IS NOT INITIAL.                           "MAWH1497299
*     LOOP AT it_intca ASSIGNING <fs_intca>.                "MAWH1497299
    IF lit_land1_region IS NOT INITIAL.                     "MAWH1497299
* Begin of AGU Note 2426192 - FBTR: VAT Refund / Travel Expenses with an address without region
*      LOOP AT lit_land1_region ASSIGNING <fs_land1_region>. "MAWH1497299
*        LOOP AT lit_beleg INTO ls_temp_data-data FROM lv_index
*          WHERE ( bldat GE lv_startdate
*              AND bldat LE lv_enddate
**             AND lndfr EQ <fs_intca>-intca ) .             "MAWH1497299
*              AND lndfr EQ <fs_land1_region>-land1          "MAWH1497299
*              and rgion eq <fs_land1_region>-rgion ) .      "MAWH1497299
*          APPEND ls_temp_data TO lit_temp_data.
*        ENDLOOP.
*      ENDLOOP.
      LOOP AT lit_land1_region ASSIGNING <fs_land1_region>.
        IF <fs_land1_region>-rgion IS INITIAL. "IF rgn is empty we check only the land1
          LOOP AT lit_beleg INTO ls_temp_data-data FROM lv_index
              WHERE bldat GE lv_startdate
                AND bldat LE lv_enddate
                AND lndfr EQ <fs_land1_region>-land1.
            IF ls_temp_data IS NOT INITIAL.
              APPEND ls_temp_data TO lit_temp_data.
            ENDIF.
          ENDLOOP.
        ELSE.
          LOOP AT lit_beleg INTO ls_temp_data-data FROM lv_index
            WHERE bldat GE lv_startdate
                AND bldat LE lv_enddate
                AND lndfr EQ <fs_land1_region>-land1
                AND rgion EQ <fs_land1_region>-rgion .
            IF ls_temp_data IS NOT INITIAL.
              APPEND ls_temp_data TO lit_temp_data.
            ENDIF.
          ENDLOOP.
        ENDIF.
      ENDLOOP.
* End of AGU Note 2426192 - FBTR: VAT Refund / Travel Expenses with an address without region
    ELSE.
      LOOP AT lit_beleg INTO ls_temp_data-data FROM lv_index
        WHERE ( bldat GE lv_startdate
            AND bldat LE lv_enddate ) .
        APPEND ls_temp_data TO lit_temp_data.
      ENDLOOP.
    ENDIF.

  ENDLOOP.

* Populate the export structure and fill the data by reading PTRV_VATDETAIL

  " This logic could be included in the previous loop where we retrieve the receipt specific data,
  " but for the convinience of code maintenance,
  " the following logic is  separated out into a different loop.
  " This improves the readability of the code. It is also worthwhile to note that there
  " is no redundant logic in the 2 loops, so it wouldn't cause any major performance depreciation.


  LOOP AT lit_temp_data ASSIGNING <fs_temp_data>.

    CLEAR ls_vat_ref_data.

* Populate logical system
    MOVE lv_logsys TO ls_vat_ref_data-awsys.

* Populate fields from Trip data
    MOVE-CORRESPONDING <fs_temp_data>-key TO ls_vat_ref_data.

* Populate all the fields from the receipt data from cluster table
    MOVE-CORRESPONDING <fs_temp_data>-data TO ls_vat_ref_data.
*   MOVE <fs_temp_data>-data-lndfr TO ls_vat_ref_data-intca."MAWH1497299

    IF ls_vat_ref_data-vat_service_code IS NOT INITIAL.
      TRY.
          CALL FUNCTION 'CONVERSION_EXIT_ALPHA_INPUT'    "GLW note 3268646 -> on FI side, the VAT Service code as leading 0 on DB table TAX_RFD_CHARS due to ALPHA
            EXPORTING
              input  = ls_vat_ref_data-vat_service_code
            IMPORTING
              output = ls_vat_ref_data-vat_service_code.
        CATCH cx_root.
      ENDTRY.
    ENDIF.

* Calculate the net amount FWBAS as the difference of PTK03-BETRG (gross amount) and PTK03-FWSTE (tax amount).
    ls_vat_ref_data-fwbas = ls_vat_ref_data-betrg - ls_vat_ref_data-fwste.


* Populate the country/state of establishment and company code
    READ TABLE lit_pernr INTO ls_pernr WITH KEY pernr = <fs_temp_data>-key-pernr BINARY SEARCH.
    IF sy-subrc EQ 0.
      ls_vat_ref_data-bukrs         = ls_pernr-bukrs.
      ls_vat_ref_data-intca_estblsh = ls_pernr-land1.
    ENDIF.


* Populate VAT details
    CALL METHOD cl_fitv_vat_details=>read_per_receipt
      EXPORTING
        iv_pernr       = <fs_temp_data>-key-pernr
        iv_reinr       = <fs_temp_data>-key-reinr
        iv_perio       = <fs_temp_data>-key-perio
        iv_pdvrs       = <fs_temp_data>-key-pdvrs
        iv_belnr       = <fs_temp_data>-data-belnr
      RECEIVING
        rs_vat_details = ls_vat_details
      EXCEPTIONS
        key_not_found  = 1
        OTHERS         = 2.
    IF sy-subrc = 0.
      MOVE-CORRESPONDING ls_vat_details TO ls_vat_ref_data.
* begin ZFJN1506975
    ELSE.
      READ TABLE lit_head ASSIGNING <fs_head> WITH KEY pernr = <fs_temp_data>-key-pernr
                                                       reinr = <fs_temp_data>-key-reinr
                                                       .
      ls_vat_ref_data-intca = cl_fitv_vat_details=>get_country_iso2(
          iv_morei        = <fs_head>-morei
          iv_land1        = <fs_temp_data>-data-lndfr
          iv_rgion        = <fs_temp_data>-data-rgion
             ).
* end ZFJN1506975
    ENDIF.

* Append the record to the exported table
    APPEND ls_vat_ref_data TO et_vat_refund_data.
  ENDLOOP.
ENDFUNCTION.