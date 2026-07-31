* ==== CLASS POOL ZCL_HRFPM_CD_ACC_BUILD_DOCS_UN ====
CLASS-POOL .
*"* class pool for class ZCL_HRFPM_CD_ACC_BUILD_DOCS_UN

*"* local type definitions
INCLUDE ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCCDEF.

*"* class ZCL_HRFPM_CD_ACC_BUILD_DOCS_UN definition
*"* public declarations
  INCLUDE ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCU.
*"* protected declarations
  INCLUDE ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCO.
*"* private declarations
  INCLUDE ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCI.
ENDCLASS. "ZCL_HRFPM_CD_ACC_BUILD_DOCS_UN definition

*"* macro definitions
INCLUDE ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCCMAC.
*"* local class implementation
INCLUDE ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCCIMP.

CLASS ZCL_HRFPM_CD_ACC_BUILD_DOCS_UN IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_HRFPM_CD_ACC_BUILD_DOCS_UN implementation


* ---- ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCI ----
PRIVATE SECTION.

* ---- ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCM001 ----
METHOD POST_DOCUMENTS.
*--- prec:   DOCUMENT_HAS_PERSISTENT_NUMBER

  DATA L_DOCDATE        TYPE SYDATUM.
  DATA LT_POSITIONS     TYPE TABLE OF HRFPM_ACC_IF_HR.
  DATA LS_POSITION      LIKE LINE OF LT_POSITIONS.
  DATA L_SUBRC          TYPE SY-SUBRC.
  DATA LT_MESSAGES      TYPE TABLE OF BAPIRET2.
  DATA LS_FM_VALUES     TYPE HRFPM_FPM_DOC_ACC_VALUE.
  DATA LS_FM_POS_TMP    TYPE HRFPM_FM_POS.
  DATA LS_UPD_INFO      LIKE LINE OF ET_UPDATE_INFO.

  FIELD-SYMBOLS:
       <ACC_POS> LIKE LINE OF LT_POSITIONS,
       <UPD_INFO> LIKE LINE OF ET_UPDATE_INFO.

  CLEAR ET_UPDATE_INFO.

  TRY.
      BUILD_DOCUMENT(
        EXPORTING
          IS_POS             = IS_HRFPM_FM_POS
        IMPORTING
          ES_POSITION_APP    = LS_POSITION ).

      INSERT LS_POSITION INTO TABLE LT_POSITIONS.
      LS_UPD_INFO-KEY_POS = IS_HRFPM_FM_POS-KEY_POS.
      INSERT LS_UPD_INFO INTO TABLE ET_UPDATE_INFO.

      IF LS_POSITION-OBJ_TYPE = 'HRBLK' OR
         UPDATE_LOGIC->FM_DOC_EXISTS_IN_FM(
             "maybe something for a note?
             IS_FM_POS     = IS_HRFPM_FM_POS
             IS_FM_POS_KEY = IS_HRFPM_FM_POS-KEY_POS )
             IS INITIAL .

*---     WGOSS1289086
*---     THIS IS ACTUALLY THE 'NULL APPROVAL SCENARIO'
*---     WHICH HAS TO BE HANDLED at an other place
**--     don't create 'zero'-docuemnts to avoid dead-locks
**---    Example:
**---     1. Create a docuemnt on an account where the master data
**---        chekcs in FM fail.
**---      ==> status of reference #1 changes  to 'ERROR'
**---     2. Correct the situation by changing the account assignment
**---     3. the PBC-reference #1 has now the delta zero, however
**---        if the system tried to post it again, the master data
**---        error would reappear, leading to  DEAD LOCK SITUATION
**---     4. The void references that arise form this are to be dealt
**---        with at another place (CL_HRFPM_CD_REGISTRATOR)
*        IF not ls_position-obj_type = 'HRBLK' and    "WGOSS1223767
*          ls_position-delta-delta_amount = 0 .
*          READ TABLE lt_positions   ASSIGNING <acc_pos> INDEX 1.
*          <acc_pos>-status = cl_hrfpm_const=>upd_status_fm_posted.
*        ELSE.

        READ TABLE LT_POSITIONS ASSIGNING <ACC_POS> INDEX 1.

        CHANGE_NEW_DOC_BEF_POST(
          EXPORTING
            IS_FM_DOC    = I_HRFPM_FM_DOC
            IS_FM_POS    = IS_HRFPM_FM_POS
           IMPORTING
             EP_POST_DATE = L_DOCDATE
          CHANGING
            CS_EXT_POS   =  <ACC_POS> ).

        CL_HRFPM_ACCOUNTING_INTERFACE=>ACCOUNTING_DOCUMENT_CREATE(
              EXPORTING
               I_COMP_CODE      = IS_HRFPM_FM_POS-BUKRS
               I_POSTING_DATE   = L_DOCDATE
               I_CHECK_ONLY     = IP_FLG_CHECK_ONLY
               I_DERIVE_DATE    = L_DOCDATE
             IMPORTING
               E_SUBRC          = L_SUBRC
               ET_RETURN        = LT_MESSAGES
             CHANGING
               CT_POSITIONS_EXT_APP = LT_POSITIONS  ).

