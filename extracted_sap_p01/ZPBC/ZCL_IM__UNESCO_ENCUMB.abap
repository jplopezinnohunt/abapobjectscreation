* ==== CLASS POOL ZCL_IM__UNESCO_ENCUMB ====
CLASS-POOL .
*"* class pool for class ZCL_IM__UNESCO_ENCUMB

*"* local type definitions
INCLUDE ZCL_IM__UNESCO_ENCUMB=========CCDEF.

*"* class ZCL_IM__UNESCO_ENCUMB definition
*"* public declarations
  INCLUDE ZCL_IM__UNESCO_ENCUMB=========CU.
*"* protected declarations
  INCLUDE ZCL_IM__UNESCO_ENCUMB=========CO.
*"* private declarations
  INCLUDE ZCL_IM__UNESCO_ENCUMB=========CI.
ENDCLASS. "ZCL_IM__UNESCO_ENCUMB definition

*"* macro definitions
INCLUDE ZCL_IM__UNESCO_ENCUMB=========CCMAC.
*"* local class implementation
INCLUDE ZCL_IM__UNESCO_ENCUMB=========CCIMP.

CLASS ZCL_IM__UNESCO_ENCUMB IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM__UNESCO_ENCUMB implementation


* ---- ZCL_IM__UNESCO_ENCUMB=========CI ----
PRIVATE SECTION.
*"* private components of class ZCL_IM__UNESCO_ENCUMB
*"* do not include other source files here!!!

* ---- ZCL_IM__UNESCO_ENCUMB=========CM001 ----
METHOD ADJUST_REQ_WITH_VALIDITY.

  DATA LS_REQ        LIKE IS_REQ.
  DATA LS_VAL        TYPE HRFPM_TIME.
  DATA LV_AMOUNT_SAV TYPE BETRG.
  DATA LS_VAL_SAV    TYPE HRFPM_TIME.


  BREAK-POINT ID Z_ENCUMB_PROTO.

  IF IS_NEW_VAL-BEGDA GT IS_REQ-ENDDA OR
    IS_NEW_VAL-ENDDA LT IS_REQ-BEGDA.
    INSERT IS_REQ INTO TABLE ET_REQ_SKIPPED.
  ELSEIF  IS_NEW_VAL-BEGDA LE IS_REQ-BEGDA AND
    IS_NEW_VAL-ENDDA GE IS_REQ-ENDDA.
    INSERT IS_REQ INTO TABLE ET_REQ_ADJUSTED.
  ELSE.
    "overlap situation
    LS_REQ = IS_REQ.
    LV_AMOUNT_SAV = IS_REQ-BETRG.
    MOVE-CORRESPONDING IS_REQ TO LS_VAL_SAV.

    "start spliting requirement
    "determinging the new begda
    IF LS_REQ-BEGDA LT IS_NEW_VAL-BEGDA.
      "that portion before the new validity has to be skipped
      LS_VAL-BEGDA = IS_REQ-BEGDA.
      LS_VAL-ENDDA = IS_NEW_VAL-BEGDA - 1.

      ZCL_HRFPM_REQUIREMENT_SERVICES=>ADJUST_COST_DIST_AMOUNT(
         EXPORTING
          IS_NEW_VALIDITY = LS_VAL
        CHANGING
          CS_REQUIREMENT = LS_REQ  ).

      MOVE-CORRESPONDING LS_VAL TO LS_REQ.
      INSERT LS_REQ INTO TABLE ET_REQ_SKIPPED.

      "becomes the starting point for next check
      LV_AMOUNT_SAV = LS_REQ-BETRG
              = LV_AMOUNT_SAV - LS_REQ-BETRG.

      LS_VAL_SAV-BEGDA = LS_REQ-BEGDA = IS_NEW_VAL-BEGDA.
      LS_VAL_SAV-ENDDA = LS_REQ-ENDDA = IS_REQ-ENDDA.

    ENDIF.

    "determine the new endda
    IF LS_REQ-ENDDA GT IS_NEW_VAL-ENDDA.

      LS_VAL-BEGDA = IS_NEW_VAL-ENDDA + 1.
      LS_VAL-ENDDA = IS_REQ-ENDDA .

      ZCL_HRFPM_REQUIREMENT_SERVICES=>ADJUST_COST_DIST_AMOUNT(
         EXPORTING
          IS_NEW_VALIDITY = LS_VAL
        CHANGING
          CS_REQUIREMENT  = LS_REQ  ).

      MOVE-CORRESPONDING LS_VAL TO LS_REQ.
      INSERT LS_REQ INTO TABLE ET_REQ_SKIPPED.

      LV_AMOUNT_SAV = LS_REQ-BETRG
                    = LV_AMOUNT_SAV - LS_REQ-BETRG.
      LS_REQ-ENDDA  = IS_NEW_VAL-ENDDA.
      LS_REQ-BEGDA  = LS_VAL_SAV-BEGDA.
    ENDIF.

    "the result of the spliting process goes to the
    "adjusted records
    INSERT LS_REQ INTO TABLE ET_REQ_ADJUSTED.

  ENDIF.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM002 ----
METHOD DO_HANDLE_VACANCY.
  "standard behaviour!
  "UNESCO requires Precommitment ONLY for vacant and integrated positions
  BREAK-POINT ID Z_ENCUMB_PROTO.

*1.	For positions it removes those requirement records that are due to occupation
*    (characterized by non-empty component HROBJECT_DP)
*2.	In order to maintain the expected consistency of the requirements data set,
*    it has at the same time in the requirement records for personal numbers to
*    delete the pointers to positions. (if this would not be done, errors would be
*    occurring during the step of transferring the requirements to acounting)
  "deactivated:
  "deleting P-> S  pointers would lead to incorrect PCS-documents

  DATA LS_REQ LIKE LINE OF CT_REQUIREMENT.
  DATA LT_REQUIREMENT LIKE CT_REQUIREMENT.

  LT_REQUIREMENT = CT_REQUIREMENT.
  CLEAR CT_REQUIREMENT.

  LOOP AT LT_REQUIREMENT INTO LS_REQ.
    IF LS_REQ-HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_S .
      IF NOT LS_REQ-HROBJECT_DP IS INITIAL.
        CONTINUE.
      ENDIF.
    ELSEIF LS_REQ-HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_P.
      IF LS_REQ-HROBJECT_DP-OTYPE =  CL_HRFPM_CONST=>OTYPE_S.
        CLEAR LS_REQ-HROBJECT_DP.
      ENDIF.
    ENDIF.
    INSERT LS_REQ INTO TABLE CT_REQUIREMENT.
  ENDLOOP.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM003 ----
METHOD IF_EX_HRFPM_ENCUMB_IV~CHECK_ACC_IV.
  DATA LS_PERIOD TYPE HRFPM_TIME.

  BREAK-POINT ID Z_ENCUMB_PROTO.

  LS_PERIOD-BEGDA = P_BEGDA.
  LS_PERIOD-ENDDA = P_ENDDA.

  INIT_REQU_FILTER( ).

  TRY .
      MO_REQUIREMENT_FILTER->DO_REQUIREMENT_FILTRATION(
         EXPORTING IS_FILTRATION_PERIOD = LS_PERIOD
         CHANGING  CT_REQUIREMENT = P_COST_DIST ).
    CATCH CX_HRFPM_DC INTO EXC_DC.

      CREATE OBJECT EXC_DYN_ENC
        EXPORTING
