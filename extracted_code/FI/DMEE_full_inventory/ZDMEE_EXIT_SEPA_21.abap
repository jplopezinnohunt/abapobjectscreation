FUNCTION ZDMEE_EXIT_SEPA_21.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"--------------------------------------------------------------------

  FIELD-SYMBOLS: <item> TYPE dmee_paym_if_type.

  ASSIGN i_item TO <item>.

*{   REPLACE        D01K9B01IR                                        1
*\  PERFORM batch_id USING <item>-fpayh
  PERFORM batch_id USING <item>-fpayh <item>-fpayhx
*}   REPLACE
                         G_RENUM.
    C_VALUE = G_RENUM.

ENDFUNCTION.