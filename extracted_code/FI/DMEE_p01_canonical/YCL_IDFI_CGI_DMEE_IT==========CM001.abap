  METHOD get_credit.

    CASE i_node_path.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
*       this node holds the value of the Clearing system member ID
        IF i_fpayh-zbnkl IS NOT INITIAL.
          c_value = i_fpayh-zbnkl.
        ELSE.
          "c_value = i_fpayh-zbnky.
          CLEAR c_value.
        ENDIF.

      WHEN OTHERS.
*       call the generic functionality
        super->get_credit(
          EXPORTING
            flt_val_debit_or_credit =  flt_val_debit_or_credit
            flt_val_country         =  flt_val_country            " Country ISO code
            i_tree_id               =  i_tree_id                  " DMEE:  ID for a DMEE format tree
            i_tree_type             =  i_tree_type                " DMEE: tree type
            i_param                 =  i_param
            i_uparam                =  i_uparam
            i_extension             =  i_extension                " DMEE: Extended Interface for Exit Module
            i_fpayh                 =  i_fpayh                    " Payment medium: Payment data
            i_fpayhx                =  i_fpayhx                   " Payment Medium: Prepared Data for Payment
            i_fpayp                 =  i_fpayp                    " Payment medium: Data on paid items
            i_root_nodes            =  i_root_nodes
            i_node_path             =  i_node_path
          CHANGING
            c_value                 =  c_value
            o_value                 =  o_value
            n_value                 =  n_value
            p_value                 =  p_value
        ).
    ENDCASE.

  ENDMETHOD.