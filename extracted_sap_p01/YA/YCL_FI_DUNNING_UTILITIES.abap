* ==== CLASS POOL YCL_FI_DUNNING_UTILITIES ====
CLASS-POOL .
*"* class pool for class YCL_FI_DUNNING_UTILITIES

*"* local type definitions
INCLUDE YCL_FI_DUNNING_UTILITIES======CCDEF.

*"* class YCL_FI_DUNNING_UTILITIES definition
*"* public declarations
  INCLUDE YCL_FI_DUNNING_UTILITIES======CU.
*"* protected declarations
  INCLUDE YCL_FI_DUNNING_UTILITIES======CO.
*"* private declarations
  INCLUDE YCL_FI_DUNNING_UTILITIES======CI.
ENDCLASS. "YCL_FI_DUNNING_UTILITIES definition

*"* macro definitions
INCLUDE YCL_FI_DUNNING_UTILITIES======CCMAC.
*"* local class implementation
INCLUDE YCL_FI_DUNNING_UTILITIES======CCIMP.

CLASS YCL_FI_DUNNING_UTILITIES IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_FI_DUNNING_UTILITIES implementation


* ---- YCL_FI_DUNNING_UTILITIES======CI ----
PRIVATE SECTION.

  CLASS-DATA MO_INSTANCE TYPE REF TO YCL_FI_DUNNING_UTILITIES .
  DATA MV_DUNNING_FORM_NAME TYPE SO_OBJ_DES .

  CLASS-METHODS GET_TEMPLATE_SO10
    IMPORTING
      !IV_ID TYPE TDID DEFAULT 'ST'
      !IV_LANGUAGE TYPE SPRAS DEFAULT SY-LANGU
      !IV_TDNAME TYPE TDOBNAME
      !IV_OBJECT TYPE TDOBJECT DEFAULT 'TEXT'
    RETURNING
      VALUE(RV_STRING) TYPE STRING .

* ---- YCL_FI_DUNNING_UTILITIES======CM001 ----
  METHOD GET_CUSTOMER_DATA.

    TYPES: BEGIN OF TY_NAME,
             NAME1 TYPE AD_NAME1,
             NAME2 TYPE AD_NAME2,
             NAME3 TYPE AD_NAME3,
             NAME4 TYPE AD_NAME4,
           END OF TY_NAME.
    DATA LS_NAME TYPE TY_NAME.

    CLEAR EV_NAME.

    SELECT SINGLE * FROM KNA1 WHERE KUNNR = @IV_KUNNR INTO @DATA(LS_KNA1).
    IF SY-SUBRC = 0 AND LS_KNA1-ADRNR IS NOT INITIAL.
      SELECT SINGLE * FROM ADRC WHERE ADDRNUMBER = @LS_KNA1-ADRNR INTO @DATA(LS_ADRC).
      MOVE-CORRESPONDING LS_ADRC TO LS_NAME.
    ENDIF.

    IF LS_NAME IS INITIAL.
      MOVE-CORRESPONDING LS_KNA1 TO LS_NAME.
    ENDIF.

    CHECK LS_NAME IS NOT INITIAL.
    EV_NAME1 = LS_NAME-NAME1.
    IF LS_KNA1-KTOKD = 'MSAC' OR LS_KNA1-KTOKD = 'MSCO'.
      EV_NAME = |{ LS_NAME-NAME2 } { LS_NAME-NAME3 } { LS_NAME-NAME4 }|.
    ELSE.
      EV_NAME = |{ LS_NAME-NAME2 }{ LS_NAME-NAME3 }{ LS_NAME-NAME4 }|.
    ENDIF.

    EV_TENANT = IS_TENANT( IV_KUNNR = IV_KUNNR ).

  ENDMETHOD.

* ---- YCL_FI_DUNNING_UTILITIES======CM002 ----
  METHOD GET_DUNNING_FORM_NAME.

    RV_DUNNING_FORM_NAME = MV_DUNNING_FORM_NAME.

  ENDMETHOD.

* ---- YCL_FI_DUNNING_UTILITIES======CM003 ----
  METHOD GET_INSTANCE.

    IF MO_INSTANCE IS INITIAL.
      MO_INSTANCE = NEW YCL_FI_DUNNING_UTILITIES( ).
    ENDIF.

    RO_INSTANCE = MO_INSTANCE.

  ENDMETHOD.

