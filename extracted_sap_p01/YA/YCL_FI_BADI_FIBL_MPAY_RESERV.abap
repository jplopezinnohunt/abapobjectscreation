* ==== CLASS POOL YCL_FI_BADI_FIBL_MPAY_RESERV ====
CLASS-POOL .
*"* class pool for class YCL_FI_BADI_FIBL_MPAY_RESERV

*"* local type definitions
INCLUDE YCL_FI_BADI_FIBL_MPAY_RESERV==CCDEF.

*"* class YCL_FI_BADI_FIBL_MPAY_RESERV definition
*"* public declarations
  INCLUDE YCL_FI_BADI_FIBL_MPAY_RESERV==CU.
*"* protected declarations
  INCLUDE YCL_FI_BADI_FIBL_MPAY_RESERV==CO.
*"* private declarations
  INCLUDE YCL_FI_BADI_FIBL_MPAY_RESERV==CI.
ENDCLASS. "YCL_FI_BADI_FIBL_MPAY_RESERV definition

*"* macro definitions
INCLUDE YCL_FI_BADI_FIBL_MPAY_RESERV==CCMAC.
*"* local class implementation
INCLUDE YCL_FI_BADI_FIBL_MPAY_RESERV==CCIMP.

CLASS YCL_FI_BADI_FIBL_MPAY_RESERV IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FI_BADI_FIBL_MPAY_RESERV implementation


* ---- YCL_FI_BADI_FIBL_MPAY_RESERV==CI ----
PRIVATE SECTION.

* ---- YCL_FI_BADI_FIBL_MPAY_RESERV==CM001 ----
  METHOD IF_EX_FIBL_MPAY_RESERVATION~PAYMENT_RUN_CHECK.

*----------------------------------------------------------------------*
* Sample BAdI implementation from SAP Note 2599466                     *
*----------------------------------------------------------------------*
* Table ZFI_BCM_ACTIVE to activate BCM for company code/payment method *
*                                                                      *
* MANDT  MANDT  (Key)   values from T000                               *
* ZBUKR  DZBUKR (Key)   values from T042B                              *
* RZAWE  RZAWE  (Key)   values from T042E                              *
*----------------------------------------------------------------------*
* Idea:                                                                *
*   -  Insert entry for company code and specific payment methods      *
*      to activate payment methods for BCM                             *
*   -  Insert entry for company code with empty payment method (space) *
*      to activate entire company code for BCM                         *
*----------------------------------------------------------------------*

    TYPES:
      BEGIN OF TY_RZAWE,
        ZBUKR TYPE DZBUKR,
        RZAWE TYPE RZAWE,
      END OF TY_RZAWE.

    DATA:
      LS_ACTIVE TYPE ZFI_BCM_ACTIVE,
      LT_RZAWE  TYPE TABLE OF TY_RZAWE,
      LS_RZAWE  TYPE TY_RZAWE.

    C_XMERGE = ABAP_FALSE.

    IF IS_REGUH-LAUFI(1) = 'B' OR IS_REGUH-LAUFI+5 EQ 'P'.
      C_XMERGE = ABAP_TRUE.
      EXIT.
    ENDIF.

* use informtion of first payment for payroll and travel
*    IF is_reguh-laufi+5 EQ 'P'.
*      ls_rzawe-zbukr = is_reguh-zbukr.
*      ls_rzawe-rzawe = is_reguh-rzawe.
*      APPEND ls_rzawe TO lt_rzawe.
*
** read payment run parameters for F110 or F111
*    ELSE.
    CALL FUNCTION 'Z_FI_PAYMENT_RUN_PARAMETERS'
      EXPORTING
        I_LAUFD  = IS_REGUH-LAUFD
        I_LAUFI  = IS_REGUH-LAUFI
      IMPORTING
        ET_RZAWE = LT_RZAWE.
*    ENDIF.

* check if one of the payment methods is registered for BCM
    LOOP AT LT_RZAWE INTO LS_RZAWE.
      SELECT SINGLE * FROM ZFI_BCM_ACTIVE
                      INTO LS_ACTIVE
                     WHERE ZBUKR EQ LS_RZAWE-ZBUKR
                       AND RZAWE EQ LS_RZAWE-RZAWE.
      IF SY-SUBRC EQ 0.
        C_XMERGE = ABAP_TRUE.
        EXIT.

*   if no specific entry found, check generic entry for company code
      ELSE.
        SELECT SINGLE * FROM ZFI_BCM_ACTIVE
                        INTO LS_ACTIVE
                       WHERE ZBUKR EQ LS_RZAWE-ZBUKR
                         AND RZAWE EQ SPACE.   "all payment methods
        IF SY-SUBRC EQ 0.
          C_XMERGE = ABAP_TRUE.
          EXIT.
        ENDIF.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_FI_BADI_FIBL_MPAY_RESERV==CO ----
PROTECTED SECTION.

* ---- YCL_FI_BADI_FIBL_MPAY_RESERV==CU ----
CLASS YCL_FI_BADI_FIBL_MPAY_RESERV DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  INTERFACES IF_BADI_INTERFACE .
  INTERFACES IF_EX_FIBL_MPAY_RESERVATION .