*         textid   = textid
          PREVIOUS = EXC_DC.

      MESSAGE E899(HRFPM) WITH
         'ERROR DURING REQUIREMENT FILTRATION' '' '' ''.

      EXC_DYN_ENC->SET_SY_MESSAGE( ).

      RAISE EXCEPTION EXC_DYN_ENC.
  ENDTRY.


ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM004 ----
METHOD IF_EX_HRFPM_ENCUMB_IV~GET_ACTIVE_FLAG.
  "the dynamic encumbrance creation is currently
  "no supported at all by the standard
  "==> has to be done in the filtration BbadI
  P_DYN_ENC_ACTIVE = SPACE.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM005 ----
METHOD IF_EX_HRFPM_ENCUMB_IV~GET_OBJECT_ENC_IV.
  DATA LS_ACTV_OVERALL_INTERVAL TYPE T77HRFPM_ENCUMB.

  BREAK-POINT ID Z_ENCUMB_PROTO.

  INIT_ENCUMB_HANDLING( ).

  TRY.
      CL_HRFPM_GET_ADMIN_CUST=>GET_ACTIVE_ENCUMB_IV(
        EXPORTING
           P_INITRUN     = MV_IN_INITRUN
        IMPORTING
           P_ENC_DATE_IV  = LS_ACTV_OVERALL_INTERVAL ).

      P_ENC_DATE_IV =
         MO_ENCUMB_HANDLING->GET_DETAIL_INTERVAL(
            IS_HROBJECT    = P_OBJECT
            IS_ACTV_ENCUMB = LS_ACTV_OVERALL_INTERVAL ) .

    CATCH CX_HRFPM_DB_OPERATION .
    CATCH CX_HRFPM_AD_CUSTOMIZING .
  ENDTRY.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM006 ----
METHOD INIT_ENCUMB_HANDLING.
  DATA LS_CONTEXT TYPE ZIF_ENCUMB_HANDLING=>TS_CONTEXT.
  TRY .
      IF IV_RUNID IS INITIAL.
        CL_HRFPM_ADMINISTRATOR=>GET_RUNID(
             IMPORTING P_RUNID = IV_RUNID ).
      ENDIF.
      LS_CONTEXT-RUNID = IV_RUNID.
      MO_ENCUMB_HANDLING = ZIF_ENCUMB_HANDLING~GET_INSTANCE( LS_CONTEXT ) .

      "until a configuration for the enddate deetermination rules
      "is available, use hard-coded values

********Quasi-config *****************************
     "adjust according to the needs
*{   REPLACE        D01K9B04Y9                                        1
*\      mv_extension_years = 1.
      "as per a change request from Spring 2019
      " Temporary positions need to be financed until end
      " of contract date: and that may exceed three years
      " ==> according to communication with business
      " no contract end date will exceed 3 years from today
      " so a limit of 10 should be sufficient
      MV_EXTENSION_YEARS = 10.
*}   REPLACE
**************************************************
      MV_IN_INITRUN = CL_HRFPM_ADMINISTRATOR=>ZZ_GET_USED_RUN_VARIANT( )-INITRUN.
    CATCH CX_HRFPM_ADMINISTRATOR.
  ENDTRY.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM007 ----
METHOD INIT_REQU_FILTER.
  DATA LS_CONTEXT TYPE ZIF_REQUIREMENT_FILTER=>TS_CONTEXT.

  TRY .
      IF IV_RUNID IS INITIAL.
        CL_HRFPM_ADMINISTRATOR=>GET_RUNID(
             IMPORTING P_RUNID = IV_RUNID ).
      ENDIF.

      LS_CONTEXT-RUNID = IV_RUNID.
      LS_CONTEXT-NEW_REQ_ACTV =
         CL_BPREP_REQUIREMENT_MANAGER=>NEW_REQ_RATING_ACTIVE.

      MO_REQUIREMENT_FILTER =
             ZIF_REQUIREMENT_FILTER~GET_INSTANCE( LS_CONTEXT ) .
      MV_IN_INITRUN = CL_HRFPM_ADMINISTRATOR=>ZZ_GET_USED_RUN_VARIANT( )-INITRUN.
    CATCH CX_HRFPM_ADMINISTRATOR.
  ENDTRY.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM008 ----
METHOD ZIF_ENCUMB_HANDLING~GET_INSTANCE.
  "prototype
  RO_INSTANCE = ME.
  RO_INSTANCE->SET_CONTEXT( IS_CONTEXT ).
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM009 ----
  METHOD ZIF_ENCUMB_HANDLING~GET_OVERALL_INTERVAL.
    "delegated to subclasses
    RS_OVERALL_INTERVAL = IS_ACTV_ENCUMB-DATE_IV.
    RETURN.
  ENDMETHOD.                    "zif_encumb_handling~get_overall_interval

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00A ----
METHOD ZIF_ENCUMB_HANDLING~SET_CONTEXT.
  ZIF_ENCUMB_HANDLING~MS_CONTEXT = IS_CONTEXT.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00B ----
METHOD ZIF_REQUIREMENT_FILTER~DO_REQUIREMENT_FILTRATION.
  "delegated to subclasses
  RETURN.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00C ----
METHOD ZIF_REQUIREMENT_FILTER~GET_INSTANCE.
  ZIF_REQUIREMENT_FILTER~MS_CONTEXT = IS_CONTEXT.
  RO_INSTANCE = ME.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00D ----
METHOD ZIF_REQUIREMENT_FILTER~SET_CONTEXT.
  ZIF_REQUIREMENT_FILTER~MS_CONTEXT = IS_CONTEXT.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00E ----
  METHOD ZIF_ENCUMB_HANDLING~GET_DETAIL_INTERVAL.
    "delegated to subclass.
    RETURN.
  ENDMETHOD.                    "zif_encumb_handling~get_detail_interval

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00F ----
  METHOD DET_DETAIL_PERIOD.

    "The overall commitment period is modified based
    "on individual characterists of the object

    "For PERNR, the commitment period enddate is specified
    "by the contract enddate depending from the
    "

    FIELD-SYMBOLS <DET_DATA> TYPE TS_DETAIL_PERIOD_DET_DATA.

    BREAK-POINT ID Z_ENCUMB_PROTO.
    ASSIGN IRS_DETERMINATION_DATA->* TO <DET_DATA>.

    RS_DETAIL_INTERVAL = IS_OVERALL_PERIOD.

    IF IS_HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_P.
      "only for PERNR can a detail variant be determined
      "
      IF CONTRACT_TYPE_IS_TEMPORARY( <DET_DATA>-ANSVH ) = ABAP_TRUE.
        "Temporary
        "in these cases encumbrances have to be created
        "the most up to the contract enddate within
        "the overall period
        IF NOT <DET_DATA>-CONTRACT_END_DATE IS INITIAL.
          IF <DET_DATA>-CONTRACT_END_DATE LT IS_OVERALL_PERIOD-ENDDA.
            RS_DETAIL_INTERVAL-ENDDA = <DET_DATA>-CONTRACT_END_DATE.
          ENDIF.

          "break todo!!.
          IF <DET_DATA>-CONTRACT_END_DATE LT IS_OVERALL_PERIOD-BEGDA.
            CLEAR RS_DETAIL_INTERVAL.
          ENDIF.
        ENDIF.

      ELSE.
        CASE <DET_DATA>-ANSVH.
          WHEN '01' OR '02' OR '07'.
            "Fixed
            "only in PFF-case is the commitment enddate
            "given by the contract enddate.
            "in all the other cases it is identical to
            "the overall period
            IF <DET_DATA>-GSBER = 'PFF'
            "04/07/2017: as of now
            "'OPF' has the same rules as 'PFF'
              OR <DET_DATA>-GSBER = 'OPF'.
              RS_DETAIL_INTERVAL-ENDDA = IS_BIENNIUM-ENDDA.
            ENDIF.
