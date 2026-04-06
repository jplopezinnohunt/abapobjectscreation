  METHOD constructor.
    "Get PPC customizing
    SELECT a~land1,
           a~deb_cre,
           b~pay_type,
           a~tag_full,
           b~code_ord,
           b~ppc_code,
           b~ppc_value,
           b~pay_struc,
           b~pay_field
           FROM ytfi_ppc_tag AS a INNER JOIN ytfi_ppc_struc AS b ON  b~land1 = a~lan
                                                                 AND b~tag_id = a~ta
           INTO TABLE @mt_ppc_cus.
    "Get SCB customizing
    SELECT * FROM t015l INTO TABLE @mt_t015l.
  ENDMETHOD.