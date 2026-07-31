* ==== CLASS POOL ZCL_IM_HRFPM_ENHLG ====
CLASS-POOL .
*"* class pool for class ZCL_IM_HRFPM_ENHLG

*"* local type definitions
INCLUDE ZCL_IM_HRFPM_ENHLG============CCDEF.

*"* class ZCL_IM_HRFPM_ENHLG definition
*"* public declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG============CU.
*"* protected declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG============CO.
*"* private declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG============CI.
ENDCLASS. "ZCL_IM_HRFPM_ENHLG definition

*"* macro definitions
INCLUDE ZCL_IM_HRFPM_ENHLG============CCMAC.
*"* local class implementation
INCLUDE ZCL_IM_HRFPM_ENHLG============CCIMP.

CLASS ZCL_IM_HRFPM_ENHLG IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM_HRFPM_ENHLG implementation


* ---- ZCL_IM_HRFPM_ENHLG============CI ----
PRIVATE SECTION.
*"* private components of class ZCL_IM_HRFPM_ENHLG
*"* do not include other source files here!!!

* ---- ZCL_IM_HRFPM_ENHLG============CM001 ----
METHOD CLASS_CONSTRUCTOR.

  GO_ACC_CONTEXT_TYPE ?=
    CL_ABAP_TYPEDESCR=>DESCRIBE_BY_NAME( GC_ACC_CONTEXT_TYPE ).

ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG============CM002 ----
METHOD IF_HRFPM_APPL_LOG_ENHANCEMENT~FILL_LINE.

  CASE IP_ENH_STRUC_NAME.
    WHEN 'ZHRFPM_ENH_APPL_LOG_DOCINFO'.
      "not longer used: zz-fields havbe been moved into standard enhancement FMACC
      "'HRFPM_DISPLOG_ACC_CONTENT'
      FILL_DOCINFO(
        EXPORTING
          IS_BAL_MSG        = IS_BAL_MSG
          IP_ENH_STRUC_NAME = IP_ENH_STRUC_NAME
        CHANGING
          CD_ENH_STRUC_DATA = CD_ENH_STRUC_DATA ).
    WHEN 'ZHRFPM_ENH_APPL_LOG_AVC_OBJ'.

  ENDCASE.

ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG============CM003 ----
METHOD IF_HRFPM_APPL_LOG_ENHANCEMENT~CHANGE_FIELD_CAT.
  "do not display the currency field again
  FIELD-SYMBOLS <FIELD_CAT> LIKE LINE OF CT_FIELD_CATALOGUE.
  LOOP AT CT_FIELD_CATALOGUE ASSIGNING <FIELD_CAT>
      WHERE REF_TABNAME = GC_ENH_STRUC_NAME
        AND FIELDNAME = 'ZZCURRENCY'.
    <FIELD_CAT>-TECH = 'X'.
  ENDLOOP.
ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG============CM004 ----
METHOD FILL_DOCINFO.

  "purpose of this method is to convert
  "the non-numeric field-values of the accounting-context containing info about
  "the delta-amount and approvied amount of an document into currency-format
  "(Background: the context structure 'hrfpm_displog_accounting' does not
  "contain numerical fields, since this generally not possible for structures that
  "are meant to be used as context in the bal-Log)

  "Prec: version 13 of note 1447465 has been downloaded (this makes
  "the amount fields of the (non.nnumerical) acc-context convertible into
  "numerical values)


  FIELD-SYMBOLS <CTX> TYPE HRFPM_DISPLOG_ACCOUNTING.
  FIELD-SYMBOLS <DOC_INFO> TYPE ZHRFPM_ENH_APPL_LOG_DOCINFO.
  DATA LV_EXT_HELP TYPE CHAR200.

  DATA LS_TABLE_FIELD TYPE TABFIELD.

  CHECK GC_ACC_CONTEXT_TYPE = IS_BAL_MSG-BAL_MSG-CONTEXT-TABNAME.

  "make context accessible
  ASSIGN IS_BAL_MSG-BAL_MSG-CONTEXT-VALUE TO <CTX> CASTING.
  ASSIGN CD_ENH_STRUC_DATA TO <DOC_INFO>.

  LS_TABLE_FIELD-TABNAME   = 'ZHRFPM_ENH_APPL_LOG_DOCINFO'.

  LS_TABLE_FIELD-FIELDNAME = 'ZZBETRG'.
  LV_EXT_HELP = <CTX>-BETRG.

  CALL FUNCTION 'RS_CONV_EX_2_IN'
    EXPORTING
      INPUT_EXTERNAL               = LV_EXT_HELP
      TABLE_FIELD                  = LS_TABLE_FIELD
      CURRENCY                     = <DOC_INFO>-ZZCURRENCY
    IMPORTING
      OUTPUT_INTERNAL              = <DOC_INFO>-ZZBETRG
    EXCEPTIONS
      INPUT_NOT_NUMERICAL          = 1
      TOO_MANY_DECIMALS            = 2
      MORE_THAN_ONE_SIGN           = 3
      ILL_THOUSAND_SEPARATOR_DIST  = 4
      TOO_MANY_DIGITS              = 5
      SIGN_FOR_UNSIGNED            = 6
      TOO_LARGE                    = 7
      TOO_SMALL                    = 8
      INVALID_DATE_FORMAT          = 9
      INVALID_DATE                 = 10
      INVALID_TIME_FORMAT          = 11
      INVALID_TIME                 = 12
      INVALID_HEX_DIGIT            = 13
      UNEXPECTED_ERROR             = 14
      INVALID_FIELDNAME            = 15
      FIELD_AND_DESCR_INCOMPATIBLE = 16
      INPUT_TOO_LONG               = 17
      NO_DECIMALS                  = 18
      INVALID_FLOAT                = 19
      CONVERSION_EXIT_ERROR        = 20
      OTHERS                       = 21.

  IF SY-SUBRC <> 0.
