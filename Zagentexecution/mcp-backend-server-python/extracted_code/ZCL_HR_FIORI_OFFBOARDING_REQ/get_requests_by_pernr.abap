METHOD get_requests_by_pernr.
  " Initialisation
  CLEAR: et_requests, rs_return.
  REFRESH: et_requests.

  " Vérification PERNR
  IF iv_pernr IS INITIAL.
    rs_return-type    = 'E'.
*    rs_return-message = 'The PERNR is empty.'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '058'
      INTO rs_return-message.
    RETURN.
  ENDIF.

  " Variables
  DATA: lt_temp_requests  TYPE zv_hrfiori_req_tt,
        ls_last_request   TYPE zv_hrfiori_req,
        lt_guids          TYPE HASHED TABLE OF guid WITH UNIQUE KEY table_line,
        lr_effective_date TYPE RANGE OF dats,
        lr_endda          TYPE RANGE OF dats,
        lr_actiontype     TYPE RANGE OF char50.

  " Traitement des filtres
  IF it_filters IS NOT INITIAL.
    LOOP AT it_filters ASSIGNING FIELD-SYMBOL(<fs_filter>).
      CASE to_upper( <fs_filter>-property ).

          " Filtre EffectiveDate
        WHEN c_effectivedate.
          LOOP AT <fs_filter>-select_options ASSIGNING FIELD-SYMBOL(<fs_opt>).
            DATA(lv_date_value) = <fs_opt>-low.
            IF lv_date_value CP '____-__-__'.
              REPLACE ALL OCCURRENCES OF '-' IN lv_date_value WITH ''.
            ENDIF.
            DATA lv_date_conv TYPE dats.
            lv_date_conv = lv_date_value.
            APPEND VALUE #( sign = <fs_opt>-sign option = <fs_opt>-option low = lv_date_conv high = <fs_opt>-high )
                   TO lr_effective_date.
          ENDLOOP.

          " Filtre EndDate
        WHEN c_endda.
          LOOP AT <fs_filter>-select_options ASSIGNING <fs_opt>.
            DATA(lv_date_value2) = <fs_opt>-low.
            IF lv_date_value2 CP '____-__-__'.
              REPLACE ALL OCCURRENCES OF '-' IN lv_date_value2 WITH ''.
            ENDIF.
            DATA lv_date_conv2 TYPE dats.
            lv_date_conv2 = lv_date_value2.
            APPEND VALUE #( sign = <fs_opt>-sign option = <fs_opt>-option low = lv_date_conv2 high = <fs_opt>-high )
                   TO lr_endda.
          ENDLOOP.

          " Filtre ActionType (clé directe)
        WHEN c_actiontype.
          LOOP AT <fs_filter>-select_options ASSIGNING <fs_opt>.
            APPEND VALUE #( sign = <fs_opt>-sign
                            option = <fs_opt>-option
                            low = <fs_opt>-low
                            high = <fs_opt>-high ) TO lr_actiontype.
          ENDLOOP.

      ENDCASE.
    ENDLOOP.
  ENDIF.

  " SELECT avec filtres de base
  SELECT *
    FROM zv_hrfiori_req
    INTO TABLE @lt_temp_requests
    WHERE creator_pernr = @iv_pernr
    ORDER BY guid ASCENDING, seqno DESCENDING.

  " Application des filtres sur les données récupérées
  IF lr_effective_date IS NOT INITIAL.
    DELETE lt_temp_requests WHERE effective_date NOT IN lr_effective_date.
  ENDIF.

  IF lr_endda IS NOT INITIAL.
    DELETE lt_temp_requests WHERE endda NOT IN lr_endda.
  ENDIF.

  IF lr_actiontype IS NOT INITIAL.
    DELETE lt_temp_requests WHERE action_type NOT IN lr_actiontype.
  ENDIF.

  " Garder le SEQNO le plus grand par GUID
  LOOP AT lt_temp_requests INTO ls_last_request.
    READ TABLE lt_guids WITH KEY table_line = ls_last_request-guid TRANSPORTING NO FIELDS.
    IF sy-subrc <> 0.
      APPEND ls_last_request TO et_requests.
      INSERT ls_last_request-guid INTO TABLE lt_guids.
    ENDIF.
  ENDLOOP.

  " Résultat
  IF et_requests IS INITIAL.
    rs_return-type    = 'W'.
*    rs_return-message = 'No queries found.'.
    MESSAGE ID 'ZHRFIORI' TYPE 'W' NUMBER '047'
      INTO rs_return-message.
  ELSE.
    rs_return-type    = 'S'.
*    rs_return-message = |{ lines( et_requests ) } request(s) found.| .
    DATA(lv_nb_req) = lines( et_requests ).
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '059'
      INTO rs_return-message WITH lv_nb_req.
  ENDIF.
ENDMETHOD.