*        WHEN
*            '03' OR '04' OR '05' OR '06' OR '18' OR '20'
*            "new contract type as of 2014
*             OR '21'.
*
*          "Temporary
*          "in these cases encumbrances have to be created
*          "the most up to the contract enddate within
*          "the overall period
*          IF NOT <det_data>-contract_end_date IS INITIAL.
*            IF <det_data>-contract_end_date LT is_overall_period-endda.
*              rs_detail_interval-endda = <det_data>-contract_end_date.
*            ENDIF.
*
*            "break todo!!.
*            IF <det_data>-contract_end_date LT is_overall_period-begda.
*              CLEAR rs_detail_interval.
*            ENDIF.
*          ENDIF.

          WHEN '22' OR '23' OR '24'.
            "short term contracts, period is determined entirely by
            "duration of 'different account assignments' (Is this neccessary at all ???)
            DATA LTR_INFTY TYPE RANGE OF INFTY.
            DATA LS_INFTY LIKE LINE OF LTR_INFTY.

            LS_INFTY-OPTION = 'EQ'.
            LS_INFTY-SIGN   = 'I'.
            LS_INFTY-LOW    = '0014'.
            APPEND LS_INFTY TO LTR_INFTY.
            LS_INFTY-LOW    = '0015'.
            APPEND LS_INFTY TO LTR_INFTY.
            LS_INFTY-OPTION = 'CP'.
            LS_INFTY-LOW    = '2002'.
            APPEND LS_INFTY TO LTR_INFTY.


            SELECT MIN( BEGDA ) MAX( ENDDA )  FROM ASSOB_HR
            INTO (RS_DETAIL_INTERVAL-BEGDA , RS_DETAIL_INTERVAL-ENDDA)
                WHERE PERNR = IS_HROBJECT-OBJID
                  AND SPRPS NE 'X'
                  AND INFTY IN LTR_INFTY
*                AND ( infty = '0014' OR infty = '0015' OR infty = '2002' )
                  AND NOT ( BEGDA GT IS_OVERALL_PERIOD-ENDDA
                            OR ENDDA LT IS_OVERALL_PERIOD-BEGDA ).

            IF SY-SUBRC <> 0.
              RS_DETAIL_INTERVAL = IS_OVERALL_PERIOD.
            ELSE.
              "start date always that of overall period
              RS_DETAIL_INTERVAL-BEGDA = IS_OVERALL_PERIOD-BEGDA.
              IF RS_DETAIL_INTERVAL-ENDDA GT IS_OVERALL_PERIOD-ENDDA.
                RS_DETAIL_INTERVAL-ENDDA = IS_OVERALL_PERIOD-ENDDA.
              ENDIF.
            ENDIF.
          WHEN OTHERS.
*        "in all other cases the enddate of encumbranees
*        "are specified by the business area the person pertains to
*        "(this is: the 'overall period')
            RETURN.
        ENDCASE.
      ENDIF.
    ENDIF.


  ENDMETHOD.                    "DET_DETAIL_PERIOD

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00G ----
  METHOD DET_OVERALL_PERIOD_DET_ID.

    "this method does the context depending determination of rule-Id's
    "TODO create a configuration for this (for example a feature)

    "currently the following rules are supported
    " c_enc_mod_id_0: 'Use the current biennium'
    " c_enc_mod_id_1: 'Use first/second half of biennium
    " c_enc_mod_id_88: #extend a biennium by a fixed amount of years'

    BREAK-POINT ID Z_ENCUMB_PROTO.
    FIELD-SYMBOLS <DATA> TYPE TS_OVERALL_PERIOD_DET_DATA.

    ASSIGN IRS_DETERMINATION_DATA->* TO <DATA>.

    "temporarily until it is clear where
    "business area for Positions is to be taken from
    IF IS_HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_S.
      RV_MOD_ID = C_ENC_MOD_ID_0.
      BREAK TODO_SCENARIO2!!!.
*    ELSEIF sy-datum(4) = is_biennium-endda(4).
*      "second half:
*        rv_mod_id = c_enc_mod_id_1_2.
    ELSEIF CONTRACT_TYPE_IS_TEMPORARY( <DATA>-ANSVH ) = ABAP_TRUE.
      "change request June-2019
      "Temporary staff needs to be financed until contract end date within
      "biennium + extension
      RV_MOD_ID = C_ENC_MOD_ID_88.
    ELSE.
      CASE <DATA>-GSBER.
        WHEN 'GEF'.
          RV_MOD_ID = C_ENC_MOD_ID_0.
*        WHEN 'OPF'.
*          rv_mod_id = c_enc_mod_id_1.
*          IF sy-datum(4) = is_biennium-begda(4)
*            AND NOT mv_in_initrun IS INITIAL.
*            "preparation of second half of OPF-funding
*            "(can requested if
*            "1. the active commitment period = initial commitment creation
*            "2. the run runs as initial run
*            rv_mod_id = c_enc_mod_id_1_3.
*          ENDIF.
        WHEN 'PFF'
          "04/07/2017: as of now
          "'OPF' has the same rules as 'PFF'
          OR 'OPF'.
          RV_MOD_ID = C_ENC_MOD_ID_88.
        WHEN OTHERS.

          MESSAGE A899(HRFPM)
           WITH 'NO VALID DETERMINATION DATA'
                'FOR OVERALL PERIOD DEETRMINATION'
                '' '' INTO MSG_DUMMY.

          CREATE OBJECT EXC_DYN_ENC
            EXPORTING
              HROBJECT = IS_HROBJECT.

          EXC_DYN_ENC->SET_SY_MESSAGE( ).
          RAISE EXCEPTION EXC_DYN_ENC.
      ENDCASE.
    ENDIF.
  ENDMETHOD.                    "det_overall_period_det_id

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00H ----
METHOD PROVIDE_DETAIL_PERIOD_DATA.
  DATA LT_0016 TYPE TABLE OF P0016.
  DATA LT_0001 TYPE TABLE OF P0001.
  DATA LRS_DATE_DET_DATA TYPE REF TO TS_DETAIL_PERIOD_DET_DATA.

  FIELD-SYMBOLS <P0016> LIKE LINE OF LT_0016.
  FIELD-SYMBOLS <P0001> LIKE LINE OF LT_0001.

  BREAK-POINT ID Z_ENCUMB_PROTO.
  CREATE DATA LRS_DATE_DET_DATA.
  RRS_PERIOD_DET_DATA = LRS_DATE_DET_DATA.

  IF IS_HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_P.

    GET_LATEST_INFTY_RECORDS(
      EXPORTING
         IS_HROBJECT   = IS_HROBJECT
         IS_SEL_PERIOD = IS_SEL_PERIOD
         IV_INFTY      = '0001'
       IMPORTING
         ET_RECORDS   = LT_0001 ).

    GET_LATEST_INFTY_RECORDS(
       EXPORTING
          IS_HROBJECT   = IS_HROBJECT
          IS_SEL_PERIOD = IS_SEL_PERIOD
          IV_INFTY      = '0016'
        IMPORTING
          ET_RECORDS   = LT_0016 ).


    CLEAR MSG_DUMMY.

    READ TABLE LT_0001 ASSIGNING <P0001> INDEX 1.
    IF NOT <P0001> IS ASSIGNED.
      MESSAGE A003(ZPBC) WITH IS_HROBJECT '0001' INTO MSG_DUMMY.
