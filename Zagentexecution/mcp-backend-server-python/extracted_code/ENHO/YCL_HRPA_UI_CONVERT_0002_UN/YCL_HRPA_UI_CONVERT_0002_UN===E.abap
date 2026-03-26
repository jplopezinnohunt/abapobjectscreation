ENHANCEMENT 1  .
  DATA ls_t005t TYPE t005t.
  DATA ls_gender TYPE T77PAD_GENDER_T.

  SELECT SINGLE *
    FROM  t005t INTO ls_t005t
    WHERE  spras  = sy-langu
      AND  land1 = <r0002>-GBLND.

    MOVE ls_t005t-landx TO <r0002>-GBLND_TEXT.

  SELECT SINGLE *
    FROM T77PAD_GENDER_T INTO ls_gender
    WHERE spras = sy-langu
      AND gender = <r0002>-GESCH.

  MOVE ls_gender-gender_text TO <r0002>-GESCH_TEXT.

ENDENHANCEMENT.
