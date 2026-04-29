  METHOD country_specific_call.
*   ---------------------------------------------------------------------
*   FPAYHX-REF14:
*   ---------------------------------------------------------------------
*    0     6    10
*   SUN  SeqTp
*   ---------------------------------------------------------------------
    DATA lv_bktcp TYPE t042n-bktcp.                         " n2942194
    DATA lv_bankl TYPE t042m-bankl.                         " start of n2893975
    DATA lv_bnkid TYPE t042m-bnkid.

    CONCATENATE is_fpayhx-ubnkl is_fpayhx-ubknt INTO lv_bankl.

    SELECT SINGLE bnkid FROM t042m INTO lv_bnkid
                                   WHERE bukrs = is_fpayh-zbukr
                                   AND   land1 = is_fpayhx-ubnks
                                   AND   bankl = lv_bankl.

    IF  sy-subrc <> 0.
      SELECT SINGLE bnkid FROM t042m INTO lv_bnkid
                                     WHERE bukrs = is_fpayh-zbukr
                                     AND   land1 = is_fpayhx-ubnks
                                     AND   bankl = space.

      IF sy-subrc <> 0.
        SELECT SINGLE bnkid FROM t042m INTO lv_bnkid
                                       WHERE bukrs = space
                                       AND   land1 = is_fpayhx-ubnks
                                       AND   bankl = space.
      ENDIF.
    ENDIF.

    cs_fpayhx_fref-ref14(6) = lv_bnkid+04(6).               " end of n2893975


    SELECT SINGLE bktcp FROM t042n INTO lv_bktcp            " start of n2942194
                                   WHERE land1 = is_fpayhx-ubnks
                                   AND   bankl = lv_bankl
                                   AND   zlsch = is_fpayh-rzawe.

    IF sy-subrc <> 0.
*  if no ZBNKL
      SELECT SINGLE bktcp FROM t042n INTO lv_bktcp
                                     WHERE land1 = is_fpayhx-ubnks
                                     AND   bankl = space
                                     AND   zlsch = is_fpayh-rzawe.
    ENDIF.

    CASE lv_bktcp.
      WHEN '01'.
        cs_fpayhx_fref-ref14+06(4) = 'FRST'.
      WHEN '17'.
        cs_fpayhx_fref-ref14+06(4) = 'RCUR'.
      WHEN '19'.
        cs_fpayhx_fref-ref14+06(4) = 'FNAL'.
      WHEN OTHERS.
        cs_fpayhx_fref-ref14+06(4) = is_fpayhx-seq_type.
    ENDCASE.                                                " end of n2942194
  ENDMETHOD.