METHOD contracttypeset_get_entityset.

  "----------------------------------------------------------------------
  " Déclaration des variables locales
  "----------------------------------------------------------------------
  DATA: ls_anvsh   TYPE zcl_hr_fiori_offboarding_req=>ty_anvsh,      " Structure source (type contrat)
        ls_return  TYPE zcl_zhrf_offboard_mpc=>ts_contracttype,      " Structure cible (OData)
        lt_anvsh   TYPE zcl_hr_fiori_offboarding_req=>tt_anvsh,      " Table source
        lt_return  TYPE zcl_zhrf_offboard_mpc=>tt_contracttype,      " Table cible
        lo_object  TYPE REF TO zcl_hr_fiori_offboarding_req.         " Instance de la classe métier

  "----------------------------------------------------------------------
  " Étape 1 : Instanciation de la classe métier
  "           (accès centralisé à la logique Offboarding)
  "----------------------------------------------------------------------
  lo_object = zcl_hr_fiori_offboarding_req=>get_instance( ).

  "----------------------------------------------------------------------
  " Étape 2 : Récupération de la liste des types de contrat
  "           via la méthode métier correspondante
  "----------------------------------------------------------------------
  lo_object->get_contract_type(
    IMPORTING
      ot_list = lt_anvsh
  ).

  "----------------------------------------------------------------------
  " Étape 3 : Transformation du format interne vers le format OData
  "----------------------------------------------------------------------
  LOOP AT lt_anvsh INTO ls_anvsh.
    MOVE ls_anvsh-id   TO ls_return-id.
    MOVE ls_anvsh-text TO ls_return-text.
    APPEND ls_return TO lt_return.
  ENDLOOP.

  "----------------------------------------------------------------------
  " Étape 4 : Affectation de la table résultante à l’entityset OData
  "----------------------------------------------------------------------
  et_entityset = lt_return.

ENDMETHOD.
