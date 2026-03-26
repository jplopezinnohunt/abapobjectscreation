  METHOD requesttypevhset_get_entityset.
    SELECT * FROM zthrfiori_reqtyp INTO CORRESPONDING FIELDS OF TABLE et_entityset
        WHERE language EQ sy-langu.
  ENDMETHOD.
