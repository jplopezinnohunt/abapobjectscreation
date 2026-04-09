
* 4.6C
* WKUL9CK029370 24112000 Saldo im Beleg: Rundungspfennig zweiter Ordnung

*---------------------------------------------------------------------*
*       INCLUDE LHRTSF04 .                                            *
*---------------------------------------------------------------------*

*----------------------------------------------------------------------*
*       Form  VAT_COMPARISON
*----------------------------------------------------------------------*
* routine compares the tax amounts on the debit and credit side.       *
* During transfer-posting both tax amounts must be equal!              *
* WKU New version for Prima Nota
*----------------------------------------------------------------------*
form vat_comparison.
* compare whether the sum for a special VAT indicator is equal on
* debit and credit side.
  data: s_bschl like bz-slbsl,
        h_bschl like bz-hnbsl,
        mwskz   like bz-mwskz,
*       ktosl   like vat_comparison-ktosl,               "WKUK010228
        kschl   like vat_comparison-kschl,                  "WKUK010228
        s_betrg like vat_comparison-betrg,
        s_wmwst like vat_comparison-wmwst,
        s_wrbtr like vat_comparison-wrbtr,                  "WKUK029370
        h_betrg like vat_comparison-betrg,
*       H_WMWST LIKE VAT_COMPARISON-WMWST.                  "WKUK029370
        h_wmwst like vat_comparison-wmwst,                  "WKUK029370
        h_wrbtr like vat_comparison-wrbtr.                  "WKUK029370
  DATA: txjcd LIKE bz-txjcd.                    "GLW note 1817466
  DATA: tax_date TYPE txdat. "GLW note 1819167

  DATA: vat_delta LIKE bz-vat_delta.

  check not net_amounts is initial.
  sort vat_comparison.
* VAT_Comparison contains two blocks of data:
* 1. debit posting-key =  space ; credit posting-key <> space
* 2. debit posting-key <> space ; credit posting-key =  space
  loop at vat_comparison where w_slb is initial.
    clear: s_bschl, h_bschl, s_betrg, h_betrg, s_wmwst, h_wmwst, mwskz.
    s_bschl = vat_comparison-w_slb.
    h_bschl = vat_comparison-w_hnb.
    mwskz   = vat_comparison-mwskz.
*   ktosl   = vat_comparison-ktosl.                      "WKUK010228
    kschl   = vat_comparison-kschl.                         "WKUK010228
    txjcd   = vat_comparison-txjcd.                   "GLW note 1817466
    tax_date = vat_comparison-tax_date. "GLW note 1819167
    vat_delta = vat_comparison-vat_delta.
    IF NOT s_bschl IS INITIAL.
      s_betrg = vat_comparison-betrg.
      s_wmwst = vat_comparison-wmwst.
      s_wrbtr = vat_comparison-wrbtr.                       "WKUK029370
    else.
      h_betrg = vat_comparison-betrg * -1.
      h_wmwst = vat_comparison-wmwst * -1.
      h_wrbtr = vat_comparison-wrbtr * -1.                  "WKUK029370
    endif.
* determine the opposite posting key.
    if not s_bschl is initial.
      h_bschl = vat_comparison-hnbsl.
      clear s_bschl.
    else.
      s_bschl = vat_comparison-slbsl.
      clear h_bschl.
    endif.
* read the opposite posting key
    loop at vat_comparison where w_slb eq s_bschl
                           and   w_hnb eq h_bschl
                           and   mwskz eq mwskz
*                          and   ktosl eq ktosl          "WKUK010228
                           AND   kschl EQ kschl             "WKUK010228
                           AND txjcd EQ txjcd    "GLW note 1817466
                           AND tax_date EQ tax_date "GLW note 1819167
                           AND vat_delta EQ vat_delta. "GLW note 2098779
      if not s_bschl is initial.
        s_betrg = vat_comparison-betrg.
        s_wmwst = vat_comparison-wmwst.
        s_wrbtr = vat_comparison-wrbtr.                     "WKUK029370
      else.
        h_betrg = vat_comparison-betrg * -1.
        h_wmwst = vat_comparison-wmwst * -1.
        h_wrbtr = vat_comparison-wrbtr * -1.                "WKUK029370
      endif.
* both amounts (debit side/credit side) are equal
      if s_betrg eq h_betrg and s_wmwst ne h_wmwst.
        perform vat_correction using s_wmwst h_wmwst.
      endif.
* second order rounding: gross amounts are not equal,       "WKUK029370
* but net amounts are equal and tax amounts are not equal   "WKUK029370
      if s_betrg ne h_betrg and                             "WKUK029370
         s_wrbtr eq h_wrbtr and s_wmwst ne h_wmwst.         "WKUK029370
        perform vat_correction using s_wmwst h_wmwst.       "WKUK029370
      endif.                                                "WKUK029370
      exit.
    endloop.
  endloop.
endform.                                                "VAT_COMPARISON