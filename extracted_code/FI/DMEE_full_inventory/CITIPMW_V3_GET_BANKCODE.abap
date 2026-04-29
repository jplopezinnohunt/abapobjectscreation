FUNCTION /citipmw/v3_get_bankcode.
*"----------------------------------------------------------------------
*"*"Global Interface:
*"  IMPORTING
*"     VALUE(I_BANKS) LIKE  BNKA-BANKS
*"     VALUE(I_BANKL) LIKE  BNKA-BNKLZ OPTIONAL
*"     VALUE(I_BANKY) LIKE  BNKA-BANKL OPTIONAL
*"  EXPORTING
*"     VALUE(E_CLCODE)
*"     VALUE(E_BKCODE) TYPE  EDIF1131_A
*"     VALUE(E_ECSIC)
*"  EXCEPTIONS
*"      NO_T005_ENTRY
*"      NO_BNKA_ENTRY
*"----------------------------------------------------------------------

  DATA:
    ls_bnka  LIKE bnka,
    lc_intca LIKE t005-intca,
    li_len   LIKE sy-fdpos.

* Read ISO country code of bank country --------------------------------
  CHECK NOT i_banks IS INITIAL.
  CALL FUNCTION 'COUNTRY_CODE_SAP_TO_ISO'
    EXPORTING
      sap_code = i_banks
    IMPORTING
      iso_code = lc_intca
    EXCEPTIONS
      OTHERS   = 1.
  IF sy-subrc NE 0.
    MESSAGE ID sy-msgid TYPE 'W' NUMBER sy-msgno
            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4
            RAISING no_t005_entry.
  ENDIF.

* If necessary read bank data table ------------------------------------
  IF lc_intca EQ 'US'.                 "bank number only in US needed
    IF i_bankl IS INITIAL AND NOT i_banky IS INITIAL.
      CALL FUNCTION 'READ_BANK_ADDRESS'
        EXPORTING
          bank_country = i_banks
          bank_number  = i_banky
        IMPORTING
          bnka_wa      = ls_bnka
        EXCEPTIONS
          OTHERS       = 4.
      IF sy-subrc NE 0.
        MESSAGE ID sy-msgid TYPE 'W' NUMBER sy-msgno
                WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4
                RAISING no_bnka_entry.
      ELSE.
        i_bankl = ls_bnka-bnklz.
      ENDIF.
    ENDIF.
    CALL FUNCTION 'GET_EXT_BANKACCOUNT_NO'
      EXPORTING
        i_bank_country = i_banks
        i_blz          = i_bankl
      IMPORTING
        e_ext_blz      = i_bankl.
  ENDIF.

* Initialization -------------------------------------------------------
  CLEAR: e_clcode, e_ecsic.
  e_bkcode = '999'.

* Determine bank clearing codes ----------------------------------------
  CASE lc_intca.
    WHEN 'AT'.                          "Austria
      e_clcode = 'AT'.                  "...Austrian Bankleitzahl
      e_bkcode = '014'.
      e_ecsic = 'ATBLZ'.
    WHEN 'AU'.                          "Australia
      e_clcode = 'AU'.                  "...Australian Bank State Branch Code (BSB)
      e_ecsic = 'AUBSB'.
    WHEN 'BE'.                          "Belgium
      e_bkcode = '011'.
    WHEN 'CA'.                          "Canada
      e_clcode = 'CC'.                  "...Canadian Payments Association
      e_ecsic = 'CACPA'.
    WHEN 'CH'.                          "Switzerland
      e_clcode = 'SW'.                  "...Swiss Clearing Code (BC Code)
      e_bkcode = '007'.
      e_ecsic = 'CHBCC'.
    WHEN 'CN'.                          "China
      e_ecsic = 'CNAPS'.                "...CNAPS Identifier
    WHEN 'DE'.                          "Germany
      e_clcode = 'BL'.                  "...German Bankleitzahl
      e_bkcode = '001'.
      e_ecsic = 'DEBLZ'.
    WHEN 'DK'.                          "Denmark
      e_bkcode = '012'.
    WHEN 'ES'.                          "Spain
      e_clcode = 'ES'.                  "...Spanish Domestic Interbanking Code
      e_bkcode = '017'.
      e_ecsic = 'ESNCC'.
    WHEN 'FI'.                          "Finland
      e_bkcode = '010'.
    WHEN 'FR'.                          "France
      e_bkcode = '004'.
    WHEN 'GB'.                          "Great Britain
      e_clcode = 'SC'.                  "...CHAPS Branch Sort Code
      e_bkcode = '013'.
      e_ecsic = 'GBDSC'.                "...UK Domestic Sort Code
    WHEN 'GR'.                          "Greece
      e_ecsic = 'GRBIC'.                "...Helenic Bank Identification Code
    WHEN 'HK'.                          "Hong Kong
      e_ecsic = 'HKNCC'.                "...Hong Kong Bank Code
    WHEN 'IE'.                          "Ireland
      e_clcode = 'SC'.                  "...CHAPS Branch Sort Code
      e_ecsic = 'IENCC'.                "...Irish National Clearing Code
    WHEN 'IN'.                          "India
      e_ecsic = 'INFSC'.                "...Indian Financial System Code
    WHEN 'IT'.                          "Italy
      e_clcode = 'IT'.                  "...Italian Domestic Identification Code
      e_bkcode = '006'.
      e_ecsic = 'ITNCC'.
    WHEN 'JP'.                          "Japan
      e_ecsic = 'JPZGN'.                "...Japan Zengin Clearing Code
    WHEN 'NO'.                          "Norway
      e_bkcode = '009'.
    WHEN 'NZ'.                          "New Zealand
      e_ecsic = 'NZNCC'.                "...New Zealand National Clearing Code
    WHEN 'PL'.                          "Poland
      e_ecsic = 'PLKNR'.                "...Polish National Clearing Code
    WHEN 'PT'.                          "Portugal
      e_ecsic = 'PTNCC'.                "...Portuguese National Clearing Code
    WHEN 'RU'.                          "Russia
      e_ecsic = 'RUCBC'.                "...Russian Central Bank Identification Code
    WHEN 'SE'.                          "Sweden
      e_bkcode = '005'.                 "...Sweden Bankgiro Clearing Code
      e_ecsic = 'SESBA'.
    WHEN 'SG'.                          "Singapore
      e_ecsic = 'SGIBG'.                "...IBG Sort Code
    WHEN 'TW'.                          "Taiwan
      e_ecsic = 'TWNCC'.                "...Financial Institution Code
    WHEN 'ZA'.                          "South Africa
      e_ecsic = 'ZANCC'.                "...South African National Clearing Code
    WHEN 'US'.                          "USA
      li_len = STRLEN( i_bankl ).
      CASE li_len.
        WHEN 9.                         "...Fedwire Routing Number
          e_clcode = 'FW'.
          e_bkcode = '003'.
          e_ecsic = 'USABA'.
        WHEN 6.                         "...CHIPS Universal Identifier
          e_clcode = 'CH'.
          e_bkcode = '015'.
        WHEN 4.                         "...CHIPS Participant Code
          e_clcode = 'CP'.
          e_bkcode = '016'.
          e_ecsic = 'USPID'.
      ENDCASE.
  ENDCASE.

ENDFUNCTION.