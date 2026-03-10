  METHOD filter_process_list.

    CONSTANTS: lc_initiator_ee   TYPE hcmfab_asr_initiator_role VALUE 'HRASRD',
               lc_change_child   TYPE hcmfab_asr_process VALUE 'ZHR_CHANGE_CHILD',
               lc_change_brother TYPE hcmfab_asr_process VALUE 'ZHR_FAMILY_CHANGE_BROTHER',
               lc_change_sister  TYPE hcmfab_asr_process VALUE 'ZHR_FAMILY_CHANGE_SISTER',

               lc_dep_review     TYPE hcmfab_asr_process VALUE 'ZHR_DEP_REVIEW',
               lc_dep_survey     TYPE hcmfab_asr_process VALUE 'ZHR_DEPENDENT_SURVEY',
               lc_second_dep_rev TYPE hcmfab_asr_process VALUE 'ZHR_SECOND_DEPEND_REVIEW',
               lc_spouse         TYPE hcmfab_asr_process VALUE 'ZHR_FAMILY_SPOUSE',
               lc_spouse_un      TYPE hcmfab_asr_process VALUE 'ZHR_SPSE_UN',
               lc_spouse_unesco  TYPE hcmfab_asr_process VALUE 'ZHR_SPSE_UNES'.
*               lc_dependents     TYPE hcmfab_asr_process VALUE 'ZHR_DEPENDENTS_REVIEW'.

    DATA: lv_pernr            TYPE pernr_d,
          lv_usrid            TYPE sysid,
          lf_child            TYPE boolean,
          lf_brother          TYPE boolean,
          lf_sister           TYPE boolean,
          lf_dep_review       TYPE boolean,
          lf_dep_survey       TYPE boolean,
          lf_second_dep_rev   TYPE boolean,
          lf_can_be_requested TYPE boolean,
          lf_spouse           TYPE boolean,
          lt_pa0021           TYPE STANDARD TABLE OF pa0021,
          ls_pa0021           TYPE pa0021,
          lt_pa0021_959       TYPE STANDARD TABLE OF hcmt_bsp_pa_un_r0021,
          ls_pa0021_959       TYPE hcmt_bsp_pa_un_r0021,
          lv_inftybegda       TYPE dats,
          lv_endofyear        TYPE dats,
          ls_current_campaign TYPE zthrfiori_dep_dl,
          lv_depfound         TYPE flag,
          ls_process          TYPE hcmfab_s_process_list ##NEEDED.
*          lv_dat_tmp        TYPE datum.

*   Check if process list for employee is available
    LOOP AT ct_process INTO ls_process
        WHERE initiator_role = lc_initiator_ee.
      EXIT.
    ENDLOOP.
    CHECK sy-subrc = 0.

*   Get personnel number of connect user.
    MOVE iv_userid TO lv_usrid.
    SELECT SINGLE pernr INTO lv_pernr
      FROM pa0105
        WHERE subty = '0001'
          AND endda >= sy-datum
          AND begda <= sy-datum
          AND usrid = lv_usrid ##WARN_OK.

