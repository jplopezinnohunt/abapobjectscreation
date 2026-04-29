FUNCTION Z_DMEE_EXIT_TAX_NUMBER.
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

* Extended template function module -----------------------------------*

data: w_item type dmee_paym_if_type,
      w_lifnr type lifnr,
      w_lfa1 type lfa1,
      w_stcd type stcd1.


w_item = i_item.
w_lifnr = w_item-fpayh-gpa1r.

clear w_lfa1.
select single *
             into w_lfa1
             from lfa1
             where lifnr = w_lifnr.

if w_lfa1-stkzn is initial.
  w_stcd = w_lfa1-stcd1.
 else. "nat. person
   w_stcd = w_lfa1-stcd2.
endif.

c_value = w_stcd.

ENDFUNCTION.