*   No data for determination of interval found: Object &1 , Infotype &2
    ENDIF.

    READ TABLE LT_0016 ASSIGNING <P0016> INDEX 1.
    IF NOT <P0016> IS ASSIGNED.
      MESSAGE A003(ZPBC) WITH IS_HROBJECT '0016' INTO MSG_DUMMY.
    ENDIF.

    IF NOT MSG_DUMMY IS INITIAL.
      CREATE OBJECT EXC_DYN_ENC
        EXPORTING
          HROBJECT = IS_HROBJECT.

      EXC_DYN_ENC->SET_SY_MESSAGE( ).
      RAISE EXCEPTION EXC_DYN_ENC.
    ELSE.
      LRS_DATE_DET_DATA->ANSVH =  <P0001>-ANSVH.
      LRS_DATE_DET_DATA->CONTRACT_END_DATE = <P0016>-CTEDT.
      LRS_DATE_DET_DATA->GSBER = <P0001>-GSBER.
    ENDIF.
  ENDIF.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00I ----
METHOD PROVIDE_OVERALL_PERIOD_DATA.

  DATA LT_P0001 TYPE TABLE OF P0001.

  DATA LRS_DET_DATA TYPE REF TO TS_OVERALL_PERIOD_DET_DATA.
  FIELD-SYMBOLS <P0001> LIKE LINE OF LT_P0001.


  BREAK-POINT ID Z_ENCUMB_PROTO.

  CREATE DATA LRS_DET_DATA.
  RRS_PERIOD_DET_DATA = LRS_DET_DATA.

  CASE IS_HROBJECT-OTYPE.
    WHEN CL_HRFPM_CONST=>OTYPE_S.

      RRS_PERIOD_DET_DATA =
         PROVIDE_OVERALL_PERIOD_DATA_S(
             IS_HROBJECT = IS_HROBJECT
             IS_SEL_PERIOD = IS_SEL_PERIOD ).

    WHEN CL_HRFPM_CONST=>OTYPE_P.
*{   REPLACE        D01K9B050N                                        1
*\      "depends obviously on the earliest record found
*\      get_latest_infty_records(
*\        EXPORTING
*\          is_hrobject   = is_hrobject
*\          is_sel_period = is_sel_period
*\          iv_infty      = '0001'
*\       IMPORTING
*\          et_records      = lt_p0001 ).
*\
*\      CLEAR msg_dummy.
*\
*\      READ TABLE lt_p0001 ASSIGNING <p0001> INDEX 1.
*\      IF <p0001> IS ASSIGNED.
*\        lrs_det_data->gsber = <p0001>-gsber.
*\      ELSE.
*\        MESSAGE a003(zpbc) WITH is_hrobject '0001' INTO msg_dummy.
*\*   No data for determination of interval found: Object &1 , Infotype &2
*\        CREATE OBJECT exc_dyn_enc
*\          EXPORTING
*\            hrobject = is_hrobject.
*\        exc_dyn_enc->set_sy_message( ).
*\        RAISE EXCEPTION exc_dyn_enc.
*\      ENDIF.
     "change request
     "temporary positions need to be financed until 'highdate' regardless of their
     "business area
     "to that end the contract details are needed
      " ==> so just reuse the datas for detail period
     DATA LRS_DETAIL_DET_DATA TYPE REF TO TS_DETAIL_PERIOD_DET_DATA.
     LRS_DETAIL_DET_DATA ?= PROVIDE_DETAIL_PERIOD_DATA(
             IS_HROBJECT   = IS_HROBJECT
             IS_SEL_PERIOD = IS_SEL_PERIOD ).

     MOVE-CORRESPONDING LRS_DETAIL_DET_DATA->* TO LRS_DET_DATA->*.

*}   REPLACE
  ENDCASE.

ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00J ----
  METHOD DET_OVERALL_PERIOD.

    "UNESCO wants for PERNR the overall encumbrance period depending from
    "different features of a contract/org criteria and the biennium

    "Two Steps:
    "1. derive a 'determination id' --> det_overall_period_det_id
    "2. based on that do the calculation of the endddate; this
    "calculation is always with respect to the biennium


    "TODO: make this configurable:
    "one idea: provide a filtered badi, where the filter values
    "are exactly the determination ID´'s from step 1

*
    BREAK-POINT ID Z_ENCUMB_PROTO.

    DATA LS_BIENNIUM TYPE HRFPM_TIME.

    "Biennium
    LS_BIENNIUM = DET_BIENNIUM_FROM_ENC_IV(
        IS_HROBJECT    = IS_HROBJECT
        IS_ENC_IV      = IS_ACTV_ENCUMB  ).


    CASE DET_OVERALL_PERIOD_DET_ID(
             IS_HROBJECT   = IS_HROBJECT
             IRS_DETERMINATION_DATA = IRS_DETERMINATION_DATA
             IS_BIENNIUM = LS_BIENNIUM ).
      WHEN C_ENC_MOD_ID_1 .

        CLEAR MSG_DUMMY.
        "ONE year offset from start date of current fiscal year
        "(in fact the start date of that half of the biennium
        "where sy-datum belongs to)
        "Precondition: half of the biennium starts at the beginning of
        "a fiscal year (calendar year)
        RS_OVERALL_INTERVAL = LS_BIENNIUM.
        IF
          "this is indeed possible (when running an initial run for
          "example)
          "sy-datum LT ls_biennium-begda OR
          SY-DATUM GT LS_BIENNIUM-ENDDA.
          "something has not been fully understood.
          ASSERT 1 = 2.

        ELSEIF SY-DATUM(4) = LS_BIENNIUM-BEGDA(4)
          "in initial run the biennium at this time is alreadz correct
          OR NOT MV_IN_INITRUN IS INITIAL.
          "first half of biennium
          RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-BEGDA(4) .
        ELSEIF SY-DATUM(4) = LS_BIENNIUM-ENDDA(4).
          "second half and not in init run
          RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-ENDDA(4) .
        ELSE.
