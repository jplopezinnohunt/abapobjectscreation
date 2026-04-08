ENHANCEMENT 2  .
  DATA lv_shm_trip TYPE boole_d.
  CONSTANTS cs_shm_trip TYPE rs38l_fnam VALUE 'SHM_TRIP'.

          IMPORT lv_shm_trip
              FROM MEMORY ID cs_shm_trip.
  IF lv_shm_trip EQ abap_true.
    DATA lt_return TYPE BAPIRETTAB.
      CALL FUNCTION 'ZPTRM_UNES_FORM_GET'
        EXPORTING
          i_employeenumber   = EMPLOYEENUMBER
          i_tripnumber       = TRIPNUMBER
          i_periodnumber     = PERIODNUMBER
          i_trip_component   = ' '
         i_trip_data_source = 'MYK'
*          i_trip_data_source = data_source                  "GLWK026984
        TABLES
          et_return          = lt_return.
      FREE MEMORY ID cs_shm_trip.
  ENDIF.
ENDENHANCEMENT.
