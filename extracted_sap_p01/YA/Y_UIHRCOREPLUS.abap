* ==== CLASS POOL Y_UIHRCOREPLUS ====
CLASS-POOL .
*"* class pool for class Y_UIHRCOREPLUS

*"* local type definitions
INCLUDE Y_UIHRCOREPLUS================CCDEF.

*"* class Y_UIHRCOREPLUS definition
*"* public declarations
  INCLUDE Y_UIHRCOREPLUS================CU.
*"* protected declarations
  INCLUDE Y_UIHRCOREPLUS================CO.
*"* private declarations
  INCLUDE Y_UIHRCOREPLUS================CI.
ENDCLASS. "Y_UIHRCOREPLUS definition

*"* macro definitions
INCLUDE Y_UIHRCOREPLUS================CCMAC.
*"* local class implementation
INCLUDE Y_UIHRCOREPLUS================CCIMP.

CLASS Y_UIHRCOREPLUS IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "Y_UIHRCOREPLUS implementation


* ---- Y_UIHRCOREPLUS================CI ----
PRIVATE SECTION.

* ---- Y_UIHRCOREPLUS================CM001 ----
  METHOD IF_EX_HRPAD00INFTYUI~INITIALIZE.
  ENDMETHOD.

* ---- Y_UIHRCOREPLUS================CM002 ----
  METHOD IF_EX_HRPAD00INFTYUI~OUTPUT_CONVERSION.

    LOOP AT FIELD_ATTRIBUTES INTO DATA(LS_FIELD_ATTRIBUTES).

    LOOP AT LS_FIELD_ATTRIBUTES-FIELD_ATTRIBUTE INTO DATA(LS_FIELD).

      CASE LS_FIELD-FIELD_NAME.

        WHEN 'INITSXX'.
          MODIFY LS_FIELD_ATTRIBUTES-FIELD_ATTRIBUTE FROM VALUE #( FIELD_PROPERTY = 'B' ) USING KEY PRIMARY_KEY
                                                     TRANSPORTING FIELD_PROPERTY
                                                     WHERE FIELD_NAME = 'INITS'.

        WHEN OTHERS.
          " No action needed
      ENDCASE.
    ENDLOOP.

    MODIFY FIELD_ATTRIBUTES FROM LS_FIELD_ATTRIBUTES.
  ENDLOOP.

  ENDMETHOD.

* ---- Y_UIHRCOREPLUS================CO ----
PROTECTED SECTION.

* ---- Y_UIHRCOREPLUS================CU ----
CLASS Y_UIHRCOREPLUS DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

PUBLIC SECTION.

  INTERFACES IF_BADI_INTERFACE .
  INTERFACES IF_EX_HRPAD00INFTYUI .