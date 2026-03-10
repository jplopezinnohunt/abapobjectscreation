METHOD class_constructor.
  " Initialize constants for document types related to offboarding process
  gc_document_types-separation_letter  = c_hroffboard_sep.  "'HROFFBOARD_SEP'.  Separation Letter
  gc_document_types-repatriation_travel  = c_hroffboard_rep."'HROFFBOARD_REP'.  Repatriation Trip
  gc_document_types-exit_questionnaire = c_hroffboard_exit. "'HROFFBOARD_EXIT'. Exit Questionnaire
  gc_document_types-exit_questionnaire = c_hroffboard_ship. "'HROFFBOARD_SHIP'. Repatriation shipment

  " Initialize constants for status codes used during the process
  gc_status-not_uploaded = c_not_uploaded. "'NOT_UPLOADED'.    " Document not uploaded yet
  gc_status-uploaded     = c_uploaded.     "'UPLOADED'.        " Document uploaded
  gc_status-completed    = c_completed.    "'COMPLETED'.       " Process completed
  gc_status-pending      = c_pending.      "'PENDING'.         " Process pending

  " Initialize constants for archive configuration
  gc_archives-archive_id = c_content_repo. " 'A2'.             " Archive ID
  gc_archives-sap_object = c_object_type.  "'PREL'.           " SAP object type for archiving
  gc_archives-doc_class  = c_doc_class.    "'HROFFBOARD'.     " Document class for HR Offboarding
ENDMETHOD.