*        ENDIF.
      ELSEIF NOT UPDATE_LOGIC->FM_DOC_IS_TRANSFERRED_TO_FM(
         IS_HRFPM_FM_POS-KEY_POS ) IS INITIAL.

        READ TABLE LT_POSITIONS ASSIGNING <ACC_POS> INDEX 1.

        CHANGE_EXISTING_DOC_BEF_POST(
          EXPORTING
            IS_FM_DOC    = I_HRFPM_FM_DOC
            IS_FM_POS    = IS_HRFPM_FM_POS
           IMPORTING
             EP_DERIVE_DATE = L_DOCDATE
          CHANGING
            CS_EXT_POS   =  <ACC_POS> ).

        CL_HRFPM_ACCOUNTING_INTERFACE=>ACCOUNTING_DOCUMENT_CHANGE(
          EXPORTING
            I_COMP_CODE      = IS_HRFPM_FM_POS-BUKRS
            I_CHECK_ONLY     = IP_FLG_CHECK_ONLY
            I_DERIVE_DATE    = L_DOCDATE
          IMPORTING
            E_SUBRC          = L_SUBRC
            ET_RETURN        = LT_MESSAGES
          CHANGING
            CT_POSITIONS_EXT_APP = LT_POSITIONS ).

      ELSE.
        TRY.
            "WGOSS01261042
            RAISE EXCEPTION TYPE CX_HRFPM_ACC_POSTING
              EXPORTING
                TEXTID          =
CX_HRFPM_ACC_POSTING=>FM_DOC_HAS_WRONG_STATUS
                ABDAT           = IS_HRFPM_FM_POS-DUE_DATE
                MODULE_NAME     = C_MODULE_NAME
                RESP_DEP        = CL_HRFPM_CONST=>RESP_DEP_AD
                ACC_ASS         = IS_HRFPM_FM_POS-ACC_ASS
                ACC_DOC_POS     = IS_HRFPM_FM_POS-KEY_POS
                DEP_ACC_DOC_POS = IS_HRFPM_FM_POS-DEP_FM_DOC.
          CATCH CX_HRFPM_ACC_POSTING INTO EXC_ACC.
            MESSAGE A106(HRFPM) INTO MSG_DUMMY.
            EXC_ACC->SET_SY_MESSAGE( ).
            RAISE EXCEPTION EXC_ACC.
        ENDTRY.
      ENDIF.

      READ TABLE LT_MESSAGES WITH KEY TYPE = 'E'
                  TRANSPORTING NO FIELDS.

      IF SY-SUBRC <> 0 AND L_SUBRC IS INITIAL.
        READ TABLE ET_UPDATE_INFO ASSIGNING <UPD_INFO> INDEX 1.
        READ TABLE LT_POSITIONS   ASSIGNING <ACC_POS> INDEX 1.
        <UPD_INFO>-FLG_UPDATE_STATUS = <ACC_POS>-STATUS.
      ELSE.

        LS_FM_VALUES-BETRG = IS_HRFPM_FM_POS-BETRG.
        LS_FM_VALUES-DELTA_AMOUNT = IS_HRFPM_FM_POS-DELTA_AMOUNT.
        LS_FM_VALUES-WAERS = IS_HRFPM_FM_POS-WAERS.
        LS_FM_VALUES-DUE_DATE = L_DOCDATE.

        CASE LS_POSITION-OBJ_TYPE.
          WHEN 'HRBLK'.
            RAISE EXCEPTION TYPE CX_HRFPM_PCS_POSTING
              EXPORTING
                TEXTID       = CX_HRFPM_PCS_POSTING=>POSTING_FAILED
                MODULE_NAME  = C_MODULE_NAME
                IT_FM_RETURN = LT_MESSAGES
                ACC_ASS      = IS_HRFPM_FM_POS-ACC_ASS
                ACC_VALUES   = LS_FM_VALUES
                ACC_DOC_POS  = IS_HRFPM_FM_POS-KEY_POS
                RESP_DEP     = CL_HRFPM_CONST=>RESP_DEP_RW
                ABDAT        = L_DOCDATE.
          WHEN OTHERS.
            RAISE EXCEPTION TYPE CX_HRFPM_FM_POSTING
              EXPORTING
                TEXTID       = CX_HRFPM_FM_POSTING=>POSTING_FAILED
                MODULE_NAME  = C_MODULE_NAME
                IT_FM_RETURN = LT_MESSAGES
                ACC_ASS      = IS_HRFPM_FM_POS-ACC_ASS
                ACC_DOC_POS  = IS_HRFPM_FM_POS-KEY_POS
                ACC_VALUES   = LS_FM_VALUES
                RESP_DEP     = CL_HRFPM_CONST=>RESP_DEP_RW
                ABDAT        = L_DOCDATE.
        ENDCASE.
      ENDIF.
    CATCH CX_HRFPM_ADMINISTRATOR.
* should never happen
    CATCH CX_HRFPM_ACC_POSTING INTO EXC_FPM.
      MESSAGE E119(HRFPM)
         WITH IS_HRFPM_FM_POS-KEY_POS INTO MSG_DUMMY.
*     Fehler beim Ändern eines Belegs im Rechnungswesen
      EXC_FPM->SET_SY_MESSAGE( ).
      CX_HRFPM=>OVERWRITE_EXCEPTION( CHANGING CO_EXC = EXC_FPM ).
      EXC_ACC ?= EXC_FPM.
      RAISE EXCEPTION EXC_ACC.
  ENDTRY.
ENDMETHOD.

* ---- ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCO ----
PROTECTED SECTION.

* ---- ZCL_HRFPM_CD_ACC_BUILD_DOCS_UNCU ----
CLASS ZCL_HRFPM_CD_ACC_BUILD_DOCS_UN DEFINITION
  PUBLIC
  INHERITING FROM CL_HRFPM_CD_ACC_BUILD_DOCS
  CREATE PUBLIC .

PUBLIC SECTION.

  METHODS POST_DOCUMENTS
    REDEFINITION .