* ==== CLASS POOL YCL_FM_UTILITIES ====
CLASS-POOL .
*"* class pool for class YCL_FM_UTILITIES

*"* local type definitions
INCLUDE YCL_FM_UTILITIES==============CCDEF.

*"* class YCL_FM_UTILITIES definition
*"* public declarations
  INCLUDE YCL_FM_UTILITIES==============CU.
*"* protected declarations
  INCLUDE YCL_FM_UTILITIES==============CO.
*"* private declarations
  INCLUDE YCL_FM_UTILITIES==============CI.
ENDCLASS. "YCL_FM_UTILITIES definition

*"* macro definitions
INCLUDE YCL_FM_UTILITIES==============CCMAC.
*"* local class implementation
INCLUDE YCL_FM_UTILITIES==============CCIMP.

CLASS YCL_FM_UTILITIES IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FM_UTILITIES implementation


* ---- YCL_FM_UTILITIES==============CI ----
PRIVATE SECTION.

* ---- YCL_FM_UTILITIES==============CM001 ----
  METHOD GET_FM_AREA_FROM_COMPANY_CODE.

    CLEAR RV_FIKRS.
    SELECT SINGLE FIKRS FROM T001 WHERE BUKRS = @IV_BUKRS INTO @RV_FIKRS.

  ENDMETHOD.

* ---- YCL_FM_UTILITIES==============CO ----
PROTECTED SECTION.

* ---- YCL_FM_UTILITIES==============CU ----
CLASS YCL_FM_UTILITIES DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  CLASS-METHODS GET_FM_AREA_FROM_COMPANY_CODE
    IMPORTING
      !IV_BUKRS TYPE BUKRS
    RETURNING
      VALUE(RV_FIKRS) TYPE FIKRS .