* Implement suitable error handling here:
    "do not raise unnecccesaraily many messages
  ENDIF.
*

  LS_TABLE_FIELD-FIELDNAME = 'ZZDELTA_AMOUNT'.
  LV_EXT_HELP = <CTX>-ACC_VALUES-DELTA_AMOUNT.

  CALL FUNCTION 'RS_CONV_EX_2_IN'
    EXPORTING
      INPUT_EXTERNAL               = LV_EXT_HELP
      TABLE_FIELD                  = LS_TABLE_FIELD
      CURRENCY                     = <DOC_INFO>-ZZCURRENCY
    IMPORTING
      OUTPUT_INTERNAL              = <DOC_INFO>-ZZDELTA_AMOUNT
    EXCEPTIONS
      INPUT_NOT_NUMERICAL          = 1
      TOO_MANY_DECIMALS            = 2
      MORE_THAN_ONE_SIGN           = 3
      ILL_THOUSAND_SEPARATOR_DIST  = 4
      TOO_MANY_DIGITS              = 5
      SIGN_FOR_UNSIGNED            = 6
      TOO_LARGE                    = 7
      TOO_SMALL                    = 8
      INVALID_DATE_FORMAT          = 9
      INVALID_DATE                 = 10
      INVALID_TIME_FORMAT          = 11
      INVALID_TIME                 = 12
      INVALID_HEX_DIGIT            = 13
      UNEXPECTED_ERROR             = 14
      INVALID_FIELDNAME            = 15
      FIELD_AND_DESCR_INCOMPATIBLE = 16
      INPUT_TOO_LONG               = 17
      NO_DECIMALS                  = 18
      INVALID_FLOAT                = 19
      CONVERSION_EXIT_ERROR        = 20
      OTHERS                       = 21.

  IF SY-SUBRC <> 0.
* Implement suitable error handling here
  ENDIF.
*

ENDMETHOD.

* ---- ZCL_IM_HRFPM_ENHLG============CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_IM_HRFPM_ENHLG
*"* do not include other source files here!!!

  CLASS-DATA GO_ACC_CONTEXT_TYPE TYPE REF TO CL_ABAP_STRUCTDESCR .
  CLASS-DATA GC_ACC_CONTEXT_TYPE TYPE TABNAME VALUE 'HRFPM_DISPLOG_ACCOUNTING'. "#EC NOTEXT .

* ---- ZCL_IM_HRFPM_ENHLG============CU ----
CLASS ZCL_IM_HRFPM_ENHLG DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

*"* public components of class ZCL_IM_HRFPM_ENHLG
*"* do not include other source files here!!!
  INTERFACES IF_BADI_INTERFACE .
  INTERFACES IF_HRFPM_APPL_LOG_ENHANCEMENT .

  CONSTANTS GC_ENH_STRUC_NAME TYPE TABNAME VALUE 'ZHRFPM_ENH_APPL_LOG_DOCINFO'. "#EC NOTEXT

  CLASS-METHODS CLASS_CONSTRUCTOR .
  METHODS FILL_DOCINFO
    IMPORTING
      !IS_BAL_MSG TYPE HRFPM_LG_LOG_MSG
      !IP_ENH_STRUC_NAME TYPE HRFPM_APPL_LOG_ENHC_STRUC
    CHANGING
      !CD_ENH_STRUC_DATA TYPE DATA
    RAISING
      CX_HRFPM_LGENHNC .