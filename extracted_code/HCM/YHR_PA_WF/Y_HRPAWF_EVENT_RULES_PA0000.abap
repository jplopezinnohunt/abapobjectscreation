FUNCTION Y_HRPAWF_EVENT_RULES_PA0000
  IMPORTING
    VALUE(AFTER_IMAGE) LIKE PRELP
    VALUE(BEFORE_IMAGE) LIKE PRELP
    VALUE(BUSINESSOBJECT) LIKE SWOTBASDAT-OBJTYPE
    VALUE(OPERATION) LIKE T779W-WFOPR
  EXPORTING
    VALUE(EVENT) LIKE SWETYPECOU-EVENT
  TABLES
    EVENTS_PER_OPERATION LIKE EVENTPOPER OPTIONAL.




  DATA: beforeimage LIKE p0000.
  DATA: afterimage  LIKE p0000.

*  DATA(lo_trace) = NEW ycl_bc_trace_file( ).
*  IF lo_trace->open_dataset( ) = 0.
*    lo_trace->transfer_to_file( iv_field = 'SY-CPROG' iv_value = sy-cprog ).
*    lo_trace->transfer_to_file( iv_field = 'SY-REPID' iv_value = sy-repid ).
*    lo_trace->close_dataset( ).
*  ENDIF.

  CHECK sy-cprog <> 'SAPMHTTP'. "do not trigger event for WF Separation

  beforeimage = before_image.
  afterimage  = after_image.

  CASE operation.
    WHEN 'DEL'.

    WHEN OTHERS."INSERT/UPDATE

      CHECK beforeimage-stat2 NE afterimage-stat2.
*   Only when statuschanges

      IF beforeimage-pernr IS INITIAL.
*   New P0000 entry ==> employee was hired
*** Event HIRED now triggered in HR_EVENT_RULES_PA0001   "L9CK016869
*        IF AFTERIMAGE-STAT2 EQ '3'.                     "L9CK016869
*          EVENT = 'HIRED'.                              "L9CK016869
*        ENDIF.                                          "L9CK016869
      ELSE."before image not initial
        IF beforeimage-stat2 EQ '3'.
*     Employee was active
          CASE afterimage-stat2.
            WHEN '2'. event = 'RETIRED'.
            WHEN '0'. event = 'COMPANYLEFT'.
          ENDCASE.
        ELSEIF beforeimage-stat2 EQ '0' AND afterimage-stat2 EQ '3'
            OR beforeimage-stat2 EQ '2' AND afterimage-stat2 EQ '3'.
* Employee was inactive
          event = 'REHIRED'.
        ENDIF."beforeimage-stat2 eq 3
      ENDIF."before image is initial
  ENDCASE.

ENDFUNCTION.