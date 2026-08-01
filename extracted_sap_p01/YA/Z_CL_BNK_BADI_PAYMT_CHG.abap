* ==== CLASS POOL Z_CL_BNK_BADI_PAYMT_CHG ====
CLASS-POOL .
*"* class pool for class Z_CL_BNK_BADI_PAYMT_CHG

*"* local type definitions
INCLUDE Z_CL_BNK_BADI_PAYMT_CHG=======CCDEF.

*"* class Z_CL_BNK_BADI_PAYMT_CHG definition
*"* public declarations
  INCLUDE Z_CL_BNK_BADI_PAYMT_CHG=======CU.
*"* protected declarations
  INCLUDE Z_CL_BNK_BADI_PAYMT_CHG=======CO.
*"* private declarations
  INCLUDE Z_CL_BNK_BADI_PAYMT_CHG=======CI.
ENDCLASS. "Z_CL_BNK_BADI_PAYMT_CHG definition

*"* macro definitions
INCLUDE Z_CL_BNK_BADI_PAYMT_CHG=======CCMAC.
*"* local class implementation
INCLUDE Z_CL_BNK_BADI_PAYMT_CHG=======CCIMP.

CLASS Z_CL_BNK_BADI_PAYMT_CHG IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "Z_CL_BNK_BADI_PAYMT_CHG implementation


* ---- Z_CL_BNK_BADI_PAYMT_CHG=======CI ----
PRIVATE SECTION.

* ---- Z_CL_BNK_BADI_PAYMT_CHG=======CM001 ----
  METHOD IF_EX_BNK_ORIG_PAYMT_CHG~ON_RESUBMIT.

** SAP note 1333640 - call standard fallback implementation **
  DATA: FALLBACK TYPE REF TO CL_BNK_BADI_ORIG_PAYMT_CHG.

  CREATE OBJECT FALLBACK.

  CALL METHOD FALLBACK->IF_EX_BNK_ORIG_PAYMT_CHG~ON_RESUBMIT
    EXPORTING
      I_REGUH = I_REGUH.

  ENDMETHOD.

* ---- Z_CL_BNK_BADI_PAYMT_CHG=======CM002 ----
  METHOD IF_EX_BNK_ORIG_PAYMT_CHG~ON_REJECT.
**----------------------------------------------------------------------------
** SAP note 1333640
** Proposal for automatic system action on batch/payment rejection:
** Reset cleared items and reverse payment documents (F110)
**
** Before applying this automatically, first create a class
** Z_CL_BNK_BADI_PAYMT_CHG that implements interface IF_EX_BNK_ORIG_PAYMT_CHG
**
** Update "LG20100827: Write aplication log (SLG1/FBPM)
**----------------------------------------------------------------------------

  DATA: LF_T001 TYPE T001,
        L_GJAHR TYPE GJAHR,
        L_EXTNUMBER TYPE BALNREXT.                          "LG20100827

  CONCATENATE 'ON_REJECT'
              SY-DATUM SY-UZEIT SY-UNAME INTO L_EXTNUMBER . "LG20100827

*- Get year from posting date
  CALL FUNCTION 'COMPANY_CODE_READ'
    EXPORTING
      I_BUKRS = I_REGUH-ZBUKR
    IMPORTING
      E_T001  = LF_T001
    EXCEPTIONS
      OTHERS  = 5.

  IF SY-SUBRC <> 0.                                         "LG20100827
    CALL FUNCTION 'BNK_UI_LOG_MSG_ADD'                      "LG20100827
      EXPORTING
        I_MSGID     = SY-MSGID
        I_MSGNO     = SY-MSGNO
        I_MSGTY     = 'E'
        I_MSGV1     = SY-MSGV1
        I_MSGV2     = SY-MSGV2
        I_MSGV3     = SY-MSGV3
        I_MSGV4     = SY-MSGV4
        I_EXTNUMBER = L_EXTNUMBER.
    MESSAGE ID SY-MSGID TYPE 'I' NUMBER SY-MSGNO            "LG20100827
            WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    CALL FUNCTION 'BNK_UI_LOG_SAVE'.
    EXIT.
  ENDIF.

  CALL FUNCTION 'DATE_TO_PERIOD_CONVERT'
    EXPORTING
      I_DATE  = I_REGUH-ZALDT "posting date
      I_PERIV = LF_T001-PERIV
    IMPORTING
      E_GJAHR = L_GJAHR
    EXCEPTIONS
      OTHERS  = 5.

  IF SY-SUBRC <> 0.                                         "LG20100827
    CALL FUNCTION 'BNK_UI_LOG_MSG_ADD'                      "LG20100827
      EXPORTING
        I_MSGID     = SY-MSGID
        I_MSGNO     = SY-MSGNO
        I_MSGTY     = 'E'
        I_MSGV1     = SY-MSGV1
        I_MSGV2     = SY-MSGV2
        I_MSGV3     = SY-MSGV3
        I_MSGV4     = SY-MSGV4
        I_EXTNUMBER = L_EXTNUMBER.
    MESSAGE ID SY-MSGID TYPE 'I' NUMBER SY-MSGNO            "LG20100827
            WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    CALL FUNCTION 'BNK_UI_LOG_SAVE'.
    EXIT.
  ENDIF.

  CALL FUNCTION 'J_1B_FBRA_POSTING_AUFRUFEN'
    EXPORTING
      I_AUGBL           = I_REGUH-VBLNR
      I_BUKRS           = I_REGUH-ZBUKR
      I_GJAHR           = L_GJAHR "derived from I_REGUH-ZALDT
      I_STGRD           = '01'
    EXCEPTIONS
      NOT_POSSIBLE_FBRA = 1
      NOT_POSSIBLE_FB08 = 2
      OTHERS            = 3.

  IF SY-SUBRC <> 0.
    CALL FUNCTION 'BNK_UI_LOG_MSG_ADD'                      "LG20100827
      EXPORTING
        I_MSGID     = SY-MSGID
        I_MSGNO     = SY-MSGNO
        I_MSGTY     = SY-MSGTY
        I_MSGV1     = SY-MSGV1
        I_MSGV2     = SY-MSGV2
        I_MSGV3     = SY-MSGV3
        I_MSGV4     = SY-MSGV4
        I_EXTNUMBER = L_EXTNUMBER.
    MESSAGE ID SY-MSGID TYPE 'I' NUMBER SY-MSGNO
            WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
    CALL FUNCTION 'BNK_UI_LOG_SAVE'.
  ENDIF.


  ENDMETHOD.

* ---- Z_CL_BNK_BADI_PAYMT_CHG=======CO ----
PROTECTED SECTION.

* ---- Z_CL_BNK_BADI_PAYMT_CHG=======CU ----
CLASS Z_CL_BNK_BADI_PAYMT_CHG DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  INTERFACES IF_EX_BNK_ORIG_PAYMT_CHG .
  INTERFACES IF_BADI_INTERFACE .