* ==== CLASS POOL ZCL_IM__UNESCO_ENCUMB_ENCPER ====
CLASS-POOL .
*"* class pool for class ZCL_IM__UNESCO_ENCUMB_ENCPER

*"* local type definitions
INCLUDE ZCL_IM__UNESCO_ENCUMB_ENCPER==CCDEF.

*"* class ZCL_IM__UNESCO_ENCUMB_ENCPER definition
*"* public declarations
  INCLUDE ZCL_IM__UNESCO_ENCUMB_ENCPER==CU.
*"* protected declarations
  INCLUDE ZCL_IM__UNESCO_ENCUMB_ENCPER==CO.
*"* private declarations
  INCLUDE ZCL_IM__UNESCO_ENCUMB_ENCPER==CI.
ENDCLASS. "ZCL_IM__UNESCO_ENCUMB_ENCPER definition

*"* macro definitions
INCLUDE ZCL_IM__UNESCO_ENCUMB_ENCPER==CCMAC.
*"* local class implementation
INCLUDE ZCL_IM__UNESCO_ENCUMB_ENCPER==CCIMP.

CLASS ZCL_IM__UNESCO_ENCUMB_ENCPER IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM__UNESCO_ENCUMB_ENCPER implementation


* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CI ----
PRIVATE SECTION.
*"* private components of class ZCL_IM__UNESCO_ENCUMB_ENCPER
*"* do not include other source files here!!!

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CM001 ----
  METHOD IF_HRFPM_DC_PERIOD~OBJECT_GET_PERIOD.

    DATA LS_VALIDITY TYPE HRFPM_TIME.

    CLEAR:
       EXC_DYN_ENC,
       E_SKIP.
    TRY .

        IF_EX_HRFPM_ENCUMB_IV~GET_OBJECT_ENC_IV(
          EXPORTING
            P_OBJECT      = I_OBJECT-HROBJECT
          IMPORTING
            P_ENC_DATE_IV = LS_VALIDITY ).

        IF LS_VALIDITY IS INITIAL.
          E_SKIP = 'X'.
        ELSE.
          "cut with existence interval
          "should actuially be integrated into get_object_enc_iv, but this
          "means enhancing the BadI-interface etc. just avoid this for the
          "tiem beeing..
          E_BEGDA = LS_VALIDITY-BEGDA.
          E_ENDDA = LS_VALIDITY-ENDDA.

          IF E_BEGDA LT I_OBJECT-BEGDA.
            E_BEGDA = I_OBJECT-BEGDA.
          ENDIF.

          IF E_ENDDA GT I_OBJECT-ENDDA.
            E_ENDDA = I_OBJECT-ENDDA.
          ENDIF.
        ENDIF.
      CATCH CX_HRFPM_DYNAMIC_ENC_IV INTO EXC_DYN_ENC.
        E_SKIP = 'X'.
    ENDTRY.


    IF NOT E_SKIP IS INITIAL.
      TRY.
          RAISE EXCEPTION TYPE CX_HRFPM_DYNAMIC_ENC_IV
            EXPORTING
              PREVIOUS    = EXC_DYN_ENC
              HROBJECT    = I_OBJECT-HROBJECT
              MODULE_NAME = CL_HRFPM_CONST=>MODULE_NAME_DC
              RESP_DEP    = CL_HRFPM_CONST=>RESP_DEP_AD.
        CATCH  CX_HRFPM_DYNAMIC_ENC_IV INTO EXC_DYN_ENC.
          MESSAGE W002(ZPBC) WITH I_OBJECT-HROBJECT INTO MSG_DUMMY.
          EXC_DYN_ENC->SET_SY_MESSAGE( ).
          "just add a message to the message log
          CL_HRFPM_APPL_LOG=>WRITE_EXCEPTION_LOG( EXC_DYN_ENC ).
      ENDTRY.
    ENDIF.



  ENDMETHOD.                    "IF_HRFPM_DC_PERIOD~OBJECT_GET_PERIOD

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CM002 ----
METHOD ZIF_ENCUMB_HANDLING~GET_OVERALL_INTERVAL.
    "UNESCO wants for PERNR the overall encumbrance period depending from
    "different features of a contract/org criteria

    BREAK-POINT ID Z_ENCUMB_PROTO.

    DATA LS_BIENNIUM TYPE HRFPM_TIME.
    "Biennium is 'Start date of active period
                                                            "+ 2 Years
    LS_BIENNIUM = DET_BIENNIUM_FROM_ENC_IV(
        IS_HROBJECT  = IS_HROBJECT
        IS_ENC_IV    = IS_ACTV_ENCUMB  ).

    RS_OVERALL_INTERVAL =
      DET_OVERALL_PERIOD(
        IRS_DETERMINATION_DATA =
            PROVIDE_OVERALL_PERIOD_DATA(
                 IS_HROBJECT    = IS_HROBJECT
                 "this actually means´: the last recrod
                 "in the CURRENT biennium is determining
                  IS_SEL_PERIOD  = LS_BIENNIUM )
        IS_HROBJECT            = IS_HROBJECT
        IS_ACTV_ENCUMB         = IS_ACTV_ENCUMB ).
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CM003 ----
METHOD IF_EX_HRFPM_ENCUMB_IV~CHECK_ACC_IV.
  "not implemented
  ASSERT 1 = 2.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CM004 ----
