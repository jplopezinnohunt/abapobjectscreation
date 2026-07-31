* ==== CLASS POOL ZCL_INFTY_SERVICE_PD ====
CLASS-POOL .
*"* class pool for class ZCL_INFTY_SERVICE_PD

*"* local type definitions
INCLUDE ZCL_INFTY_SERVICE_PD==========CCDEF.

*"* class ZCL_INFTY_SERVICE_PD definition
*"* public declarations
  INCLUDE ZCL_INFTY_SERVICE_PD==========CU.
*"* protected declarations
  INCLUDE ZCL_INFTY_SERVICE_PD==========CO.
*"* private declarations
  INCLUDE ZCL_INFTY_SERVICE_PD==========CI.
ENDCLASS. "ZCL_INFTY_SERVICE_PD definition

*"* macro definitions
INCLUDE ZCL_INFTY_SERVICE_PD==========CCMAC.
*"* local class implementation
INCLUDE ZCL_INFTY_SERVICE_PD==========CCIMP.

CLASS ZCL_INFTY_SERVICE_PD IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_INFTY_SERVICE_PD implementation


* ---- ZCL_INFTY_SERVICE_PD==========CI ----
PRIVATE SECTION.
*"* private components of class ZCL_INFTY_SERVICE_PD
*"* do not include other source files here!!!

* ---- ZCL_INFTY_SERVICE_PD==========CM001 ----
METHOD PUT_INTO_BUFFER.

  DATA LT_WPLOG TYPE STANDARD TABLE OF WPLOG.
  DATA LT_OBJECTS TYPE STANDARD TABLE OF HROBJECT.

  CL_HR_PNNNN_TYPE_CAST=>PNNNN_TO_WPLOG_TAB(
    EXPORTING
      PNNNN_TAB = IT_PNNNN
    IMPORTING
       WPLOG_TAB = LT_WPLOG ).

  CALL FUNCTION 'RH_PM_INFTY_BUFFER_FILL'
    EXPORTING
      INFTY   = MV_INFTY
      SUBTY   = MV_SUBTY
    TABLES
      INNNN   = LT_WPLOG
      OBJECTS = LT_OBJECTS.

ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_PD==========CM002 ----
METHOD READ_INFTY_FROM_BUFFER.
  "PM has its own buffer
  CALL FUNCTION 'RH_PM_READ_INFTY'
    EXPORTING
      ACT_PLVAR        = IS_HROBJECT-PLVAR
      ACT_OTYPE        = IS_HROBJECT-OTYPE
      ACT_OBJID        = IS_HROBJECT-OBJID
      ACT_BEGDA        = IS_SEL_PERIOD-BEGDA
      ACT_ENDDA        = IS_SEL_PERIOD-ENDDA
      ACT_ISTAT        = MV_ISTAT
      ACT_INFTY        = MV_INFTY
      ACT_SUBTY        = MV_SUBTY
*     AUTHORITY        = 'DISP'
    TABLES
      INNNN            = ET_PNNNN
    EXCEPTIONS
      NO_ACTIVE_PLVAR  = 1
      OBJECT_NOT_FOUND = 2
      NOTHING_FOUND    = 3
      OTHERS           = 4.
ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_PD==========CM003 ----
METHOD READ_INFTY_FROM_DB.
  CALL FUNCTION 'RH_PM_READ_INFTY'
    EXPORTING
      ACT_PLVAR        = IS_HROBJECT-PLVAR
      ACT_OTYPE        = IS_HROBJECT-OTYPE
      ACT_OBJID        = IS_HROBJECT-OBJID
      ACT_BEGDA        = IS_SEL_PERIOD-BEGDA
      ACT_ENDDA        = IS_SEL_PERIOD-ENDDA
      ACT_ISTAT        = MV_ISTAT
      ACT_INFTY        = MV_INFTY
      ACT_SUBTY        = MV_SUBTY
*     AUTHORITY        = 'DISP'
    TABLES
      INNNN            = ET_PNNNN
    EXCEPTIONS
      NO_ACTIVE_PLVAR  = 1
      OBJECT_NOT_FOUND = 2
      NOTHING_FOUND    = 3
      OTHERS           = 4.
ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_PD==========CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_INFTY_SERVICE_PD
*"* do not include other source files here!!!

  METHODS PUT_INTO_BUFFER
    REDEFINITION .
  METHODS READ_INFTY_FROM_BUFFER
    REDEFINITION .
  METHODS READ_INFTY_FROM_DB
    REDEFINITION .

* ---- ZCL_INFTY_SERVICE_PD==========CU ----
CLASS ZCL_INFTY_SERVICE_PD DEFINITION
  PUBLIC
  INHERITING FROM ZCL_INFTY_SERVICE
  CREATE PUBLIC .

PUBLIC SECTION.
*"* public components of class ZCL_INFTY_SERVICE_PD
*"* do not include other source files here!!!