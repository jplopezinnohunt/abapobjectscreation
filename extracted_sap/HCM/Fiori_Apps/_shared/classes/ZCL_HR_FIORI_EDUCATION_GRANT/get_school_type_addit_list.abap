  METHOD get_school_type_addit_list.
*
*    DATA: ls_school_type TYPE zshr_vh_generic,
*          ls_dd07v       TYPE dd07v,
*          lt_dd07v       TYPE STANDARD TABLE OF dd07v.

*MOLGA  MOLGA CHAR  2 0 Country Grouping
*EGTYP  PUN_EGTYP CHAR  4 0 EG Type or classification
*EGDDS  PUN_EGDDS CHAR  1 0 Duty Station flag for designated
*EGPRE  PUN_EGPRE CHAR  1 0 EG Identifier for Pre Primary
*EGPSC  PUN_EGPSC CHAR  1 0 NPO: EG Post Secondary Identifier
*EGEDL  ZUN_EGEDL CHAR  1 0 NPO: Education Grant CEB Educational level

*T7UNPAD_EGST


    DATA: ls_t7unpad_egst_t TYPE t7unpad_egst_t,
          ls_return         TYPE zshr_vh_generic.

    SELECT * INTO TABLE @DATA(lt_t7unpad_egst_t)
      FROM t7unpad_egst_t
        WHERE sprsl EQ @sy-langu AND
           molga = @c_molga_un.

    LOOP AT lt_t7unpad_egst_t INTO ls_t7unpad_egst_t.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_egst_t-egtyp TO ls_return-id,
        ls_t7unpad_egst_t-egtyt TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.



  ENDMETHOD.