*          rs_overall_interval-endda(4) = ls_biennium-endda(4) .
*          rs_overall_interval-begda = '99990101'.
*          rs_overall_interval-begda(4) = ls_biennium-endda(4).
          MESSAGE A001(ZPBC) WITH IS_HROBJECT INTO MSG_DUMMY.
        ENDIF.

      WHEN C_ENC_MOD_ID_1_2.
        "cut off scenario:
        "do not longer account of changes occuring in the first half!
        "might be one way of dealing with Scenario2 fiscal year change
        "(changing fiscal year in the middle of a biennium)
        RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-ENDDA(4) .
        RS_OVERALL_INTERVAL-BEGDA(4) = LS_BIENNIUM-ENDDA(4) .
      WHEN C_ENC_MOD_ID_1_3.
        CLEAR MSG_DUMMY.
        "prolongation scenario
        "(e.g. preparation of OPF-funding for second half of biennium  when
        "still in first half)
        IF NOT SY-DATUM(4) = LS_BIENNIUM-BEGDA(4).
          "enforce process consistency
          MESSAGE A001(ZPBC) WITH IS_HROBJECT INTO MSG_DUMMY.
        ELSE.
          RS_OVERALL_INTERVAL = LS_BIENNIUM.
          "rs_overall_interval-endda(4) = ls_biennium-endda(4) .
        ENDIF.
      WHEN C_ENC_MOD_ID_0.  "(= Biennium)
        "keep the overall period
        "this should actually no be happening
        RS_OVERALL_INTERVAL = LS_BIENNIUM.
      WHEN C_ENC_MOD_ID_88. "biennium + extension period
        "(reason: in certain contexts (like PFF-funding) it is required
        "that in case the contract enddate exceed the biennium,
        "(pre)commitment documents be created beyond the biennium.
        RS_OVERALL_INTERVAL = LS_BIENNIUM.

        RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-ENDDA(4)
          "currently the extension period is not transparently
          "configurable, use a quasi-constant, that is set
          "to a value at initalization
          + MV_EXTENSION_YEARS.
      WHEN OTHERS.
        MESSAGE A001(ZPBC) WITH IS_HROBJECT INTO MSG_DUMMY.
    ENDCASE.

    "finally it has to be assured that the date are compatible
    "with the commitment processor settings

    "overall period calculated by applicaation of rules must
    "not exceed the overal commitmentintrval

    IF NOT MSG_DUMMY IS INITIAL.
      CREATE OBJECT EXC_DYN_ENC
        EXPORTING
          HROBJECT = IS_HROBJECT.

      EXC_DYN_ENC->SET_SY_MESSAGE( ).
      RAISE EXCEPTION EXC_DYN_ENC.
    ENDIF.

    ASSERT RS_OVERALL_INTERVAL-BEGDA GE IS_ACTV_ENCUMB-BEGDA
       AND RS_OVERALL_INTERVAL-ENDDA LE IS_ACTV_ENCUMB-ENDDA.

  ENDMETHOD.                    "detoverall_period_det_id

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00K ----
METHOD DO_HANDLE_COMMITMENT_PERIOD.
   "delegated to subclasses
  RETURN.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00L ----
METHOD DET_BIENNIUM_FROM_ENC_IV.
  DATA LV_YEAR_SPAN TYPE I.
*  Service method: for an overall commitment interval
* ENC_IV  the method determines the ‘relevant biennium’;

* assumption 1:
  "enddate is Dec-31
  ASSERT IS_ENC_IV-ENDDA+4(4) = '1231'.

* assumption 2.
  "encumbrance interval covers at least two years
  "where 'actually' the valid encumbrance interval ('Biennium')
  "ends one year before the enddate
  LV_YEAR_SPAN = IS_ENC_IV-ENDDA(4) - IS_ENC_IV-BEGDA(4) .
*{   REPLACE        D01K9B04Z3                                        1
*\  assert lv_year_span BETWEEN 1 and 2.
  ASSERT LV_YEAR_SPAN GE 1.
*}   REPLACE

* Construct the biennium
   "a biennium begins always at the begin of the encumbrance period ...
   RS_BIENNIUM-BEGDA = IS_ENC_IV-BEGDA.

   "... and ends one year BEFORE the end of the encumbrance period
   RS_BIENNIUM-ENDDA = IS_ENC_IV-ENDDA.
*{   REPLACE        D01K9B04Z3                                        2
*\   rs_biennium-endda(4) = is_enc_iv-endda(4) - 1.
   RS_BIENNIUM-ENDDA(4) = RS_BIENNIUM-BEGDA(4) + 1.
*}   REPLACE

ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00M ----
METHOD GET_SCENARIO.
  RV_SCENARIO = C_SCENARIO_STAT.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00N ----
METHOD GET_EARLIEST_INFTY_RECORDS.

  DATA LRT_PNNNN TYPE REF TO DATA.
  FIELD-SYMBOLS <TPNNNN> TYPE TABLE.


  GO_INFTY_SERVICE =
    ZCL_INFTY_SERVICE=>S_GET_INSTANCE(
        IV_INFTY    = IV_INFTY
        IV_SUBTY    = IV_SUBTY
        IV_HIERARCHY = IV_HIERARCHY ).

  LRT_PNNNN = GO_INFTY_SERVICE->CREATE_TAB_INSTANCE( ).
  ASSIGN LRT_PNNNN->* TO <TPNNNN>.

  GO_INFTY_SERVICE->READ_INFTY_IN_PERIOD(
     EXPORTING
      IS_HROBJECT   = IS_HROBJECT
      IS_SEL_PERIOD = IS_SEL_PERIOD
     IMPORTING
       ET_PNNNN = <TPNNNN>  ).

  GO_INFTY_SERVICE->GET_EARLIEST_IN_PERIOD(
      EXPORTING
        IS_SEL_PERIOD = IS_SEL_PERIOD
        IT_PNNNN  = <TPNNNN>
      IMPORTING
        ET_PNNNN_EARLIEST  = ET_RECORDS ).


ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00O ----
METHOD GET_LATEST_INFTY_RECORDS.

  DATA LRT_PNNNN TYPE REF TO DATA.
  FIELD-SYMBOLS <TPNNNN> TYPE TABLE.


  GO_INFTY_SERVICE =
    ZCL_INFTY_SERVICE=>S_GET_INSTANCE(
        IV_INFTY    = IV_INFTY
        IV_SUBTY    = IV_SUBTY ).

  LRT_PNNNN = GO_INFTY_SERVICE->CREATE_TAB_INSTANCE( ).
  ASSIGN LRT_PNNNN->* TO <TPNNNN>.

  GO_INFTY_SERVICE->READ_INFTY_IN_PERIOD(
     EXPORTING
      IS_HROBJECT   = IS_HROBJECT
      IS_SEL_PERIOD = IS_SEL_PERIOD
     IMPORTING
       ET_PNNNN = <TPNNNN>  ).

  GO_INFTY_SERVICE->GET_LATEST_IN_PERIOD(
      EXPORTING
        IS_SEL_PERIOD = IS_SEL_PERIOD
        IT_PNNNN  = <TPNNNN>
      IMPORTING
        ET_PNNNN_LATEST  = ET_RECORDS ).

ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00P ----
METHOD PROVIDE_OVERALL_PERIOD_DATA_S.
  DATA LT_P1008 TYPE TABLE OF P1008.
  FIELD-SYMBOLS <P1008> LIKE LINE OF LT_P1008.
  DATA LT_P1018_EXP TYPE TABLE OF P1018_EXP.
  DATA LRS_DET_DATA TYPE REF TO TS_OVERALL_PERIOD_DET_DATA.
  FIELD-SYMBOLS <P1018> LIKE LINE OF LT_P1018_EXP.

  BREAK-POINT ID Z_ENCUMB_PROTO.

  CREATE DATA LRS_DET_DATA.
  RRS_PERIOD_DET_DATA = LRS_DET_DATA.

  GET_LATEST_INFTY_RECORDS(
   EXPORTING
     IS_HROBJECT   = IS_HROBJECT
     IS_SEL_PERIOD = IS_SEL_PERIOD
     IV_INFTY      = '1008'
     "iv_hierarchy  = abap_true
  IMPORTING
     ET_RECORDS      = LT_P1008 ).

  IF NOT LT_P1008 IS INITIAL.
    READ TABLE LT_P1008 INDEX 1 ASSIGNING <P1008>.

    IF <P1008> IS ASSIGNED.
      LRS_DET_DATA->GSBER = <P1008>-GSBER.
    ELSE.
      MESSAGE A003(ZPBC) WITH IS_HROBJECT '1008' INTO MSG_DUMMY.