*    -----------------------------------------------------------------------------
*   Filter for child, brother and sister
*    -----------------------------------------------------------------------------
*   Check if the connected user has at least one child, one brother and one sister
    SELECT SINGLE * INTO ls_pa0021
      FROM pa0021
        WHERE pernr = lv_pernr
          AND ( subty = '14' OR subty = '2' )
          AND endda >= sy-datum
          AND begda <= sy-datum ##WARN_OK.
    IF sy-subrc <> 0.
      lf_child = abap_true.
    ENDIF.

    SELECT SINGLE * INTO ls_pa0021
      FROM pa0021
        WHERE pernr = lv_pernr
          AND subty = '6'
          AND endda >= sy-datum
          AND begda <= sy-datum ##WARN_OK.
    IF sy-subrc <> 0.
      lf_brother = abap_true.
    ENDIF.

    SELECT SINGLE * INTO ls_pa0021
     FROM pa0021
       WHERE pernr = lv_pernr
         AND subty = '7'
         AND endda >= sy-datum
         AND begda <= sy-datum ##WARN_OK.
    IF sy-subrc <> 0.
      lf_sister = abap_true.
    ENDIF.


    SELECT SINGLE * INTO ls_current_campaign
      FROM zthrfiori_dep_dl
       WHERE zyear = sy-datum+0(4).

    lv_endofyear = ls_current_campaign-deadline_date.
    lv_endofyear+4(4) = '1231'.

    refresh lt_pa0021_959.
    clear ls_pa0021_959.

    SELECT  *
     FROM pa0021 AS p21
        INNER JOIN pa0959 AS p959
        ON p21~pernr EQ p959~pernr
        AND p21~subty EQ p959~subty
        AND p21~objps EQ p959~objps
        AND p21~begda EQ p959~begda
        AND p21~endda EQ p959~endda
       WHERE p21~pernr = @lv_pernr
         AND (  ( p21~endda BETWEEN @ls_current_campaign-survey_begda
              AND @lv_endofyear )
         OR ( p21~begda BETWEEN @ls_current_campaign-survey_begda
              AND @lv_endofyear )
         OR ( p21~begda <= @lv_endofyear
              AND p21~endda >= @ls_current_campaign-survey_begda ) )
         AND p959~famst <> '3' " différent de divorcé
         AND ( p21~subty = '1' OR p21~subty = '10' OR p21~subty = '11' )
      INTO CORRESPONDING FIELDS OF TABLE @lt_pa0021_959.

    LOOP AT lt_pa0021_959 INTO ls_pa0021_959 WHERE endda >= sy-datum.
      lf_spouse = abap_true.
    ENDLOOP.


* Spouse, Spouse working at UN Org, Spouse working at UNESCO.
    IF lf_spouse = abap_true.
      CASE ls_pa0021_959-famsa.
        WHEN '1'.
          LOOP AT ct_process INTO ls_process
              WHERE initiator_role = lc_initiator_ee
                AND process_id = lc_spouse_un OR process_id = lc_spouse_unesco .
            DELETE ct_process.
          ENDLOOP.
        WHEN '10'.
          LOOP AT ct_process INTO ls_process
              WHERE initiator_role = lc_initiator_ee
                AND process_id = lc_spouse OR process_id = lc_spouse_un .
            DELETE ct_process.
            ENDLOOP.
        WHEN '11'.
          LOOP AT ct_process INTO ls_process
              WHERE initiator_role = lc_initiator_ee
                AND process_id = lc_spouse OR process_id = lc_spouse_unesco .
            DELETE ct_process.
          ENDLOOP.
        WHEN OTHERS.
      ENDCASE.

    ENDIF.
*   Remove some process if no child, brother or sister
    IF lf_child = abap_true.
      LOOP AT ct_process INTO ls_process
        WHERE initiator_role = lc_initiator_ee
          AND process_id = lc_change_child.
        DELETE ct_process.
      ENDLOOP.
    ENDIF.

    IF lf_brother = abap_true.
      LOOP AT ct_process INTO ls_process
        WHERE initiator_role = lc_initiator_ee
          AND process_id = lc_change_brother.
        DELETE ct_process.
      ENDLOOP.
    ENDIF.

    IF lf_sister = abap_true.
      LOOP AT ct_process INTO ls_process
        WHERE initiator_role = lc_initiator_ee
          AND process_id = lc_change_sister.
        DELETE ct_process.
      ENDLOOP.
    ENDIF.

*   -----------------------------------------------------------------------------
*   Filter for processes dependent review
*   -----------------------------------------------------------------------------
*   Check review deadline for current year
    check_deadline_for_dep_review( EXPORTING iv_user_id = sy-uname
                                   IMPORTING ov_can_be_requested = lf_can_be_requested ).

    IF lf_can_be_requested = abap_true.
