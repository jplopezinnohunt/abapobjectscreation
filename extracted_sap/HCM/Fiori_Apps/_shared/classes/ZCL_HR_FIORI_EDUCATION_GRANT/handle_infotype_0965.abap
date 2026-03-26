    METHOD handle_infotype_0965.

      DATA: lv_locking_user TYPE syst_uname ##NEEDED,
            lv_text_coments TYPE string,
            ls_p0965        TYPE p0965,
            ls_req          TYPE zthrfiori_breq,
            ls_info_advs    TYPE zthr_eg_advance,
            ls_info_att     TYPE zthr_eg_attend,
            ls_info_child   TYPE zthr_eg_child,
            ls_info_claims  TYPE zthr_eg_claim,
            ls_info_elig    TYPE zthr_eg_eligib,
            ls_info_entl    TYPE zthr_eg_entitl,
            ls_info_otherc  TYPE zthr_eg_othercom,
            ls_info_school  TYPE zthr_eg_school,
            ls_infty        TYPE p0965,
            ls_return       TYPE bapireturn1,
            ls_key          TYPE bapipakey ##NEEDED,
            ls_adv_claim    TYPE t7unpad_egexpmgt,
            ls_split        TYPE swastrtab,
            ls_text         TYPE hrpad_text,
            ls_pskey        TYPE pskey,
            lt_p0965        TYPE STANDARD TABLE OF p0965,
            lt_info_advs    TYPE STANDARD TABLE OF zthr_eg_advance,
            lt_info_claims  TYPE STANDARD TABLE OF zthr_eg_claim,
            lt_adv_claim    TYPE STANDARD TABLE OF t7unpad_egexpmgt,
            lt_split        TYPE STANDARD TABLE OF swastrtab,
            lt_text         TYPE hrpad_text_tab,
            lo_util         TYPE REF TO cl_hrpao_data_transfer_0965.

*   ----------------------------------------------------------------
*   01 - CREATE INFOTYPE 0965
*   ----------------------------------------------------------------
*   Get request and all infotype information

      SELECT SINGLE * INTO ls_req
        FROM zthrfiori_breq
          WHERE guid = iv_guid.

      IF ls_req-request_status EQ c_req_submited_employee_claims. ##TODO "Uniformiser toutes les constants au seins de la meme classe Constnat à créer
**********************************************  **********************************************  **********************************************
**********************************************  Infotype Update  *****************************************************************************
**********************************************  **********************************************  **********************************************
        CLEAR : lt_p0965,ls_p0965.
        REFRESH : lt_p0965.
        "read existing infotype
        CALL FUNCTION 'HR_READ_INFOTYPE'
          EXPORTING
            pernr     = ls_req-creator_pernr
            infty     = '0965'
            begda     = ls_req-begda
            endda     = ls_req-endda
          TABLES
            infty_tab = lt_p0965.
        LOOP AT lt_p0965 INTO ls_p0965
          WHERE subty = ls_req-subty
            AND objps = ls_req-objps.
          EXIT.
        ENDLOOP.

        CLEAR: ls_adv_claim, lt_adv_claim[].
        SELECT * INTO TABLE lt_info_claims
            FROM zthr_eg_claim
              WHERE request_guid = iv_guid.


        LOOP AT lt_info_claims INTO ls_info_claims.
          MOVE-CORRESPONDING ls_info_claims TO ls_adv_claim ##ENH_OK.

          ls_adv_claim-egpyt = 'CLM'.

          ls_adv_claim-pernr = ls_p0965-pernr.
          ls_adv_claim-infty = ls_p0965-infty.
          ls_adv_claim-subty = ls_p0965-subty.
          ls_adv_claim-objps = ls_p0965-objps.
          ls_adv_claim-seqnr = ls_p0965-seqnr.
          ls_adv_claim-begda = ls_p0965-begda.
          ls_adv_claim-endda = ls_p0965-endda.
          IF ls_adv_claim-exdat IS INITIAL.
            ls_adv_claim-exdat = |{ sy-datum(6) }16|.
          ENDIF.
          APPEND ls_adv_claim TO lt_adv_claim.

        ENDLOOP.
        IF lt_adv_claim[] IS  NOT INITIAL.
          CREATE OBJECT lo_util.

          lo_util->save_adv_clm_data( EXPORTING iv_advclm = lt_adv_claim
                                                iv_p0965  = ls_p0965
                                                iv_flag   = 'CLM' ).
          COMMIT WORK.
          FREE lo_util.
        ENDIF.



      ELSE.

**********************************************  **********************************************  **********************************************
**********************************************  Infotype Creation  ***************************************************************************
**********************************************  **********************************************  **********************************************

