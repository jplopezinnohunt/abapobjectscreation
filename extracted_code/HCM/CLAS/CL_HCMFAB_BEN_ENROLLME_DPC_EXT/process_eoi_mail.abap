METHOD process_eoi_mail.

  DATA: ls_offer TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer.

  LOOP AT it_offer INTO ls_offer
  WHERE eoirq = c_true AND
        eoipr = c_false AND
        ( bpcat = c_health_plan OR bpcat = c_insurance_plan ).

    send_eoi_mail(
      EXPORTING
        iv_grp_date  = ls_offer-eogrp
        iv_plan_name = ls_offer-txt_plan
        iv_pernr     = ls_offer-pernr
    ).

  ENDLOOP.

ENDMETHOD.
