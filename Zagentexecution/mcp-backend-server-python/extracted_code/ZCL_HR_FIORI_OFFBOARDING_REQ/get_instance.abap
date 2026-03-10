method get_instance.

  "----------------------------------------------------------------------
  " Récupération de l’instance unique (Pattern Singleton)
  "----------------------------------------------------------------------
  " Cette méthode implémente le design pattern Singleton.
  " Elle retourne toujours la même instance de la classe :
  "  - Si l’instance n’existe pas encore, elle est créée.
  "  - Sinon, l’instance existante est simplement renvoyée.
  "----------------------------------------------------------------------

  " Vérifier si une instance existe déjà
  if mo_instance is initial.

    " Créer l’instance si elle n’existe pas encore
    create object mo_instance.

  endif.

  " Retourner l’instance unique
  ro_instance = mo_instance.

endmethod.
