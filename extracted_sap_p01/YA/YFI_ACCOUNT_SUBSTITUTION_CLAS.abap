*&---------------------------------------------------------------------*
*&  Include           YFI_ACCOUNT_SUBSTITUTION_CLAS
*&---------------------------------------------------------------------*
*---------------------------------------------------------------------*
*       CLASS lcl_handle_events DEFINITION
*---------------------------------------------------------------------*
* §5.1 define a local class for handling events of cl_salv_table
*---------------------------------------------------------------------*
CLASS LCL_HANDLE_EVENTS DEFINITION.
  PUBLIC SECTION.
    METHODS:
      ON_USER_COMMAND FOR EVENT ADDED_FUNCTION OF CL_SALV_EVENTS_TABLE
        IMPORTING E_SALV_FUNCTION,
      ON_SINGLE_CLICK FOR EVENT LINK_CLICK OF CL_SALV_EVENTS_TABLE
        IMPORTING ROW COLUMN.
ENDCLASS.                    "lcl_handle_events DEFINITION

*---------------------------------------------------------------------*
*       CLASS lcl_handle_events IMPLEMENTATION
*---------------------------------------------------------------------*
* §5.2 implement the events for handling the events of cl_salv_table
*---------------------------------------------------------------------*
CLASS LCL_HANDLE_EVENTS IMPLEMENTATION.

  METHOD ON_USER_COMMAND.

    DATA LV_ROW TYPE SY-TABIX.

    CASE E_SALV_FUNCTION.
      WHEN 'YINS'.
        CALL SELECTION-SCREEN 9001 STARTING AT 10 05.
        IF SY-SUBRC = 0.
          GO_SUBST_BL->INSERT_ROW( IV_BLART = P_BLART1
                                   IV_GSBER = P_GSBER1
                                   IT_HKONT = S_HKONT1[] ).
          GO_SUBST_BL->REFRESH_ALV( ).
        ENDIF.
      WHEN 'YCOP'.
        LV_ROW = GO_SUBST_BL->GET_ROW_SELECTED( ).
        IF LV_ROW IS NOT INITIAL.
          GO_SUBST_BL->GET_DATA_FROM_ROW_INDEX( EXPORTING IV_ROW_INDEX = LV_ROW
                                                IMPORTING EV_BLART = P_BLART2
                                                          EV_GSBER = P_GSBER2
                                                          ET_HKONT = S_HKONT3[] ).
          CLEAR: P_BLART3, P_GSBER3.
          CALL SELECTION-SCREEN 9002 STARTING AT 10 05.
          IF SY-SUBRC = 0.
            GO_SUBST_BL->INSERT_ROW( IV_BLART = P_BLART3
                                     IV_GSBER = P_GSBER3
                                     IT_HKONT = S_HKONT3[] ).
            GO_SUBST_BL->REFRESH_ALV( ).
          ENDIF.
        ENDIF.
      WHEN 'YDEL'.
        LV_ROW = GO_SUBST_BL->GET_ROW_SELECTED( ).
        IF LV_ROW IS NOT INITIAL.
          GO_SUBST_BL->DELETE_ROW( LV_ROW ).
          GO_SUBST_BL->REFRESH_ALV( ).
        ENDIF.
      WHEN 'YCHK'.
        GO_SUBST_BL->CHECK_ACCOUNTS( ).
    ENDCASE.

  ENDMETHOD.                    "on_user_command

  METHOD ON_SINGLE_CLICK.

    DATA LV_ROW TYPE SY-TABIX.
    DATA LT_HKONT_BEFORE TYPE RANGE OF HKONT.

    IF COLUMN = 'HKSEL'.
      LV_ROW = GO_SUBST_BL->GET_ROW_SELECTED( ).
      S_HKONT[] = GO_SUBST_BL->GET_ACCOUNTS( LV_ROW ).
      LT_HKONT_BEFORE = S_HKONT[].
      CALL SELECTION-SCREEN 9000 STARTING AT 10 05.
      IF SY-SUBRC = 0 AND LT_HKONT_BEFORE <> S_HKONT[].
        GO_SUBST_BL->SET_ACCOUNTS( EXPORTING IV_ROW_INDEX = LV_ROW
                                             IT_HKONT = S_HKONT[] ).
        GO_SUBST_BL->REFRESH_ALV( ).
      ENDIF.
    ENDIF.

    IF COLUMN = 'HKDIS'.
      LV_ROW = GO_SUBST_BL->GET_ROW_SELECTED( ).
      GO_SUBST_BL->DISPLAY_ACCOUNT_LIST( LV_ROW ).
    ENDIF.

  ENDMETHOD.

ENDCLASS.                    "lcl_handle_events IMPLEMENTATION