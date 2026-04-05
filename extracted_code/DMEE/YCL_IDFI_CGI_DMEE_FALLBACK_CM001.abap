  METHOD get_credit.
******* Put here tag redefinition for FALLBACK class (general case)
******* For country specific redefinition tag, use DMEE VGI country BADI
    CASE i_node_path.
*      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
**       this node holds the value of the Clearing system member ID
*        IF i_fpayh-zbnkl IS NOT INITIAL.
*          c_value = i_fpayh-zbnkl.
*        ELSE.
**          c_value = i_fpayh-zbnky.
*          CLEAR c_value.
*        ENDIF.
      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Nm>'.
        "If payment origin is TR-CM-BT, then put item text to this tag
        IF i_fpayp-origin = 'TR-CM-BT'.
          c_value = i_fpayp-sgtxt.
        ENDIF.
        "Only 35 first characters, remaining characters must be set in tag <StrtNm>
        mv_cdtr_name = c_value.
        IF c_value+35 IS NOT INITIAL.
          CLEAR c_value+35.
        ENDIF.
        mv_fpayh = i_fpayh.   "Set to buffer for tag <StrtNm>
      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
        IF i_fpayh = mv_fpayh AND mv_cdtr_name+35 IS NOT INITIAL.
          c_value = |{ mv_cdtr_name+35 } { c_value }|.
        ENDIF.
        IF c_value+70 IS NOT INITIAL.
          CLEAR c_value+70.
        ENDIF.
    ENDCASE.
  ENDMETHOD.