*     No data for determination of interval found: Object &1 , Infotype &2
      CREATE OBJECT EXC_DYN_ENC
        EXPORTING
          HROBJECT = IS_HROBJECT.
      EXC_DYN_ENC->SET_SY_MESSAGE( ).
      RAISE EXCEPTION EXC_DYN_ENC.
    ENDIF.
  ENDIF.

  "used It1018 instead
  CHECK 1 = 2.
*  get_latest_infty_records(
*   EXPORTING
*     is_hrobject   = is_hrobject
*     is_sel_period = is_sel_period
*     iv_infty      = '1018'
*  IMPORTING
*     et_records      = lt_p1018_exp ).
*
*  IF NOT lt_p1018_exp IS INITIAL.
*    LOOP AT lt_p1018_exp ASSIGNING <p1018>.
*      IF sy-subrc = 1 .
*        lrs_det_data->gsber = <p1018>-gsber.
*      ELSE.
*        IF NOT ( <p1018>-gsber IS INITIAL OR
*          lrs_det_data->gsber  = <p1018>-gsber ).
*
*          MESSAGE a899(hrfpm)
*           WITH 'NO VALID DETERMINATION DATA'
*                'FOR OVERALL PERIOD DETERMINATION'
*                '' '' INTO msg_dummy.
*
*          CREATE OBJECT exc_dyn_enc
*            EXPORTING
*              hrobject = is_hrobject.
*
*          exc_dyn_enc->set_sy_message( ).
*          RAISE EXCEPTION exc_dyn_enc.
*        ENDIF.
*      ENDIF.
*    ENDLOOP.
*  ENDIF.

ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00Q ----
METHOD CHECK_ACC_ASS_INTEGRATED.
  "should be configurable, but for the time beeing this should do.
  CASE IS_REQUIREMENT-ACC_ASS-BUKRS.
    WHEN 'UNES'
      OR 'UBO'.
      RV_IS_INTEGRATED = ABAP_TRUE.
    WHEN OTHERS.
      RV_IS_INTEGRATED = ABAP_FALSE.
  ENDCASE.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00R ----
METHOD DO_HANDLE_ACC_ASSIGNMENT.
  "filtration with respect to account assignment
  FIELD-SYMBOLS <REQ> LIKE LINE OF CT_REQUIREMENT.
  DATA LV_TABIX TYPE SY-TABIX.

  LOOP AT CT_REQUIREMENT ASSIGNING <REQ>.
    LV_TABIX = SY-TABIX.
    IF CHECK_ACC_ASS_INTEGRATED( <REQ> ) = ABAP_FALSE.
      DELETE CT_REQUIREMENT INDEX LV_TABIX.
    ENDIF.
  ENDLOOP.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00S ----
  METHOD _DET_OVERALL_PERIOD.

    "UNESCO wants for PERNR the overall encumbrance period depending from
    "different features of a contract/org criteria and the biennium

    "Two Steps:
    "1. derive a 'determination id' --> det_overall_period_det_id
    "2. based on that do the calculation of the endddate; this
    "calculation is always with respect to the biennium


    "TODO: make this configurable:
    "one idea: provide a filtered badi, where the filter values
    "are exactly the determination ID´'s from step 1

*
    BREAK-POINT ID Z_ENCUMB_PROTO.

    DATA LS_BIENNIUM TYPE HRFPM_TIME.

    "Biennium
    LS_BIENNIUM = DET_BIENNIUM_FROM_ENC_IV(
        IS_HROBJECT    = IS_HROBJECT
        IS_ENC_IV      = IS_ACTV_ENCUMB  ).


    CASE DET_OVERALL_PERIOD_DET_ID(
             IS_HROBJECT   = IS_HROBJECT
             IRS_DETERMINATION_DATA = IRS_DETERMINATION_DATA
             IS_BIENNIUM = LS_BIENNIUM ).
      WHEN C_ENC_MOD_ID_1 .

        CLEAR MSG_DUMMY.
        "ONE year offset from start date of current fiscal year
        "(in fact the start date of that half of the biennium
        "where sy-datum belongs to)
        "Precondition: half of the biennium starts at the beginning of
        "a fiscal year (calendar year)
        RS_OVERALL_INTERVAL = LS_BIENNIUM.
