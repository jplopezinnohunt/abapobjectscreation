METHOD is_persinfo_application.

  CLEAR rv_is_persinfo_application.
  IF iv_application_id = gc_application_id-mypersonaldata OR
     iv_application_id = gc_application_id-myaddresses OR
     iv_application_id = gc_application_id-mybankdetails OR
     iv_application_id = gc_application_id-myfamilymembers OR
     iv_application_id = gc_application_id-mycommunication OR
     iv_application_id = gc_application_id-myinternaldata OR
     iv_application_id = gc_application_id-myexternalorganizations OR
     iv_application_id = gc_application_id-mymedicalinformation.
    rv_is_persinfo_application = abap_true.
  ENDIF.

ENDMETHOD.
