FUNCTION /CITIPMW/V3_DMEE_EXIT_CGI_XML.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     REFERENCE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"----------------------------------------------------------------------
  TABLES: T001Z.

  DATA: ld_id(35),
        ld_ir(35),
        ls_fpayh TYPE fpayh,
        ls_fpayp TYPE fpayp,
        l_item   TYPE dmee_paym_if_type.

* Build up internal tables of payment documents
  l_item   = i_item.
  ls_fpayh = l_item-fpayh.
  ls_fpayp = l_item-fpayp.

     IF i_extension-node-tech_name = 'Id' OR
        i_extension-node-tech_name = 'BIC' OR
        i_extension-node-tech_name = 'BICOrBEI'.

***********************************************************************
* ID of sender                                                        *
***********************************************************************

    CLEAR ld_id.

*Get Parameter Value for 'Id' and 'BICOrBEI':
    SELECT SINGLE * FROM t001z WHERE bukrs = ls_fpayh-zbukr AND
                                     party = 'CGIID'.
    IF sy-subrc eq '0'.
      ld_id = t001z-paval.
      c_value = ld_id.
    ENDIF.

  ELSEIF i_extension-node-tech_name = 'Issr'.
***********************************************************************
* Issuer                                                              *
***********************************************************************

* Initialize value
    CLEAR ld_ir.

* Get Parameter Value for Issuer:
    SELECT SINGLE * FROM t001z
                      WHERE bukrs = ls_fpayp-bukrs AND
                            party = 'CGIIR'.
    IF sy-subrc eq '0'.
      ld_ir = t001z-paval.
      c_value = ld_ir.
    ENDIF.

  ENDIF.


ENDFUNCTION.