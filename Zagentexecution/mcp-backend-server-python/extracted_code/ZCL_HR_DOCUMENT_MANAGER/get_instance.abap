method get_instance.
  "--------------------------------------------------------
  " Pattern Singleton : retourne une instance unique de la classe
  "--------------------------------------------------------

  " Vérifier si l'instance existe déjà
  if mo_instance is initial.
    " Créer une nouvelle instance si elle n'existe pas
    create object mo_instance.
  endif.

  " Retourner l'instance unique
  ro_instance = mo_instance.

endmethod.
