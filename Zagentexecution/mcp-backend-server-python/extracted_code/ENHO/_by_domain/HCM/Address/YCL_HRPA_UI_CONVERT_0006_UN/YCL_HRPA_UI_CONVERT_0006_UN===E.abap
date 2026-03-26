ENHANCEMENT 1  .
  DATA ls_t005t TYPE t005t.

  SELECT SINGLE *
    FROM  t005t INTO ls_t005t
    WHERE  spras  = sy-langu
      AND  land1 = <r0006>-LAND1.

    MOVE ls_t005t-landx TO <r0006>-LAND1_TEXT.
ENDENHANCEMENT.
