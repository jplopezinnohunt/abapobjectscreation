* ==== CLASS POOL ZCL_IM_HRFPM_ENHLG_GRP ====
CLASS-POOL .
*"* class pool for class ZCL_IM_HRFPM_ENHLG_GRP

*"* local type definitions
INCLUDE ZCL_IM_HRFPM_ENHLG_GRP========CCDEF.

*"* class ZCL_IM_HRFPM_ENHLG_GRP definition
*"* public declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG_GRP========CU.
*"* protected declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG_GRP========CO.
*"* private declarations
  INCLUDE ZCL_IM_HRFPM_ENHLG_GRP========CI.
ENDCLASS. "ZCL_IM_HRFPM_ENHLG_GRP definition

*"* macro definitions
INCLUDE ZCL_IM_HRFPM_ENHLG_GRP========CCMAC.
*"* local class implementation
INCLUDE ZCL_IM_HRFPM_ENHLG_GRP========CCIMP.

CLASS ZCL_IM_HRFPM_ENHLG_GRP IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "ZCL_IM_HRFPM_ENHLG_GRP implementation


* ---- ZCL_IM_HRFPM_ENHLG_GRP========CI ----
  PRIVATE SECTION.
*"* private components of class ZZCL_IM_HRFPM_ENHLG_GRP
*"* do not include other source files here!!!

* ---- ZCL_IM_HRFPM_ENHLG_GRP========CM001 ----
  METHOD EXTRACT_BAL_MSG_FROM_LINE.
    DATA LS_MSG TYPE CL_HRFPM_LG_UTILS=>TS_MSG.

*  ASSERT mo_outlist_line_type->applies_to_data( id_outline )
*            = abap_true.

    CREATE DATA RRS_BAL_MSG.


    MOVE-CORRESPONDING ID_OUTLINE TO:
         LS_MSG,
         LS_MSG-MSG_HNDL.

    IF NOT LS_MSG-MSG_HNDL IS INITIAL.
      CALL FUNCTION 'BAL_LOG_MSG_READ'
        EXPORTING
          I_S_MSG_HANDLE = LS_MSG-MSG_HNDL
        IMPORTING
          E_S_MSG        = RRS_BAL_MSG->*
        EXCEPTIONS
          LOG_NOT_FOUND  = 1
          OTHERS         = 2.
    ENDIF.

  ENDMETHOD.                    "EXTRACT_BAL_MSG_FROM_LINE

* ---- ZCL_IM_HRFPM_ENHLG_GRP========CM002 ----
  METHOD FILL_OBJECT_INFO.
    DATA LS_AWB_APPLC_OBJECT TYPE HRFPM_AWB_APPLC_OBJECT.
    DATA LX TYPE REF TO CX_HRFPM.
    DATA LX_ACC TYPE REF TO CX_HRFPM_ACC_POSTING.
    DATA LS_OBJ_TXT TYPE HRFPM_LG_COMMON_FIELDS-OBJECT_TEXTS.
    DATA LRT_HROBJ TYPE REF TO HROBJECT_TAB.
    FIELD-SYMBOLS <HROBJ> LIKE LINE OF LX->HROBJECTS.


    TRY .
        IF IO_LINE_HANDLER IS BOUND .
          LX ?= IO_LINE_HANDLER.
        ELSE.
          LX ?= CL_HRFPM_LG_UTILS=>GET_LOG_HANDLER(
               EXTRACT_BAL_MSG_FROM_LINE( CD_OUTPUT_LINE ) ).
        ENDIF.

        IF NOT LX->HROBJECT-OTYPE = CL_HRFPM_CONST=>OTYPE_EARMARK_DOC.
          ASSIGN LX->HROBJECT TO <HROBJ>.
        ELSE.
          READ TABLE LX->HROBJECTS ASSIGNING <HROBJ> INDEX 1.
          IF SY-SUBRC <> 0.
            LX_ACC ?= LX.
            LRT_HROBJ = GET_AFFECTED_OBJECTS_OF_ED( LX_ACC->ACC_DOC_POS  ).
            IF LINES( LRT_HROBJ->* ) = 1.
              READ TABLE LRT_HROBJ->* ASSIGNING <HROBJ> INDEX 1.
            ENDIF.
          ENDIF.
        ENDIF.

        IF <HROBJ> IS ASSIGNED.
          MOVE-CORRESPONDING <HROBJ> TO:
             CD_OUTPUT_LINE,
             LS_AWB_APPLC_OBJECT.
          CALL FUNCTION 'HRFPM_COMPLETE_INFTYP_PS'
            CHANGING
              CS_AWB_APPLC_OBJECT = LS_AWB_APPLC_OBJECT.

          MOVE-CORRESPONDING:
             LS_AWB_APPLC_OBJECT TO LS_OBJ_TXT,
             LS_OBJ_TXT TO CD_OUTPUT_LINE.

        ENDIF.
      CATCH CX_SY_MOVE_CAST_ERROR.
    ENDTRY.
  ENDMETHOD.                    "fill_object_info

* ---- ZCL_IM_HRFPM_ENHLG_GRP========CM003 ----
  METHOD GET_AFFECTED_OBJECTS_OF_ED.
    DATA LS_FM_DOC TYPE HRFPM_FM_DOC.
    DATA LX_ACC TYPE REF TO CX_HRFPM_ACC_POSTING.

    CREATE DATA RT_HROBJECT.

    TRY .

        REPLACE '$' IN IS_FM_DOC-BELNR WITH ''.

        CL_HRFPM_DB_INTERFACE=>GET_SINGLE_FM_DOC(
          EXPORTING
            IS_FM_DOC_KEY_POS        = IS_FM_DOC
            IP_BUFFERED              = 'X'
           IMPORTING
            ES_FM_DOC_HDR            = LS_FM_DOC ).

        INSERT LS_FM_DOC-HROBJECT INTO TABLE RT_HROBJECT->*.
      CATCH CX_HRFPM_DB_OPERATION.
    ENDTRY.
  ENDMETHOD.                    "get_affected_objects_of_ed

* ---- ZCL_IM_HRFPM_ENHLG_GRP========CO ----
PROTECTED SECTION.

*"* protected components of class ZZCL_IM_HRFPM_ENHLG_GRP
*"* do not include other source files here!!!
  METHODS EXTRACT_BAL_MSG_FROM_LINE
    IMPORTING
      !ID_OUTLINE TYPE DATA
    RETURNING
      VALUE(RRS_BAL_MSG) TYPE REF TO BAL_S_MSG .
  METHODS GET_AFFECTED_OBJECTS_OF_ED
    IMPORTING
      VALUE(IS_FM_DOC) TYPE HRFPM_FM_KEY_POS
    RETURNING
      VALUE(RT_HROBJECT) TYPE REF TO HROBJECT_TAB .
  METHODS FILL_OBJECT_INFO
    IMPORTING
      VALUE(IO_LINE_HANDLER) TYPE REF TO CX_HRFPM OPTIONAL
    CHANGING
      !CD_OUTPUT_LINE TYPE DATA .

* ---- ZCL_IM_HRFPM_ENHLG_GRP========CU ----
*----------------------------------------------------------------------*
*       CLASS ZCL_IM_HRFPM_ENHLG_GRP DEFINITION
*----------------------------------------------------------------------*
*
*----------------------------------------------------------------------*
CLASS ZCL_IM_HRFPM_ENHLG_GRP DEFINITION
  PUBLIC
  INHERITING FROM CL_IM_HRFPM_LG_ENHCMNTGRP_ACC
  CREATE PUBLIC .

PUBLIC SECTION.