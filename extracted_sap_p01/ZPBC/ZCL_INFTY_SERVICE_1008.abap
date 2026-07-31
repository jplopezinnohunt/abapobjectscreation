* ==== CLASS POOL ZCL_INFTY_SERVICE_1008 ====
CLASS-POOL .
*"* class pool for class ZCL_INFTY_SERVICE_1008

*"* local type definitions
INCLUDE ZCL_INFTY_SERVICE_1008========CCDEF.

*"* class ZCL_INFTY_SERVICE_1008 definition
*"* public declarations
  INCLUDE ZCL_INFTY_SERVICE_1008========CU.
*"* protected declarations
  INCLUDE ZCL_INFTY_SERVICE_1008========CO.
*"* private declarations
  INCLUDE ZCL_INFTY_SERVICE_1008========CI.
ENDCLASS. "ZCL_INFTY_SERVICE_1008 definition

*"* macro definitions
INCLUDE ZCL_INFTY_SERVICE_1008========CCMAC.
*"* local class implementation
INCLUDE ZCL_INFTY_SERVICE_1008========CCIMP.

CLASS ZCL_INFTY_SERVICE_1008 IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_INFTY_SERVICE_1008 implementation


* ---- ZCL_INFTY_SERVICE_1008========CI ----
PRIVATE SECTION.
*"* private components of class ZCL_INFTY_SERVICE_1008
*"* do not include other source files here!!!

* ---- ZCL_INFTY_SERVICE_1008========CM001 ----
METHOD READ_INFTY_FROM_DB.
  TRY.
      CALL FUNCTION 'HRFPM_PROVIDE_1008'
        EXPORTING
*         IV_ISTAT         = '1'
          IS_SELPER        = IS_SEL_PERIOD
          IS_HROBJECT      = IS_HROBJECT
          IV_BUFFER_MODE   = MV_READ_BUFFERED
           IV_PROVIDE_BUKRS = ' '
           IV_PROVIDE_KOKRS = ' '
        TABLES
          ET_INNNN         = ET_PNNNN.

    CATCH CX_BPREP_REQ_MAN_INTERNAL.
  ENDTRY.
*
ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_1008========CM002 ----
METHOD READ_INFTY_FROM_BUFFER.
  "no own buffer?? TODO => provide standard classes
  " next SP?
RETURN.
ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_1008========CM003 ----
METHOD PUT_INTO_BUFFER.
  "not yet supported => needs to handeld in a completely
  "differnt way => provide hierarchy-bsed reading!!
  RETURN.
ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_1008========CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_INFTY_SERVICE_1008
*"* do not include other source files here!!!

  METHODS READ_INFTY_FROM_BUFFER
    REDEFINITION .
  METHODS READ_INFTY_FROM_DB
    REDEFINITION .
  METHODS PUT_INTO_BUFFER
    REDEFINITION .

* ---- ZCL_INFTY_SERVICE_1008========CU ----
CLASS ZCL_INFTY_SERVICE_1008 DEFINITION
  PUBLIC
  INHERITING FROM ZCL_INFTY_SERVICE
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.
*"* public components of class ZCL_INFTY_SERVICE_1008
*"* do not include other source files here!!!