*        IF
*          "this is indeed possible (when running an initial run for
*          "example)
*          "sy-datum LT ls_biennium-begda OR
*          sy-datum GT ls_biennium-endda.
*          "something has not been fully understood.
*          ASSERT 1 = 2.
*
*        ELSEIF sy-datum(4) = ls_biennium-begda(4)
*          "in initial run the biennium at this time is alreadz correct
*          OR NOT mv_in_initrun IS INITIAL.
*          "first half of biennium
*          rs_overall_interval-endda(4) = ls_biennium-begda(4) .
*        ELSEIF sy-datum(4) = ls_biennium-endda(4).
*          "second half and not in init run
*          rs_overall_interval-endda(4) = ls_biennium-endda(4) .
*        ELSE.
**          rs_overall_interval-endda(4) = ls_biennium-endda(4) .
**          rs_overall_interval-begda = '99990101'.
**          rs_overall_interval-begda(4) = ls_biennium-endda(4).
*          MESSAGE a001(zpbc) WITH is_hrobject INTO msg_dummy.
*
*          CREATE OBJECT exc_dyn_enc
*            EXPORTING
*              hrobject = is_hrobject.
*
*          exc_dyn_enc->set_sy_message( ).
*          RAISE EXCEPTION exc_dyn_enc.
*        ENDIF.

        ASSERT SY-DATUM(4) LE LS_BIENNIUM-ENDDA(4).

        IF SY-DATUM(4) LT LS_BIENNIUM-BEGDA(4)  .
          "run starts before biennium that is processed in this run
          IF NOT MV_IN_INITRUN IS INITIAL.
            "in init run
            RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-BEGDA(4) .
          ELSE.
            MESSAGE A001(ZPBC) WITH IS_HROBJECT INTO MSG_DUMMY.
          ENDIF.
        ELSEIF SY-DATUM(4) = LS_BIENNIUM-BEGDA(4).
          "run starts in first half of the biennium processed in this run
          IF NOT MV_IN_INITRUN IS INITIAL.
            MESSAGE A001(ZPBC) WITH IS_HROBJECT INTO MSG_DUMMY.
          ELSE.
            RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-BEGDA(4) .
          ENDIF.
        ELSEIF SY-DATUM(4) = LS_BIENNIUM-ENDDA(4).
          "run starts in second half of the biennium 'of this run'
          IF NOT MV_IN_INITRUN IS INITIAL.
            MESSAGE A001(ZPBC) WITH IS_HROBJECT INTO MSG_DUMMY.
          ELSE.
            RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-ENDDA(4) .
            "this means a rolling period! that is the commitment
            "period is now the full binnium
          ENDIF.
        ENDIF.
      WHEN C_ENC_MOD_ID_1_2.
        "cut off scenario:
        "do not longer account of changes occuring in the first half!
        "might be one way of dealing with Scenario2 fiscal year change
        "(changing fiscal year in the middle of a biennium)
        RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-ENDDA(4) .
        RS_OVERALL_INTERVAL-BEGDA(4) = LS_BIENNIUM-ENDDA(4) .
      WHEN C_ENC_MOD_ID_0.  "(= Biennium)
        "keep the overall period
        "this should actually no be happening
        RS_OVERALL_INTERVAL = LS_BIENNIUM.
      WHEN C_ENC_MOD_ID_88. "biennium + extension period
        "(reason: in certain contexts (like PFF-funding) it is required
        "that in case the contract enddate exceed the biennium,
        "(pre)commitment documents be created beyond the biennium.
        RS_OVERALL_INTERVAL = LS_BIENNIUM.

        RS_OVERALL_INTERVAL-ENDDA(4) = LS_BIENNIUM-ENDDA(4)
          "currently the extension period is not transparently
          "configurable, use a quasi-constant, that is set
          "to a value at initalization
          + MV_EXTENSION_YEARS.
      WHEN OTHERS.
        MESSAGE A001(ZPBC) WITH IS_HROBJECT INTO MSG_DUMMY.

        CREATE OBJECT EXC_DYN_ENC
          EXPORTING
            HROBJECT = IS_HROBJECT.

        EXC_DYN_ENC->SET_SY_MESSAGE( ).
        RAISE EXCEPTION EXC_DYN_ENC.
    ENDCASE.

    "finally it has to be assured that the date are compatible
    "with the commitment processor settings

    "overall period calculated by applicaation of rules must
    "not exceed the overal commitmentintrval

    ASSERT RS_OVERALL_INTERVAL-BEGDA GE IS_ACTV_ENCUMB-BEGDA
       AND RS_OVERALL_INTERVAL-ENDDA LE IS_ACTV_ENCUMB-ENDDA.


  ENDMETHOD.                    "detoverall_period_det_id

* ---- ZCL_IM__UNESCO_ENCUMB=========CM00T ----
  METHOD CONTRACT_TYPE_IS_TEMPORARY.
    "SAP_: decision is needed at several plaveces now =
    "make it reusable
    RV_IS_TEMPORARY = BOOLC( IV_CONTRACT_TYPE = '03'
                             OR IV_CONTRACT_TYPE = '04'
                             OR IV_CONTRACT_TYPE = '05'
                             OR IV_CONTRACT_TYPE = '06'
                             OR IV_CONTRACT_TYPE = '18'
                             OR IV_CONTRACT_TYPE = '20'
                             OR IV_CONTRACT_TYPE = '21' ).
  ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB=========CO ----
PROTECTED SECTION.

