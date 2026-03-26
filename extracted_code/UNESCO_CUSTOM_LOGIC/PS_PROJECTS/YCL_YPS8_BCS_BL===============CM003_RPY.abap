  METHOD DISPLAY_ALV.

    MV_REPID = IV_REPID.

    "Init ALV
    TRY.
        CALL METHOD CL_SALV_TABLE=>FACTORY
*      EXPORTING
*        list_display   = IF_SALV_C_BOOL_SAP=>FALSE
*        r_container    =
*        container_name =
          IMPORTING
            R_SALV_TABLE = MO_SALV_TABLE
          CHANGING
            T_TABLE      = MT_RESULT.
      CATCH CX_SALV_MSG .
    ENDTRY.

    "ALV functions activation
    ME->SET_FUNCTIONS( ).

    "ALV columns
    ME->SET_COLUMNS( ).

    "ALV layout
    ME->SET_LAYOUT( ).

    "ALV display settings
    ME->SET_DISPLAY_SETTINGS( ).

    "Display list
    MO_SALV_TABLE->DISPLAY( ).

  ENDMETHOD.