*     Check if dependents review process exists for current year
      check_yearly_dep_review( EXPORTING iv_pernr = lv_pernr
                                         iv_process = lc_dep_review
                               IMPORTING ov_review_exists = lf_dep_review ).
      check_yearly_dep_review( EXPORTING iv_pernr = lv_pernr
                                         iv_process = lc_dep_survey
                               IMPORTING ov_review_exists = lf_dep_survey  ).
      check_yearly_dep_review( EXPORTING iv_pernr = lv_pernr
                                         iv_process = lc_second_dep_rev
                               IMPORTING ov_review_exists = lf_second_dep_rev ).
    ENDIF.

*   Remove some process if needed
*    IF lf_dep_review = abap_true OR lf_can_be_requested = abap_false.
*      LOOP AT ct_process INTO ls_process
*              WHERE initiator_role = lc_initiator_ee
*                AND process_id = lc_dep_review.
*        DELETE ct_process.
*      ENDLOOP.
*    ENDIF.
*
*    IF lf_dep_survey = abap_true OR lf_can_be_requested = abap_false.
*      LOOP AT ct_process INTO ls_process
*              WHERE initiator_role = lc_initiator_ee
*                AND process_id = lc_dep_survey.
*        DELETE ct_process.
*      ENDLOOP.
*    ENDIF.
*
*    IF lf_second_dep_rev = abap_true OR lf_can_be_requested = abap_false.
*      LOOP AT ct_process INTO ls_process
*              WHERE initiator_role = lc_initiator_ee
*                AND process_id = lc_second_dep_rev.
*        DELETE ct_process.
*      ENDLOOP.
*    ENDIF.

* Vérifier qu'il existe au moins un dependant Jira1604

    SELECT * INTO CORRESPONDING FIELDS OF TABLE lt_pa0021_959
      FROM pa0021 AS p21
            INNER JOIN pa0959 AS p959
            ON p21~pernr EQ p959~pernr
            AND p21~subty EQ p959~subty
            AND p21~objps EQ p959~objps
            AND p21~begda EQ p959~begda
        AND p21~endda EQ p959~endda
        WHERE p21~pernr = lv_pernr
          AND p959~famst <> '3' " différent de divorcé
          AND ( p21~subty = '1' OR p21~subty = '10' OR p21~subty = '11'
                OR p21~subty = '3' OR p21~subty = '4'
                OR p21~subty = '6' OR p21~subty =  '7' )
          AND (  ( p21~endda BETWEEN ls_current_campaign-survey_begda
              AND lv_endofyear )
          OR ( p21~begda BETWEEN ls_current_campaign-survey_begda
              AND lv_endofyear )
          OR ( p21~begda <= lv_endofyear
              AND p21~endda >= ls_current_campaign-survey_begda ) ).

    IF sy-subrc EQ 0.
      LOOP AT lt_pa0021_959 INTO ls_pa0021_959
        WHERE kdgbr IS NOT INITIAL.
        lv_depfound = 'X'.
        EXIT.
      ENDLOOP.
    ENDIF.


*   Remove some process if needed
    IF lf_dep_review = abap_true OR lf_can_be_requested = abap_false OR lv_depfound NE 'X'.
      LOOP AT ct_process INTO ls_process
              WHERE initiator_role = lc_initiator_ee
                AND process_id = lc_dep_review.
        DELETE ct_process.
      ENDLOOP.
    ENDIF.


***Code commenté pour faciliter les tests: à décommenter pour mise en prod
* Filtrer sur la récurrence du process reveiw for dependents

*    lv_dat_tmp = sy-datum - 365.

*    SELECT *
*      INTO TABLE @DATA(lt_proc)
*      FROM t5asrprocesses
*      WHERE object_key EQ @lv_pernr
*        AND ( status EQ 'STARTED' OR status EQ 'CONFIRMED' )
*        AND init_date GE @lv_dat_tmp ##NEEDED.
*
*    IF sy-subrc EQ 0.
*      LOOP AT ct_process INTO ls_process
*        WHERE initiator_role = lc_initiator_ee
*          AND process_id = lc_dependents.
*        DELETE ct_process.
*      ENDLOOP.
*    ENDIF.

  ENDMETHOD.
