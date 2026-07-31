* ==== CLASS POOL ZCL_IM_PBC_HRFPM_INT_MAN ====
CLASS-POOL .
*"* class pool for class ZCL_IM_PBC_HRFPM_INT_MAN

*"* local classes
INCLUDE ZCL_IM_PBC_HRFPM_INT_MAN======CL.

*"* class ZCL_IM_PBC_HRFPM_INT_MAN definition
*"* public declarations
  INCLUDE ZCL_IM_PBC_HRFPM_INT_MAN======CU.
*"* protected declarations
  INCLUDE ZCL_IM_PBC_HRFPM_INT_MAN======CO.
*"* private declarations
  INCLUDE ZCL_IM_PBC_HRFPM_INT_MAN======CI.
ENDCLASS. "ZCL_IM_PBC_HRFPM_INT_MAN definition

CLASS ZCL_IM_PBC_HRFPM_INT_MAN IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM_PBC_HRFPM_INT_MAN implementation


* ---- ZCL_IM_PBC_HRFPM_INT_MAN======CI ----
PRIVATE SECTION.
*"* private components of class ZCL_IM_PBC_HRFPM_INT_MAN
*"* do not include other source files here!!!

* ---- ZCL_IM_PBC_HRFPM_INT_MAN======CM001 ----
METHOD IF_EX_HRFPM_INT_MAN~MODIFY_INTERVALS.
  DATA: W_P0001    TYPE P0001,
        T_P0001    TYPE TABLE OF P0001,
        W_CT_INT_T TYPE HRFPM_INTEGRATION_INTERVALS.

  DATA : LT_1081    TYPE TABLE OF P1081,
         LT_OBJECTS TYPE TABLE OF HROBJECT,
         LS_OBJECT  TYPE          HROBJECT,
         LS_1081    TYPE          P1081.

  IF P_OTYPE = 'P'.
    CALL FUNCTION 'RH_PM_READ_INFTY'
      EXPORTING
        ACT_PLVAR        = P_PLVAR
        ACT_OTYPE        = P_OTYPE
        ACT_OBJID        = P_OBJID
        ACT_BEGDA        = P_BEGDA
        ACT_ENDDA        = P_ENDDA
        ACT_ISTAT        = P_ISTAT
        ACT_INFTY        = '0001'
*       ACT_SUBTY        =
*       AUTHORITY        = 'DISP'
      TABLES
        INNNN            = T_P0001
      EXCEPTIONS
        NO_ACTIVE_PLVAR  = 1
        OBJECT_NOT_FOUND = 2
        NOTHING_FOUND    = 3
        OTHERS           = 4.
    IF SY-SUBRC <> 0.
* Implement suitable error handling here
    ENDIF.


* IT 1081 position id from position
  ELSEIF P_OTYPE = 'S'.
    LS_OBJECT-PLVAR = P_PLVAR.
    LS_OBJECT-OTYPE = P_OTYPE.
    LS_OBJECT-OBJID = P_OBJID.
    APPEND LS_OBJECT TO LT_OBJECTS.

    CALL FUNCTION 'RH_READ_INFTY'
      EXPORTING
*       AUTHORITY            = 'DISP'
*       WITH_STRU_AUTH       = 'X'
*       PLVAR                =
*       OTYPE                =
*       OBJID                =
        INFTY                = '1081'
*       ISTAT                = ' '
*       EXTEND               = 'X'
*       SUBTY                = ' '
        BEGDA                = P_BEGDA
        ENDDA                = P_ENDDA
*       CONDITION            = '00000'
*       INFTB                = '1'
*       SORT                 = 'X'
*       VIA_T777D            = ' '
      TABLES
        INNNN                = LT_1081
        OBJECTS              = LT_OBJECTS
      EXCEPTIONS
        ALL_INFTY_WITH_SUBTY = 1
        NOTHING_FOUND        = 2
        NO_OBJECTS           = 3
        WRONG_CONDITION      = 4
        WRONG_PARAMETERS     = 5
        OTHERS               = 6.

  ENDIF.

  CLEAR W_CT_INT_T.
  SORT T_P0001.
  LOOP AT CT_INTEGRATION_TIMES INTO W_CT_INT_T.
    CLEAR W_P0001.
    LOOP AT T_P0001 INTO W_P0001 WHERE BEGDA <= W_CT_INT_T-ENDDA
                                   AND ENDDA >= W_CT_INT_T-BEGDA.
      W_CT_INT_T-ZZABKRS = W_P0001-ABKRS.
    ENDLOOP.                                                "t_p0001
    W_CT_INT_T-ZZOTYPE = P_OTYPE.

    LOOP AT LT_1081 INTO LS_1081 WHERE BEGDA <= W_CT_INT_T-ENDDA
                                   AND ENDDA >= W_CT_INT_T-BEGDA.
      W_CT_INT_T-ZZPOSITION_ID = LS_1081-POSITION_ID.
    ENDLOOP.

    MODIFY CT_INTEGRATION_TIMES FROM W_CT_INT_T.
  ENDLOOP.

ENDMETHOD.

* ---- ZCL_IM_PBC_HRFPM_INT_MAN======CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_IM_PBC_HRFPM_INT_MAN
*"* do not include other source files here!!!

* ---- ZCL_IM_PBC_HRFPM_INT_MAN======CU ----
CLASS ZCL_IM_PBC_HRFPM_INT_MAN DEFINITION
  PUBLIC
  INHERITING FROM CL_IM_HRFPM_INT_STANDARD
  CREATE PUBLIC .

PUBLIC SECTION.
*"* public components of class ZCL_IM_PBC_HRFPM_INT_MAN
*"* do not include other source files here!!!

  METHODS IF_EX_HRFPM_INT_MAN~MODIFY_INTERVALS
    REDEFINITION .