* ---- YCL_FI_DUNNING_UTILITIES======CM004 ----
  METHOD SET_DUNNING_FORM_NAME.

    MV_DUNNING_FORM_NAME = IV_DUNNING_FORM_NAME.

  ENDMETHOD.

* ---- YCL_FI_DUNNING_UTILITIES======CM005 ----
  METHOD IS_TENANT.

    TYPES: BEGIN OF TY_RESULT,
             INTRENO      TYPE VICNCN-INTRENO, " Contract number
             BP_PARTNER   TYPE BUT000-PARTNER, " Business Partner number
             PARTNER_GUID TYPE BUT000-PARTNER_GUID,
             KUNNR        TYPE KNA1-KUNNR,     " Customer Number
             STAT         TYPE JEST-STAT,
           END OF TY_RESULT.
    DATA LT_RESULT TYPE TABLE OF TY_RESULT.

    CLEAR RV_IS_TENANT.

    SELECT CN~INTRENO,              " Contract number
           REL~PARTNER      AS BP_PARTNER,
           BP~PARTNER_GUID,
           CL~CUSTOMER      AS KUNNR,
           JS~STAT
           FROM VICNCN AS CN
           INNER JOIN VIBPOBJREL    AS REL ON  REL~INTRENO = CN~INTRENO        " VICNCN-INTRENO    = VIBPOBJREL-INTRENO
           INNER JOIN BUT000        AS BP  ON  BP~PARTNER = REL~PARTNER        " VIBPOBJREL-PARTNER= BUT000-PARTNER
           INNER JOIN CVI_CUST_LINK AS CL  ON  CL~PARTNER_GUID = BP~PARTNER_GUID " BUT000-PARTNER_GUID = CVI_CUST_LINK-PARTNER_GUID
           INNER JOIN KNA1          AS K   ON  K~KUNNR = CL~CUSTOMER          " CVI_CUST_LINK-CUSTOMER = KNA1-KUNNR
           INNER JOIN JEST          AS JS  ON  JS~OBJNR = CN~OBJNR
                                           AND JS~STAT = 'I0119'      "Object status : Active
                                           AND JS~INACT = ''          "Indicator: Status Is Inactive
           WHERE CL~CUSTOMER = @IV_KUNNR
           AND   CN~RECNENDABS >= @SY-DATUM " Nicolas Correct this line
           INTO TABLE @LT_RESULT.

    IF LT_RESULT IS INITIAL.
      RV_IS_TENANT = ABAP_FALSE.
    ELSE.
      RV_IS_TENANT = ABAP_TRUE.
    ENDIF.

  ENDMETHOD.

* ---- YCL_FI_DUNNING_UTILITIES======CM006 ----
  METHOD GET_FORM_SPECIFIC_DATA.

    CASE IV_FORM_TYPE.
      WHEN 'ICH'.
        IF IV_LANGU = 'F'.
          EV_CONTRIBUTION = 'Contribution mise en recouvrement due au Fonds pour la sauvegarde du patrimoine culturel immatériel'.
          EV_FUND = 'Fonds pour la sauvegarde du patrimoine culturel immatériel'.
        ELSE.
          EV_CONTRIBUTION = 'Assessed contribution due to the Fund for the Safeguarding of the Intangible Cultural Heritage'.
          EV_FUND = 'Fund for the Safeguarding of the Intangible Cultural Heritage'.
        ENDIF.
      WHEN 'WHF'.
        IF IV_LANGU = 'F'.
          EV_CONTRIBUTION = 'Contribution mise en recouvrement due au Fonds pour la protection du patrimoine mondial culturel et naturel'.
          EV_FUND = 'Fonds pour la protection du patrimoine mondial culturel et naturel'.
        ELSE.
          EV_CONTRIBUTION = |Assessed contribution due to the World Heritage Fund{ CL_ABAP_CHAR_UTILITIES=>CR_LF }for the Protection of the World Cultural and Natural Heritage|.
          EV_FUND = 'World Heritage Fund for the Protection of the World Cultural and Natural Heritage'.
        ENDIF.
      WHEN OTHERS.
        EXIT.
    ENDCASE.

    EV_P1_L1 = GET_TEMPLATE_SO10( IV_LANGUAGE = IV_LANGU IV_TDNAME = |YFI_DUNNING_FORM_{ IV_FORM_TYPE }_P1_L1| ).
    EV_P1_L2 = GET_TEMPLATE_SO10( IV_LANGUAGE = IV_LANGU IV_TDNAME = |YFI_DUNNING_FORM_{ IV_FORM_TYPE }_P1_L2| ).
    EV_P1_L3 = GET_TEMPLATE_SO10( IV_LANGUAGE = IV_LANGU IV_TDNAME = |YFI_DUNNING_FORM_{ IV_FORM_TYPE }_P1_L3| ).
    EV_P1_L4 = GET_TEMPLATE_SO10( IV_LANGUAGE = IV_LANGU IV_TDNAME = |YFI_DUNNING_FORM_{ IV_FORM_TYPE }_P1_L4| ).

  ENDMETHOD.

