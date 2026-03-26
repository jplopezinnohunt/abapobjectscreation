ENHANCEMENT 1  .
  DATA yylo_instance TYPE REF TO ycl_idfi_cgi_dmee_fallback.
  yylo_instance = ycl_idfi_cgi_dmee_fallback=>get_instance( ).
  yylo_instance->get_credit( EXPORTING flt_val_debit_or_credit = flt_val_debit_or_credit
                                       flt_val_country         = flt_val_country
                                       i_tree_id               = i_tree_id
                                       i_tree_type             = i_tree_type
                                       i_param                 = i_param
                                       i_uparam                = i_uparam
                                       i_extension             = i_extension
                                       i_fpayh                 = i_fpayh
                                       i_fpayhx                = i_fpayhx
                                       i_fpayp                 = i_fpayp
                                       i_root_nodes            = i_root_nodes
                                       i_node_path             = i_node_path
                             CHANGING  c_value                 = c_value
                                       o_value                 = o_value
                                       n_value                 = n_value
                                       p_value                 = p_value ).
ENDENHANCEMENT.
