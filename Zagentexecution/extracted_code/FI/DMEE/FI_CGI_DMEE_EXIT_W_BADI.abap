FUNCTION fi_cgi_dmee_exit_w_badi.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE_ABA
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID_ABA
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     REFERENCE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE_ABA
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"----------------------------------------------------------------------

*  Initialize Exporting parameters
  CLEAR: o_value, c_value, n_value, p_value.

  FIELD-SYMBOLS: <fs_item> TYPE dmee_paym_if_type.
  ASSIGN i_item TO <fs_item>.

* Filters of Badi
  DATA: lv_debit_or_credit(10),
        lv_debit_or_credit_filter(10).
  DATA lv_bank_country LIKE fpayhx-ubiso.

* path of node, including node
  DATA lv_node_path TYPE string.
* nodes before <GrpHdr> or <PmntInf>
  DATA: lv_root_nodes TYPE string,
        lv_area       TYPE string.

* check if format is credit transfer or direct debit
  IF <fs_item>-fpayh-mguid IS NOT INITIAL. " SEPA Mandate exists
    lv_debit_or_credit = 'DEBIT'.
  ELSE.
* no SEPA Mandate->check payment method settings to decide if it is incoming payment
    case <fs_item>-fpayhx-xeinz.
      when space.         " outgoing payment
        lv_debit_or_credit = 'CREDIT'.
      when 'X'.        " incoming payment
        lv_debit_or_credit = 'DEBIT'.
    endcase.
  ENDIF .

* begin of note 2366540
* in case of FICA Payment Run - use FKK prefix filter to get FICA relevant enh.implementation

* check it is FICA Payment Run:
  cl_idfi_cgi_dmee_utils=>get_area(
    EXPORTING
      is_fpayh     = <fs_item>-fpayh
    IMPORTING
      ev_area      = lv_area
      ).

  IF lv_area EQ 'FI-CA'.
* use prefix FKK in case of FICA document
    CONCATENATE 'FKK_ '  lv_debit_or_credit INTO lv_debit_or_credit_filter.
  ELSE.
* no prefix needed
    lv_debit_or_credit_filter = lv_debit_or_credit.
  ENDIF.
* end of note 2366540

  IF <fs_item>-fpayhx-ubiso IS NOT INITIAL.
    lv_bank_country = <fs_item>-fpayhx-ubiso.
  ELSE.
    lv_bank_country = <fs_item>-fpayhx-ubnks.
  ENDIF.

  DATA: l_badi TYPE REF TO fi_cgi_dmee_countries.

  DATA: l_badi_c   TYPE REF TO fi_cgi_dmee_countries_cust.

  TRY.
      GET BADI l_badi
        FILTERS
          bank_country    = lv_bank_country
          credit_or_debit = lv_debit_or_credit_filter.

      DATA li_number_of_impl TYPE i.
      li_number_of_impl = cl_badi_query=>number_of_implementations( l_badi ).
      IF li_number_of_impl > 0.
*       Get the node path and the root nodes
        cl_idfi_cgi_dmee_utils=>get_splitted_path(
          EXPORTING
            is_extension  = i_extension
            iv_tree_type  = i_tree_type
            iv_tree_id    = i_tree_id
          IMPORTING
            ev_path       = lv_node_path
            ev_root_nodes = lv_root_nodes
        ).

*       Set Note To Payee from ITAB Table
        cl_idfi_cgi_dmee_utils=>set_note2payee( it_itab = i_tab[] ). "n2322683

*       get value of node or boolean value for technical node
        CALL BADI l_badi->get_value
          EXPORTING
            flt_val_debit_or_credit = lv_debit_or_credit
            flt_val_country         = lv_bank_country
            i_tree_id               = i_tree_id
            i_tree_type             = i_tree_type
            i_param                 = i_param
            i_uparam                = i_uparam
            i_extension             = i_extension
            i_fpayh                 = <fs_item>-fpayh
            i_fpayhx                = <fs_item>-fpayhx
            i_fpayp                 = <fs_item>-fpayp
            i_root_nodes            = lv_root_nodes
            i_node_path             = lv_node_path
          CHANGING
            c_value                 = c_value
            o_value                 = o_value
            n_value                 = n_value
            p_value                 = p_value.

      ENDIF.

    CATCH cx_badi_not_implemented.
* fallback class will be called
  ENDTRY.

* call BAdI for customer
  TRY.
      GET BADI l_badi_c
        FILTERS
          bank_country    = lv_bank_country
          credit_or_debit = lv_debit_or_credit_filter.

      li_number_of_impl = cl_badi_query=>number_of_implementations( l_badi_c ).

      IF li_number_of_impl > 0.
        IF lv_node_path IS NOT INITIAL.
*       Get the node path and the root nodes
          cl_idfi_cgi_dmee_utils=>get_splitted_path(
            EXPORTING
              is_extension  = i_extension
              iv_tree_type  = i_tree_type
              iv_tree_id    = i_tree_id
            IMPORTING
              ev_path       = lv_node_path
              ev_root_nodes = lv_root_nodes
          ).
        ENDIF.
*       get value of node or boolean value for technical node,
*       i_extension-node-node_type = 'TECH' is technical node
        CALL BADI l_badi_c->get_value
          EXPORTING
            flt_val_debit_or_credit = lv_debit_or_credit
            flt_val_country         = lv_bank_country
            i_tree_id               = i_tree_id
            i_tree_type             = i_tree_type
            i_param                 = i_param
            i_uparam                = i_uparam
            i_extension             = i_extension
            i_fpayh                 = <fs_item>-fpayh
            i_fpayhx                = <fs_item>-fpayhx
            i_fpayp                 = <fs_item>-fpayp
            i_root_nodes            = lv_root_nodes
            i_node_path             = lv_node_path
          CHANGING
            c_value                 = c_value
            o_value                 = o_value
            n_value                 = n_value
            p_value                 = p_value.
      ENDIF.

    CATCH cx_badi_not_implemented.
  ENDTRY.
ENDFUNCTION.