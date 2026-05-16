FUNCTION y_fi_paymedium_101_20.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(I_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"     VALUE(I_FORMAT_PARAMS) LIKE  FPM_SELPAR-PARAM
*"     VALUE(I_FILENAME) LIKE  REGUT-FSNAM
*"     VALUE(I_XFILESYSTEM) TYPE  DFILESYST
*"  TABLES
*"      T_FILE_OUTPUT STRUCTURE  FPM_FILE
*"  CHANGING
*"     REFERENCE(C_FILENAME) LIKE  REGUT-FSNAM
*"  EXCEPTIONS
*"      CANCEL_PAYMENT_MEDIUM
*"----------------------------------------------------------------------


*-----------------------------------------------------------------------
* Creates header record of payment medium format S.W.I.F.T. MT 101
* (sequence A)
* Fields:
*   20  (mandatory) - sender's reference (=payment run refernce RENUM)
*   28D (mandatory) - counter (<paymt. msg. no.> / out of <total>)
*   50L             - payer's identification (name)
*   50H             - payer: bank account, name and address
*   52A or C        - sender - housebank (SWIFT code or address)
*   51A             - initiating instution --- not used
*   30              - expected transaction execution date
*   25              - user authorization (user name)
*-----------------------------------------------------------------------

* Data declarations
  DATA:
    lc_dummy(35)        TYPE c.

  DATA:
    BEGIN OF ls_mt101h,
      20_tag(4)        TYPE c,
      20_value(16)     TYPE c,
      21r_tag(5)       TYPE c,
      21r_value(16)    TYPE c,
      28d_tag(5)       TYPE c,  "counter
      28d_value1(5)    TYPE c,
      28d_value2(6)    TYPE c,
      50l_tag(5)       TYPE c,  "payer
      50l_value(35)    TYPE c,
      50h_tag(5)       TYPE c,
      50h_value1(35)   TYPE c,
      50h_value2_1(35) TYPE c,
      50h_value2_2(35) TYPE c,
      50h_value2_3(35) TYPE c,
      50h_value2_4(35) TYPE c,
      52_tag(5)        TYPE c,
      52_value1(35)    TYPE c,  "party identifier (D/C ind. not used)
      52_value2(35)    TYPE c,
      30_tag(4)        TYPE c,
      30_value(6)      TYPE c,
      25_tag(4)        TYPE c,
      25_value(35)     TYPE c,
      endofprefix      TYPE paymsgn4_fpm,
    END OF ls_mt101h.

  DATA: w_offset TYPE i.


* Read format sepecific selection parameters
  gs_swift = i_format_params.

* Create header record
****** NME DEL 20230214 - Reactivated 20230301
  IF NOT gb_newheader_mt101 IS INITIAL.
    PERFORM z_create_header
            USING    'SOGEXXXXCMI'
                     i_fpayhx-uswif         "SWIFT code of send. bank
                     i_fpayh-hbkid          "Housebank ID
                     '101'                  "SWIFT message type
                     i_fpayhx-dtelz         "Rec. bank (from housebank)
                     i_fpayh-zswif          "SWIFT code of rec. bank
                     i_fpayh-zbnks          "Bank country
                     i_fpayh-zbnky          "Bank key
            CHANGING t_file_output[].       "Output table
  ENDIF.
******

* Fill field 20 (sender's reference)
***  PERFORM fill_field_reference
***          USING    i_fpayhx-renum           "Sender's Reference
***                   ' '                      "Not used
***                   ':20:'                   "Tag
***          CHANGING ls_mt101h-20_tag
***                   ls_mt101h-20_value.
  ls_mt101h-20_tag = ':20:'.
  CONCATENATE 'FR14H819' i_fpayhx-renum+1(7)
    INTO ls_mt101h-20_value.
  PERFORM prepare_string_with_x_chars
          CHANGING ls_mt101h-20_value.

***I_KONAKOV - 28D removed as we don't need it / Reactivated by NME 20220322
* Fill counter (as of SWIFT Nov. 2001)
* message no 00001 out of 00001
  PERFORM fill_field_28
          USING    '1'                      "message number 1
                   '1'                      "out of a total of 1
                   ':28D:'                  "tag
          CHANGING ls_mt101h-28d_tag
                   ls_mt101h-28d_value1
                   ls_mt101h-28d_value2.


***I_KONAKOV - 21R
  ls_mt101h-21r_tag = ':21R:'.
  ls_mt101h-21r_value = i_fpayhx-renum+1(7).
  PERFORM prepare_string_with_x_chars
          CHANGING ls_mt101h-21r_value.
***

***I_KONAKOV - 50L is not used for the time being
** Fill field 50L (ordering customer)
*  SELECT SINGLE * FROM t001 WHERE  bukrs = i_fpayh-zbukr.
*  IF NOT t001-butxt IS INITIAL.
*    PERFORM fill_field_reference
*            USING    t001-butxt             "paying cocode: name
*                     ' '
*                     ':50L:'
*            CHANGING ls_mt101h-50l_tag
*                     ls_mt101h-50l_value.
*    PERFORM prepare_string_with_x_chars
*            CHANGING ls_mt101h-50l_value.
*  ENDIF.


* Fill field 50H (ordering customer)
  PERFORM fill_field_50
          USING    i_fpayhx-ubknt_ext       "Bank account number
                   i_fpayhx-aust1           "issuer name 1
                   i_fpayhx-aust2           "issuer name 2
                   i_fpayhx-aust3           "issuer street
                   i_fpayhx-austo           "issuer city
                   i_fpayh-zbukr            "paying company code
                   i_fpayh-doc1t            "document type
                   i_fpayh-doc1r            "paymt. doc. number
                   ':50H:'
          CHANGING ls_mt101h-50h_tag
                   ls_mt101h-50h_value1
                   ls_mt101h-50h_value2_1
                   ls_mt101h-50h_value2_2
                   ls_mt101h-50h_value2_3
                   ls_mt101h-50h_value2_4.
***I_KONAKOV 04/08/2011 - add control key (request from M.Spronk)
  IF NOT i_fpayhx-ubkon IS INITIAL.
    CLEAR ls_mt101h-50h_value1.
    CONCATENATE '/' i_fpayhx-ubknt_ext i_fpayhx-ubkon INTO ls_mt101h-50h_value1.
    PERFORM prepare_string_with_x_chars CHANGING ls_mt101h-50h_value1.
  ENDIF.
***
***I_KONAKOV - IBAN instead of account if any
  IF NOT i_fpayhx-uiban IS INITIAL.
    CLEAR ls_mt101h-50h_value1.
    CONCATENATE '/' i_fpayhx-uiban INTO ls_mt101h-50h_value1.
    PERFORM prepare_string_with_x_chars CHANGING ls_mt101h-50h_value1.
  ENDIF.
***
  PERFORM prepare_string_with_x_chars
          CHANGING:ls_mt101h-50h_value2_1,
                   ls_mt101h-50h_value2_2,
                   ls_mt101h-50h_value2_3,
                   ls_mt101h-50h_value2_4.

* Fill field 52A or 52C (Ordering institution) optional
  PERFORM fill_bank_field
          USING    ' '                    "Bank account number
                   i_fpayhx-uswif         "ISO Bank Code Identifier
                   ' '                    "Bank name
                   ' '                    "Bank street
                   ' '                    "Bank location
                   ' '                    "Bank region
                   ' '                    "Bank country
                   ' '                    "Bank key
                   i_fpayhx-ubnkl_ext     "National Bank identifier
                   i_fpayhx-ubcod_ext     "National Bank Clearing Code
                   ' '                    "Bank branch
                   '52'                   "Tag of field 52
                   'AC'                   "Allowed options
                   ' '                    "Do not read bank data
                   ' '                    "Application (doc. type)
                   ' '                    "Reference (doc. number)
          CHANGING ls_mt101h-52_tag       "Tag of field 52
                   ls_mt101h-52_value1    "Party identifier
                   ls_mt101h-52_value2    "BIC code
                   lc_dummy               "Not used
                   lc_dummy               "Not used
                   lc_dummy.              "Not used

* Fill field 30 (requested execution date)
  PERFORM fill_field_30
          USING    i_fpayh-ausfd            "Value date
          CHANGING ls_mt101h-30_tag
                   ls_mt101h-30_value.

  PERFORM fill_field_reference
          USING    sy-uname              "User name
                   ' '
                   ':25:'
          CHANGING ls_mt101h-25_tag
                   ls_mt101h-25_value.
  PERFORM prepare_string_with_x_chars
          CHANGING ls_mt101h-25_value.

* Collect fields into output table
  PERFORM fill_output_table
          USING      ls_mt101h              "Formate structure
          CHANGING   t_file_output[].       "Output table


ENDFUNCTION.