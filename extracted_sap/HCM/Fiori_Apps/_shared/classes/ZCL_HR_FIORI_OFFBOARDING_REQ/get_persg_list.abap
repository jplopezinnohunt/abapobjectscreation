method get_persg_list.

  " --------------------------------------------------------------------
  " Déclaration des variables locales
  " --------------------------------------------------------------------
  data: ls_return type ty_persg,                 " Structure temporaire pour chaque entrée
        ls_t501t  type t501t,                   " Structure de la table T501T
        lt_return type tt_persg,                " Table interne résultat (persg + texte)
        lt_t501t  type standard table of t501t. " Table interne pour stocker les enregistrements T501T

  " --------------------------------------------------------------------
  " Lecture des données T501T filtrées par langue de l’utilisateur
  " --------------------------------------------------------------------
  select t501t~*
    into table @lt_t501t
    from t501t INNER JOIN ZTHR_OFFB_PERSG ON  t501t~persg EQ ZTHR_OFFB_PERSG~persg
    where sprsl = @sy-langu.                     " Filtre sur la langue système

  " --------------------------------------------------------------------
  " Parcours des enregistrements T501T pour construire la table de sortie
  " --------------------------------------------------------------------
  loop at lt_t501t into ls_t501t.
    ls_return-id   = ls_t501t-persg.          " Code du groupe de personnel
    ls_return-text = ls_t501t-ptext.          " Libellé du groupe de personnel

    " Ajout de l’entrée dans la table interne résultat
    append ls_return to lt_return.
  endloop.

  " --------------------------------------------------------------------
  " Transfert de la table interne vers le paramètre d’export
  " --------------------------------------------------------------------
  ot_list = lt_return.

endmethod.
