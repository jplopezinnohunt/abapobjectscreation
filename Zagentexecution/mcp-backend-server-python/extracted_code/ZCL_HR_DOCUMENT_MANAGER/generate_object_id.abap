METHOD generate_object_id.

  "--------------------------------------------------------
  " Génère un object_id unique à partir de la request_id et du doc_type
  "--------------------------------------------------------
  DATA lv_concat TYPE string.
  DATA lv_hash   TYPE string.

  " Concaténation des informations pour former la base du hash
  lv_concat = |{ iv_request_id }_{ iv_doc_type }|.

  " Génération d'un hash SHA1 pour éviter les doublons
  CALL FUNCTION 'CALCULATE_HASH_FOR_CHAR'
    EXPORTING
      alg  = 'SHA1'    " Algorithme SHA1
      data = lv_concat
    IMPORTING
      hashstring = lv_hash.

  " Limiter à 20 caractères pour respecter la taille maximale
  rv_object_id = lv_hash(20).

ENDMETHOD.