METHOD IF_EX_HRFPM_ENCUMB_IV~GET_ACTIVE_FLAG.
  "not implemented
  ASSERT 1 = 2.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CM005 ----
METHOD ZIF_ENCUMB_HANDLING~GET_DETAIL_INTERVAL.
  BREAK-POINT ID Z_ENCUMB_PROTO.

  DATA LS_BIENNIUM TYPE HRFPM_TIME.

  LS_BIENNIUM =
     DET_BIENNIUM_FROM_ENC_IV(
         IS_HROBJECT = IS_HROBJECT
         IS_ENC_IV   = IS_ACTV_ENCUMB  ).
  "step 1: get the overall interval within that the detailed
  "interval has to be determined

  "by default: detail interval = overall interval
  RS_DETAIL_INTERVAL =
       ZIF_ENCUMB_HANDLING~GET_OVERALL_INTERVAL(
           IS_HROBJECT    = IS_HROBJECT
           IS_ACTV_ENCUMB = IS_ACTV_ENCUMB ).

  IF IS_HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_P.
    "only for PERNR the detail interval might be differnt
    RS_DETAIL_INTERVAL =
        DET_DETAIL_PERIOD(
              IS_BIENNIUM        = LS_BIENNIUM
              IS_OVERALL_PERIOD  = RS_DETAIL_INTERVAL
              IS_HROBJECT        = IS_HROBJECT
              IRS_DETERMINATION_DATA  =
                  "2. provide necceary data
                  "0001-ANSVH, 0016-CTEDT
                  PROVIDE_DETAIL_PERIOD_DATA(
                     IS_HROBJECT    = IS_HROBJECT
*{   REPLACE        D01K9B05UY                                        1
*\                     is_sel_period  = ls_biennium  ) ).
                     "malke sure to select the latest records available
                     IS_SEL_PERIOD  = RS_DETAIL_INTERVAL  ) ).
*}   REPLACE

  ENDIF.
ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CM006 ----
  METHOD IF_HRFPM_DC_PERIOD~OBJECT_SPLIT_PERIOD.
  ENDMETHOD.

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_IM__UNESCO_ENCUMB_ENCPER
*"* do not include other source files here!!!

* ---- ZCL_IM__UNESCO_ENCUMB_ENCPER==CU ----
CLASS ZCL_IM__UNESCO_ENCUMB_ENCPER DEFINITION
  PUBLIC
  INHERITING FROM ZCL_IM__UNESCO_ENCUMB
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.
*"* public components of class ZCL_IM__UNESCO_ENCUMB_ENCPER
*"* do not include other source files here!!!

  INTERFACES IF_BADI_INTERFACE .
  INTERFACES IF_HRFPM_DC_PERIOD .

  METHODS IF_EX_HRFPM_ENCUMB_IV~CHECK_ACC_IV
    REDEFINITION .
  METHODS IF_EX_HRFPM_ENCUMB_IV~GET_ACTIVE_FLAG
    REDEFINITION .
  METHODS ZIF_ENCUMB_HANDLING~GET_DETAIL_INTERVAL
    REDEFINITION .
  METHODS ZIF_ENCUMB_HANDLING~GET_OVERALL_INTERVAL
    REDEFINITION .