METHOD concat_investment_offer.

  DATA:   lv_amt_inp          TYPE ben_beeamt,
          lv_amount           TYPE string,
          lv_perc             TYPE string.

  MOVE is_investment-inv_amt TO lv_amt_inp.

  convert_decimal_to_string(
    EXPORTING
      iv_input_amt  = lv_amt_inp
      iv_curr       = is_investment-curre
    IMPORTING
      ev_output_amt = lv_amount
  ).

  lv_perc = is_investment-inv_pct.

  CONDENSE lv_perc NO-GAPS.

  CONCATENATE is_investment-inv_name '(' lv_amount '-' lv_perc ')' INTO ev_investment.

ENDMETHOD.