*--- Begin (+) si / 24.09.2025 : Select replacement - One Main table
        SELECT SINGLE * FROM zthrfiori_eg_mai
          INTO  @DATA(ls_eg_main)
           WHERE guid EQ @iv_guid.
        ls_infty = CORRESPONDING #( ls_eg_main ).
        ls_info_otherc = CORRESPONDING #( ls_eg_main MAPPING line1 = text1 line2 = text2 line3 = text3  ).
        "Trasnco de TEXT2 pour stocker le texte et non la key du domaine
        "Lecture des valeurs du domaine
        cl_reca_ddic_doma=>get_values( EXPORTING id_name   = 'ZD_HRFIORI_CURRPAY'
*                                             id_langu = 'E'
                                      IMPORTING et_values = DATA(lt_rsdomaval) ).

        IF line_exists( lt_rsdomaval[ domvalue_l = ls_info_otherc-line1 ] ).
          ls_info_otherc-line1 =  lt_rsdomaval[ domvalue_l = ls_info_otherc-line1 ]-ddtext .
        ENDIF.

*--- End (+) SI / 24.09.2025 : Select replacement - One Main table

*--- Begin (-) Deactivated SI / 24.09.2025 : One Main table
*    SELECT SINGLE * INTO ls_info_att
*      FROM zthr_eg_attend
*        WHERE guid = iv_guid.
*    SELECT SINGLE * INTO ls_info_child
*      FROM zthr_eg_child
*        WHERE guid = iv_guid.
*    SELECT SINGLE * INTO ls_info_elig
*      FROM zthr_eg_eligib
*        WHERE guid = iv_guid.
*    SELECT SINGLE * INTO ls_info_entl
*      FROM zthr_eg_entitl
*        WHERE guid = iv_guid.
*    SELECT SINGLE * INTO ls_info_otherc
*      FROM zthr_eg_othercom
*        WHERE guid = iv_guid.
*    SELECT SINGLE * INTO ls_info_school
*      FROM zthr_eg_school
*        WHERE guid = iv_guid.

*--- End (-) Deactivated SI / 24.09.2025 : One Main table

        SELECT * INTO TABLE lt_info_advs
          FROM zthr_eg_advance
            WHERE request_guid = iv_guid.
        SELECT * INTO TABLE lt_info_claims
          FROM zthr_eg_claim
            WHERE request_guid = iv_guid.

*   Check if there is text (tab Others in infotype screen)
        IF ls_info_otherc-line1 IS  NOT INITIAL OR ls_info_otherc-line2 IS  NOT INITIAL OR ls_info_otherc-line3 IS  NOT INITIAL.
          ls_infty-itxex = abap_true.
        ENDIF.

        ls_infty-pernr = ls_req-creator_pernr.
        ls_infty-infty = '0965'.
        ls_infty-subty = ls_req-subty.
        ls_infty-famsa = ls_req-subty.
        ls_infty-objps = ls_req-objps.
        ls_infty-seqnr = ls_req-seqnr.
        ls_infty-begda = ls_req-begda.
        ls_infty-endda = ls_req-endda.

*   Lock employee folder
        CALL FUNCTION 'HR_EMPLOYEE_ENQUEUE'
          EXPORTING
            number       = ls_infty-pernr
          IMPORTING
            return       = ls_return
            locking_user = lv_locking_user.

        IF ls_return-type = 'E'.
          ov_return_code = 4.
          MESSAGE ID ls_return-id TYPE ls_return-type NUMBER ls_return-number
            INTO ov_message.

          RETURN.
        ENDIF.

*   Create infotype
        CALL FUNCTION 'HR_INFOTYPE_OPERATION'
          EXPORTING
            infty         = '0965'
            number        = ls_infty-pernr
            subtype       = ls_infty-subty
*           OBJECTID      =
*           LOCKINDICATOR =
            validityend   = ls_infty-endda
            validitybegin = ls_infty-begda
*           RECORDNUMBER  =
            record        = ls_infty
            operation     = 'INS'
*           TCLAS         = 'A'
*           DIALOG_MODE   = '2'
            nocommit      = iv_no_commit
*           VIEW_IDENTIFIER        =
*           SECONDARY_RECORD       =
          IMPORTING
            return        = ls_return
            key           = ls_key.

        IF ls_return-type = 'E'.
          ov_return_code = 4.
          MESSAGE ID ls_return-id TYPE ls_return-type NUMBER ls_return-number
            WITH ls_return-message_v1 ls_return-message_v2
                 ls_return-message_v3 ls_return-message_v4
            INTO ov_message.

          RETURN.
        ENDIF.

