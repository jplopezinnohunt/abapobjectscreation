FUNCTION /citipmw/v3_wl949_bic_or_id.
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

  DATA:   lwa_item   TYPE dmee_paym_if_type,
          lwa_item1   TYPE dmee_paym_if_type,
          l_fpayhx   TYPE fpayhx,
          l_fpayh    TYPE fpayh,
          l_fpayp    TYPE fpayp.

  DATA: temp(10) TYPE c,
        l_piuid(35) TYPE c,
        l_svlcd(4) TYPE c.

  DATA : l_waers TYPE waers.

  lwa_item = i_item.
  l_fpayhx  = lwa_item-fpayhx.
  l_fpayh  = lwa_item-fpayh.

  CLEAR temp.

  IF l_fpayhx-lclinstrm_prty = 'CITI949'.

* WL: ACH	568/569	 & Cash & MPAY (Mass 840) - map routing code 'R'
    IF l_fpayhx-svclvl_cd = 'NURG' OR
       l_fpayhx-svclvl_cd = 'CASH' OR
       l_fpayhx-svclvl_cd = 'MPAY'.

      IF l_fpayhx-waers <> 'NOK'.
        temp = 'R'.
* Exception : for Bene Currency NOK map 'BIC'
      ELSEif l_fpayhx-waers = 'NOK' .
        temp = 'S'.
      ENDIF.

* WL: SEPA  935 - map swift 'S'.
    ELSEIF  l_fpayhx-svclvl_cd = 'SEPA'.

      temp = 'S'. "Map Swift code

* WL: Wire 570/571 - Map routing code if available else default to SWIFT mapping
    ELSEIF  l_fpayhx-svclvl_cd = 'URGP' OR l_fpayhx-svclvl_cd = 'URNS'.
* Default Logic to map the Routing(MemberID) if Available else map SWIFT(BIC)
*      IF NOT l_fpayh-zbnkl IS INITIAL.
*        temp = 'R'.
*      ELSE.
*        temp = 'S'.
*      ENDIF.
* Map all the creditor agent tags for Wire Transfers ( BIC , Member ID & Bank Name and Address )
      temp = ' '.
* WL: Others Cheques  386 - map ' '.
    ELSE.
      temp = ' '.
    ENDIF.
  ELSE.

* If not World Link Payments
  ENDIF.

  c_value = temp.

*}   INSERT
ENDFUNCTION.