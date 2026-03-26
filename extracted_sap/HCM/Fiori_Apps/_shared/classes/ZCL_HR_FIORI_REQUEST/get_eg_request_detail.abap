  METHOD get_eg_request_detail.

    SELECT SINGLE * FROM zthrfiori_eg_mai  INTO CORRESPONDING FIELDS OF @rs_detail_eg WHERE guid EQ @iv_guid.
    IF sy-subrc EQ 0.
      "Fill text fields that are not stored in DB
      "FanatTxt
      "FasexTxt
      "return fasexTxt, fanatTxt EgsctTxt
      IF rs_detail_eg-fasex IS NOT INITIAL.
        rs_detail_eg-fasex_txt = cl_eain_get_text=>get_gender_text( ifd_gesch = rs_detail_eg-fasex ).
      ENDIF.
      IF rs_detail_eg-fanat IS NOT INITIAL.
        rs_detail_eg-fanat_txt = cl_eain_get_text=>get_nationality_text( ifd_natio = rs_detail_eg-fanat ).
      ENDIF.
      IF rs_detail_eg-egsct IS NOT INITIAL.
        SELECT SINGLE landx50 INTO  @rs_detail_eg-egsct_txt
        FROM t005t WHERE land1 EQ @rs_detail_eg-egsct
          AND spras = @sy-langu.
      ENDIF.

*DSTAT_TXT
      IF rs_detail_eg-dstat IS NOT INITIAL.
        SELECT SINGLE dstxt INTO @rs_detail_eg-dstat_txt
         FROM t7unpad_ds_t
           WHERE dstat EQ @rs_detail_eg-dstat AND   sprsl = @sy-langu
             AND molga = @zcl_hr_fiori_education_grant=>c_molga_un.
      ENDIF.
*NATIO_TXT
      IF rs_detail_eg-natio IS NOT INITIAL.
        rs_detail_eg-natio_txt = cl_eain_get_text=>get_nationality_text( ifd_natio = rs_detail_eg-natio ).
      ENDIF.

*CTTYP_TXT
      IF rs_detail_eg-cttyp IS NOT INITIAL.
      ENDIF.
      SELECT SINGLE cttxt  INTO @rs_detail_eg-cttyp_txt
         FROM t547s WHERE cttyp EQ @rs_detail_eg-cttyp
           AND sprsl = @sy-langu.
    ENDIF.

  ENDMETHOD.