* ---- YCL_FI_DUNNING_UTILITIES======CM007 ----
  METHOD GET_TEMPLATE_SO10.

    DATA LT_LINES TYPE TLINE_TAB.
    DATA LT_STREAM TYPE TABLE OF STRING.

    CLEAR RV_STRING.

    "Get mail content
    CALL FUNCTION 'READ_TEXT'
      EXPORTING
*       CLIENT                  = SY-MANDT
        ID                      = IV_ID
        LANGUAGE                = IV_LANGUAGE
        NAME                    = IV_TDNAME
        OBJECT                  = IV_OBJECT
*       ARCHIVE_HANDLE          = 0
*       LOCAL_CAT               = ' '
*  IMPORTING
*       HEADER                  =
*       OLD_LINE_COUNTER        =
      TABLES
        LINES                   = LT_LINES
      EXCEPTIONS
        ID                      = 1
        LANGUAGE                = 2
        NAME                    = 3
        NOT_FOUND               = 4
        OBJECT                  = 5
        REFERENCE_CHECK         = 6
        WRONG_ACCESS_TO_ARCHIVE = 7
        OTHERS                  = 8.

    CALL FUNCTION 'CONVERT_ITF_TO_STREAM_TEXT'
      EXPORTING
*       LANGUAGE     = SY-LANGU
        LF           = 'X'
      IMPORTING
        STREAM_LINES = LT_STREAM
      TABLES
        ITF_TEXT     = LT_LINES
*       text_stream  =
      .

    READ TABLE LT_STREAM INTO RV_STRING INDEX 1.

  ENDMETHOD.

* ---- YCL_FI_DUNNING_UTILITIES======CO ----
PROTECTED SECTION.

* ---- YCL_FI_DUNNING_UTILITIES======CU ----
CLASS YCL_FI_DUNNING_UTILITIES DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  CLASS-METHODS GET_FORM_SPECIFIC_DATA
    IMPORTING
      !IV_FORM_TYPE TYPE CHAR10
      !IV_LANGU TYPE LANGU
    EXPORTING
      !EV_CONTRIBUTION TYPE STRING
      !EV_FUND TYPE STRING
      !EV_P1_L1 TYPE STRING
      !EV_P1_L2 TYPE STRING
      !EV_P1_L3 TYPE STRING
      !EV_P1_L4 TYPE STRING .
  CLASS-METHODS IS_TENANT
    IMPORTING
      !IV_KUNNR TYPE KUNNR
    RETURNING
      VALUE(RV_IS_TENANT) TYPE XFELD .
  CLASS-METHODS GET_CUSTOMER_DATA
    IMPORTING
      !IV_KUNNR TYPE KUNNR
    EXPORTING
      !EV_NAME1 TYPE STRING
      !EV_NAME TYPE STRING
      !EV_TENANT TYPE BOOLE_D .
  METHODS GET_DUNNING_FORM_NAME
    RETURNING
      VALUE(RV_DUNNING_FORM_NAME) TYPE SO_OBJ_DES .
  CLASS-METHODS GET_INSTANCE
    RETURNING
      VALUE(RO_INSTANCE) TYPE REF TO YCL_FI_DUNNING_UTILITIES .
  METHODS SET_DUNNING_FORM_NAME
    IMPORTING
      !IV_DUNNING_FORM_NAME TYPE SO_OBJ_DES .