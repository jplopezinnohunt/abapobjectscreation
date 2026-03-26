ENHANCEMENT 1  .
  CHECK c_subrc IS INITIAL.
  DELETE FROM ytfm_fund_c5 WHERE fikrs   = u_fikrs
                           AND   fincode = u_fincode.
ENDENHANCEMENT.
