* ==== CLASS POOL YCL_MM_MRM_CHECK ====
CLASS-POOL .
*"* class pool for class YCL_MM_MRM_CHECK

*"* local type definitions
INCLUDE YCL_MM_MRM_CHECK==============CCDEF.

*"* class YCL_MM_MRM_CHECK definition
*"* public declarations
  INCLUDE YCL_MM_MRM_CHECK==============CU.
*"* protected declarations
  INCLUDE YCL_MM_MRM_CHECK==============CO.
*"* private declarations
  INCLUDE YCL_MM_MRM_CHECK==============CI.
ENDCLASS. "YCL_MM_MRM_CHECK definition

*"* macro definitions
INCLUDE YCL_MM_MRM_CHECK==============CCMAC.
*"* local class implementation
INCLUDE YCL_MM_MRM_CHECK==============CCIMP.

CLASS YCL_MM_MRM_CHECK IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_MM_MRM_CHECK implementation


* ---- YCL_MM_MRM_CHECK==============CI ----
PRIVATE SECTION.

* ---- YCL_MM_MRM_CHECK==============CM001 ----
  METHOD CHECK_IR_SEGREGATION_OF_DUTIES.

    DATA LT_EKBE TYPE TABLE OF EKBE.

    "For each purchase order item, get the user wo did the good receipt
    "Check if the user who do the invoice is not the same who did the good receipt
    RV_SUBRC = 0.
    LOOP AT IT_DRSEG INTO DATA(LS_DRSEG) WHERE EBELN IS NOT INITIAL.
      CLEAR LT_EKBE.
      SELECT * FROM EKBE WHERE EBELN = @LS_DRSEG-EBELN
                         AND   EBELP = @LS_DRSEG-EBELP
                         AND   VGABE = '1'  "Good receipt
                    INTO TABLE @LT_EKBE.
      SORT LT_EKBE BY BLDAT DESCENDING BELNR DESCENDING.
      READ TABLE LT_EKBE INTO DATA(LS_EKBE) INDEX 1.
      CHECK SY-SUBRC = 0.
      IF LS_EKBE-ERNAM = SY-UNAME.
        RV_SUBRC = 8.
        EXIT.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.

* ---- YCL_MM_MRM_CHECK==============CO ----
PROTECTED SECTION.

* ---- YCL_MM_MRM_CHECK==============CU ----
CLASS YCL_MM_MRM_CHECK DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  CLASS-METHODS CHECK_IR_SEGREGATION_OF_DUTIES
    IMPORTING
      !IT_DRSEG TYPE MMCR_TDRSEG
    RETURNING
      VALUE(RV_SUBRC) TYPE SY-SUBRC .