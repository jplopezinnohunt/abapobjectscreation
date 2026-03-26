

--- Method Implementation: YCL_FI_ACCOUNT_SUBST_READ=====CCMAC ---
*"* use this source file for any macro definitions you need
*"* in the implementation part of the class



--- Method Implementation: YCL_FI_ACCOUNT_SUBST_READ=====CM001 ---
  METHOD read.

    TYPES: BEGIN OF ty_subst,
             bukrs TYPE bukrs,
             blart TYPE blart,
             gsber TYPE gsber,
           END OF ty_subst.

    DATA lt_subst TYPE TABLE OF ty_subst.
    DATA lt_hkont_range TYPE RANGE OF hkont.

    CLEAR rv_gsber.

    SELECT DISTINCT bukrs, blart, gsber
       FROM ytfi_ba_subst
       WHERE bukrs = @iv_bukrs
       AND   blart = @iv_blart
       AND   sign <> @space
      INTO TABLE @lt_subst.

    LOOP AT lt_subst INTO DATA(ls_subst).
      SELECT sign,
             opti AS option,
             low,
             high
        FROM ytfi_ba_subst
        WHERE bukrs = @ls_subst-bukrs
        AND   blart = @ls_subst-blart
        AND   gsber = @ls_subst-gsber
        AND   sign <> @space
        INTO TABLE  @lt_hkont_range.
      CHECK lt_hkont_range IS NOT INITIAL.
      IF iv_hkont IN lt_hkont_range.
        rv_gsber = ls_subst-gsber.
        EXIT.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.
