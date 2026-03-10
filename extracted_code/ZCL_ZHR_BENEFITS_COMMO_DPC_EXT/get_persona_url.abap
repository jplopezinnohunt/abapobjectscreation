  METHOD get_persona_url.
    CONSTANTS: lc_persona_pa30 TYPE string
    VALUE '/sap/bc/personas?~transaction=PA30&sap-personas-flavor=005056BE9B021FD08EBF3534CDD9B237&sap-language=EN'.

    DATA: ls_return TYPE zcl_zhr_benefits_commo_mpc_ext=>ts_personaurl.

    ls_return-id = '001'.
    CASE sy-sysid.
      WHEN 'D01'.
        ls_return-url = 'https://hq-sap-ts3.hq.int.unesco.org'.
      WHEN 'TS3'.
        ls_return-url = 'https://hq-sap-ts3.hq.int.unesco.org'.
      WHEN 'P01'.
        ls_return-url = 'https://hq-sap-p01.hq.hq.int.unesco.org'.
    ENDCASE.

    CONCATENATE ls_return-url lc_persona_pa30 INTO ls_return-url.

    copy_data_to_ref( EXPORTING is_data = ls_return
                    CHANGING cr_data  = os_return ).

  ENDMETHOD.
