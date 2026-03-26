METHOD get_contract_type.

  " Table interne SAP contenant les libellés des types de contrat
  DATA: lt_t542t  TYPE STANDARD TABLE OF t542t,
        ls_return TYPE zstr_anvsh.   " Structure de sortie (ID + TEXT)

  " 1. Récupération des types de contrat dans la langue de connexion
  SELECT t542t~*
    FROM t542t INNER JOIN ZTHR_OFFB_ANSVH on t542t~ansvh eq ZTHR_OFFB_ANSVH~ansvh
    WHERE spras = @sy-langu
      AND molga = 'UN'
    INTO TABLE @lt_t542t.

  " 2. Si rien trouvé → fallback en anglais
  IF sy-subrc <> 0.
    SELECT  t542t~*
      FROM t542t INNER JOIN ZTHR_OFFB_ANSVH on t542t~ansvh eq ZTHR_OFFB_ANSVH~ansvh
      WHERE spras = 'E'
        AND molga = 'UN'
      INTO TABLE @lt_t542t.
  ENDIF.

  " 3. Toujours vérifier si données présentes
  IF lt_t542t IS INITIAL.
    rs_return-type    = 'E'.
*    rs_return-message = 'No contract type found'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '060'
      INTO rs_return-message.
    CLEAR ot_list.
    RETURN.
  ENDIF.

  " 4. Remplissage de la table de sortie OT_LIST
  LOOP AT lt_t542t INTO DATA(ls_t542t).
    ls_return-id   = ls_t542t-ansvh.  " Code du type de contrat
    ls_return-text = ls_t542t-atx.    " Libellé du type de contrat
    APPEND ls_return TO ot_list.      " Ajout dans la table exportée
  ENDLOOP.

  " 5. Message succès
  rs_return-type    = 'S'.
*  rs_return-message = 'Contract types successfully retrieved'.
  MESSAGE ID 'ZHRFIORI' TYPE 'S' NUMBER '061'
      INTO rs_return-message.

ENDMETHOD.
