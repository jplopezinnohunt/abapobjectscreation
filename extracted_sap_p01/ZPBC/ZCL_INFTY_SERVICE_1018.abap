* ==== CLASS POOL ZCL_INFTY_SERVICE_1018 ====
CLASS-POOL .
*"* class pool for class ZCL_INFTY_SERVICE_1018

*"* local type definitions
INCLUDE ZCL_INFTY_SERVICE_1018========CCDEF.

*"* class ZCL_INFTY_SERVICE_1018 definition
*"* public declarations
  INCLUDE ZCL_INFTY_SERVICE_1018========CU.
*"* protected declarations
  INCLUDE ZCL_INFTY_SERVICE_1018========CO.
*"* private declarations
  INCLUDE ZCL_INFTY_SERVICE_1018========CI.
ENDCLASS. "ZCL_INFTY_SERVICE_1018 definition

*"* macro definitions
INCLUDE ZCL_INFTY_SERVICE_1018========CCMAC.
*"* local class implementation
INCLUDE ZCL_INFTY_SERVICE_1018========CCIMP.

CLASS ZCL_INFTY_SERVICE_1018 IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_INFTY_SERVICE_1018 implementation


* ---- ZCL_INFTY_SERVICE_1018========CI ----
PRIVATE SECTION.
*"* private components of class ZCL_INFTY_SERVICE_1018
*"* do not include other source files here!!!

* ---- ZCL_INFTY_SERVICE_1018========CM001 ----
METHOD PUT_INTO_BUFFER.
  "not yet supported => needs to handeld in a completely
  "differnt way => provide hierarchy-bsed reading!!
  RETURN.
ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_1018========CM002 ----
METHOD READ_INFTY_FROM_BUFFER.
  "no own buffer?? TODO => provide standard classes
  " next SP?
RETURN.
ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_1018========CM003 ----
METHOD READ_INFTY_FROM_DB.
  DATA LT_OBJECTS TYPE STANDARD TABLE OF HRROOTOB.
  DATA LS_OBJECT LIKE LINE OF LT_OBJECTS.
  DATA LT_COST_DIST TYPE STANDARD TABLE OF HRI1001_COST .
  FIELD-SYMBOLS <COST_DIST> LIKE LINE OF LT_COST_DIST.
  DATA LT_P1018_EXP TYPE STANDARD TABLE OF P1018_EXP.
  DATA LS_P1018_EXP LIKE LINE OF LT_P1018_EXP.



  MOVE-CORRESPONDING IS_HROBJECT TO LS_OBJECT.
  INSERT LS_OBJECT INTO TABLE LT_OBJECTS.

  CALL FUNCTION 'RH_COSTCENTER_OF_OBJECT_GET'
    EXPORTING
      PLVAR                        = IS_HROBJECT-PLVAR
      BEGDA                        = IS_SEL_PERIOD-BEGDA
      ENDDA                        = IS_SEL_PERIOD-ENDDA
*     SVECT                        = '1'
*     ACTIVE                       =
*     DIST                         = 'X'
*     OBJECT_ONLY                  =
      BUFFERED_ACCESS              = MV_READ_BUFFERED
*      READ_IT0001
*     I0027_FLAG                   =
*     OMBUFFER_MODE                =
*     READ_EX_RELAT                = ' '
*     CHECK_AUTH_1018              = ' '
    TABLES
      IN_OBJECTS                   = LT_OBJECTS
*     MAIN_COSTCENTERS             =
      DIST_COSTCENTERS             = LT_COST_DIST
*     INIT_TAB                     =
*     GIVEN_P0001_TAB              =
*     COST_PATHS                   =
    EXCEPTIONS
      GIVEN_P0001_TAB_NOT_COMPLETE = 1
      NO_AUTHORIZATION_1018        = 2
      OTHERS                       = 3.

  IF SY-SUBRC <> 0.
*   Implement suitable error handling here
  ELSE.
    LOOP AT LT_COST_DIST ASSIGNING <COST_DIST>.
      MOVE-CORRESPONDING <COST_DIST> TO LS_P1018_EXP.
      INSERT LS_P1018_EXP INTO TABLE LT_P1018_EXP.
    ENDLOOP.
    ET_PNNNN = LT_P1018_EXP.
  ENDIF.

ENDMETHOD.

* ---- ZCL_INFTY_SERVICE_1018========CO ----
PROTECTED SECTION.
*"* protected components of class ZCL_INFTY_SERVICE_1018
*"* do not include other source files here!!!

  METHODS READ_INFTY_FROM_BUFFER
    REDEFINITION .
  METHODS READ_INFTY_FROM_DB
    REDEFINITION .
  METHODS PUT_INTO_BUFFER
    REDEFINITION .

* ---- ZCL_INFTY_SERVICE_1018========CU ----
CLASS ZCL_INFTY_SERVICE_1018 DEFINITION
  PUBLIC
  INHERITING FROM ZCL_INFTY_SERVICE
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.
*"* public components of class ZCL_INFTY_SERVICE_1018
*"* do not include other source files here!!!