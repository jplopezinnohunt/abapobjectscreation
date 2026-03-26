  METHOD if_ex_acc_document~change .

    DATA: ls_ekkn TYPE ekkn.
    FIELD-SYMBOLS <accit> TYPE accit.
    DATA ls_extension2    TYPE bapiparex.

    DATA: wa_extension   TYPE bapiparex,
          ext_value(960) TYPE c,
          wa_accit       TYPE accit,
          l_ref          TYPE REF TO data,
          l_check        TYPE okcode.
    FIELD-SYMBOLS: <l_struc> TYPE any,
                   <l_field> TYPE any.

    IF c_extension2 IS NOT INITIAL.
      "Read Header data
      LOOP AT c_extension2  INTO wa_extension WHERE structure = 'HEADER'.
        CHECK wa_extension-valuepart1 = 'BUS_ACT' AND wa_extension-valuepart2 = 'RFST'.
        c_acchd-glvor = 'RFST'.
        c_acchd-tcode = wa_extension-valuepart3.
        l_check = 'X'.
      ENDLOOP.
      IF l_check = 'X '.

        " Read Line data
*      SORT c_extension2 BY structure.
        LOOP AT c_extension2  INTO wa_extension WHERE structure = 'LINE'.
           c_acchd-glvor = 'RFST'.
          LOOP AT c_accit ASSIGNING <accit> WHERE posnr = wa_extension-valuepart1.
            <accit>-bstat = 'S'. "Allows request document without balance control
            <accit>-bschl = '39'.
             <accit>-umskz = 'F'.
            <accit>-ZUMSK = 'A'.
            <accit>-XANET = 'X'.
            <accit>-ebeln = wa_extension-valuepart2.
            <accit>-ebelp = wa_extension-valuepart3.
            <accit>-zekkn = wa_extension-valuepart4.
*GEt PO information for Cost center elements
            SELECT SINGLE * FROM ekkn
             WHERE ebeln = @<accit>-ebeln AND
                   ebelp = @<accit>-ebelp AND
                   zekkn = @<accit>-zekkn
            INTO CORRESPONDING FIELDS OF @ls_ekkn.
            IF sy-subrc  = 0.
              <accit>-kostl = ls_ekkn-kostl.
              <accit>-geber = ls_ekkn-geber.
              <accit>-fistl = ls_ekkn-fistl.
              <accit>-ps_psp_pnr = ls_ekkn-ps_psp_pnr.


            ENDIF.
          ENDLOOP.

        ENDLOOP.
      ENDIF.
    ENDIF.
  ENDMETHOD.
