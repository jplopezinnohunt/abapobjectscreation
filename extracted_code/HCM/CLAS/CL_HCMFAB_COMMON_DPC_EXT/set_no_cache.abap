METHOD set_no_cache.

  DATA: ls_header TYPE ihttpnvp.

  ls_header-name  = 'Cache-Control'.                        "#EC NOTEXT
  ls_header-value = 'no-cache, no-store'.                   "#EC NOTEXT
  set_header( ls_header ).

  ls_header-name  = 'Pragma'.                               "#EC NOTEXT
  ls_header-value = 'no-cache'.                             "#EC NOTEXT
  set_header( ls_header ).

ENDMETHOD.