*"* protected components of class ZCL_IM__UNESCO_ENCUMB
*"* do not include other source files here!!!
  ALIASES C_ENC_MOD_ID_0
    FOR ZIF_ENCUMB_HANDLING~C_ENC_MOD_ID_0 .
  ALIASES C_ENC_MOD_ID_1
    FOR ZIF_ENCUMB_HANDLING~C_ENC_MOD_ID_1 .
  ALIASES C_ENC_MOD_ID_1_2
    FOR ZIF_ENCUMB_HANDLING~C_ENC_MOD_ID_1_2 .
  ALIASES C_ENC_MOD_ID_1_3
    FOR ZIF_ENCUMB_HANDLING~C_ENC_MOD_ID_1_3 .
  ALIASES C_ENC_MOD_ID_88
    FOR ZIF_ENCUMB_HANDLING~C_ENC_MOD_ID_88 .

  TYPES:
    TT_REQ_SORTED TYPE SORTED TABLE OF HRBPREP_REQUIREMENT_ACC_ASS
         WITH NON-UNIQUE KEY
            HROBJECT DUE_DATE BEGDA ENDDA ACC_ASS CITEM .
  TYPES:
    BEGIN OF TS_OVERALL_PERIOD_DET_DATA,
             GSBER TYPE GSBER,
             "change request June-2019
             "'temporary' smployees need to be
             "financed until high date
             "need contract type as additional
             "decision criterion
             ANSVH TYPE P0001-ANSVH,
           END OF TS_OVERALL_PERIOD_DET_DATA .
  TYPES:
    BEGIN OF TS_DETAIL_PERIOD_DET_DATA,
            ANSVH TYPE P0001-ANSVH,
            CONTRACT_END_DATE TYPE P0016-CTEDT,
            GSBER TYPE GSBER,
          END OF TS_DETAIL_PERIOD_DET_DATA .
  TYPES T_SCENARIO TYPE CHAR2 .

  DATA MV_EXTENSION_YEARS TYPE I .
  CLASS-DATA EXC_ADMIN TYPE REF TO CX_HRFPM_ADMINISTRATOR .
  CLASS-DATA MSG_DUMMY TYPE STRING .
  CLASS-DATA GO_INFTY_SERVICE TYPE REF TO ZIF_INFTY_SERVICES .
  DATA MO_ENCUMB_HANDLING TYPE REF TO ZIF_ENCUMB_HANDLING .
  DATA MO_REQUIREMENT_FILTER TYPE REF TO ZIF_REQUIREMENT_FILTER .
  CLASS-DATA EXC_ROOT TYPE REF TO CX_HRFPM .
  CLASS-DATA EXC_DC TYPE REF TO CX_HRFPM_DC .
  CLASS-DATA EXC_DYN_ENC TYPE REF TO CX_HRFPM_DYNAMIC_ENC_IV .
  CONSTANTS C_SCENARIO_DYN TYPE T_SCENARIO VALUE '02' ##NO_TEXT.
  CONSTANTS C_SCENARIO_STAT TYPE T_SCENARIO VALUE '01' ##NO_TEXT.
  DATA MV_IN_INITRUN TYPE FLAG .

  METHODS CONTRACT_TYPE_IS_TEMPORARY
    IMPORTING
      !IV_CONTRACT_TYPE TYPE ANSVH
    RETURNING
      VALUE(RV_IS_TEMPORARY) TYPE BOOLE_D .
  METHODS CHECK_ACC_ASS_INTEGRATED
    IMPORTING
      !IS_REQUIREMENT TYPE HRBPREP_REQUIREMENT_ACC_ASS
    RETURNING
      VALUE(RV_IS_INTEGRATED) TYPE BOOLE_D .
  METHODS DET_BIENNIUM_FROM_ENC_IV
    IMPORTING
      !IS_HROBJECT TYPE HROBJECT
      !IS_ENC_IV TYPE T77HRFPM_ENCUMB
    RETURNING
      VALUE(RS_BIENNIUM) TYPE HRFPM_OBJECT_VALIDITY_IV .
  METHODS DET_OVERALL_PERIOD
    IMPORTING
      !IRS_DETERMINATION_DATA TYPE REF TO DATA
      !IS_HROBJECT TYPE HROBJECT
      !IS_ACTV_ENCUMB TYPE T77HRFPM_ENCUMB
    RETURNING
      VALUE(RS_OVERALL_INTERVAL) TYPE HRFPM_TIME
    RAISING
      CX_HRFPM_DYNAMIC_ENC_IV .
  METHODS _DET_OVERALL_PERIOD
    IMPORTING
      !IRS_DETERMINATION_DATA TYPE REF TO DATA
      !IS_HROBJECT TYPE HROBJECT
      !IS_ACTV_ENCUMB TYPE T77HRFPM_ENCUMB
    RETURNING
      VALUE(RS_OVERALL_INTERVAL) TYPE HRFPM_TIME
    RAISING
      CX_HRFPM_DYNAMIC_ENC_IV .
  METHODS DET_OVERALL_PERIOD_DET_ID
    IMPORTING
      !IRS_DETERMINATION_DATA TYPE REF TO DATA
      !IS_HROBJECT TYPE HROBJECT
      !IS_SEL_PERIOD TYPE HRFPM_TIME OPTIONAL
      !IS_BIENNIUM TYPE HRFPM_TIME
    RETURNING
      VALUE(RV_MOD_ID) TYPE ZIF_ENCUMB_HANDLING=>T_MOD_ID
    RAISING
      CX_HRFPM_DYNAMIC_ENC_IV .
  METHODS DET_DETAIL_PERIOD
    IMPORTING
      !IRS_DETERMINATION_DATA TYPE REF TO DATA
      !IS_OVERALL_PERIOD TYPE HRFPM_TIME
      !IS_HROBJECT TYPE HROBJECT
      !IS_BIENNIUM TYPE HRFPM_TIME
    RETURNING
      VALUE(RS_DETAIL_INTERVAL) TYPE HRFPM_TIME
    RAISING
      CX_HRFPM_DYNAMIC_ENC_IV .
  METHODS INIT_ENCUMB_HANDLING
    IMPORTING
      VALUE(IV_RUNID) TYPE HRFPM_RUNID OPTIONAL .
  METHODS INIT_REQU_FILTER
    IMPORTING
      VALUE(IV_RUNID) TYPE HRFPM_RUNID OPTIONAL .
  METHODS PROVIDE_OVERALL_PERIOD_DATA
    IMPORTING
      !IS_HROBJECT TYPE HROBJECT
      !IS_SEL_PERIOD TYPE HRFPM_TIME
    RETURNING
      VALUE(RRS_PERIOD_DET_DATA) TYPE REF TO DATA
    RAISING
      CX_HRFPM_DYNAMIC_ENC_IV .
  METHODS GET_LATEST_INFTY_RECORDS
    IMPORTING
      !IS_HROBJECT TYPE HROBJECT
      !IS_SEL_PERIOD TYPE HRFPM_TIME
      !IV_INFTY TYPE INFTY
      !IV_SUBTY TYPE SUBTY OPTIONAL
    EXPORTING
      !ET_RECORDS TYPE TABLE .
  METHODS PROVIDE_DETAIL_PERIOD_DATA
    IMPORTING
      !IS_HROBJECT TYPE HROBJECT
      !IS_SEL_PERIOD TYPE HRFPM_TIME
    RETURNING
      VALUE(RRS_PERIOD_DET_DATA) TYPE REF TO DATA
    RAISING
      CX_HRFPM_DYNAMIC_ENC_IV .
  METHODS GET_EARLIEST_INFTY_RECORDS
    IMPORTING
      !IS_HROBJECT TYPE HROBJECT
      !IS_SEL_PERIOD TYPE HRFPM_TIME
      !IV_INFTY TYPE INFTY
      !IV_SUBTY TYPE SUBTY OPTIONAL
      !IV_HIERARCHY TYPE ABAP_BOOL OPTIONAL
    EXPORTING
      !ET_RECORDS TYPE TABLE .
  METHODS GET_SCENARIO
    IMPORTING
      !IS_SEL_PER TYPE HRFPM_TIME
      !IS_HROBJECT TYPE HROBJECT
    RETURNING
      VALUE(RV_SCENARIO) TYPE T_SCENARIO .
  METHODS PROVIDE_OVERALL_PERIOD_DATA_S
    IMPORTING
      !IS_HROBJECT TYPE HROBJECT
      !IS_SEL_PERIOD TYPE HRFPM_TIME
    RETURNING
      VALUE(RRS_PERIOD_DET_DATA) TYPE REF TO DATA
    RAISING
      CX_HRFPM_DYNAMIC_ENC_IV .

* ---- ZCL_IM__UNESCO_ENCUMB=========CU ----
CLASS ZCL_IM__UNESCO_ENCUMB DEFINITION
  PUBLIC
  CREATE PUBLIC .

PUBLIC SECTION.

*"* public components of class ZCL_IM__UNESCO_ENCUMB
*"* do not include other source files here!!!
  INTERFACES IF_EX_HRFPM_ENCUMB_IV .
  INTERFACES ZIF_ENCUMB_HANDLING .
  INTERFACES ZIF_REQUIREMENT_FILTER .

  CLASS-METHODS ADJUST_REQ_WITH_VALIDITY
    IMPORTING
      !IS_NEW_VAL TYPE HRFPM_TIME
      !IS_REQ TYPE HRBPREP_REQUIREMENT_ACC_ASS
    EXPORTING
      !ET_REQ_ADJUSTED TYPE HRBPREP_REQUIREMENT_ACC_ASS_IT
      !ET_REQ_SKIPPED TYPE HRBPREP_REQUIREMENT_ACC_ASS_IT
    RAISING
      CX_HRFPM_ADMINISTRATOR .
  METHODS DO_HANDLE_ACC_ASSIGNMENT
    IMPORTING
      !IS_FILTRATION_PERIOD TYPE HRFPM_TIME
    CHANGING
      !CT_REQUIREMENT TYPE HRBPREP_REQUIREMENT_ACC_ASS_IT
    RAISING
      CX_HRFPM_DC .
  METHODS DO_HANDLE_VACANCY
    IMPORTING
      !IS_FILTRATION_PERIOD TYPE HRFPM_TIME
    CHANGING
      !CT_REQUIREMENT TYPE HRBPREP_REQUIREMENT_ACC_ASS_IT
    RAISING
      CX_HRFPM_DC .
  METHODS DO_HANDLE_COMMITMENT_PERIOD
    IMPORTING
      !IS_FILTRATION_PERIOD TYPE HRFPM_TIME
    CHANGING
      !CT_REQUIREMENT TYPE HRBPREP_REQUIREMENT_ACC_ASS_IT
    RAISING
      CX_HRFPM_DC .