*   Unlock employee folder
        CALL FUNCTION 'HR_EMPLOYEE_DEQUEUE'
          EXPORTING
            number = ls_infty-pernr
          IMPORTING
            return = ls_return.

        IF ls_return-type = 'E'.
          ov_return_code = 4.
          MESSAGE ID ls_return-id TYPE ls_return-type NUMBER ls_return-number
            INTO ov_message.

          RETURN.
        ENDIF.

*   If no commit parameter is set, we don't perform following updates
        IF iv_no_commit = abap_false.

*   ----------------------------------------------------------------
*   02 - GET CREATED INFOTYPE 0965 FOR NEXT OPERATIONS
*   ----------------------------------------------------------------
*     Get created infotype
          CALL FUNCTION 'HR_READ_INFOTYPE'
            EXPORTING
              pernr     = ls_infty-pernr
              infty     = '0965'
              begda     = ls_infty-begda
              endda     = ls_infty-endda
            TABLES
              infty_tab = lt_p0965.
          LOOP AT lt_p0965 INTO ls_p0965
            WHERE subty = ls_infty-subty
              AND objps = ls_infty-objps.
            EXIT.
          ENDLOOP.

*   ----------------------------------------------------------------
*   03 - SAVE ADVANCE DATA
*   ----------------------------------------------------------------
*     Save advances
          CLEAR: ls_adv_claim, lt_adv_claim[].
          LOOP AT lt_info_advs INTO ls_info_advs.
            MOVE-CORRESPONDING ls_info_advs TO ls_adv_claim ##ENH_OK.

            ls_adv_claim-egpyt = 'ADV'.

            ls_adv_claim-pernr = ls_p0965-pernr.
            ls_adv_claim-infty = ls_p0965-infty.
            ls_adv_claim-subty = ls_p0965-subty.
            ls_adv_claim-objps = ls_p0965-objps.
            ls_adv_claim-seqnr = ls_p0965-seqnr.
            ls_adv_claim-begda = ls_p0965-begda.
            ls_adv_claim-endda = ls_p0965-endda.
            IF ls_adv_claim-exdat IS INITIAL.
              ls_adv_claim-exdat = |{ sy-datum(6) }16|.
            ENDIF.
            APPEND ls_adv_claim TO lt_adv_claim.

          ENDLOOP.
          IF lt_adv_claim[] IS  NOT INITIAL.
            CREATE OBJECT lo_util.

            lo_util->save_adv_clm_data( EXPORTING iv_advclm = lt_adv_claim
                                                  iv_p0965  = ls_p0965
                                                  iv_flag   = 'ADV' ).
            COMMIT WORK.
            FREE lo_util.
          ENDIF.

*   ----------------------------------------------------------------
*   04 - SAVE CLAIMS DATA
*   ----------------------------------------------------------------
*     Save claims
          CLEAR: ls_adv_claim, lt_adv_claim[].
          LOOP AT lt_info_claims INTO ls_info_claims.
            MOVE-CORRESPONDING ls_info_claims TO ls_adv_claim ##ENH_OK.

            ls_adv_claim-egpyt = 'CLM'.

            ls_adv_claim-pernr = ls_p0965-pernr.
            ls_adv_claim-infty = ls_p0965-infty.
            ls_adv_claim-subty = ls_p0965-subty.
            ls_adv_claim-objps = ls_p0965-objps.
            ls_adv_claim-seqnr = ls_p0965-seqnr.
            ls_adv_claim-begda = ls_p0965-begda.
            ls_adv_claim-endda = ls_p0965-endda.
            IF ls_adv_claim-exdat IS INITIAL.
              ls_adv_claim-exdat = |{ sy-datum(6) }16|.
            ENDIF.
            APPEND ls_adv_claim TO lt_adv_claim.

          ENDLOOP.
          IF lt_adv_claim[] IS  NOT INITIAL.
            CREATE OBJECT lo_util.

            lo_util->save_adv_clm_data( EXPORTING iv_advclm = lt_adv_claim
                                                  iv_p0965  = ls_p0965
                                                  iv_flag   = 'CLM' ).
            COMMIT WORK.
            FREE lo_util.
          ENDIF.

*   ----------------------------------------------------------------
*   05 - SAVE TEXTS IN CLUSTER (INFOTYPE TEXTS)
*   ----------------------------------------------------------------
          IF ls_p0965-itxex = abap_true.
*       Save texts (tab Others in infotype screen)
*       Concatenate all texts in  one string
            CONCATENATE ls_info_otherc-line1 ls_info_otherc-line2 ls_info_otherc-line3
              INTO lv_text_coments.
