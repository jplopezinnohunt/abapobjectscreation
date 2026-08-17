FUNCTION Y_FI_PAYMEDIUM_06.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IS_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(IS_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"     VALUE(I_PAYMEDIUM) TYPE  XFELD OPTIONAL
*"  EXPORTING
*"     REFERENCE(ES_FPAYHX_CREF) LIKE  FPAYHX_CREF STRUCTURE
*"        FPAYHX_CREF
*"  TABLES
*"      T_FPAYP STRUCTURE  FPAYP
*"----------------------------------------------------------------------

data: w_fpayp type fpayp,
      w_cbldat(10).

clear w_fpayp.
loop at t_fpayp into w_fpayp.
  clear YVENDOR_PAYM_REF.
  select single *
               from YVENDOR_PAYM_REF
               where bukrs = w_fpayp-doc2r(4)
                 and lifnr = w_fpayp-gpa2r
                 and blart = w_fpayp-vor1r.
*                 and belnr = w_fpayp-doc2r+4(10)
*                 and gjahr = w_fpayp-doc2r+14(4).

  if sy-subrc is initial. "Vendor ref. for document
    w_fpayp-zref01 = YVENDOR_PAYM_REF-VENDOR_PAYM_REF.

   else.
     clear YVENDOR_PAYM_REF.
     select single *
                  from YVENDOR_PAYM_REF
                  where bukrs = w_fpayp-doc2r(4)
                    and lifnr = w_fpayp-gpa2r
                    and blart = w_fpayp-vor1r.
*                    and belnr = space
*                    and gjahr = '0000'.
     if  sy-subrc is initial. "Vendor ref. for doc.type
       w_fpayp-zref01 = YVENDOR_PAYM_REF-VENDOR_PAYM_REF.
      else. "old-style note to payee
        write w_fpayp-bldat to w_cbldat no-zero dd/mm/yyyy.
        case is_fpayhx-preftyp. "what is format of note
          when 'SAMPLE 01'.
            concatenate 'No.'
                        w_fpayp-xblnr
                        '/'
                        w_cbldat
                   into w_fpayp-zref01.
          when 'SAP SEPA'.
            concatenate '/INV/'
                        w_fpayp-xblnr
                        ' '
                        w_cbldat
                   into w_fpayp-zref01.
          when others.
        endcase. "preftyp
     endif.
  endif.
  modify t_fpayp from w_fpayp transporting zref01.
endloop. "t_fpayp

ENDFUNCTION.