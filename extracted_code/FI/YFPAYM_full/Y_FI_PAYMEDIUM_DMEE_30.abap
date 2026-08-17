FUNCTION Y_FI_PAYMEDIUM_DMEE_30.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(I_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"  TABLES
*"      T_FPAYP STRUCTURE  FPAYP
*"      T_PAYMENT_DETAILS STRUCTURE  FPM_PAYD
*"      T_FILE_OUTPUT STRUCTURE  FPM_FILE
*"--------------------------------------------------------------------
  DATA: wa_fpayp    TYPE fpayp.
  DATA: tab_item    LIKE TABLE OF dmee_payd,
        wa_tab_item TYPE dmee_payd.

***
  data: wa_paym_ref like YVENDOR_PAYM_REF,
        wa_item     type dmee_paym_if_type,
        params      type fpm_selpar-param.
***

  wa_item-fpayh  = i_fpayh.
  wa_item-fpayhx = i_fpayhx.

  LOOP AT t_fpayp INTO wa_fpayp.
    wa_item-fpayp = wa_fpayp.
***
    clear wa_paym_ref.
    select single * into wa_paym_ref
                    from YVENDOR_PAYM_REF
                    where bukrs = wa_fpayp-bukrs
                      and lifnr = wa_fpayp-gpa2r(10)
                      and blart = wa_fpayp-vor1r(2).
*                      and belnr = wa_fpayp-doc2r+4(10)
*                      and gjahr = wa_fpayp-doc2r+14(4).
    if sy-subrc <> 0.

    endif. "sy-subrc
***
    REFRESH tab_item.
    LOOP AT t_payment_details.
      wa_tab_item-type = t_payment_details-type.
      wa_tab_item-text = t_payment_details-text.
      APPEND wa_tab_item TO tab_item.
    ENDLOOP.

    CALL FUNCTION 'DMEE_PUT_ITEM'
         EXPORTING
              item        = wa_item
*             param       =
              uparam      = params
         TABLES
              item_tab    = tab_item
              file_output = t_file_output.
  ENDLOOP.

*  Build up internal sum table for file sheet
***  IF x_filesheet_tab = 'X'.
***    PERFORM build_filesheet_tab USING i_fpayh
***                                      i_fpayhx.
***  ENDIF.

ENDFUNCTION.