*       Split the string into a table of field of 78 characters (cluster constraints)
            CALL FUNCTION 'SWA_STRING_SPLIT'
              EXPORTING
                input_string         = lv_text_coments
                max_component_length = '78'
              TABLES
                string_components    = lt_split.

            LOOP AT lt_split INTO ls_split.
              ls_text = ls_split-str.
              APPEND ls_text TO lt_text.
            ENDLOOP.

            MOVE-CORRESPONDING ls_p0965 TO ls_pskey.

            TRY.
                CALL METHOD cl_hrpa_text_cluster=>update
                  EXPORTING
                    tclas         = 'A'
                    pskey         = ls_pskey
                    histo         = space
*                   uname         = sy-uname
*                   aedtm         = sy-datum
                    pgmid         = space
                    text_tab      = lt_text
                    no_auth_check = abap_true.
            ENDTRY.
          ENDIF.

        ENDIF.


      ENDIF.



    ENDMETHOD.


*--- Begin (-) Deactivated SI / 24.09.2025 : One Main table
**   Prepare infotype data
*    MOVE-CORRESPONDING ls_info_att TO ls_infty ##ENH_OK ##NEEDED.
*    MOVE-CORRESPONDING ls_info_child TO ls_infty ##ENH_OK.
*    MOVE-CORRESPONDING ls_info_elig TO ls_infty ##ENH_OK.
*    MOVE-CORRESPONDING ls_info_entl TO ls_infty ##ENH_OK ##NEEDED.
*    MOVE-CORRESPONDING ls_info_school TO ls_infty ##ENH_OK.
*--- End (-) Deactivated SI / 24.09.2025 : One Main table


**   Temporary soution for demo
*    IF ls_infty-exmnr IS INITIAL.
*      ls_infty-exmnr = '6715'.
*    ENDIF.
*    IF ls_infty-egtyp IS INITIAL.
*      ls_infty-egtyp = '0004'.
*    ENDIF.
**      ls_infty-EGYEA
*    IF ls_infty-egyfr IS INITIAL.
*      ls_infty-egyfr = ls_infty-begda.
*    ENDIF.
*    IF ls_infty-egyto IS INITIAL.
*      ls_infty-egyto = ls_infty-endda.
*    ENDIF.
*    ls_infty-egcst = ls_infty-egsst = ''.
*    ls_infty-preas = '50'.
*    ls_infty-egc01 = 'X'.
*    ls_infty-egbrs = '01'.
*    IF ls_infty-egcur IS INITIAL.
*      ls_infty-egcur = 'USD'.
*    ENDIF.
*    IF ls_infty-egsct IS INITIAL.
*      ls_infty-egsct = 'US'.
*    ENDIF.
*    IF ls_infty-ort01 IS INITIAL.
*      ls_infty-ort01 = 'NEW YORK'.
*    ENDIF.
*    IF ls_infty-egfac IS INITIAL.
*      ls_infty-egfac = '28.22'.
*    ENDIF.
*    IF ls_infty-eggrd IS INITIAL.
*      ls_infty-eggrd = '0010'.
*    ENDIF.
*    IF ls_infty-egssl IS INITIAL.
*      ls_infty-egssl = '10000017'.
*    ENDIF.
*    IF ls_infty-egc01 IS INITIAL.
*      ls_infty-egc01 = 'X'.
*    ENDIF.
**      ls_infty-EGADV VERSION
*    IF ls_infty-egrcd IS INITIAL.
*      ls_infty-egrcd = '20270221'.
*    ENDIF.
**      ls_infty-EGRIN
*    IF ls_infty-egsna IS INITIAL.
*      ls_infty-egsna = 'BRONX COMMUNITY COLLEGE'.
*    ENDIF.
*    IF ls_infty-egbrs IS INITIAL.
*      ls_infty-egbrs = '01'.
*    ENDIF.
*    IF ls_infty-egbsg IS INITIAL.
*      ls_infty-egbsg = 100.
*    ENDIF.
*    IF ls_infty-trfgr IS INITIAL.
*      ls_infty-trfgr = 'P-5'.
*    ENDIF.
*    IF ls_infty-trfst IS INITIAL.
*      ls_infty-trfst = '02'.
*    ENDIF.
*    IF ls_infty-egsty IS INITIAL.
*      ls_infty-egsty = '2'.
*    ENDIF.
**      ls_infty-EGLIN
*    IF ls_infty-tuition_waers IS INITIAL.
*      ls_infty-tuition_waers = 'USD'.
*    ENDIF.
**      ls_infty-EXTADV
*
*
*
*    ls_infty-elibegda = '20250922'.
*    ls_infty-eliendda = '20260102'.
*      ls_infty-EGBPR
*      ls_infty-CAFFACd
