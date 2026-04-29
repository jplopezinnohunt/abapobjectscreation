FUNCTION /citipmw/v3_cgi_bank_name.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     REFERENCE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"--------------------------------------------------------------------

  DATA:  lv_bank_name(35),
         lv_bank_name_temp(35),
         lwa_item       TYPE dmee_paym_if_type,
         l_fpayh        TYPE fpayh,
         l_fpayhx    TYPE fpayhx,
         itab_adrc TYPE TABLE OF adrc,
         wa_adrc TYPE adrc,
         wa_addrnr TYPE ad_addrnum,
         wa_bnka        LIKE bnka.

  " Start of Note 1961687
*  DATA: format_params_str TYPE fpm_selpar-param,
*        format_params     TYPE fpm_cgi.

  DATA: lv_nation  TYPE ad_nation.

*  FIELD-SYMBOLS: <fs_format_params> TYPE any.

*  CALL FUNCTION 'FI_PAYM_PARAMETERS_GET'
*       IMPORTING
*       e_format_params = format_params_str.
*
*  ASSIGN format_params_str TO <fs_format_params>.
*         <fs_format_params> = format_params_str.
*         format_params = <fs_format_params>.
*         lv_nation = format_params-nation.
  " End of Note 1961687



  lwa_item = i_item.
  l_fpayh  = lwa_item-fpayh.
  l_fpayhx = lwa_item-fpayhx.

  lv_nation = l_fpayhx-nation.

  CLEAR: wa_bnka,wa_adrc,wa_addrnr.
  SELECT SINGLE adrnr FROM bnka INTO wa_bnka-adrnr
                      WHERE banks = lwa_item-fpayh-zbnks
                        AND bankl = lwa_item-fpayh-zbnky.

  wa_addrnr = wa_bnka-adrnr.

  IF NOT wa_addrnr IS INITIAL.
    CALL FUNCTION 'ADDR_SELECT_ADRC_SINGLE'
      EXPORTING
        addrnumber        = wa_addrnr
      TABLES
        et_adrc           = itab_adrc
      EXCEPTIONS
        address_not_exist = 1
        parameter_error   = 2
        internal_error    = 3
        OTHERS            = 4.
    IF sy-subrc <> 0.
*      MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
*            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.

    ELSE.
      READ TABLE itab_adrc INTO wa_adrc
              WITH KEY nation = lv_nation.            " Note 1961687
      IF NOT wa_adrc IS INITIAL.
        MOVE wa_adrc-name1 TO lv_bank_name_temp.
      ENDIF.
    ENDIF.
  ENDIF.                                                    "N2050269

  IF lv_bank_name_temp IS INITIAL.
    lv_bank_name = l_fpayh-zbnka.
  ELSE.
    lv_bank_name = lv_bank_name_temp.
  ENDIF.

  c_value = lv_bank_name.

ENDFUNCTION.