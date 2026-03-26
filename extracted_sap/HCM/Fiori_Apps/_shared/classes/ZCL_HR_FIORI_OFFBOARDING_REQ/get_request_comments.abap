method get_request_comments.

  " --------------------------------------------------------------------
  " Déclaration du type pour le mapping étape technique → libellé métier
  " --------------------------------------------------------------------
  types: begin of ty_step_map,
           field_name type string, " Nom technique de l’étape
           step_name  type string, " Libellé fonctionnel
         end of ty_step_map.

  types: tt_step_map type standard table of ty_step_map with default key.

  " --------------------------------------------------------------------
  " Déclaration des variables
  " --------------------------------------------------------------------
  data: lv_guid_raw type ze_hrfiori_guidreq,
        ls_comment  type zstr_comments,
        ls_step_map type ty_step_map.

  data: lt_steps_map       type tt_step_map,
*        lt_req             TYPE STANDARD TABLE OF zthrfiori_dapprv WITH DEFAULT KEY,
        lt_comments_unique type sorted table of zstr_comments
                             with unique key guid step_name.

  " --------------------------------------------------------------------
  " Initialisation du mapping step_name (étapes techniques → libellés métiers)
  " --------------------------------------------------------------------
  clear lt_steps_map.

  ls_step_map-field_name = c_request_init.           ls_step_map-step_name = text-015. "'Request Initiation'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_sep_slwop.              ls_step_map-step_name = text-016. "'Separation / SLWOP Letter'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_sep_staf.               ls_step_map-step_name = text-017. "'Separation Letter Staff'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_sep_oth_parties.        ls_step_map-step_name = text-018. "'Separation SLWOP Other Parties'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_checkout.               ls_step_map-step_name = text-019. "'Checkout progress'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_travel.                 ls_step_map-step_name = text-020. "'Travel'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_shipment.               ls_step_map-step_name = text-021. "'Shipment'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_salary_suspense.        ls_step_map-step_name = text-022. "'Salary Suspense'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_action_rec_iris.        ls_step_map-step_name = text-023. "'Action REC IRIS'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_paf.                    ls_step_map-step_name = text-024. "'PAF'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_closed.                 ls_step_map-step_name = text-025. "'Closed'.
  append ls_step_map to lt_steps_map.
  ls_step_map-field_name = c_cancelled.              ls_step_map-step_name = text-027. "'Cancelled'.
  append ls_step_map to lt_steps_map.


  " --------------------------------------------------------------------
  " Nettoyage préalable du paramètre d’export
  " --------------------------------------------------------------------
  clear et_comments.

  try.
      lv_guid_raw = iv_guid.

      " ------------------------------------------------------------------
      " Lecture des données jointes DAPPRV + REQSTA
      " ------------------------------------------------------------------
      select
            a~guid,
             a~seqno,
             a~date_approval,
             a~comments,
             b~request_init,
             b~sep_slwop,
             b~checkout,
             b~travel,
             b~shipment,
             b~salary_suspense,
             b~closed,
             b~cancelled,
             b~sep_letter_staf,
              b~sep_slwop_oth_parties,
              b~action_rec_iris,
              b~paf,
             b~upd_pernr,
             b~upd_fname,
             b~upd_lname
        from zthrfiori_dapprv as a
        inner join zthrfiori_reqsta as b
          on a~guid = b~guid
         and a~seqno = b~seqno
        into table @data(lt_req)
        where a~guid = @lv_guid_raw .

      " ------------------------------------------------------------------
      " Parcours des étapes pour construire la table de commentaires
      " ------------------------------------------------------------------
      loop at lt_req into data(ls_req).

        loop at lt_steps_map into ls_step_map.

          field-symbols: <fs_field> type any.
          assign component ls_step_map-field_name of structure ls_req to <fs_field>.

          " Si le step est actif
          if sy-subrc = 0 and <fs_field> = 'X'.
            clear ls_comment.
            ls_comment-guid        = ls_req-guid.
            ls_comment-step_name   = ls_step_map-step_name.
            ls_comment-upd_pernr   = ls_req-upd_pernr.
            ls_comment-upd_fname   = ls_req-upd_fname.
            ls_comment-upd_lname   = ls_req-upd_lname.

            " Date et commentaire correspondant au step
            ls_comment-date_approval = ls_req-date_approval.
            ls_comment-comments      = ls_req-comments.

            insert ls_comment into table lt_comments_unique.
          endif.

        endloop.

      endloop.

      " ------------------------------------------------------------------
      " Transfert des résultats vers le paramètre d'export
      " ------------------------------------------------------------------
      et_comments = lt_comments_unique.
      sort et_comments by date_approval descending.

    catch cx_root into data(lx_error).
      message lx_error->if_message~get_text( ) type 'E'.
  endtry.

endmethod.
