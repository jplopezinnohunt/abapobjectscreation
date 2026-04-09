* 6.06
* MAWH1492437   28072010 Erweiterte Programmprüfung im RPRAPA00: Warnung
*                        [note 1492437]

* 6.05
* GLWE38K104726 05102009 empty region in infotype and vendor master(1390608)
* PJN P7DK159028 Print parameters are ignored in RPRAPA00 in background job[1355243]
* KCNEB5K021736  23022009 RPRAPA00: Fehlermeldung 56_CORE 313 bei
*                        Variantenpflege [note 1309755]

* MAWEB5K015766 02022009 RPRAPA00: Auswahl des Infotyps / Subtyps
*                        [note 1300833]
* MAWEB5K003005 29102008 RPRAPA00: Fehlerhaftes Protokoll
*                        [note 1267636]
* 6.04 EHCP 04
* MAWE4AK022558 10042008 Verhalten bei Fehlern im Testlauf [1159536]
* KCNE4AK011667 08022008 RPRAPA00: Building Society Roll No
*                        [note 1140291]

* 6.03 EHCP 03
* MAWE38K015825 02082007 RPRAPA00: Fehler beim Abspielen der Batch-Input
*                        Mappe [note 1080713]
* 7.00
* MAWPR0K013477 03112006 RPRAPA00: Probleme bei Komponentennamen > 10
*                        Zeichen [note 995726]
* 4.70 Hot Package
* MAWP6BK120174 02122003 RPRAPA00: Probleme mit Zahlweg "Barauszahlung"
*                        im IT0009 (note 686408)
* KCNP6BK107280 22092003 RPRAPA00: Straßenname hat mehr als 40 Zeichen
*                        [note 663350]
* MAWP6BK100720 19082003 RPRAPA00 (note 652443)
* KCNP6BK050331 17122002 RPRAPA00 (note 582037)
* QIZP6BK002047 04062002 problems with BLFBK-STRAS [note 524717]
* 4.70
* QIZPL0K032746 02052002 daily run of RPRAPA00...
* QIZPL0K023533 12042002 MOLGA replaced by COUNTRY...
* QIZPL0K001223 21022002 RPRAPA00 im Core lauffähig gemacht
* QIZPL0K004145 21022002 problems with QIZP9CK113008
* QIZAL0K052366 21092001 P0009-BKREF implemented
* WKUAL0K039333 02082001 Nachkorrektur zu QIZP9CK053703
* QIZAL0K033506 12072001 Unicode
* 4.6C Hot Package
* QIZP9CK145479 26032001 problems with BLFBK-KOINH
* QIZP9BK141582 15032001 K113008 corrected
* QIZP9CK113008 11012001 problems with field LFB1-ZWELS
* QIZP9CK113008 11012001 problems with special format in P0002.
* QIZP9CK082452 13102000 create company code segments
* QIZP9CK079153 04102000 problems with P0001
* QIZP9CK053440 wrong message
* QIZP9CK052561 tax number from P0002-PERID.
* QIZP9CK047575 withholding tax data implemented
* QSCP9CK030037 08052000 BLFA1-STCD1 if filled with ' '.
* QIZP9CK001068 25022000 No Short Dump when 'Job_Close_Failed'.
* 4.6C
* QIZALRK225798 21071999 No TXJCD from template vendor to vendor
* 4.6A
* QIZP99K026920 21051999 Tax number for spain
* QIZP99K025968 21051999 Phone number for US and CA corrected
* WKUPH9K011046 03051999 Nachkorr. Hw.53125 Mahndaten nicht beim Sperren
* QSCALRK168532 14011999 Wrong creation of the street name if initial
* QIZALRK159798 09121998 Now delete bank before insert bank
* YLOPH4K023536 30101998 Fill vendor with p0002-sprsl instead sy-langu
* QIZAHRK026802 15101998 City code for Belgium corrected.
* 4.5A
* QIZPH4K012820 10071998 PME11 completed
* QIZPH4K001005 28051998 Transfer of Bank data improved
* QIZPH4K000174 26051998 RPRAPA00 and RFBIKR00 always on one server

* FORM-Routinen des RPRAPA00

*---------------------------------------------------------------------*
*       FORM CREATE_FILE_A_P                                          *
*---------------------------------------------------------------------*
FORM create_file_a_p.
  TABLES: p0062.                                            "QIZK026920
  DATA: p0002_perid LIKE p0062-codim.                       "QIZK026920
  CLEAR: blfa1, blfb1, blfbk, blfb5, blfm1.
  CLEAR: blfbw.                                             "QIZK047575
* Kred. Batch-Input-Kopfsatz
  PERFORM nodata_in_structure USING 'BLF00' nodata.
  blf00-stype = '1'.
  blf00-tcode = t_code.                "A/P_account create/change/lock
  IF t_code NE 'XK01'.
    blf00-lifnr = lfb1-lifnr.
  ELSE.                                                     "QIZK082452
* XK01...                                                   "QIZK082452
    IF NOT vendor_no IS INITIAL.                            "QIZK082452
      blf00-lifnr = vendor_no.                              "QIZK082452
*      PERFORM check_external_assignment.                    " GLW note 2614599
    ELSE.                                                   "QIZK082452
* do nothing or set vendor number via user-exit             "QIZK082452
      PERFORM set_vendor_no_by_user.                        "QIZK082452
*      PERFORM check_external_assignment.                    " GLW note 2614599
    ENDIF.
  ENDIF.
  blf00-bukrs = p0001-bukrs.           "company code
  blf00-ktokk = *lfa1-ktokk.           "template account group

* HASK036614
  CALL METHOD user_exit->set_values_for_blf00
    EXPORTING
      i_pernr = p0001-pernr
    CHANGING
      c_blf00 = blf00.
* HASK036614 end

   PERFORM check_external_assignment.    "GLW note 3034585

* file_k = blf00.                                           "MAWH1492437
  PERFORM move_struct_to_file USING blf00                   "MAWH1492437
                                    'BLF00'                 "MAWH1492437
                           CHANGING file_k.                 "MAWH1492437
  PERFORM write_file USING '1' file_k space space.
  TRANSFER file_k TO file_o.
  IF vendor_no IS INITIAL.                                  "QIZK082452
* Kred. Allgemein Teil 1
    PERFORM nodata_in_structure USING 'BLFA1' nodata.
    blfa1-stype = '2'.
    blfa1-tbnam = 'BLFA1'.
    IF t_code EQ 'XK01' OR t_code EQ 'XK02'.
* only create-mode, change-mode and refresh-mode
      PERFORM find_anred USING blfa1-anred.
* QIZK113008 begin...
      IF NOT p0002-knznm IS INITIAL.
* there is a special rule... Contains P0001-ENAME the form of address?
        IF p0001-ename CS blfa1-anred.
          IF t_code EQ 'XK01'.
            blfa1-anred = nodata.
          ELSE.
            CLEAR blfa1-anred.
          ENDIF.
        ENDIF.
      ENDIF.
* QIZK113008 end...
      IF ps_master_data_active IS INITIAL.                  "QIZK101633
        blfa1-name1 = p0001-ename.
        IF t500p-molga EQ '22'.
* Japan: name of the owner of the bank account in BLFA1-NAME3
          blfa1-name3 = p0001-sname.
        ENDIF.
      ELSE.                                                 "QIZK101633
        blfa1-pson1 = p0002-nachn.                          "QIZK101633
        blfa1-psovn = p0002-vorna.                          "QIZK101633
        blfa1-psotl = p0002-titel.                          "QIZK101633
      ENDIF.                                                "QIZK101633
      blfa1-sortl = p0002-nachn.
* Sortfield via user-exit
      PERFORM set_mc_field_by_user."Sortfield via user-exit
      blfa1-pstlz = p0006-pstlz.
      IF t500p-molga EQ '22'.
* Japan: the japanese adress will be transferred in the same order
* as in P0006:
        IF adr_kana IS INITIAL.
          blfa1-stras = p0006-ort01.
          blfa1-ort01 = p0006-ort02.
          blfa1-ort02 = p0006-stras.
        ELSE.
          blfa1-stras = p0006-or1kk.
          blfa1-ort01 = p0006-or2kk.
          blfa1-ort02 = p0006-locat.
        ENDIF.
      ELSE.
        blfa1-ort01 = p0006-ort01.
        IF p0006-ort02 IS NOT INITIAL OR old_vendor_lfa1-ort02 IS NOT INITIAL. "GLWE38K104726
          blfa1-ort02 = p0006-ort02.
        ENDIF.
        PERFORM create_street USING blfa1-stras.
      ENDIF.
*      PERFORM set_address_by_user."Address by user-exit  " GLW note 2622798: remove the call; it's too early
      blfa1-land1 = p0006-land1.
      IF p0006-state IS NOT INITIAL OR old_vendor_lfa1-regio IS NOT INITIAL. "GLWE38K104726
        blfa1-regio = p0006-state.
      ENDIF.
      blfa1-telf1 = p0006-telnr.
*   blfa1-spras = sy-langu.                                 "YLOK023536
      blfa1-spras = p0002-sprsl.                            "YLOK023536

*   IF T500P-MOLGA EQ '04'.                     "QIZK026920 "QIZK052561
      CASE t500p-molga.                                     "QIZK052561
        WHEN '04'.                                          "QIZK052561
* for Spain...
          CALL FUNCTION 'HR_E_CONVERT_PERID_IN_CODIM'       "QIZK026920
            EXPORTING                                    "QIZK026920
              perid  = p0002-perid                   "QIZK026920
            IMPORTING                                    "QIZK026920
              codim  = p0002_perid                   "QIZK026920
*             PERTR  =                                 "QIZK026920
            EXCEPTIONS                                   "QIZK026920
              error  = 1                             "QIZK026920
              OTHERS = 2.                            "QIZK026920
*   ENDIF.                                                  "QIZK026920
          IF sy-subrc IS INITIAL.                           "QIZK026920
            IF NOT p0002_perid IS INITIAL.                  "QIZK052561
              blfa1-stcd1 = p0002_perid.                    "QIZK026920
            ENDIF.                                          "QIZK052561
          ENDIF.                                            "QIZK026920
        WHEN '15'.                                          "QIZK052561
* for Italy...                                              "QIZK052561
          IF NOT p0002-perid IS INITIAL.                    "QIZK052561
            blfa1-stcd1 = p0002-perid(16).                  "QIZK052561
            blfa1-stkzn = 'X'.                              "QIZK052561
          ENDIF.                                            "QIZK052561
        WHEN '33'.                                          "VRD 2301531
* for Russia...
  DATA:   lv_pnumc(2) TYPE n.                               "VRD 2801904
          IF NOT p0002-perid IS INITIAL.
            lv_pnumc = strlen( p0002-perid ).
            IF lv_pnumc > 16. lv_pnumc = 16. ENDIF.
            blfa1-stcd1 = p0002-perid(lv_pnumc).
            blfa1-stkzn = 'X'.
          ENDIF.
        WHEN '36'.
* for UA...
          IF NOT p0002-perid IS INITIAL.
            blfa1-stcd2 = p0002-perid.
            blfa1-stkzn = 'X'.
          ENDIF.
        WHEN OTHERS.                                        "QIZK052561
* for all other countries...                                "QIZK052561
*   ENDIF.                                   "QSCP9CK030037 "QIZK052561
      ENDCASE.                                              "QIZK052561

      PERFORM set_address_by_user."Address by user-exit  "GLW note 2622798: place the call here

* HASK036614
      CALL METHOD user_exit->set_values_for_blfa1
        EXPORTING
          i_pernr = p0002-pernr
        CHANGING
          c_blfa1 = blfa1.
* HASK036614 end

*     file_k = blfa1.                                       "MAWH1492437
      PERFORM move_struct_to_file USING blfa1               "MAWH1492437
                                        'BLFA1'             "MAWH1492437
                               CHANGING file_k.             "MAWH1492437
      PERFORM write_file USING '2' file_k space space.
      TRANSFER file_k TO file_o.
    ENDIF.
* Kred. Bankverbindung
    IF t_code EQ 'XK01' OR t_code EQ 'XK02'.

* QIZ Löschen der alten Bankverbindung wieder nach vorne verlegt
* eventuelle Pflichtfelder werden von Marcela abgefangen!
* QIZALRK159798 begin
*      PERFORM delete_old_bank_data USING old_vendor_lfb1-lifnr.  "Note 1555565 part 4
* QIZALRK159798 end

* ARIK142351 begin / Note 1555565 2nd part
* Check if IMG switch 'IBAN without account number' is active
      DATA lv_iban_wo_acc_check TYPE xiban_wo_accno.

* GLW note 1776178 begin
      FIELD-SYMBOLS: <value> TYPE any.
      DATA    lv_fields TYPE string.
* check if the new fields according to note 1686666 are already existing
      lv_fields = 'BLFBK-IBAN'.
      UNASSIGN <value>.
      ASSIGN (lv_fields) TO <value>.
      IF sy-subrc IS INITIAL.
        UNASSIGN <value>.
        lv_fields = 'BLFBK-VALID_FROM'.
        ASSIGN (lv_fields) TO <value>.
      ENDIF.
* GLW note 1776178 end

      CALL FUNCTION 'FI_IBAN_WO_ACCNO_CHECK'
        IMPORTING
          e_xactivated = lv_iban_wo_acc_check.

* ARIK142351 begin / Note 1555565 3rd part
*  IF lv_iban_wo_acc_check IS INITIAL.
* For compatibility reasons check if IBAN exists in IT is done by help
* of blfbk_iban. Because the field IBAN in IT0009 (HR) might not exist.
      MOVE-CORRESPONDING p0009 TO blfbk_iban.
* ARIK145058 / Note 1566706 begin
* It must always be possible to delete non-IBAN bank data.
* Form delete_old_bank_data must take care not to create BLFBK entries for IBAN dummy banknumber ('<IBAN>...')
*  IF ( lv_iban_wo_acc_check IS INITIAL OR
*       ( lv_iban_wo_acc_check IS NOT INITIAL AND blfbk_iban-iban IS INITIAL ) ).
* ARIK145058 / Note 1566706 end
* ARIK142351 end / Note 1555565 3rd part
* ARIK142351 end / Note 1555565 2nd part

      PERFORM delete_old_bank_data USING old_vendor_lfb1-lifnr.  "Note 1555565 part 4

* BEGIN MIVO 1635738
* all necessary deletion ahs been taken care of above.
* now create new entries based on the data
* END MIVO 1635738

* now we have to transfer the new bank data to the vendor
      CLEAR blfbk.
      CLEAR file_k.
* ARIK145058 / note 1566706 begin
* Do not create BLFBK entry for IBAN as bank number is empty
*      IF p0009-bankn IS NOT INITIAL. " MIVO 1635738
      IF <value> IS ASSIGNED OR p0009-bankn IS NOT INITIAL.  "GLW note 1776178
* the new fields in BLFBK are existing. All the IBAN Logic can now be handled via BLFBK! BLFBK_IBAN and also
* the Badi-Implementation is not needed anymore! BLFBK-IBAN filled without bank account number is handled like
* blfbk_iban structure.

* ARIK145058 / note 1566706 end
* NODATA wird später gesetzt
*   perform nodata_in_structure using 'BLFBK' nodata.
        IF blfbk_iban-iban IS NOT INITIAL .  "GLW note 1776178
*          <value> = p0009-begda.        MIVO 1819171                                                      "GLW note 1776178
*          WRITE p0009-begda TO <value>. "MIVO 1819171 " MIVO 2136795
* BEGIN MIVO 2136795
          DATA: lv_valid_from TYPE iban_valfr,
                lt_tiban      LIKE tiban.

          SELECT SINGLE valid_from FROM  tiban INTO @lv_valid_from
                 WHERE  banks       = @p0009-banks
                 AND    bankl       = @p0009-bankl
                 AND    bankn       = @p0009-bankn
                 AND    bkont       = @p0009-bkont.

*          IF sy-subrc EQ 0.
          IF sy-subrc IS INITIAL AND lv_valid_from IS NOT INITIAL AND lv_valid_from < p0009-begda. "GLW note 2211189 GLW note 2950925
            WRITE lv_valid_from TO <value>.
          ELSE.
            WRITE p0009-begda TO <value>.
          ENDIF.
* END MIVO 2136795
* later, the move-corresponding brings also IBAN to blfbk
        ENDIF.                                                                                "GLW note 1776178
        blfbk-stype = '2'.
        blfbk-tbnam = 'BLFBK'.
        MOVE-CORRESPONDING p0009 TO blfbk.                  "#EC ENHOK
* QIZK145479 begin...
        IF p0009-emftx NE p0001-ename.
          blfbk-koinh = p0009-emftx.
        ELSE.
          blfbk-koinh = '!'.
        ENDIF.
* QIZK145479 end...

* QIZK002047 begin...
        IF NOT blfbk-stras IS INITIAL.
          blfbk-stras = nodata.
        ENDIF.
* QIZK002047 end...

* Begin of Insertion QKZP9BK041816 Kontoinhaber Japan
        IF t500p-molga EQ '22'.
* Japan: name of the owner of the bank account
          IF p0009-emftx IS NOT INITIAL AND                   "ARIN1673011
             p0009-emftx NE p0001-ename.                    "ARIK153387
            blfbk-koinh = p0009-emftx.                      "ARIK153387
          ELSE.                                             "ARIK153387
            blfbk-koinh = p0001-sname.
          ENDIF.                                            "ARIK153387
        ENDIF.
* End of Insertion QKZP9BK041816
*    read bank data of template temp_a_p.                   "QIZK048668
        SELECT SINGLE * FROM lfbk                           "QIZK048668
                        WHERE lifnr EQ temp_a_p.            "QIZK048668
        IF sy-subrc EQ 0.                                   "QIZK048668
          *lfbk = lfbk.                                     "QIZK048668
        ENDIF.                                              "QIZK048668
        blfbk-xezer = *lfbk-xezer.                          "QIZK048668
        IF blfbk-bkref IS INITIAL.                          "QIZK052366
* There is no P0009-BKREF entry...                          "QIZK052366
          blfbk-bkref = *lfbk-bkref.                        "QIZK001005
        ENDIF.                                              "QIZK052366
        blfbk-bvtyp = *lfbk-bvtyp.                          "QIZK001005
* Aufbauen der BANK im Zielsystem entspricht nicht dem 4.0 ALE-Szenario
* Nachlesen der Bank deaktiviert QIZP40K016960:

** Neu Bank im Zielsystem aufbauen.                      "QIZP40K016960
*    TABLES: BNKA.                                       "QIZP40K016960
*    SELECT * FROM BNKA WHERE BANKS EQ P0009-BANKS AND   "QIZP40K016960
*                             BANKL EQ P0009-BANKL.      "QIZP40K016960
*      MOVE-CORRESPONDING BNKA TO BLFBK.                 "QIZP40K016960
*    ENDSELECT.                                          "QIZP40K016960


        PERFORM clear_bnka_fields CHANGING blfbk. " GLW note 2174172

* leere P0009-Felder mit NODATA füllen
        SELECT * FROM dd03l WHERE tabname EQ 'BLFBK'
                            AND   as4local  EQ 'A'.
*        fields(5)    = 'BLFBK'.                            "MAWK013477
*        fields+5(1)  = '-'.                                "MAWK013477
*        fields+6(10) = dd03l-fieldname.                    "MAWK013477
          CONCATENATE 'BLFBK' dd03l-fieldname               "MAWK013477
                 INTO fields SEPARATED BY '-'.              "MAWK013477
          ASSIGN (fields) TO <str_fields>.
*     if <str_fields> is initial                            "QIZK001005
          IF <str_fields> IS INITIAL AND                    "QIZK001005
             fields NE 'BLFBK-XEZER' AND                    "QIZK001005
             fields NE 'BLFBK-BKREF' AND                    "QIZK001005
             fields NE 'BLFBK-BVTYP'.                       "QIZK001005
            <str_fields> = nodata.
          ENDIF.
        ENDSELECT.
*

        DATA: blfbk_help LIKE blfbk.  "GLW note 2063439
        blfbk_help = blfbk.            "GLW note 2063439

        CALL METHOD user_exit->set_values_for_blfbk         "HASK036614
          EXPORTING
*           i_pernr = p0009-pernr
             i_pernr = pernr-pernr  "GLW note 2268454: in case no it9 is existing
          CHANGING                                          "HASK036614
            c_blfbk = blfbk.                                "HASK036614

        IF  w_o_it9 IS INITIAL OR blfbk NE blfbk_help. "GLW note 2063439
* only write blfnk to file if infotype 9 existed or blfbk was changed in Badi by customer.

* Begin of KCNK011667
* field for Postbankgirokontonummer which is used for
* building society roll no is moved to the correct field.
          IF t500p-molga EQ '08'OR molga EQ '43'.
            IF NOT p0009-pskto IS INITIAL.
              MOVE p0009-pskto TO blfbk-bkref.
            ENDIF.
          ENDIF.
* End of KCNK011667

*     file_k = blfbk.                            "#EC ENHOK "MAWH1492437
          PERFORM move_struct_to_file USING blfbk               "MAWH1492437
                                            'BLFBK'             "MAWH1492437
                                   CHANGING file_k.             "MAWH1492437
          PERFORM write_file USING '2' file_k space space.
          TRANSFER file_k TO file_o.
*      ENDIF.                                       "ARIK145058 / note 1566706 MIVO 1635738
        ENDIF.     "GLW note 2063439
      ELSE.

* BEGIN MIVO 1635738
* create LFBK_IBAN entry now
* END MIVO 1635738

* QIZ Löschen der vorhandenen Bank wieder nach vorne verschoben
* eventuelle Pflichtfelder werden von Marcela abgefangen!
* QIZALRK159798 begin
* only create-mode, change-mode and refresh-mode
*    PERFORM READ_OLD_BANK_DATA USING
*                               OLD_VENDOR_LFB1-LIFNR.
** first we have to delete all old bank data.
*    LOOP AT OLD_VENDOR_LFBK.
*      CHECK P0009-BANKS NE OLD_VENDOR_LFBK-BANKS OR
*            P0009-BANKL NE OLD_VENDOR_LFBK-BANKL OR
*            P0009-BANKN NE OLD_VENDOR_LFBK-BANKN.
*      CLEAR BLFBK.
*      CLEAR FILE_K.
*      PERFORM NODATA_IN_STRUCTURE USING 'BLFBK' NODATA.
*      BLFBK-STYPE = '2'.
*      BLFBK-TBNAM = 'BLFBK'.
*      BLFBK-XDELE = 'X'.
*      BLFBK-BANKS = OLD_VENDOR_LFBK-BANKS.
*      BLFBK-BANKL = OLD_VENDOR_LFBK-BANKL.
*      BLFBK-BANKN = OLD_VENDOR_LFBK-BANKN.
*      FILE_K = BLFBK.
*      PERFORM WRITE_FILE USING '2' FILE_K SPACE SPACE.
*      TRANSFER FILE_K TO FILE_O.
*    ENDLOOP.
* QIZALRK159798 end
* ARIK145058 / Note 1566706 begin
*  ENDIF.                                 "ARIK142351 / Note 1555565
* ARIK145058 / Note 1566706 end

* ARIK145058 / Note 1566706 begin
* It must always be possible to delete IBAN bank data.
*  IF blfbk_iban-iban IS NOT INITIAL.                "ARIK142351 / Note 1555565 3rd part
* ARIK145058 / Note 1566706 end
* ARIK142351 begin / Note 1555565
* Note 1555565 part 4 begin
*      PERFORM delete_old_bank_data_iban USING old_vendor_lfb1-lifnr " MIVO 1635738
*                                              blfbk_iban-iban.      " MIVO 1635738
* Note 1555565 part 4 end
* Bank details IBAN part

* now we have to transfer the new IBAN bank data to the vendor
        CLEAR blfbk_iban.
        CLEAR file_k.
* ARIK145058 / note 1566706 begin
* Make sure currently valid bank details are used
        MOVE-CORRESPONDING p0009 TO blfbk_iban.
* Do not create BLFBK_IBAN entry for ordinary (non-IBAN) bank account
        IF blfbk_iban-iban IS NOT INITIAL.
* ARIK145058 / note 1566706 end
* NODATA wird später gesetzt
*   perform nodata_in_structure using 'BLFBK_IBAN' nodata.
          blfbk_iban-stype = '2'.
          blfbk_iban-tbnam = 'BLFBK_IBAN'.
*      MOVE-CORRESPONDING p0009 TO blfbk_iban.                    "#EC ENHOK "Note 1566706
* QIZK145479 begin...
          IF p0009-emftx NE p0001-ename.
            blfbk_iban-koinh = p0009-emftx.
          ELSE.
            blfbk_iban-koinh = '!'.
          ENDIF.
* QIZK145479 end...

* QIZK002047 begin...
          IF NOT blfbk_iban-stras IS INITIAL.
            blfbk_iban-stras = nodata.
          ENDIF.
* QIZK002047 end...

          blfbk_iban-ort01 = p0009-bkort.

* Begin of Insertion QKZP9BK041816 Kontoinhaber Japan
          IF t500p-molga EQ '22'.
* Japan: name of the owner of the bank account
            IF p0009-emftx NE p0001-ename.                  "ARIK153387
              blfbk_iban-koinh = p0009-emftx.               "ARIK153387
            ELSE.                                           "ARIK153387
              blfbk_iban-koinh = p0001-sname.
            ENDIF.                                          "ARIK153387
          ENDIF.
* End of Insertion QKZP9BK041816
*    read bank data of template temp_a_p.                   "QIZK048668
          SELECT SINGLE * FROM lfbk                         "QIZK048668
                          WHERE lifnr EQ temp_a_p.          "QIZK048668
          IF sy-subrc EQ 0.                                 "QIZK048668
            *lfbk = lfbk.                                   "QIZK048668
          ENDIF.                                            "QIZK048668
          blfbk_iban-xezer = *lfbk-xezer.                   "QIZK048668
          IF blfbk_iban-bkref IS INITIAL.                   "QIZK052366
* There is no P0009-BKREF entry...                          "QIZK052366
            blfbk_iban-bkref = *lfbk-bkref.                 "QIZK001005
          ENDIF.                                            "QIZK052366
          blfbk_iban-bvtyp = *lfbk-bvtyp.                   "QIZK001005
* Aufbauen der BANK im Zielsystem entspricht nicht dem 4.0 ALE-Szenario
* Nachlesen der Bank deaktiviert QIZP40K016960:

** Neu Bank im Zielsystem aufbauen.                      "QIZP40K016960
*    TABLES: BNKA.                                       "QIZP40K016960
*    SELECT * FROM BNKA WHERE BANKS EQ P0009-BANKS AND   "QIZP40K016960
*                             BANKL EQ P0009-BANKL.      "QIZP40K016960
*      MOVE-CORRESPONDING BNKA TO BLFBK.                 "QIZP40K016960
*    ENDSELECT.                                          "QIZP40K016960

* leere P0009-Felder mit NODATA füllen
          SELECT * FROM dd03l WHERE tabname EQ 'BLFBK_IBAN'
                              AND   as4local  EQ 'A'.
*        fields(5)    = 'BLFBK'.                            "MAWK013477
*        fields+5(1)  = '-'.                                "MAWK013477
*        fields+6(10) = dd03l-fieldname.                    "MAWK013477
            CONCATENATE 'BLFBK_IBAN' dd03l-fieldname        "MAWK013477
                   INTO fields SEPARATED BY '-'.            "MAWK013477
            ASSIGN (fields) TO <str_fields>.
*     if <str_fields> is initial                            "QIZK001005
            IF <str_fields> IS INITIAL AND                  "QIZK001005
               fields NE 'BLFBK_IBAN-XEZER' AND             "QIZK001005
               fields NE 'BLFBK_IBAN-BKREF' AND             "QIZK001005
               fields NE 'BLFBK_IBAN-BVTYP'.                "QIZK001005
              <str_fields> = nodata.
            ENDIF.
          ENDSELECT.
*

          CALL METHOD user_exit->set_values_for_blfbk_iban  "HASK036614
            EXPORTING
              i_pernr      = p0009-pernr
            CHANGING                                        "HASK036614
              c_blfbk_iban = blfbk_iban.                    "HASK036614


*     file_k = blfbk_iban.                            "#EC ENHOK "MAWH1492437
          PERFORM move_struct_to_file USING blfbk_iban               "MAWH1492437
                                            'BLFBK_IBAN'             "MAWH1492437
                                   CHANGING file_k.             "MAWH1492437
          PERFORM write_file USING '2' file_k space space.
          TRANSFER file_k TO file_o.

* ARIK142351 end / Note 1555565
        ENDIF.                                      "ARIK142351 / Note 1555565 3rd part

* BEGIN MIVO 1635738
      ENDIF.
* END MIVO 1635738

    ENDIF.
  ENDIF.                                                    "QIZK082452
* Kred. Buchungskreisdaten
* all LFB1-data of the template-vendor will be copied to new vendor
  PERFORM nodata_in_structure USING 'BLFB1' nodata.
  blfb1-stype = '2'.
  blfb1-tbnam = 'BLFB1'.
  blfb1-pernr = pernr-pernr.
  IF t_code EQ 'XK01' OR
     t_code EQ 'XK02'.
    IF NOT p0009-zlsch IS INITIAL.
*     CLEAR blfb1-zwels.                                    "QIZK113008
*     blfb1-zwels(1) = p0009-zlsch.                         "QIZK113008
      IF blfb1-zwels(1) EQ nodata.                          "QIZK141582
        blfb1-zwels(1) = p0009-zlsch.                       "QIZK141582
* QIZK004146 begin...
        IF t_code EQ 'XK02' AND ref_a_p IS INITIAL.
* Vorlagekreditor nicht gelesen wegen reinem HR-Update...
          SELECT SINGLE zwels FROM lfb1 INTO *lfb1-zwels
                 WHERE lifnr EQ temp_a_p AND bukrs EQ p0001-bukrs.
          IF sy-subrc IS INITIAL.
* Vorlagekreditor eingegeben und existiert...
* Zahlweg aus Vorlagekreditor und Infotyp 0009 zusammensetzen.
            IF *lfb1-zwels NA p0009-zlsch.
              CONCATENATE *lfb1-zwels p0009-zlsch
                          INTO blfb1-zwels.
            ELSE.
              blfb1-zwels = *lfb1-zwels.
            ENDIF.
          ELSE.
* Vorlagekreditor nicht eingegeben oder existiert nicht...
* Zahlweg aus altem Kreditor und Infotyp 0009 zusammensetzen, sonst
* verschwinden die Zahlwege des Vorlagekreditors aus dem Kreditor.
            IF lfb1-zwels NA p0009-zlsch.
              CONCATENATE lfb1-zwels p0009-zlsch
                          INTO blfb1-zwels.
            ELSE.
              blfb1-zwels = lfb1-zwels.
            ENDIF.
          ENDIF.
        ENDIF.
* QIZK004146 end...
      ELSE.                                                 "QIZK141582
        IF blfb1-zwels NA p0009-zlsch.                      "QIZK113008
          CONCATENATE blfb1-zwels p0009-zlsch               "QIZK113008
                      INTO blfb1-zwels.                     "QIZK113008
        ENDIF.                                              "QIZK113008
      ENDIF.                                                "QIZK141582
    ELSE.                                                   "MAWK120174
* Wenn der Zahlweg im IT0009 initial ist, dann handelt es   "MAWK120174
* sich um "Barzahlung". In diesem Fall darf im Kreditor kein"MAWK120174
* Zahlweg eingetragen werden (d.h. die Liste der Zahlwege   "MAWK120174
* muß leer sein).                                           "MAWK120174
      IF w_o_it9 IS INITIAL.                                "GLW note 2063439
        CLEAR blfb1-zwels.                                  "MAWK120174
      ELSE.
* employee has no infotype 9: always take the value from the reference vendor
        SELECT SINGLE zwels FROM lfb1 INTO blfb1-zwels      "GLW note 2063439
                 WHERE lifnr EQ temp_a_p AND bukrs EQ p0001-bukrs.
      ENDIF.
    ENDIF.
  ENDIF.

  IF t_code = 'XK02' AND ref_a_p IS INITIAL.  "GLW note 2099681
* change
    IF unlock IS NOT INITIAL.
      blfb1-sperr = space.
    ENDIF.
  ENDIF.
* IF blfb1-hbkid = nodata OR blfb1-hbkid IS INITIAL         "KCNK050331
  IF ( blfb1-hbkid = nodata OR blfb1-hbkid IS INITIAL )     "KCNK050331
     AND ( t_code EQ 'XK01'
     OR  ( t_code EQ 'XK02' AND NOT ref_a_p IS INITIAL ) ).
* No template data, only create-mode/refresh-mode
    blfb1-hbkid = trvhb(5).
  ENDIF.
  IF t_code EQ 'XK05'.
    blfb1-sperr = 'X'.                 "lock-flag
  ENDIF.

  CALL METHOD user_exit->set_values_for_blfb1               "HASK036614
    EXPORTING
*     i_pernr = p0009-pernr
      i_pernr = pernr-pernr "GLW note 2268454: in case no IT9 is existing
    CHANGING                                            "HASK036614
      c_blfb1 = blfb1.                                  "HASK036614

* file_k = blfb1.                                "#EC ENHOK "MAWH1492437
  PERFORM move_struct_to_file USING blfb1                   "MAWH1492437
                                    'BLFB1'                 "MAWH1492437
                           CHANGING file_k.                 "MAWH1492437
  IF t_code NE 'XK05' AND t_code NE 'XK06'.                 "WKUK011046
*   perform write_file using '2' file_k space 'X'.          "QIZK003419
    PERFORM write_file USING '2' file_k space space.        "QIZK003419
    TRANSFER file_k TO file_o.
* dunning procedure...                                      "QIZK003419
    CLEAR blfb5.                                            "QIZK003419
    CLEAR file_k.                                           "QIZK003419
    PERFORM nodata_in_structure USING 'BLFB5' nodata.       "QIZK003419
    blfb5-stype = '2'.                                      "QIZK003419
    blfb5-tbnam = 'BLFB5'.                                  "QIZK003419

    CALL METHOD user_exit->set_values_for_blfb5             "HASK036614
      EXPORTING
*       i_pernr = p0009-pernr
        i_pernr = pernr-pernr   "GLW note 2268454: in case no IT9 is existing
      CHANGING                                          "HASK036614
        c_blfb5 = blfb5.                                "HASK036614

*   file_k = blfb5.                  "#EC ENHOK "QIZK003419 "MAWH1492437
    PERFORM move_struct_to_file USING blfb5                 "MAWH1492437
                                      'BLFB5'               "MAWH1492437
                             CHANGING file_k.               "MAWH1492437
*   PERFORM WRITE_FILE USING '2' FILE_K SPACE 'X'."QIZK003419QIZK047575
    PERFORM write_file USING '2' file_k space ' '.          "QIZK047575
    TRANSFER file_k TO file_o.                              "QIZK003419
* QIZK047575 begin...
    IF t_code EQ 'XK01' OR t_code EQ 'XK02'.
      PERFORM delete_old_lfbw_data USING old_vendor_lfb1-lifnr.
    ENDIF.
    CLEAR blfbw.
    CLEAR file_k.
* read lfbw data from template vendor...
    SELECT * FROM lfbw WHERE lifnr EQ temp_a_p
                       AND   bukrs EQ p0001-bukrs.
      *lfbw = lfbw.
* routine fills BLFBW from the current *LFBW and NODATA...
      PERFORM nodata_in_structure USING 'BLFBW' nodata.
      blfbw-stype = '2'.
      blfbw-tbnam = 'BLFBW'.

      CALL METHOD user_exit->set_values_for_blfbw           "HASK036614
        EXPORTING
          i_pernr = p0001-pernr
        CHANGING                                        "HASK036614
          c_blfbw = blfbw.                              "HASK036614

*     file_k = blfbw.                                       "MAWH1492437
      PERFORM move_struct_to_file USING blfbw               "MAWH1492437
                                        'BLFBW'             "MAWH1492437
                               CHANGING file_k.             "MAWH1492437
      PERFORM write_file USING '2' file_k space 'X'.
      TRANSFER file_k TO file_o.
    ENDSELECT.
* QIZK047575 end...
*   IF NOT ( sy-subrc IS INITIAL ).             "QIZK082452 "QIZK113008
    IF NOT file_pr IS INITIAL AND                           "QIZK113008
       NOT ( sy-subrc IS INITIAL ).                         "QIZK113008
************* Start commenting C5056168 28/02/2005*****************
*       WRITE: 1(80) sy-uline.                              "QIZK082452
************* End commenting C5056168 28/02/2005*******************
    ENDIF.                                                  "QIZK082452
  ELSE.                                                     "WKUK011046
    PERFORM write_file USING '2' file_k space 'X'.          "WKUK011046
    TRANSFER file_k TO file_o.                              "WKUK011046
  ENDIF.                                                    "WKUK011046
  sel_on_file = sel_on_file + 1.
ENDFORM.                    "create_file_a_p

*&---------------------------------------------------------------------*
*&      Form  READ_FILE_K
*&---------------------------------------------------------------------*
FORM read_file_k.
  FORMAT RESET.
  SKIP.
* QIZK033506 Unicode begin...
* OPEN DATASET file_o IN TEXT MODE.

* Begin of HZIH1517930
  CONSTANTS gc_fname TYPE fileintern VALUE 'FI_TV_RPRAPA00'.

  CALL FUNCTION 'FILE_VALIDATE_NAME'
    EXPORTING
      logical_filename           = gc_fname
    CHANGING
      physical_filename          = file_o
    EXCEPTIONS
      logical_filename_not_found = 1
      validation_failed          = 2
      OTHERS                     = 3.

  IF sy-subrc <> 0.
    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
      WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
  ENDIF.
* End of HZIH1517930

  OPEN DATASET file_o IN TEXT MODE FOR OUTPUT
                         ENCODING DEFAULT
                         MESSAGE msg.
* QIZK033506 Unicode end...
  DO.
    CLEAR wa.
    READ DATASET file_o INTO wa.
    IF sy-subrc <> 0. EXIT. ENDIF.
    WRITE:/ wa.
  ENDDO.
ENDFORM.                    "read_file_k

*&---------------------------------------------------------------------*
*&      Form  NODATA_IN_STRUCTURE
*&---------------------------------------------------------------------*
*       puts the contents of NODATA in all Fields
*       and uses the template values from the LFA/B1-databases.
*----------------------------------------------------------------------*
FORM nodata_in_structure USING nodata_structure nodata.
  SELECT * FROM dd03l WHERE tabname EQ nodata_structure
                      AND   as4local  EQ 'A'.
* fill structure with NODATA
*    fields(5)    = nodata_structure.                       "MAWK013477
*    fields+5(1)  = '-'.                                    "MAWK013477
*    fields+6(10) = dd03l-fieldname.                        "MAWK013477
    CONCATENATE nodata_structure dd03l-fieldname            "MAWK013477
           INTO fields  SEPARATED BY '-'.                   "MAWK013477
    ASSIGN (fields) TO <str_fields>.
    CHECK sy-subrc IS INITIAL. "GLW note 2336952
    <str_fields> = nodata.

    CHECK dd03l-fieldname NE 'SENDE'.                       "QIZK053440

* template A/P-account only by using XK01 or by refreshing the A/P acc.
    CHECK t_code EQ 'XK01' OR
          ( t_code EQ 'XK02' AND NOT ( ref_a_p IS INITIAL ) ).
* Use the template A/P-account for databases BLFA1 and BLFB1.
    CHECK nodata_structure EQ 'BLFA1' OR
*         nodata_structure eq 'BLFB1'.                      "QIZK003419
          nodata_structure EQ 'BLFB1' OR                    "QIZK003419
*         nodata_structure eq 'BLFB5'.           "QIZK003419 QIZK047575
          nodata_structure EQ 'BLFB5' OR                    "QIZK047575
          nodata_structure EQ 'BLFBW'.                      "QIZK047575

    IF nodata_structure EQ 'BLFA1'.
      PERFORM nodata_template USING 'BLFA1' 'LFA1'.
    ELSE.
      IF nodata_structure EQ 'BLFB1'.
        PERFORM nodata_template USING 'BLFB1' 'LFB1'.
      ELSE.                                                 "QIZK003419
        IF nodata_structure EQ 'BLFB5'.                     "QIZK003419
          PERFORM nodata_template USING 'BLFB5' 'LFB5'.     "QIZK003419
        ENDIF.                                              "QIZK003419
        IF nodata_structure EQ 'BLFBW'.                     "QIZK047575
          PERFORM nodata_template USING 'BLFBW' 'LFBW'.     "QIZK047575
        ENDIF.                                              "QIZK047575
      ENDIF.
    ENDIF.
  ENDSELECT.
ENDFORM.                               " NODATA_IN_STRUCTURE

*---------------------------------------------------------------------*
*       FORM READ_A_P_ACCOUNT                                         *
*---------------------------------------------------------------------*
*       to read the template A/P-account                              *
*---------------------------------------------------------------------*
FORM read_a_p_account USING a_p_account.
  CHECK t_code EQ 'XK01' OR
      ( t_code EQ 'XK02' AND NOT ref_a_p IS INITIAL ) OR ( ( t_code EQ 'XK01' OR t_code EQ 'XK02' ) AND no_9_ok IS NOT INITIAL ). "GLW note 2063439
* only create-mode or refresh-mode
  FORMAT COLOR COL_NEGATIVE.
  SELECT SINGLE * FROM lfa1
                  WHERE lifnr EQ a_p_account.
  IF sy-subrc EQ 0.
    CLEAR lfa1-txjcd.                                       "QIZK225798
    *lfa1 = lfa1.
  ELSE.
    PERFORM fill_error_int USING space
                                 '56_CORE'                  "QIZK001223
                                 'E'
                                 '039'
                                 a_p_account
                                 space
                                 space
                                 space.
    sw_stop = 'X'.
    STOP.
  ENDIF.
* authorization-check for the template a/p-account.
  PERFORM auth_a_p_account_lfa1.
* read bank data of template a/p-account.                   "QIZK048668
  SELECT SINGLE * FROM lfbk                                 "QIZK048668
                  WHERE lifnr EQ a_p_account.               "QIZK048668
  IF sy-subrc EQ 0.                                         "QIZK048668
    *lfbk = lfbk.                                           "QIZK048668
  ENDIF.                                                    "QIZK048668
ENDFORM.                    "read_a_p_account

*---------------------------------------------------------------------*
*       FORM HR_MASTER_DATA                                           *
*---------------------------------------------------------------------*
FORM hr_master_data USING begda endda.
  TABLES: q0006.                                            "QIZK025968
  DATA: p0006_telnr LIKE p0006-telnr.                       "QIZK025968
  DATA: p0006_areac LIKE q0006-telnr.                       "QIZK025968
  DATA: p0006_areac_5(5).                                   "QIZK025968

  CHECK t_code EQ 'XK01' OR
        t_code EQ 'XK02'.
* only create-mode or refresh-mode or change-mode
* QIZK032746 begin...
  IF NOT daily IS INITIAL.
    begda = endda = sy-datum.
  ENDIF.
* QIZK032746 end...
  CLEAR w_changes.
* Measures
  PERFORM change-date USING '0000'.
  PERFORM new-infotype-data USING '0000' begda.             "QIZK032746
  rp_provide_from_last p0000 space begda endda.
* Org. Assignment already readed.
  PERFORM change-date USING '0001'.
  PERFORM new-infotype-data USING '0001' begda.             "QIZK032746
  rp_provide_from_last p0001 space begda endda.             "QIZK079153
* BEGIN WKUK039334
* rp_provide_from_last p0017 space begda endda.             "QIZK082452
* IF NOT p0017-bukrs IS INITIAL.                            "QIZK082452
*   p0001-bukrs = p0017-bukrs.                              "QIZK082452
* ENDIF.                                                    "QIZK082452
  rp_provide_from_last p0017_help space begda endda.
  IF NOT p0017_help-bukrs IS INITIAL.
    p0001-bukrs = p0017_help-bukrs.
  ENDIF.
* END WKUK039334
* Personal Data
  PERFORM change-date USING '0002'.
  PERFORM new-infotype-data USING '0002' begda.             "QIZK032746
  rp_provide_from_last p0002 space begda endda.
  PERFORM err-table USING '0002' begda endda pnp-sw-found.
* Addresses: Permanent residence
  PERFORM change-date USING '0006'.
  PERFORM new-infotype-data USING '0006' begda.             "QIZK032746
* Begin of MAWK015766
* rp_provide_from_last p0006 '1' begda endda.
  rp_provide_from_last p0006 p_subty6 begda endda.
  IF pnp-sw-found EQ '0' AND
     p_subty6     NE '1'.
    rp_provide_from_last p0006 '1' begda endda.
  ENDIF.
* End of MAWK015766
* perform change-date using '0006'.

* Find MOLGA according to Country (P0006-LAND1)             "QIZK023533
  PERFORM find_molga_for_country USING p0006-land1          "QIZK023533
                                       t500p-molga          "QIZK023533
                                       molga.               "QIZK023533
* IF t500p-molga EQ '10' AND NOT p0006-pstlz IS INITIAL.    "QIZK023533
  IF molga EQ '10' AND NOT p0006-pstlz IS INITIAL.          "QIZK023533
    PERFORM zip_code_pbo(sapfp5u0) USING p0006-pstlz.
  ENDIF.
* IF t500p-molga EQ '10' OR t500p-molga EQ '07'.            "QIZK023533
  IF molga EQ '10' OR molga EQ '07'.                        "QIZK023533
    IF NOT p0006-telnr IS INITIAL.                          "QIZK025968
* Begin of MAWK013477
*     PERFORM telnr_pbo(sapfp5u0) USING p0006-telnr         "QIZK025968
*                                       p0006_areac         "QIZK025968
*                                       p0006_telnr.        "QIZK025968
      PERFORM telnr USING p0006-telnr
                          p0006_areac
                          p0006_telnr.
* End of MAWK013477
      CONCATENATE '(' p0006_areac ')' INTO p0006_areac_5.   "QIZK025968
      CONCATENATE p0006_areac_5 p0006_telnr                 "QIZK025968
                  INTO p0006-telnr SEPARATED BY space.      "QIZK025968
    ENDIF.                                                  "QIZK025968
  ENDIF.                                                    "QIZK025968
* IF t500p-molga EQ '12' AND NOT p0006-pstlz IS INITIAL.    "QIZK023533
  IF molga EQ '12' AND NOT p0006-pstlz IS INITIAL.          "QIZK023533
    IF p0006-pstlz+4(1) NA '1234567890'.                    "QIZK031193
      p0006-pstlz+4(1) = space.                             "QIZK026802
    ENDIF.                                                  "QIZK031193
  ENDIF.                                                    "QIZK026802
  PERFORM err-table USING '0006' begda endda pnp-sw-found.
* Bank Details
  PERFORM change-date USING '0009'.
  PERFORM new-infotype-data USING '0009' begda.             "QIZK032746
* Begin of MAWK015766
*  rp_provide_from_last p0009 '2' begda endda.
*  IF pnp-sw-found EQ '0'.
*    rp_provide_from_last p0009 '0' begda endda.
*  ENDIF.
  rp_provide_from_last p0009 p_subty9 begda endda.
  IF pnp-sw-found EQ '0'.
    rp_provide_from_last p0009 '2' begda endda.
    IF pnp-sw-found EQ '0'.
      rp_provide_from_last p0009 '0' begda endda.
    ENDIF.
  ENDIF.
* End of MAWK015766
* perform change-date using '0009'.
  IF NOT ( p0009-banks IS INITIAL ) AND
           p0009-bankl IS INITIAL   AND
           p0009-bankn IS INITIAL.
* P0009 is incomplete
    CLEAR p0009-banks.
  ENDIF.
  PERFORM err-table USING '0009' begda endda pnp-sw-found.
* House bank
  PERFORM read_house_bank USING pnp-sw-found.

  CALL FUNCTION 'TRAVEL_EXISTS'                             "QIZK001223
    EXCEPTIONS                                              "QIZK001223
      travel_not_existing = 1                         "QIZK001223
      OTHERS              = 2.                        "QIZK001223

  IF sy-subrc EQ 0.                                         "QIZK001223
    PERFORM err-table USING 'XXXX' begda endda pnp-sw-found.
  ENDIF.                                                    "QIZK001223

* personnel number O.K. or not?
  IF t_code EQ 'XK02' AND ref_a_p IS INITIAL AND w_changes IS INITIAL.
* no changes in HR-master data
* QIZK032746 begin...
*   sel_no_changes = sel_no_changes + 1.
    IF daily IS INITIAL.
      sel_no_changes = sel_no_changes + 1.
    ELSE.
      sel_no_changes_for_today = sel_no_changes_for_today + 1.
    ENDIF.
* QIZK032746 end...
    REJECT.
  ENDIF.
ENDFORM.                    "hr_master_data

*---------------------------------------------------------------------*
*       FORM FIND_ANRED                                               *
*---------------------------------------------------------------------*
*  -->  ANRED                                                         *
*---------------------------------------------------------------------*
FORM find_anred USING anred.
  sy-subrc = 0.

  DATA: table_name TYPE string VALUE 'TSAD3HR'. "GLW note 1896759
* not installed in dev. system, thus dynamic!
  DATA: title TYPE char4.  "GLW note 1896759
  TABLES: tsad3t.          "GLW note 1896759
  STATICS: stv_anred TYPE t522t-ANRLT. "atext. "GLW note 1896759 MIVO 2191241

  IF t522t-anred NE p0002-anred.
    SELECT SINGLE * FROM t522t WHERE sprsl EQ sy-langu
                               AND   anred EQ p0002-anred.
* GLW note 1896759 end
    IF sy-subrc IS INITIAL.
      stv_anred = t522t-atext.
      TRY.
          SELECT SINGLE title FROM (table_name) INTO title WHERE
                anred = t522t-anred.
          IF sy-subrc IS NOT INITIAL. "GLW note 2078552
            SELECT SINGLE title FROM bbp_tsad3hr INTO title WHERE
               anred = t522t-anred.
          ENDIF.
          IF sy-subrc IS INITIAL.
            SELECT SINGLE * FROM tsad3t WHERE
               langu = sy-langu AND
               title = title.
            IF sy-subrc IS INITIAL.
              stv_anred = tsad3t-title_medi.
            ENDIF.
          ENDIF.
        CATCH cx_sy_dynamic_osql_semantics.
          sy-subrc = 0.
      ENDTRY.
    ELSE.
      CLEAR stv_anred.
    ENDIF.
* GLW note 1896759 end
  ENDIF.
*  IF sy-subrc EQ 0 AND t522t-atext NE space.              "QJEPH4K006815
  IF  stv_anred NE space.                 "GLW note 1896759  "GLW note 2359391
*   MOVE t522t-atext TO anred.
    MOVE stv_anred TO anred.
  ELSE.
    MOVE nodata TO anred.              "QJEPH4K006815
  ENDIF.
ENDFORM.                    "find_anred

*---------------------------------------------------------------------*
*       form create_street
*---------------------------------------------------------------------*
*       routine creates the combination of STRAS HSNMR POSTA
*---------------------------------------------------------------------*
FORM create_street USING field_o.

  CLEAR field_o.
* prepare the adress in order to get the 'complete street'
  rp-make-address p0001 p0002 p0006 p0001-ename '10'.
  IF NOT p0006-stras IS INITIAL.       "QSCALRK168532
    CONDENSE p0006-stras.
    IF adrs-line0 CS p0006-stras.
      field_o = adrs-line0.
      EXIT.
    ENDIF.
    IF adrs-line1 CS p0006-stras.
      field_o = adrs-line1.
      EXIT.
    ENDIF.
    IF adrs-line2 CS p0006-stras.
      field_o = adrs-line2.
      EXIT.
    ENDIF.
    IF adrs-line3 CS p0006-stras.
      field_o = adrs-line3.
      EXIT.
    ENDIF.
    IF adrs-line4 CS p0006-stras.
      field_o = adrs-line4.
      EXIT.
    ENDIF.
    IF adrs-line5 CS p0006-stras.
      field_o = adrs-line5.
      EXIT.
    ENDIF.
    IF adrs-line6 CS p0006-stras.
      field_o = adrs-line6.
      EXIT.
    ENDIF.
    IF adrs-line7 CS p0006-stras.
      field_o = adrs-line7.
      EXIT.
    ENDIF.
    IF adrs-line8 CS p0006-stras.
      field_o = adrs-line8.
      EXIT.
    ENDIF.
    IF adrs-line9 CS p0006-stras.
      field_o = adrs-line9.
      EXIT.
    ENDIF.
    IF field_o IS INITIAL.                                  "KCNK107280
      field_o = p0006-stras.                                "KCNK107280
    ENDIF.                                                  "KCNK107280
  ENDIF.                               "QSCALRK168532
ENDFORM.                    "create_street

*&---------------------------------------------------------------------*
*&      Form  RE500P
*&---------------------------------------------------------------------*
FORM  re500p
USING VALUE(persa).

  IF t500p-persa NE persa.
    t500p = space.
    t500p-persa = persa.
    *t500p = t500p.
    READ TABLE t500p.
    IF sy-subrc NE 0.
************* Start commenting C5056168 28/02/2005*****************
*      NEW-PAGE.
*      SKIP.
*      WRITE: / 'In der Tabelle'(e01), 'T500P',
*               'fehlt das Argument'(e02),
*               *t500p.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************
      CONCATENATE TEXT-e01 'T500P' TEXT-e02 *t500p INTO gv_table_msg
      SEPARATED BY space.
************* End ALV Coding C5056168 28/02/2005*****************

      t500p = space.
*      sw_stop = 'X'.                                       "PGE Note 2933331
*     STOP.                                                 "MAWK022558
      PERFORM stop_or_reject.                               "MAWK022558
    ENDIF.
  ENDIF.
ENDFORM.                                                    "re500p

*&---------------------------------------------------------------------*
*&      Form  FILL_ERROR_INT
*&---------------------------------------------------------------------*
FORM fill_error_int USING pernr arbgb msgty msgnr
                          msgv1 msgv2 msgv3 msgv4.
  error_int-pernr = pernr.
  error_int-arbgb = arbgb.
  error_int-msgty = msgty.
  error_int-msgno = msgnr.
  error_int-msgv1 = msgv1.
  error_int-msgv2 = msgv2.
  error_int-msgv3 = msgv3.
  error_int-msgv4 = msgv4.
  APPEND error_int.
ENDFORM.                    "fill_error_int

*&---------------------------------------------------------------------*
*&      Form  SUB_RFBIKR00
*&---------------------------------------------------------------------*
FORM sub_rfbikr00.
  DATA lt_abap_list TYPE TABLE OF abaplist. "GLW note 2610944
  CHECK fileonly IS INITIAL.
  DESCRIBE TABLE logtable LINES lin.
  CHECK NOT lin IS INITIAL.
  IF NOT testrun IS INITIAL.
* Non Batch-Input-Session
    SUBMIT rfbikr00 AND RETURN
                    USER sy-uname
                    WITH ds_name EQ file_o
                    WITH fl_check EQ 'X'
                    WITH xlog = 'X' EXPORTING LIST TO MEMORY.         "X=No Batch-Input "GLW note 2610944
  ELSE.
* Batch-Input-Session
*   IF jobname = space.                                     "KCNK021736
    IF back_job IS INITIAL.                                 "KCNK021736
* Batch-Input programm will be started online
      SUBMIT rfbikr00 AND RETURN
                      USER sy-uname
                      WITH ds_name EQ file_o
                      WITH fl_check EQ ' '
                      WITH xinf = 'X' EXPORTING LIST TO MEMORY.   "GLW note 2610944
    ELSE.
* Batch-Input programm will be started by a job
      PERFORM submit_job.
    ENDIF.
  ENDIF.

  IF testrun IS NOT INITIAL OR back_job IS INITIAL.
    CALL FUNCTION 'LIST_FROM_MEMORY'  "GLW note 2610944
      TABLES
        listobject = lt_abap_list
      EXCEPTIONS
        not_found  = 1
        OTHERS     = 2.

    IF sy-subrc <> 0.
      RETURN.
    ENDIF.

    CALL FUNCTION 'WRITE_LIST'    "GLW note 2610944
      TABLES
        listobject = lt_abap_list
      EXCEPTIONS
        empty_list = 1
        OTHERS     = 2.

    IF sy-subrc <> 0.
      RETURN.
    ENDIF.
  ENDIF.

ENDFORM.                    "sub_rfbikr00

*---------------------------------------------------------------------*
*       FORM SUBMIT_JOB                                               *
*---------------------------------------------------------------------*
FORM submit_job.

  CALL FUNCTION 'JOB_OPEN'
    EXPORTING
      jobname  = jobname
      jobgroup = 'A/P_Account'
    IMPORTING
      jobcount = jobcount.

  SUBMIT rfbikr00 AND RETURN
                  USER sy-uname
                  VIA JOB jobname NUMBER jobcount
                  WITH ds_name EQ file_o
                  WITH fl_check EQ ' '.

*  IF use_default_group IS INITIAL.                      "GLW note 1711827
    CALL FUNCTION 'JOB_CLOSE'
      EXPORTING
        jobname              = jobname
        jobcount             = jobcount
*     strtimmed            = 'X'.                         "QIZK000174
      strtimmed            = 'X'                          "QIZK000174
*     TARGETSYSTEM         = SY-HOST.                     "QIZK000174
*     targetsystem         = sy-host              "QIZK001068 "WKUK039333
        targetserver         = myname(20)                   "WKUK039333
      EXCEPTIONS                                            "QIZK001068
        cant_start_immediate = 1                            "QIZK001068
        invalid_startdate    = 2                            "QIZK001068
        jobname_missing      = 3                            "QIZK001068
        job_close_failed     = 4                            "QIZK001068
        job_nosteps          = 5                            "QIZK001068
        job_notex            = 6                            "QIZK001068
        lock_failed          = 7                            "QIZK001068
        OTHERS               = 8.                           "QIZK001068

*  ELSE.                                              "GLW note 1711827
*    CALL FUNCTION 'JOB_CLOSE'                        "GLW note 1711827
*      EXPORTING
*        jobname              = jobname
*        jobcount             = jobcount
*        strtimmed            = 'X'
*        targetgroup          = sap_default_btc
*      EXCEPTIONS
*        cant_start_immediate = 1
*        invalid_startdate    = 2
*        jobname_missing      = 3
*        job_close_failed     = 4
*        job_nosteps          = 5
*        job_notex            = 6
*        lock_failed          = 7
*        OTHERS               = 8.
*
*  ENDIF.                                           "GLW note 1711827

  IF sy-subrc <> 0.                                         "QIZK001068
    IF sy-subrc EQ 1.                                       "QIZK001068
*     MESSAGE w016(56) WITH 'Job'(j10)          "QIZK001068 "QIZK001223
      MESSAGE w016(56_core) WITH 'Job'(j10)                 "QIZK001223
             jobname                                        "QIZK001068
            'muß später manuell angestartet werden.'(j11).  "QIZK001068
    ELSE.                                                   "QIZK001068
*     MESSAGE a016(56) WITH                     "QIZK001068 "QIZK001223
      MESSAGE a016(56_core) WITH                            "QIZK001223
      'Job konnte nicht angelegt werden'(j12).              "QIZK001068
    ENDIF.                                                  "QIZK001068
  ENDIF.

ENDFORM.                    "submit_job

*---------------------------------------------------------------------*
*       FORM write_file                                               *
*---------------------------------------------------------------------*
FORM write_file USING VALUE(stype) VALUE(file_k) VALUE(first_process)
                                                 VALUE(last_process).
* work file
  DATA: w_file_k(78).
* work line
  DATA: w_line(78).

  CHECK NOT file_pr IS INITIAL.
************* Start commenting C5056168 28/02/2005*******************
*  FORMAT RESET.
*  IF NOT first_process IS INITIAL AND first_process_global IS INITIAL.
*    first_process_global = 'X'.
*    SKIP.
*    WRITE: 'Arbeitsdatei'(h02) TO w_line.
*    WRITE: file_o TO w_line+40.
*    CONDENSE w_line.
*    WRITE: 2(78) w_line CENTERED.
*    SKIP.
*  ENDIF.
*  CASE stype.
*    WHEN '0'.
*      WRITE  file_k TO w_file_k.
*      WRITE:/1(80) sy-uline.
*      WRITE:/ sy-vline NO-GAP.
*      FORMAT COLOR COL_HEADING INTENSIFIED.
*      WRITE: 2 w_file_k.
*      WRITE:  80 sy-vline.
*    WHEN '1'.
*      WRITE  file_k TO w_file_k.
*      WRITE:/1(80) sy-uline.
*      WRITE:/ sy-vline NO-GAP.
*      FORMAT COLOR COL_HEADING INTENSIFIED.
*      WRITE: 2 w_file_k.
*      WRITE:  80 sy-vline.
*    WHEN '2'.
*      WRITE  file_k TO w_file_k.
*      WRITE:/1(80) sy-uline.
*      WRITE:/ sy-vline NO-GAP.
*      FORMAT COLOR 4 INTENSIFIED.
*      WRITE: 2(6) w_file_k.
*      FORMAT COLOR 2 INTENSIFIED OFF.
*      SHIFT w_file_k BY 6 PLACES.
*      WRITE: 8(72) w_file_k.
*      WRITE:  80 sy-vline.
*      SHIFT file_k BY 70 PLACES.
*      WRITE file_k TO w_file_k.
*      WHILE NOT w_file_k IS INITIAL.
*        WRITE:/ sy-vline NO-GAP.
*        FORMAT COLOR 2 INTENSIFIED OFF.
*        WRITE: (78) w_file_k.
*        WRITE:  80 sy-vline.
*        SHIFT file_k BY 78 PLACES.
*        WRITE file_k TO w_file_k.
*      ENDWHILE.
*      NEW-LINE.                                             "QIZK003419
*    WHEN OTHERS.
*  ENDCASE.
*  IF NOT last_process IS INITIAL.
*    WRITE: 1(80) sy-uline.
*  ENDIF.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************
  DATA : ls_coltab_file TYPE slis_specialcol_alv,  "Color structure
         lt_coltab_file TYPE slis_t_specialcol_alv. "Color table

  IF NOT first_process IS INITIAL AND first_process_global IS INITIAL.
    first_process_global = 'X'.
    WRITE: 'Arbeitsdatei'(h02) TO w_line.
    WRITE: file_o TO w_line+40.
    CONDENSE w_line.
    MOVE : w_line TO gv_file_header_1.
  ENDIF.
  CASE stype.
    WHEN '0'.
      CLEAR : gs_outtab_file,ls_coltab_file,lt_coltab_file.
      WRITE  file_k TO w_file_k.
      MOVE: stype TO gs_outtab_file-stype,
            w_file_k TO gs_outtab_file-text,
            'TEXT' TO ls_coltab_file-fieldname,
            '1' TO ls_coltab_file-color-col,
            '1' TO ls_coltab_file-color-int.
      APPEND ls_coltab_file TO lt_coltab_file.
      MOVE lt_coltab_file TO gs_outtab_file-color.
      APPEND gs_outtab_file TO gt_outtab_file.

    WHEN '1'.
      CLEAR : gs_outtab_file,ls_coltab_file,lt_coltab_file.
      WRITE  file_k TO w_file_k.
      MOVE: stype TO gs_outtab_file-stype,
            w_file_k TO gs_outtab_file-text,
            'TEXT' TO ls_coltab_file-fieldname,
            '1' TO ls_coltab_file-color-col,
            '1' TO ls_coltab_file-color-int.
      APPEND ls_coltab_file TO lt_coltab_file.
      MOVE lt_coltab_file TO gs_outtab_file-color.
      APPEND gs_outtab_file TO gt_outtab_file.

    WHEN '2'.
      CLEAR : gs_outtab_file.
      WRITE  file_k TO w_file_k.
      MOVE : stype TO gs_outtab_file-stype,
             w_file_k+0(6) TO gs_outtab_file-text+0(6).

      SHIFT w_file_k BY 6 PLACES.
      MOVE : w_file_k TO gs_outtab_file-text+6(72).
      APPEND gs_outtab_file TO gt_outtab_file.

      SHIFT file_k BY 70 PLACES.
      WRITE file_k TO w_file_k.

      WHILE NOT w_file_k IS INITIAL.
        CLEAR : gs_outtab_file.
        MOVE : stype TO gs_outtab_file-stype,
               w_file_k TO gs_outtab_file-text.
        APPEND gs_outtab_file TO gt_outtab_file.

        SHIFT file_k BY 78 PLACES.
        WRITE file_k TO w_file_k.
      ENDWHILE.

    WHEN OTHERS.
  ENDCASE.

************* End ALV Coding C5056168 28/02/2005*******************
ENDFORM.                    "write_file

*---------------------------------------------------------------------*
*       Form  err-table
*---------------------------------------------------------------------*
*       ERRORTABLE contains all personnel numbers which were NOT      *
*       transfered to output file.                                    *
*       found = '1' -> infotype was found                             *
*       found = '0' -> infotype was not found                         *
*---------------------------------------------------------------------*
FORM err-table USING infotype begda endda found.
  DATA message_date_b(10).
  DATA message_date_e(10).
  WRITE begda TO message_date_b DD/MM/YYYY.
  WRITE endda TO message_date_e DD/MM/YYYY.

* 0 = not found / A = not activ / I = incomplete
  CHECK found EQ '0' OR found EQ 'A' OR found EQ 'I'.

  IF infotype = '0009' AND no_9_ok IS NOT INITIAL .  "GLW note 2063439
    CLEAR p0009.
    w_o_it9 = 'X'.
    RETURN.
  ENDIF.

  LOOP AT errortable WHERE pernr EQ pernr-pernr.
    errortable-name  = p0001-ename.
    CASE infotype.
      WHEN '0001'.
        errortable-p0001 = found.
      WHEN '0002'.
        errortable-p0002 = found.
      WHEN '0006'.
        errortable-p0006 = found.
      WHEN '0009'.
        errortable-p0009 = found.
      WHEN 'XXXX'.
        errortable-pxxxx = found.
    ENDCASE.
    MODIFY errortable.
  ENDLOOP.
  IF sy-subrc NE 0.
* new entry in err-table
    CLEAR errortable.
    errortable-pernr = pernr-pernr.
    errortable-name  = p0001-ename.
    CASE infotype.
      WHEN '0001'.
        errortable-p0001 = found.
      WHEN '0002'.
        errortable-p0002 = found.
      WHEN '0006'.
        errortable-p0006 = found.
      WHEN '0009'.
        errortable-p0009 = found.
      WHEN 'XXXX'.
        errortable-pxxxx = found.
    ENDCASE.
    APPEND errortable.
  ENDIF.

ENDFORM.                    "err-table

*---------------------------------------------------------------------*
*       FORM DISPLAY_MESSAGES                                         *
*---------------------------------------------------------------------*
FORM display_messages.
* display of all Messages
  DATA: sw_error(1).
  DATA: error_text(100).
************* Start ALV Coding C5056168 08/03/2005*****************

  DATA : lr_grid TYPE REF TO cl_salv_form_layout_grid,
         lr_abap TYPE REF TO cl_salv_form_abap.
************* End ALV Coding C5056168 08/03/2005*******************

  DESCRIBE TABLE error_int LINES lin.
  CHECK lin NE 0.

  CALL FUNCTION 'HR_DISPLAY_ERROR_LIST'
    EXPORTING
      no_popup = 'X'
      no_print = space
************* Start ALV Coding C5056168 08/03/2005*****************
      linesize = 80
************* End ALV Coding C5056168 08/03/2005*******************
    TABLES
      error    = error_int.

  LOOP AT error_int.
    IF error_int-msgty EQ 'E'.
      sw_error = 'X'.
    ENDIF.
  ENDLOOP.
  IF NOT sw_error IS INITIAL AND sw_stop IS NOT INITIAL. "GLW note 1989485
************* Start commenting C5056168 28/02/2005*****************
*    WRITE: /1(80) sy-uline.
*    FORMAT COLOR COL_NEGATIVE.
*    WRITE 'Arbeitsdatei'(f02)    TO error_text.
*    WRITE file_o                 TO error_text+20.
*    WRITE 'nicht benutzen!'(f03) TO error_text+65.
*    CONDENSE error_text.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE: 2(77) error_text.
*    WRITE: sy-vline.
*    WRITE: /1(80) sy-uline.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************
    WRITE 'Arbeitsdatei'(f02)    TO error_text.
    WRITE file_o                 TO error_text+20.
    WRITE 'nicht benutzen!'(f03) TO error_text+65.
    CONDENSE error_text.

    CREATE OBJECT lr_grid.

    CALL METHOD lr_grid->create_text
      EXPORTING
        row     = 2
        column  = 1
        text    = error_text
        tooltip = error_text.

    CREATE OBJECT lr_abap.

    lr_abap->set_content( lr_grid ).
    lr_abap->display( ).

************* End ALV Coding C5056168 28/02/2005*****************
  ENDIF.
ENDFORM.                    "display_messages

*---------------------------------------------------------------------*
*       FORM DISPLAY_ERR_TABLE                                        *
*---------------------------------------------------------------------*
FORM display_err_table.
* work line
  DATA: w_line(200).
* work counter
  DATA: lin1 TYPE p.
  DATA: lin2 TYPE p.
  DATA: lin3 TYPE p.                                        "QIZK082452
* print err-tables
  DESCRIBE TABLE errortable     LINES lin.
  DESCRIBE TABLE lockedtable    LINES lin1.
  DESCRIBE TABLE apaccounttable LINES lin2.
  DESCRIBE TABLE apaccount_without_pernr LINES lin3.        "QIZK082452
* CHECK  lin GT 0 OR lin1 GT 0 OR lin2 GT 0.                "QIZK082452
  CHECK  lin GT 0 OR lin1 GT 0 OR lin2 GT 0 OR lin3 GT 0.   "QIZK082452
************* Start commenting C5056168 28/02/2005*****************
*  NEW-PAGE.
*  SKIP.
*  CLEAR w_line.
*  FORMAT RESET.
*  WRITE: 'Liste der abgelehnten Mitarbeiter'(h10) TO w_line.
*  WRITE: 2(80) w_line CENTERED.
** List of employees with missing master-data
*  IF NOT lin IS INITIAL.
*    SKIP.
*    WRITE:/1(80) sy-uline.
*    FORMAT COLOR COL_HEADING INTENSIFIED.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE: 2'Fehlende Stammdaten am Selektionsstichtag'(h04).
*    WRITE: pn-begda DD/MM/YYYY.
*    WRITE:  80 sy-vline.
*    FORMAT COLOR COL_HEADING INTENSIFIED OFF.
*    WRITE:/1(80) sy-uline.
*
*    WRITE:/ sy-vline NO-GAP,
*            2 'PerNr.'(p01),
*            10 sy-vline,
*            11'Name'(p02),
*            35 sy-vline,
*            36'Org.Zuo/'(p03),
*            44 sy-vline,
*            45'Daten z.'(p05),
*            53 sy-vline,
*            54'ständ.'(p07),
*            62 sy-vline,
*            63'Bankver-'(p09),
*            71 sy-vline,
*            72'Hausbank'(p11),
*            80 sy-vline.
*
*    WRITE:/ sy-vline NO-GAP,
*            10 sy-vline,
*            35 sy-vline,
*            36'Maßnahme'(p04),
*            44 sy-vline,
*            45'Person'(p06),
*            53 sy-vline,
*            54'Wohnsitz'(p08),
*            62 sy-vline,
*            63'bindung'(p10),
*            71 sy-vline,
*            72'-> TRVHB'(p12).
*    WRITE: 80 sy-vline, /1(80) sy-uline.
*
*    LOOP AT errortable.
*      FORMAT COLOR 2 INTENSIFIED OFF.
*      WRITE:/ sy-vline NO-GAP.
*      WRITE:  2 errortable-pernr,
*             10 sy-vline,
*             11 errortable-name(24).
*      FORMAT COLOR 2 INTENSIFIED OFF.
** Org. Assignment
*      IF NOT errortable-p0001 EQ '0' AND NOT errortable-p0001 EQ 'A'.
*        WRITE: 35 sy-vline,
*               36(8)'X'.
*      ELSE.
*        WRITE: 35 sy-vline.
*        FORMAT COLOR COL_NEGATIVE INTENSIFIED.
*        IF errortable-p0001 EQ 'A'.
*          WRITE: 36(8) 'n.aktiv'(f04).
*        ELSE.
*          WRITE: 36(8) 'fehlt'(f01).
*        ENDIF.
*      ENDIF.
*      FORMAT COLOR 2 INTENSIFIED OFF.
** Personal Data
*      IF NOT errortable-p0002 EQ '0'.
*        WRITE: 44 sy-vline,
*               45(8)'X'.
*      ELSE.
*        WRITE: 44 sy-vline.
*        FORMAT COLOR COL_NEGATIVE INTENSIFIED.
*        WRITE: 45(8) 'fehlt'(f01).
*      ENDIF.
*      FORMAT COLOR 2 INTENSIFIED OFF.
** Addresses: Permanent residence
*      IF NOT errortable-p0006 EQ '0'.
*        WRITE: 53 sy-vline,
*               54(8)'X'.
*      ELSE.
*        WRITE: 53 sy-vline.
*        FORMAT COLOR COL_NEGATIVE INTENSIFIED.
*        WRITE: 54(8) 'fehlt'(f01).
*      ENDIF.
*      FORMAT COLOR 2 INTENSIFIED OFF.
** Bank Details
*      IF NOT errortable-p0009 EQ '0' AND NOT errortable-p0009 EQ 'I'.
*        WRITE: 62 sy-vline,
*               63(8)'X'.
*      ELSE.
*        WRITE: 62 sy-vline.
*        FORMAT COLOR COL_NEGATIVE INTENSIFIED.
*        IF errortable-p0009 EQ 'I'.
*          WRITE: 63(8) 'unvollst'(f14).
*        ELSE.
*          WRITE: 63(8) 'fehlt'(f01).
*        ENDIF.
*      ENDIF.
*      FORMAT COLOR 2 INTENSIFIED OFF.
** House bank
*      IF NOT errortable-pxxxx EQ '0'.
*        WRITE: 71 sy-vline,
*               72(8)'X'.
*      ELSE.
*        WRITE: 71 sy-vline.
*        FORMAT COLOR COL_NEGATIVE INTENSIFIED.
*        WRITE: 72(8) 'fehlt'(f01).
*      ENDIF.
*      FORMAT COLOR 2 INTENSIFIED OFF.
*      WRITE: 80 sy-vline.
*      WRITE: /1(80) sy-uline.
*    ENDLOOP.
*  ENDIF.
** List of all locked personnel numbers
*  DESCRIBE TABLE lockedtable LINES lin.
*  IF NOT lin IS INITIAL.
*    SKIP.
*    FORMAT COLOR COL_HEADING INTENSIFIED.
*    WRITE:/1(80) sy-uline.
** fill w_line
*    WRITE: 'Gesperrte Pesonalnummern:'(l01) TO w_line.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE:  2 w_line(78).
*    WRITE:  80 sy-vline, /1(80) sy-uline.
** fill w-line
*    CLEAR w_line.
*    FORMAT COLOR COL_HEADING INTENSIFIED OFF.
** header 2
*    WRITE:/ sy-vline NO-GAP,
*            2 'PerNr.'(p01),
*            10 sy-vline,
*            11'Name'(p02).
*    WRITE:  80 sy-vline, /1(80) sy-uline.
** lockedtable
*    LOOP AT lockedtable.
*      FORMAT COLOR 2 INTENSIFIED OFF.
*      WRITE:/ sy-vline NO-GAP.
*      WRITE:  2 lockedtable-pernr,
*             10 sy-vline,
*             11 lockedtable-name.
*      WRITE: 80 sy-vline, /1(80) sy-uline.
*    ENDLOOP.
*  ENDIF.
** Create: List of all personnel numbers which already have vendor
**         accounts
** Change: List of all personnel numbers which don't have vendor
**         accounts
*  DESCRIBE TABLE apaccounttable LINES lin.
*  IF NOT lin IS INITIAL.
*    SKIP.
*    FORMAT COLOR COL_HEADING INTENSIFIED.
*    WRITE:/1(80) sy-uline.
** fill w_line
*    CASE t_code.
*      WHEN 'XK01'.
*        WRITE: 'Mitarbeiter, die bereits einen Kreditorenstamm'(l02)
*                  TO w_line.
*        WRITE: 'besitzen'(l03) TO w_line+60.
*        CONDENSE w_line.
*      WHEN 'XK02'.
*        WRITE: 'Mitarbeiter, die noch keinen Kreditorenstamm'(l12)
*               TO w_line.
*        WRITE: 'besitzen'(l03) TO w_line+60.
*        CONDENSE w_line.
*      WHEN 'XK05'.
*        WRITE: 'Mitarbeiter, die noch keinen Kreditorenstamm'(l12)
*               TO w_line.
*        WRITE: 'besitzen'(l03) TO w_line+60.
*        CONDENSE w_line.
*    ENDCASE.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE:  2 w_line(78).
*    WRITE:  80 sy-vline, /1(80) sy-uline.
** fill w-line
*    CLEAR w_line.
*    FORMAT COLOR COL_HEADING INTENSIFIED OFF.
** header 2
*    WRITE:/ sy-vline NO-GAP,
*            2 'PerNr.'(p01),
*            10 sy-vline,
*            11'Name'(p02).
*    WRITE:  80 sy-vline, /1(80) sy-uline.
** apaccounttable
*    LOOP AT apaccounttable.
*      FORMAT COLOR 2 INTENSIFIED OFF.
*      WRITE:/ sy-vline NO-GAP.
*      WRITE:  2 apaccounttable-pernr,
*             10 sy-vline,
*             11 apaccounttable-name.
*      WRITE: 80 sy-vline, /1(80) sy-uline.
*    ENDLOOP.
*  ENDIF.
** QIZK082452 begin...
*  DESCRIBE TABLE apaccount_without_pernr LINES lin.
*  IF NOT lin IS INITIAL.
*    SKIP.
*    FORMAT COLOR COL_HEADING INTENSIFIED.
*    WRITE:/1(80) sy-uline.
** fill w_line
*    WRITE: 'Mitarbeiter, die bereits einen Kreditorenstamm'(l02)
*           TO w_line.
*    WRITE: 'besitzen'(l03) TO w_line+60.
*    CONDENSE w_line.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE:  2 w_line(78).
*    WRITE:  80 sy-vline, /1(80) sy-uline.
** fill w-line
*    CLEAR w_line.
*    WRITE:
* 'Die Angabe der Personalnummer fehlt im Buchungskreissegment!'(l04)
*    TO w_line.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE:  2 w_line(78).
*    WRITE:  80 sy-vline, /1(80) sy-uline.
** fill w-line
*    CLEAR w_line.
*    FORMAT COLOR COL_HEADING INTENSIFIED OFF.
** header 2
*    WRITE:/ sy-vline NO-GAP,
*            2 'PerNr.'(p01),
*            10 sy-vline,
*            11'Name'(p02),
*            45'Kreditor'(p20),
*            55'Buchungskreissegment'(p21).
*    WRITE:  80 sy-vline, /1(80) sy-uline.
** apaccount_without_pernr
*    LOOP AT apaccount_without_pernr.
*      FORMAT COLOR 2 INTENSIFIED OFF.
*      WRITE:/ sy-vline NO-GAP.
*      WRITE:  2 apaccount_without_pernr-pernr,
*             10 sy-vline,
*             11 apaccount_without_pernr-name,
*             45 apaccount_without_pernr-vendor_no,
*             55 apaccount_without_pernr-bukrs.
*      WRITE: 80 sy-vline, /1(80) sy-uline.
*    ENDLOOP.
*  ENDIF.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************

* List of employees with missing master-data
  IF NOT lin IS INITIAL.

    CLEAR : gs_outtab_error,gt_outtab_error.

    LOOP AT errortable.
      CLEAR : gs_outtab_error.

      MOVE : errortable-pernr TO gs_outtab_error-pernr,
             errortable-name TO gs_outtab_error-name.

* Org. Assignment
      IF NOT errortable-p0001 EQ '0' AND NOT errortable-p0001 EQ 'A'.
        MOVE : 'X' TO gs_outtab_error-action.
      ELSE.
        IF errortable-p0001 EQ 'A'.
          MOVE :  'n.aktiv'(f04) TO gs_outtab_error-action.
        ELSE.
          MOVE : 'fehlt'(f01) TO gs_outtab_error-action.
        ENDIF.
      ENDIF.

* Personal Data
      IF NOT errortable-p0002 EQ '0'.
        MOVE : 'X' TO gs_outtab_error-person_data.
      ELSE.
        MOVE : 'fehlt'(f01) TO gs_outtab_error-person_data.
      ENDIF.

* Addresses: Permanent residence
      IF NOT errortable-p0006 EQ '0'.
        MOVE : 'X' TO gs_outtab_error-perm_resi.
      ELSE.
        MOVE : 'fehlt'(f01) TO gs_outtab_error-perm_resi.
      ENDIF.

* Bank Details
      IF NOT errortable-p0009 EQ '0' AND NOT errortable-p0009 EQ 'I'.
        MOVE : 'X' TO gs_outtab_error-bank_details.
      ELSE.
        IF errortable-p0009 EQ 'I'.
          MOVE : 'unvollst'(f14) TO gs_outtab_error-bank_details.
        ELSE.
          MOVE : 'fehlt'(f01) TO gs_outtab_error-bank_details.
        ENDIF.
      ENDIF.

* House bank
      IF NOT errortable-pxxxx EQ '0'.
        MOVE : 'X' TO gs_outtab_error-house_bank.
      ELSE.
        MOVE : 'fehlt'(f01) TO gs_outtab_error-house_bank.
      ENDIF.

      APPEND gs_outtab_error TO gt_outtab_error.
    ENDLOOP.

  ENDIF.

* List of all locked personnel numbers
  DESCRIBE TABLE lockedtable LINES lin.
  IF NOT lin IS INITIAL.

* lockedtable
    CLEAR : gs_outtab_lock,gt_outtab_lock.
    LOOP AT lockedtable.
      CLEAR : gs_outtab_lock.
      MOVE : lockedtable-pernr TO gs_outtab_lock-pernr,
             lockedtable-name TO gs_outtab_lock-name.

      APPEND gs_outtab_lock TO gt_outtab_lock.
    ENDLOOP.
  ENDIF.

* Create: List of all personnel numbers which already have vendor
*         accounts
* Change: List of all personnel numbers which don't have vendor
*         accounts
  DESCRIBE TABLE apaccounttable LINES lin.
  IF NOT lin IS INITIAL.

* apaccounttable
    CLEAR : gs_outtab_apaccount,gt_outtab_apaccount.

    LOOP AT apaccounttable.
      CLEAR : gs_outtab_apaccount.
      MOVE :  apaccounttable-pernr TO gs_outtab_apaccount-pernr,
              apaccounttable-name TO gs_outtab_apaccount-name.

      APPEND gs_outtab_apaccount TO gt_outtab_apaccount.
    ENDLOOP.

  ENDIF.

* QIZK082452 begin...
  DESCRIBE TABLE apaccount_without_pernr LINES lin.
  IF NOT lin IS INITIAL.

* apaccount_without_pernr
    CLEAR : gs_outtab_apac_without_pernr,gt_outtab_apac_without_pernr.

    LOOP AT apaccount_without_pernr.
      CLEAR : gs_outtab_apac_without_pernr.

      MOVE  : apaccount_without_pernr-pernr TO
              gs_outtab_apac_without_pernr-pernr,

              apaccount_without_pernr-name TO
              gs_outtab_apac_without_pernr-name,

              apaccount_without_pernr-vendor_no TO
              gs_outtab_apac_without_pernr-vendor_no,

              apaccount_without_pernr-bukrs TO
              gs_outtab_apac_without_pernr-bukrs.

      APPEND gs_outtab_apac_without_pernr TO gt_outtab_apac_without_pernr.
    ENDLOOP.

  ENDIF.
************* End ALV Coding C5056168 28/02/2005*****************

* QIZK082452 end...
ENDFORM.                    "display_err_table

*----------------------------------------------------------------------*
*       Form  DISPLAY_LOG_TABLE
*----------------------------------------------------------------------*
FORM display_log_table.
* work line
  DATA: w_line(200).
  DESCRIBE TABLE logtable LINES lin.
  CHECK lin GT 0.
************* Start commenting C5056168 28/02/2005*****************
*  IF NOT actmode IS INITIAL.
*    FORMAT COLOR COL_HEADING INTENSIFIED.
*    WRITE:/1(80) sy-uline.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE:  'Der Job'(j01) TO w_line.
*    WRITE:  jobname TO w_line+20.
*    WRITE:  'wurde angestartet'(j02) TO w_line+40.
*    CONDENSE w_line.
*    WRITE: 2(78) w_line.
*    WRITE:  80 sy-vline, /1(80) sy-uline.
*    CLEAR w_line.
*  ENDIF.
** header 1
*  SKIP.
*  FORMAT RESET.
** fill w-line
*  CLEAR w_line.
*  WRITE: 'Arbeitsdatei'(h02) TO w_line.
*  WRITE: file_o TO w_line+40.
*  WRITE: 'enthält folgende Mitarbeiter'(h03) TO w_line+90.
*  CONDENSE w_line.
*  WRITE: 2(78) w_line CENTERED.
*  SKIP.
*  FORMAT COLOR COL_HEADING INTENSIFIED.
*  WRITE:/1(80) sy-uline.
*  WRITE: 'Selektionsstichtag: '(h01) TO w_line.
*  WRITE: pn-begda DD/MM/YYYY TO w_line+40.
*  CONDENSE w_line.
*  WRITE:/ sy-vline NO-GAP.
*  WRITE:  2 w_line(78).
*  WRITE:  80 sy-vline, /1(80) sy-uline.
*
*  FORMAT COLOR COL_HEADING INTENSIFIED OFF.
** header 2
*  WRITE:/ sy-vline NO-GAP,
*          2 'PerNr.'(p01),
*          10 sy-vline,
*          11'Name'(p02).
*  WRITE:  80 sy-vline, /1(80) sy-uline.
** logtable
*  LOOP AT logtable.
*    FORMAT COLOR 2 INTENSIFIED OFF.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE:  2 logtable-pernr,
*           10 sy-vline,
*           11 logtable-name.
*    WRITE: 80 sy-vline, /1(80) sy-uline.
*  ENDLOOP.
*  IF NOT sy-subrc IS INITIAL.
*    FORMAT COLOR 2 INTENSIFIED OFF.
*    WRITE:/ sy-vline NO-GAP.
*    WRITE:  'Es wurde kein Kreditorenstammsatz'(k01),
*            'erzeugt'(k02).
*    WRITE: 80 sy-vline, /1(80) sy-uline.
*  ENDIF.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************
* logtable

*Fill up ALV Outtab table
  CLEAR : gs_outtab_log, gt_outtab_log.
  LOOP AT logtable.
    CLEAR : gs_outtab_log.
    MOVE :  logtable-pernr TO gs_outtab_log-pernr,
            logtable-name TO gs_outtab_log-name.
    APPEND gs_outtab_log TO gt_outtab_log.
  ENDLOOP.

  IF NOT sy-subrc IS INITIAL.
    CONCATENATE TEXT-k01 TEXT-k02 INTO gv_log_fail_message.
  ENDIF.

************* End ALV Coding C5056168 28/02/2005*******************

ENDFORM.                    "display_log_table

*----------------------------------------------------------------------*
*       Form  LOG_TABLE
*----------------------------------------------------------------------*
FORM log_table.
  LOOP AT errortable WHERE pernr EQ pernr-pernr.
  ENDLOOP.
  IF sy-subrc NE 0.
* personnel number O.K.
    logtable-pernr = pernr-pernr.
    logtable-name  = p0001-ename.
    APPEND logtable.
  ELSE.
* go to the next personnel number
    sel_rejected = sel_rejected + 1.
    REJECT.
  ENDIF.
ENDFORM.                    "log_table

*----------------------------------------------------------------------*
*       Form  READ_HOUSE_BANK
*----------------------------------------------------------------------*
*       This routine determines the house bank via feature TRVHB       *
*----------------------------------------------------------------------*
FORM read_house_bank USING found.
  CLEAR pme11.
  CLEAR trvhb.
  pme11-abkrs = p0001-abkrs.
  pme11-bankl = p0009-bankl.
  pme11-banks = p0009-banks.
  pme11-zlsch = p0009-zlsch.                                "QIZK012820
  pme11-waers = p0009-waers.                                "QIZK012820
  pme11-btrtl = p0001-btrtl.
  pme11-bukrs = p0001-bukrs.
  pme11-gsber = p0001-gsber.
  pme11-juper = p0001-juper.
  pme11-kostl = p0001-kostl.
  pme11-persg = p0001-persg.
  pme11-persk = p0001-persk.
  pme11-vdsk1 = p0001-vdsk1.
  pme11-werks = p0001-werks.
  pme11-molga = t500p-molga.
  PERFORM re549d USING 'TRVHB' ' ' trvhb pack.
  IF pack NE 0.
    CLEAR trvhb.
  ENDIF.
  IF pack EQ '0'.
    found = '1'.
  ELSE.
    found = '0'.
  ENDIF.
ENDFORM.                    "read_house_bank

*&---------------------------------------------------------------------*
*&      Form  RE001
*&---------------------------------------------------------------------*
FORM  re001
USING VALUE(bukrs)
      ort01 ktopl land1 waers periv spras.
  CHECK t001_bukrs <> bukrs.
  CALL FUNCTION 'HRCA_COMPANYCODE_GETDETAIL'
    EXPORTING
      companycode = bukrs
      language    = sy-langu
    IMPORTING
      comp_name   = t001_butxt
      city        = t001_ort01
      country     = t001_land1
      currency    = t001_waers
      langu       = t001_spras
      chrt_accts  = t001_ktopl
      fy_variant  = t001_periv
    EXCEPTIONS
      not_found   = 1
      OTHERS      = 2.

  t001_bukrs = bukrs.

  IF sy-subrc <> 0.
    PERFORM fill_error_int USING pernr-pernr
                                 '56_CORE'                  "QIZK001223
                                 'E'
                                 '101'                      "QIZK001223
                                 'T001'
                                 bukrs
                                 space
                                 space.
*    sw_stop = 'X'.                                         "PGE Note 2933331
*   STOP.                                                   "MAWK022558
    PERFORM stop_or_reject.                                 "MAWK022558
  ENDIF.
  ort01 = t001_ort01.
  ktopl = t001_ktopl.
  land1 = t001_land1.
  waers = t001_waers.
  periv = t001_periv.
  spras = t001_spras.
ENDFORM.                                                    "re001

*&---------------------------------------------------------------------*
*&      Form  NODATA_TEMPLATE
*&---------------------------------------------------------------------*
*       text                                                           *
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM nodata_template USING blfxx lfx1.
  DATA: w_date LIKE blfb1-datlz.
  DATA: w_curr LIKE blfb1-webtr.
  DATA: w_dec  LIKE blfb1-kultg.
  DATA: lf_fields_help TYPE c LENGTH 47.                    "MAWK013477


  CHECK NOT ( blfxx EQ 'BLFA1' AND
*      list of all fields in LFA1, which will be filled
*      by HR-master-data
              ( dd03l-fieldname EQ 'ANRED' OR
                dd03l-fieldname EQ 'NAME1' OR
                dd03l-fieldname EQ 'NAME2' OR
                dd03l-fieldname EQ 'NAME3' OR
                dd03l-fieldname EQ 'NAME4' OR
                dd03l-fieldname EQ 'SORTL' OR
                dd03l-fieldname EQ 'STRAS' OR
                dd03l-fieldname EQ 'PFACH' OR
                dd03l-fieldname EQ 'ORT01' OR
                dd03l-fieldname EQ 'PSTLZ' OR
                dd03l-fieldname EQ 'ORT02' OR
                dd03l-fieldname EQ 'PSTL2' OR
                dd03l-fieldname EQ 'LAND1' OR
                dd03l-fieldname EQ 'REGIO' OR
                dd03l-fieldname EQ 'SPRAS' OR
                dd03l-fieldname EQ 'TELX1' OR
                dd03l-fieldname EQ 'TELF1' OR
                dd03l-fieldname EQ 'TELFX' OR
                dd03l-fieldname EQ 'TELF2' OR
                dd03l-fieldname EQ 'TELTX' OR
                dd03l-fieldname EQ 'TELBX' OR
                dd03l-fieldname EQ 'DATLT' ) ).
*  fields_lfa_b1(1)    = '*'.                               "MAWK013477
*  fields_lfa_b1+1(5)  = lfx1.                              "MAWK013477
*  fields_lfa_b1+5(1)  = '-'.                               "MAWK013477
*  fields_lfa_b1+6(10) = dd03l-fieldname.                   "MAWK013477
  CONCATENATE '*' lfx1 INTO lf_fields_help.                 "MAWK013477
  CONCATENATE lf_fields_help dd03l-fieldname                "MAWK013477
         INTO fields_lfa_b1 SEPARATED BY '-'.               "MAWK013477
  ASSIGN (fields_lfa_b1) TO <templ_fields>.
  CHECK sy-subrc IS INITIAL. "GLW note 2336952
  IF NOT ( <templ_fields> IS INITIAL ).
* There is a template-value
    <str_fields> = <templ_fields>.
    SELECT * FROM dd03l WHERE tabname EQ lfx1
             AND  as4local  EQ 'A'
*            AND  fieldname EQ fields_lfa_b1+6(10)          "MAWK013477
             AND  fieldname EQ dd03l-fieldname              "MAWK013477
             AND  ( datatype EQ 'DATS' OR
                    datatype EQ 'CURR' OR
                    datatype EQ 'DEC' ).
      IF dd03l-datatype EQ 'DATS'.
        WRITE <templ_fields> TO w_date.
        <str_fields> = w_date.
      ENDIF.
      IF dd03l-datatype EQ 'CURR'.
        WRITE <templ_fields> CURRENCY t001_waers TO w_curr.
        <str_fields> = w_curr.
      ENDIF.
      IF dd03l-datatype EQ 'DEC'.
        UNPACK <templ_fields> TO w_dec.
        <str_fields> = w_dec.
      ENDIF.
    ENDSELECT.
  ELSE.
    CLEAR lf_fields_help.                                   "MAWK013477
* the template-value is initial
    CASE lfx1.
      WHEN 'LFA1'.
*       old_fields(15)    = 'old_vendor_lfa1'.              "MAWK013477
        lf_fields_help    = 'old_vendor_lfa1'.              "MAWK013477
      WHEN 'LFB1'.
*       old_fields(15)    = 'old_vendor_lfb1'.              "MAWK013477
        lf_fields_help    = 'old_vendor_lfb1'.              "MAWK013477
      WHEN 'LFB5'.                                          "QIZK003419
*       old_fields(15)    = 'old_vendor_lfb5'.  "QIZK003419 "MAWK013477
* Start of MAWK015825
*       lf_fields_help    = 'old_vendor_lfb1'.              "MAWK013477
        lf_fields_help    = 'old_vendor_lfb5'.              "MAWK013477
* End of MAWK015825
      WHEN 'LFBW'.                                          "QIZK047575
        EXIT.                                               "QIZK047575
    ENDCASE.
*    old_fields+15(1)  = '-'.                               "MAWK013477
*    old_fields+16(10) = dd03l-fieldname.                   "MAWK013477
    CONCATENATE lf_fields_help dd03l-fieldname              "MAWK013477
           INTO old_fields SEPARATED BY '-'.                "MAWK013477
    ASSIGN (old_fields) TO <old_vendor_fields>.
    IF NOT <old_vendor_fields> IS INITIAL.
      <str_fields> = space.
    ENDIF.
  ENDIF.
ENDFORM.                    "nodata_template

*----------------------------------------------------------------------*
*       Form  AUTH_A_P_ACCOUNT
*----------------------------------------------------------------------*
*       authorization-check for the template a/p-account               *
*----------------------------------------------------------------------*
FORM auth_a_p_account_lfa1.
*------- Berechtigungsprüfung: A-Segment (BEGRU) ----------------------
  IF lfa1-begru NE space.
    AUTHORITY-CHECK OBJECT 'F_LFA1_BEK'
      ID 'BRGRU' FIELD lfa1-begru
      ID 'ACTVT' FIELD '03'.
    IF sy-subrc NE 0.
      PERFORM fill_error_int USING space
                                   'F2'
                                   'E'
                                   '342'
                                   'F_LFA1_BEK'
                                   lfa1-begru
                                   '03'
                                   space.
      sw_stop = 'X'.
      STOP.
    ENDIF.
  ENDIF.
ENDFORM.                    "auth_a_p_account_lfa1

*----------------------------------------------------------------------*
*       Form  CHECK_EXISTENCE
*----------------------------------------------------------------------*
*       Does the employee already exists as a vendor?                  *
*----------------------------------------------------------------------*
FORM check_existence USING pernr bukrs subrc.
  CLEAR lfb1.
  CLEAR old_vendor_lfa1.
  CLEAR old_vendor_lfb1.
  CLEAR old_vendor_lfb5.                                    "QIZK082452
  SELECT * FROM lfb1
          WHERE bukrs EQ bukrs
          AND   pernr EQ pernr
          AND   loevm EQ space                            "GLWE4AK124045
          AND   sperr EQ space.
    MOVE-CORRESPONDING lfb1 TO old_vendor_lfb1.
    EXIT.
  ENDSELECT.

* GLWE4AK124045 beg
  IF sy-subrc IS NOT INITIAL.
* try independently from the delete makrer:
    SELECT * FROM lfb1
           WHERE bukrs EQ bukrs
           AND   pernr EQ pernr.
      MOVE-CORRESPONDING lfb1 TO old_vendor_lfb1.
      EXIT.
    ENDSELECT.
* GLW note 1777015 begin
    IF sy-subrc IS INITIAL AND t_code = 'XK02'.  "we change vendor and there is a vendor to change, but no vendor, which is not locked or deleted!
      IF no_del IS NOT INITIAL AND no_lock IS NOT INITIAL. "we don't want to update deleted and locked vendors
        REJECT.
      ELSEIF no_lock IS NOT INITIAL. " We don't want to update locked vendors!
        SELECT *  FROM lfb1 WHERE
             bukrs EQ bukrs AND
             pernr EQ pernr AND
             sperr EQ space.
          EXIT.
        ENDSELECT.
        IF sy-subrc IS NOT INITIAL.
          REJECT.
        ENDIF.
        MOVE-CORRESPONDING lfb1 TO old_vendor_lfb1.
      ELSEIF no_del IS NOT INITIAL. "We don't wnat to update vendors marked for deletion.
        SELECT *  FROM lfb1 WHERE
           bukrs EQ bukrs AND
           pernr EQ pernr AND
           loevm EQ space.
          EXIT.
        ENDSELECT.
        IF sy-subrc IS NOT INITIAL.
          REJECT.
        ENDIF.
        MOVE-CORRESPONDING lfb1 TO old_vendor_lfb1.
      ENDIF.
* GLW note 1777015 end
    ENDIF.
* GLWE4AK124045 end
  ENDIF.
  subrc = sy-subrc.
  SELECT * FROM lfa1
           WHERE lifnr EQ old_vendor_lfb1-lifnr.
    MOVE-CORRESPONDING lfa1 TO old_vendor_lfa1.
  ENDSELECT.
  SELECT * FROM lfb5                                        "QIZK003419
           WHERE lifnr EQ old_vendor_lfb1-lifnr             "QIZK003419
           AND   bukrs EQ bukrs                             "QIZK003419
           AND   maber EQ space.                            "QIZK003419
    MOVE-CORRESPONDING lfb5 TO old_vendor_lfb5.             "QIZK003419
    EXIT.                                                   "QIZK003419
  ENDSELECT.                                                "QIZK003419

ENDFORM.                    "check_existence

*---------------------------------------------------------------------*
*       FORM CHECK_EXISTENCE_WITHOUT_BUKRS                            *
*---------------------------------------------------------------------*
*       QIZK082452                                                    *
*---------------------------------------------------------------------*
*  -->  PERNR                                                         *
*  -->  VENDOR_NO                                                     *
*---------------------------------------------------------------------*
FORM check_existence_without_bukrs USING pernr vendor_no.
  SELECT * FROM lfb1 WHERE pernr EQ pernr AND
                            loevm EQ space AND      "GLWE4AK124045
                            sperr EQ space.
* take the first one...
    EXIT.
  ENDSELECT.
* GLWE4AK124045 beg
  IF sy-subrc IS NOT INITIAL.
    SELECT * FROM lfb1 WHERE pernr EQ pernr.

* take the first one...
      EXIT.
    ENDSELECT.
  ENDIF.
* GLWE4AK124045 end
  IF sy-subrc IS INITIAL.
    vendor_no = lfb1-lifnr.
  ENDIF.
ENDFORM.                    "check_existence_without_bukrs

*---------------------------------------------------------------------*
*       FORM CHECK_EXISTENCE_WITH_BUKRS                               *
*---------------------------------------------------------------------*
*       QIZK082452                                                    *
*---------------------------------------------------------------------*
*  -->  VENDOR_NO                                                     *
*  -->  BUKRS                                                         *
*---------------------------------------------------------------------*
FORM check_existence_with_bukrs USING vendor_no bukrs.
  SELECT * FROM lfb1 WHERE lifnr EQ vendor_no
                     AND   bukrs EQ bukrs.
    EXIT.
  ENDSELECT.
  IF sy-subrc IS INITIAL.
    CASE t_code.
      WHEN 'XK01'.
        sel_ex_vendors = sel_ex_vendors + 1.
      WHEN 'XK02'.
        sel_no_vendors = sel_no_vendors + 1.
    ENDCASE.
    apaccount_without_pernr-pernr = pernr-pernr.
    apaccount_without_pernr-name  = p0001-ename.
    apaccount_without_pernr-vendor_no = vendor_no.
    apaccount_without_pernr-bukrs = bukrs.
    APPEND apaccount_without_pernr.
    REJECT.
  ENDIF.
ENDFORM.                    "check_existence_with_bukrs

*----------------------------------------------------------------------*
*       Form  STATISTICS
*----------------------------------------------------------------------*
*       text                                                           *
*----------------------------------------------------------------------*
FORM statistics.
  DATA: w_line(80).
************* Start commenting C5056168 28/02/2005*****************
*  NEW-PAGE.
*  SKIP.
*  FORMAT RESET.
** selected personnel numbers
*  WRITE: 'Selektierte Personalnummern'(s01) TO w_line+0,
*         ':'                               TO w_line+60.
*  IF sel_pernr EQ 0.
*    WRITE '     0'                         TO w_line+61.
*  ELSE.
*    WRITE sel_pernr                        TO w_line+61 NO-ZERO.
*  ENDIF.
*  WRITE:/2(76) w_line.
*  CLEAR w_line.
*  WRITE: 'davon...'(s07) TO w_line.
*  SKIP.
*  WRITE:/2(76) w_line.
*  SKIP.
*  CLEAR w_line.
** employees on output file
*  WRITE: 'Personalnummern auf der Arbeitsdatei'(s02) TO w_line+0,
*         ':'                               TO w_line+60.
*  IF sel_on_file EQ 0.
*    WRITE '     0'                         TO w_line+61.
*  ELSE.
*    WRITE sel_on_file                      TO w_line+61 NO-ZERO.
*  ENDIF.
*  WRITE:/2(76) w_line.
*  CLEAR w_line.
** locked personnel numbers
*  WRITE: 'gesperrte Personalnummern'(s06) TO w_line+0,
*         ':'                               TO w_line+60.
*  IF sel_locked EQ 0.
*    WRITE '     0'                         TO w_line+61.
*  ELSE.
*    WRITE sel_locked                       TO w_line+61 NO-ZERO.
*  ENDIF.
*  WRITE:/2(76) w_line.
*  CLEAR w_line.
*  IF t_code EQ 'XK02' AND ref_a_p IS INITIAL.
** employees, who don't have changes in HR-Master data
*    WRITE: 'Personalnummern ohne Änderungen seit dem'(s24) TO w_line+0,
*           aedat DD/MM/YYYY                  TO w_line+45.
*    CONDENSE w_line.
*    WRITE: ':'                               TO w_line+60.
*    IF sel_no_changes EQ 0.
*      WRITE '     0'                         TO w_line+61.
*    ELSE.
*      WRITE sel_no_changes                   TO w_line+61 NO-ZERO.
*    ENDIF.
*    WRITE:/2(76) w_line.
*    CLEAR w_line.
** QIZK032746 begin...
*    WRITE: text-s25  TO w_line+0.
*    CONDENSE w_line.
*    WRITE: ':'                               TO w_line+60.
*    IF sel_no_changes_for_today EQ 0.
*      WRITE '     0'                         TO w_line+61.
*    ELSE.
*      WRITE sel_no_changes_for_today         TO w_line+61 NO-ZERO.
*    ENDIF.
*    WRITE:/2(76) w_line.
*    CLEAR w_line.
** QIZK032746 end...
*  ENDIF.
** employees with incomplete master data
*  WRITE: 'Personalnummern mit fehlenden Stammdaten'(s03) TO w_line+0,
*         ':'                               TO w_line+60.
*  IF sel_rejected EQ 0.
*    WRITE '     0'                         TO w_line+61.
*  ELSE.
*    WRITE sel_rejected                     TO w_line+61 NO-ZERO.
*  ENDIF.
*  WRITE:/2(76) w_line.
*  CLEAR w_line.
*  IF t_code EQ 'XK01'.
** employees, who already have a vendor account
*    WRITE: 'Personalnummern mit bereits vorhandenem'(s04) TO w_line+0,
*           'Kreditorenstammsatz  '(s05)      TO w_line+40.
*    CONDENSE w_line.
*    WRITE: ':'                               TO w_line+60.
*    IF sel_ex_vendors EQ 0.
*      WRITE '     0'                         TO w_line+61.
*    ELSE.
*      WRITE sel_ex_vendors                   TO w_line+61 NO-ZERO.
*    ENDIF.
*    WRITE:/2(76) w_line.
*  ENDIF.
*  IF t_code EQ 'XK02' OR t_code EQ 'XK05'.
** employees, who don't have a vendor account
*    WRITE: 'Personalnummern ohne vorhandenen'(s14) TO w_line+0,
*           'Kreditorenstammsatz  '(s15)      TO w_line+40.
*    CONDENSE w_line.
*    WRITE: ':'                               TO w_line+60.
*    IF sel_no_vendors EQ 0.
*      WRITE '     0'                         TO w_line+61.
*    ELSE.
*      WRITE sel_no_vendors                   TO w_line+61 NO-ZERO.
*    ENDIF.
*    WRITE:/2(76) w_line.
*  ENDIF.
************* End commenting C5056168 28/02/2005*******************

************* Start ALV Coding C5056168 28/02/2005*****************
* selected personnel numbers
  CLEAR w_line.

  PERFORM add_statistical_message USING TEXT-s01 sel_pernr.

* employees on output file
  PERFORM add_statistical_message USING TEXT-s02 sel_on_file.

* locked personnel numbers
  PERFORM add_statistical_message USING TEXT-s06 sel_locked.

* GLW note 1989485
  IF sel_with_error > 0.
    PERFORM add_statistical_message USING TEXT-s08 sel_with_error.
  ENDIF.
* GLW note 1989485

  IF t_code EQ 'XK02' AND ref_a_p IS INITIAL.
* employees, who don't have changes in HR-Master data
    WRITE: 'Personalnummern ohne Änderungen seit dem'(s24) TO w_line+0,
           aedat DD/MM/YYYY                  TO w_line+45.
    CONDENSE w_line.

    PERFORM add_statistical_message USING w_line sel_no_changes.
    CLEAR w_line.

* QIZK032746 begin...

    PERFORM add_statistical_message USING TEXT-s25
                                          sel_no_changes_for_today.

* QIZK032746 end...
  ENDIF.
* employees with incomplete master data

* PERFORM add_statistical_message USING text-s02 sel_rejected. "MAWK003005
  PERFORM add_statistical_message USING TEXT-s03 sel_rejected. "MAWK003005

  IF t_code EQ 'XK01'.
* employees, who already have a vendor account
    WRITE: 'Personalnummern mit bereits vorhandenem'(s04) TO w_line+0,
           'Kreditorenstammsatz  '(s05)      TO w_line+40.
    CONDENSE w_line.

    PERFORM add_statistical_message USING w_line sel_ex_vendors.
    CLEAR : w_line.
  ENDIF.

  IF t_code EQ 'XK02' OR t_code EQ 'XK05'.
* employees, who don't have a vendor account
    WRITE: 'Personalnummern ohne vorhandenen'(s14) TO w_line+0,
           'Kreditorenstammsatz  '(s15)      TO w_line+40.
    CONDENSE w_line.

    PERFORM add_statistical_message USING w_line sel_no_vendors.
    CLEAR : w_line.
  ENDIF.

************* End ALV Coding C5056168 28/02/2005*******************

ENDFORM.                    "statistics

*----------------------------------------------------------------------*
*       Form  CHECK_LOCKED
*----------------------------------------------------------------------*
*       text                                                           *
*----------------------------------------------------------------------*
FORM check_locked.
  CHECK sy-batch IS INITIAL.
  PERFORM enqueue_pernr(sapfp50g) USING pernr-pernr ' '.
  IF sy-subrc <> 0.
* personnel number locked
    sel_locked = sel_locked + 1.
    lockedtable-pernr = pernr-pernr.
    lockedtable-name  = p0001-ename.
    APPEND lockedtable.
************* Start commenting C5056168 28/02/2005*****************
*    IF NOT file_pr IS INITIAL. ULINE. ENDIF.
************* End commenting C5056168 28/02/2005*******************
    REJECT.
  ELSE.
    PERFORM dequeue_pernr(sapfp50g) USING pernr-pernr.
  ENDIF.
ENDFORM.                    "check_locked

*----------------------------------------------------------------------*
*       Form  AUTH_A_P_ACCOUNT_LFB1
*----------------------------------------------------------------------*
FORM auth_a_p_account_lfb1.
*------- Berechtigungspruefung: Firmenebene (BUKRS, BEGRU) -------------
  IF lfb1-bukrs NE space.
    AUTHORITY-CHECK OBJECT 'F_LFA1_BUK'
      ID 'BUKRS' FIELD lfb1-bukrs
      ID 'ACTVT' FIELD '03'.
    IF sy-subrc NE 0.
      PERFORM fill_error_int USING pernr-pernr
                                   'F2'
                                   'E'
                                   '344'
                                   lfb1-bukrs
                                   '03'
                                   'F_LFA1_BUK'
                                   space.
      sw_stop = 'X'.
*     STOP.                                                 "MAWK022558
      PERFORM stop_or_reject.                               "MAWK022558
    ENDIF.
  ENDIF.
  IF lfb1-begru NE space.
    AUTHORITY-CHECK OBJECT 'F_LFA1_BEK'
      ID 'BRGRU' FIELD lfb1-begru
      ID 'ACTVT' FIELD '03'.
    IF sy-subrc NE 0.
      PERFORM fill_error_int USING pernr-pernr
                                   'F2'
                                   'E'
                                   '343'
                                   lfb1-bukrs
                                   'F_LFA1_BEK'
                                   lfb1-begru
                                   '03'.
      sw_stop = 'X'.
*     STOP.                                                 "MAWK022558
      PERFORM stop_or_reject.                               "MAWK022558
    ENDIF.
  ENDIF.
ENDFORM.                    "auth_a_p_account_lfb1

*----------------------------------------------------------------------*
*       Form  CHANGE-DATE
*----------------------------------------------------------------------*
FORM change-date USING infotype.
* further improvement by GLW note 3031698
  DATA yesterday TYPE d.

  yesterday = sy-datum - 1.   "GLW note 2614136

  CHECK daily IS INITIAL.                                   "QIZK032746

  CHECK t_code EQ 'XK02' AND w_changes IS INITIAL.
* only HR-Master data, which were changed after AEDAT
  CASE infotype.
    WHEN '0000'.
      LOOP AT p0000 WHERE aedtm GE aedat OR begda BETWEEN aedat AND sy-datum. "GLW note 3117949
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
    WHEN '0001'.
      LOOP AT p0001 WHERE aedtm GE aedat OR begda BETWEEN aedat AND sy-datum. "GLW note 3117949
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
    WHEN '0002'.
      LOOP AT p0002 WHERE aedtm GE aedat OR begda BETWEEN aedat AND sy-datum. "GLW note 3117949
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
    WHEN '0006'.
      LOOP AT p0006 WHERE aedtm GE aedat OR begda BETWEEN aedat AND sy-datum OR endda BETWEEN aedat AND yesterday.  "GLW note 2614136 "GLW note 3117949
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
    WHEN '0009'.
      LOOP AT p0009 WHERE aedtm GE aedat OR begda BETWEEN aedat AND sy-datum OR endda BETWEEN aedat AND yesterday.  "GLW note 2614136 "GLW note 3117949
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
  ENDCASE.
ENDFORM.                    "change-date

*&--------------------------------------------------------------------*
*&      Form  new-infotype-data
*&--------------------------------------------------------------------*
*       QIZK032746
*---------------------------------------------------------------------*
FORM new-infotype-data USING infotype begda.

  DATA: yesterday LIKE sy-datum.   "GLW note 2352796
  CHECK NOT daily IS INITIAL.

* if the preferred subtypes of infotypes 6 and 9 are delimited by yesterday without a new set starting today,
* beginning with today the default subtype gets valid. The current logic does not recognize this situation.
  yesterday = begda - 1.    "GLW note 2352796

  CHECK t_code EQ 'XK02' AND w_changes IS INITIAL.
* only HR-Master data, which have changes beginning at BEGDA...
  CASE infotype.
    WHEN '0000'.
      LOOP AT p0000 WHERE begda EQ begda.
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
    WHEN '0001'.
      LOOP AT p0001 WHERE begda EQ begda.
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
    WHEN '0002'.
      LOOP AT p0002 WHERE begda EQ begda.
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
    WHEN '0006'.
      LOOP AT p0006 WHERE begda EQ begda OR endda EQ yesterday.   "GLW note 2614136
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
*      IF w_changes IS INITIAL.   "GLW note 2352796
*        LOOP AT p0006 WHERE subty EQ p_subty6 AND endda EQ yesterday.
*          w_changes = w_changes + 1.
*        ENDLOOP.
*      ENDIF.
    WHEN '0009'.
      LOOP AT p0009 WHERE begda EQ begda OR endda EQ yesterday.  "GLW note 2614136
        EXIT.
      ENDLOOP.
      IF sy-subrc EQ 0.
        w_changes = w_changes + 1.
      ENDIF.
*      IF w_changes IS INITIAL.   "GLW note 2352796
*        LOOP AT p0009 WHERE subty EQ p_subty9 AND endda EQ yesterday.
*          w_changes = w_changes + 1.
*        ENDLOOP.
*      ENDIF.
  ENDCASE.

ENDFORM.                    "new-infotype-data

*----------------------------------------------------------------------*
*       Form  READ_OLD_BANK_DATA
*----------------------------------------------------------------------*
*       routine reads all old bank keys of the existent vendor
*       in order to delete them.
*----------------------------------------------------------------------*
FORM read_old_bank_data USING vendor.
  CLEAR old_vendor_lfbk.
  REFRESH old_vendor_lfbk.
  SELECT * FROM lfbk WHERE lifnr EQ vendor.
    MOVE-CORRESPONDING lfbk TO old_vendor_lfbk.
    APPEND old_vendor_lfbk.
  ENDSELECT.
ENDFORM.                    "read_old_bank_data

*&---------------------------------------------------------------------*
*&      Form  DELETE_OLD_BANK_DATA
*&---------------------------------------------------------------------*
*  new routine with 4.6A                               QIZALRK159798
*----------------------------------------------------------------------*
FORM delete_old_bank_data USING p_old_vendor_lfb1_lifnr.

  IF no_dele IS NOT INITIAL AND w_o_it9 IS NOT INITIAL. " GLW note 2319692
    RETURN.
  ENDIF.

  PERFORM read_old_bank_data USING
                             p_old_vendor_lfb1_lifnr.

*  CHECK no_dele IS INITIAL.
*  CHECK NOT: ( no_dele IS INITIAL AND w_o_it9 IS NOT INITIAL ). "GLW note 2104401
* there is no infotype 9 existing. Existing one on vendor shall not be deleted

* ARIN1628758 begin
* Delete BLFBK bank data if account number = IBAN account number
* Later an IBAN entry with the same account number will be created
* for the vendor using BLFBK_IBAN
  DATA: old_vendor_account_number LIKE old_vendor_lfbk-bankn,
*      iban_account_number LIKE old_vendor_account_number, MIVO 1661897
        creation_from_iban        TYPE abap_bool. " MIVO 1635738

* BEGIN MIVO 1635738
*  IF p0009-bankn IS INITIAL.
*    creation_from_iban = abap_true.
*  ELSE.
*    creation_from_iban = abap_false.
*  ENDIF.
* END MIVO 1635738

* BEGIN MIVO 1661897
*IF blfbk_iban-iban IS NOT INITIAL.
*  CALL FUNCTION 'CONVERT_IBAN_2_BANK_ACCOUNT'
*    EXPORTING I_IBAN = blfbk_iban-iban
*    IMPORTING E_BANK_ACCOUNT = iban_account_number.
**  Remove leading zeros for purpose of comparison
*  SHIFT iban_account_number LEFT DELETING LEADING '0'.
*ENDIF.
* END MIVO 1661897
* ARIN1628758 end

* this is redesigned with note GLW 1952136

* first we have to delete all old bank data.
  LOOP AT old_vendor_lfbk.
* ARIN1628758 begin
    old_vendor_account_number = old_vendor_lfbk-bankn.
*  Remove leading zeros for purpose of comparison
    SHIFT old_vendor_account_number LEFT DELETING LEADING '0'.
* BEGIN MIVO 1635738
*    IF old_vendor_account_number CS '<IBAN>'.  "GLW note 1994427
*     we are dealing with an IBAN entry in the vendor master.
*     delete it if creating new record via bank account or not the same
    DATA: lv_old_vendor_iban TYPE iban.
*     Get iban of vendor
    CALL FUNCTION 'READ_IBAN'
      EXPORTING
        i_banks        = old_vendor_lfbk-banks
        i_bankl        = old_vendor_lfbk-bankl
        i_bankn        = old_vendor_lfbk-bankn
        i_bkont        = space
        i_bkref        = space
      IMPORTING
        e_iban         = lv_old_vendor_iban
      EXCEPTIONS
        iban_not_found = 1.

*      IF sy-subrc NE 0.
*        CONTINUE.
*      ENDIF.

*    ENDIF.

    IF old_vendor_account_number CS '<IBAN>'.  "GLW note 1994427
*      CLEAR old_vendor_lfbk-bankn.
      old_vendor_lfbk-bankn = nodata.  "GLW note 2046892
    ENDIF.

*      IF ( creation_from_iban EQ abap_false ) OR
*         NOT ( p0009-banks     EQ old_vendor_lfbk-banks AND
*               p0009-bankl     EQ old_vendor_lfbk-bankl AND
*               blfbk_iban-iban EQ lv_old_vendor_iban ).
**        create deletion record for LFBK_IBAN
*        CLEAR blfbk_iban.
*        CLEAR file_k.
*        PERFORM nodata_in_structure USING 'BLFBK_IBAN' nodata.
*        blfbk_iban-stype = '2'.
*        blfbk_iban-tbnam = 'BLFBK_IBAN'.
*        blfbk_iban-xdele = 'X'.
*        blfbk_iban-banks = old_vendor_lfbk-banks.
*        blfbk_iban-bankl = old_vendor_lfbk-bankl.
**        blfbk_iban-bankn = old_vendor_lfbk-bankn.
*        blfbk_iban-iban = lv_old_vendor_iban.
**       file_k = blfbk.                              "#EC ENHOK "MAWH1492437
*        PERFORM move_struct_to_file USING blfbk_iban                 "MAWH1492437
*                                          'BLFBK_IBAN'               "MAWH1492437
*                                 CHANGING file_k.                    "MAWH1492437
*        PERFORM write_file USING '2' file_k space space.
*        TRANSFER file_k TO file_o.
*      ENDIF.
*    ELSE.
* handling of a regular bank account entry in vendor master
* delete entry if creating new one via iban or if identical
*      IF ( creation_from_iban EQ abap_true ) OR
*         NOT ( p0009-banks EQ old_vendor_lfbk-banks AND
*               p0009-bankl EQ old_vendor_lfbk-bankl AND
*               p0009-bankn EQ old_vendor_lfbk-bankn ).
* create deletion record for LFBK
* ARIN1628758 end
*    CHECK p0009-banks NE old_vendor_lfbk-banks OR
*          p0009-bankl NE old_vendor_lfbk-bankl OR
**          p0009-bankn NE old_vendor_lfbk-bankn.               "ARIN1628758
*          p0009-bankn NE old_vendor_lfbk-bankn OR              "ARIN1628758
*          iban_account_number EQ old_vendor_account_number.    "ARIN1628758

*    CHECK NOT old_vendor_lfbk-bankn CS '<IBAN>'.   "ARIK145058 / Note 1566706

    CLEAR blfbk.
    CLEAR file_k.
    PERFORM nodata_in_structure USING 'BLFBK' nodata.
    blfbk-stype = '2'.
    blfbk-tbnam = 'BLFBK'.
    blfbk-xdele = 'X'.
    IF lv_old_vendor_iban IS NOT INITIAL. "GLW note 1994427
      blfbk-iban = lv_old_vendor_iban.     "GLW note 1952136
    ENDIF.
    blfbk-banks = old_vendor_lfbk-banks.
    blfbk-bankl = old_vendor_lfbk-bankl.
    blfbk-bankn = old_vendor_lfbk-bankn.
*       file_k = blfbk.                              "#EC ENHOK "MAWH1492437
    PERFORM move_struct_to_file USING blfbk                 "MAWH1492437
                                      'BLFBK'               "MAWH1492437
                             CHANGING file_k.               "MAWH1492437
    PERFORM write_file USING '2' file_k space space.
    TRANSFER file_k TO file_o.
*      ENDIF.
*    ENDIF.
* END MIVO 1635738
  ENDLOOP.
ENDFORM.                               " DELETE_OLD_BANK_DATA

* Note 1555565 part 4 end

*---------------------------------------------------------------------*
*       FORM DELETE_OLD_LFBW_DATA                                     *
*---------------------------------------------------------------------*
* QIZK047575 new routine
*---------------------------------------------------------------------*
FORM delete_old_lfbw_data USING p_old_vendor_lfb1_lifnr.

  CLEAR old_vendor_lfbw.
  REFRESH old_vendor_lfbw.
  IF p_old_vendor_lfb1_lifnr IS INITIAL. "note 2985625
    RETURN.
  ENDIF.
  SELECT * FROM lfbw WHERE lifnr EQ p_old_vendor_lfb1_lifnr.
    MOVE-CORRESPONDING lfbw TO old_vendor_lfbw.
    APPEND old_vendor_lfbw.
  ENDSELECT.

* first we have to delete all old bank data.
  LOOP AT old_vendor_lfbw.
    CLEAR blfbw.
    CLEAR file_k.
    blfbw-stype = '2'.
    blfbw-tbnam = 'BLFBW'.
    blfbw-xdele = 'X'.
    blfbw-witht = old_vendor_lfbw-witht.
*   file_k = blfbw.                                         "MAWH1492437
    PERFORM move_struct_to_file USING blfbw                 "MAWH1492437
                                      'BLFBW'               "MAWH1492437
                             CHANGING file_k.               "MAWH1492437
    PERFORM write_file USING '2' file_k space space.
    TRANSFER file_k TO file_o.
  ENDLOOP.
ENDFORM.                               " DELETE_OLD_LFBW_DATA

*&---------------------------------------------------------------------*
*&      Form  find_Molga_for_country
*&---------------------------------------------------------------------*
*       QIZK023533
*&---------------------------------------------------------------------*
FORM find_molga_for_country  USING p_land1
                                   p_molga_in
                                   p_molga_out.
  TABLES: t005, t500l.
*  STATICS: country_already_checked LIKE t005-land1.        "MAWK100720

*  IF p_land1 EQ country_already_checked.                   "MAWK100720
* p_molga_out already correct... normaly there is nothing to do, but...
*    IF p_molga_out IS INITIAL.                             "MAWK100720
*      p_molga_out = p_molga_in.                            "MAWK100720
*    ENDIF.                                                 "MAWK100720
*  ELSE.                                                    "MAWK100720
* there is a new country for checking...
  p_molga_out = p_molga_in.
  SELECT * FROM t005 WHERE land1 EQ p_land1.
    IF NOT t005-intca IS INITIAL.
* there is a ISO code for LAND1...
      SELECT * FROM t500l WHERE intca EQ t005-intca.
* there is a MOLGA for ISO code...
        p_molga_out = t500l-molga.
      ENDSELECT.
    ENDIF.
  ENDSELECT.
*  ENDIF.
*  country_already_checked  = p_land1.                       "K100720
ENDFORM.                    "find_Molga_for_country

************* Start ALV Coding C5056168 28/02/2005*****************

*&---------------------------------------------------------------------*
*&      Form  display_alv_list
*&---------------------------------------------------------------------*
*       Display ALV List
*----------------------------------------------------------------------*
FORM display_alv_list USING iv_list_count TYPE char1.

  DATA : lv_structure_name TYPE dd02l-tabname.

  CLEAR : gs_layout,gt_events,gs_print,gt_fieldcat.

  gv_repid = sy-repid.

*Build Events
  PERFORM eventtab_build_alv USING iv_list_count CHANGING gt_events.
*Change layout structure
  gs_layout-min_linesize = 140.
  gs_layout-no_hotspot = abap_true.
  IF iv_list_count = 1.
    gs_layout-list_append = gc_y.
    gs_layout-no_colhead = gc_x.
    gs_layout-coltab_fieldname = 'COLOR'.
  ELSEIF iv_list_count = 8.
    gs_layout-no_vline = gc_x.
    gs_layout-no_colhead = gc_x.
    gs_layout-list_append = gc_x.
  ELSE.
    gs_layout-list_append = gc_x.
  ENDIF.
*Build fieldcatalog
  IF iv_list_count = 1.
    lv_structure_name =  gc_struct_alv1.
  ELSEIF iv_list_count = 2 OR iv_list_count = 4 OR iv_list_count = 5
                           OR iv_list_count = 6.
    lv_structure_name =  gc_struct_alv3.

  ELSEIF iv_list_count = 3.
    lv_structure_name =  gc_struct_alv2.
  ELSEIF iv_list_count = 8.
    lv_structure_name =  gc_struct_stats.
  ENDIF.

  PERFORM build_fieldcat_alv USING iv_list_count lv_structure_name.
  CLEAR : lv_structure_name.

*Assign Outtab ALV table to field symbol
  CASE iv_list_count.
    WHEN '1'.
      ASSIGN gt_outtab_file TO <gf_outtab>.
    WHEN '2'.
      ASSIGN gt_outtab_log TO <gf_outtab>.
    WHEN '3'.
      ASSIGN gt_outtab_error TO <gf_outtab>.
    WHEN '4'.
      ASSIGN gt_outtab_lock TO <gf_outtab>.
    WHEN '5'.
      ASSIGN gt_outtab_apaccount TO <gf_outtab>.
    WHEN '6'.
      ASSIGN gt_outtab_apac_without_pernr TO <gf_outtab>.
    WHEN '8'.
      ASSIGN gt_outtab_stats TO <gf_outtab>.
  ENDCASE.

*  Print Info
  gs_print-no_print_listinfos = abap_true.
  gs_print-no_print_selinfos  = abap_true.

  IF iv_list_count = 1 OR iv_list_count = 3 OR iv_list_count = 8.
    gs_print-no_new_page = abap_false.

  ELSEIF iv_list_count = 2.
    gs_print-no_new_page = abap_true.
  ELSEIF ( iv_list_count = 4 AND gt_outtab_error IS INITIAL )
   OR ( iv_list_count = 5 AND gt_outtab_error IS INITIAL AND
                              gt_outtab_lock IS INITIAL )
   OR ( iv_list_count = 6 AND gt_outtab_error IS INITIAL AND
                              gt_outtab_lock IS INITIAL AND
                              gt_outtab_apaccount IS INITIAL ).
    gs_print-no_new_page = abap_false.
  ELSE.
    gs_print-no_new_page = abap_true.

  ENDIF.

  PERFORM output_alv.

  CLEAR : gs_layout,gt_events,gs_print,gt_fieldcat.

ENDFORM.                    " display_alv_list

*&---------------------------------------------------------------------*
*&      Form  add_statistical_message
*&---------------------------------------------------------------------*
*      Add statistical message to application log
*----------------------------------------------------------------------*
*      -->IV_MSG    Message text
*      -->IV_COUNT  Count
*----------------------------------------------------------------------*
FORM add_statistical_message  USING iv_msg iv_count.

  CLEAR : gs_outtab_stats.

  MOVE : iv_msg TO gs_outtab_stats-sttxt,
         iv_count TO gs_outtab_stats-stcnt.

  APPEND gs_outtab_stats TO gt_outtab_stats.

ENDFORM.                    " add_statistical_message

*&---------------------------------------------------------------------*
*&      Form  eventtab_build_alv
*&---------------------------------------------------------------------*
*      Events Build
*      ----> IV_LIST_COUNT
*      <---> XT_EVENTS
*----------------------------------------------------------------------*
FORM eventtab_build_alv USING iv_list_count TYPE char1 CHANGING
xt_events TYPE
slis_t_event.

  DATA : ls_events TYPE slis_alv_event."events strcuture

  CALL FUNCTION 'REUSE_ALV_EVENTS_GET'
    EXPORTING
      i_list_type     = 0
    IMPORTING
      et_events       = xt_events
    EXCEPTIONS
      list_type_wrong = 1
      OTHERS          = 2.
  IF sy-subrc <> 0.
    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
  ENDIF.

*Top of Page
  CLEAR : ls_events.
  READ TABLE xt_events INTO ls_events WITH KEY name =
slis_ev_top_of_page.
  CASE iv_list_count.
    WHEN '1'.
      ls_events-form = gc_top_of_page_file.
    WHEN '2'.
      ls_events-form = gc_top_of_page_log.
    WHEN '3'.
      ls_events-form = gc_top_of_page_error.
    WHEN '4'.
      ls_events-form = gc_top_of_page_lock.
    WHEN '5'.
      ls_events-form = gc_top_of_page_apac.
    WHEN '6'.
      ls_events-form = gc_top_of_page_apac_wo_pernr.
    WHEN '8'.
      ls_events-form = gc_top_of_page_stats.
  ENDCASE.

  MODIFY xt_events FROM ls_events TRANSPORTING form
  WHERE name = slis_ev_top_of_page .

  IF iv_list_count = 1.
*Top of List
    CLEAR : ls_events.
    READ TABLE xt_events INTO ls_events WITH KEY name =
  slis_ev_top_of_list.
    ls_events-form = slis_ev_top_of_list.
    MODIFY xt_events FROM ls_events TRANSPORTING form
    WHERE name = slis_ev_top_of_list.

*End of List
    CLEAR : ls_events.
    READ TABLE xt_events INTO ls_events WITH KEY name =
  slis_ev_end_of_list.
    ls_events-form = slis_ev_end_of_list.
    MODIFY xt_events FROM ls_events TRANSPORTING form
    WHERE name = slis_ev_end_of_list.

*PF Status
    CLEAR : ls_events.
    READ TABLE xt_events INTO ls_events WITH KEY name =
 slis_ev_pf_status_set.
    ls_events-form = slis_ev_pf_status_set.
    MODIFY xt_events FROM ls_events TRANSPORTING form
    WHERE name = slis_ev_pf_status_set.

  ENDIF.

ENDFORM.                    " eventtab_build_alv
*&---------------------------------------------------------------------*
*&      Form  output_alv
*&---------------------------------------------------------------------*
*       Output ALV
*----------------------------------------------------------------------*
FORM output_alv .

  CALL FUNCTION 'REUSE_ALV_LIST_DISPLAY'
    EXPORTING
      i_callback_program = gv_repid
      is_layout          = gs_layout
      it_fieldcat        = gt_fieldcat
      it_events          = gt_events
      is_print           = gs_print
*     i_suppress_empty_data = abap_true        "PJN P7DK159028
    TABLES
      t_outtab           = <gf_outtab>
    EXCEPTIONS
      program_error      = 1
      OTHERS             = 2.
  IF sy-subrc <> 0.
    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
  ENDIF.

  CLEAR : gs_layout, gt_fieldcat,gt_events,gs_print.

ENDFORM.                    " output_alv
*&---------------------------------------------------------------------*
*&      Form  build_fieldcat_alv
*&---------------------------------------------------------------------*
*       Build Fuild catalogue
*----------------------------------------------------------------------*
*      -->IV_LIST_COUNT List count of append list
*      -->IV_STRUCT     Structure name
*----------------------------------------------------------------------*
FORM build_fieldcat_alv  USING  iv_list_count TYPE char1 iv_struct_name
TYPE dd02l-tabname.

  CALL FUNCTION 'REUSE_ALV_FIELDCATALOG_MERGE'
    EXPORTING
      i_program_name         = gv_repid
      i_structure_name       = iv_struct_name
    CHANGING
      ct_fieldcat            = gt_fieldcat
    EXCEPTIONS
      inconsistent_interface = 1
      program_error          = 2
      OTHERS                 = 3.
  IF sy-subrc <> 0.
    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
  ENDIF.

  CASE iv_list_count.
    WHEN '1'.
      PERFORM modify_fieldcat_file CHANGING gt_fieldcat.
    WHEN '2' OR '4' OR '5'.
      PERFORM modify_fieldcat_log CHANGING gt_fieldcat.
    WHEN '3'.
      PERFORM modify_fieldcat_error CHANGING gt_fieldcat.
    WHEN '6'.
      PERFORM modify_fieldcat_apac_wo_pernr CHANGING gt_fieldcat.
    WHEN '8'.
      PERFORM modify_fieldcat_stats CHANGING gt_fieldcat.
  ENDCASE.

ENDFORM.                    " build_fieldcat_alv

*&---------------------------------------------------------------------*
*&      Form  pf_status_set
*&---------------------------------------------------------------------*
*       Set PF Status
*----------------------------------------------------------------------*
FORM pf_status_set USING iv_extab TYPE slis_t_extab.        "#EC CALLED

  SET PF-STATUS 'APPEND'.

ENDFORM.                    " pf_status_set

*&---------------------------------------------------------------------*
*&      Form  top_of_list
*&---------------------------------------------------------------------*
*       Top of List for file output
*----------------------------------------------------------------------*
FORM top_of_list.                                           "#EC CALLED

  DATA : lr_grid TYPE REF TO cl_salv_form_layout_grid,
         lr_abap TYPE REF TO cl_salv_form_abap.

  CHECK NOT msg IS INITIAL.

  CREATE OBJECT lr_grid.

  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  CALL METHOD lr_grid->create_text
    EXPORTING
      row     = 3
      column  = 1
      text    = msg
      tooltip = msg.


  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_list

*&---------------------------------------------------------------------*
*&      Form  top_of_page_file
*&---------------------------------------------------------------------*
*       Top of Page for file output
*----------------------------------------------------------------------*
FORM top_of_page_file.                                      "#EC CALLED

  DATA : lr_grid TYPE REF TO cl_salv_form_layout_grid,
         lr_abap TYPE REF TO cl_salv_form_abap.

  CREATE OBJECT lr_grid.
  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  CALL METHOD lr_grid->create_text
    EXPORTING
      row     = 4
      column  = 1
      text    = gv_file_header_1
      tooltip = gv_file_header_1.
  CALL METHOD lr_grid->create_text
    EXPORTING
      row     = 5
      column  = 1
      text    = space
      tooltip = space.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_page_file

*&---------------------------------------------------------------------*
*&      Form  top_of_page_log
*&---------------------------------------------------------------------*
*       Top of Page for Log table output
*----------------------------------------------------------------------*
FORM top_of_page_log.                                       "#EC CALLED

  DATA : lr_grid         TYPE REF TO cl_salv_form_layout_grid,
         lr_abap         TYPE REF TO cl_salv_form_abap,
         lv_heading(200) TYPE        c.

  CREATE OBJECT lr_grid.
  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  IF NOT actmode IS INITIAL.
    WRITE:  'Der Job'(j01) TO lv_heading.
    WRITE:  jobname TO lv_heading+20.
    WRITE:  'wurde angestartet'(j02) TO lv_heading+40.
    CONDENSE lv_heading.
    CALL METHOD lr_grid->create_text
      EXPORTING
        row     = 3
        column  = 1
        text    = lv_heading
        tooltip = lv_heading.
    CLEAR lv_heading.
  ENDIF.

  CLEAR lv_heading.
  WRITE: 'Arbeitsdatei'(h02) TO lv_heading.
  WRITE: file_o TO lv_heading+40.
  WRITE: 'enthält folgende Mitarbeiter'(h03) TO lv_heading+90.
  CONDENSE lv_heading.
  CALL METHOD lr_grid->create_text
    EXPORTING
      row     = 4
      column  = 1
      text    = lv_heading
      tooltip = lv_heading.

  CLEAR : lv_heading.
  WRITE: 'Selektionsstichtag: '(h01) TO lv_heading.
  WRITE: pn-begda DD/MM/YYYY TO lv_heading+40.
  CONDENSE lv_heading.

  CALL METHOD lr_grid->create_text
    EXPORTING
      row     = 5
      column  = 1
      text    = lv_heading
      tooltip = lv_heading.

  CLEAR : lv_heading.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_page_log

*&---------------------------------------------------------------------*
*&      Form  top_of_page_error
*&---------------------------------------------------------------------*
*       Top of Page for Error table output
*----------------------------------------------------------------------*
FORM top_of_page_error.                                     "#EC CALLED

  DATA : lr_grid           TYPE REF TO cl_salv_form_layout_grid,
         lr_abap           TYPE REF TO cl_salv_form_abap,
         lv_heading(200)   TYPE        c,
         lv_date_begda(10) TYPE        c.

  CREATE OBJECT lr_grid.

  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  WRITE: 'Liste der abgelehnten Mitarbeiter'(h10) TO lv_heading.

  CALL METHOD lr_grid->create_header_information
    EXPORTING
      row     = 3
      column  = 1
      text    = lv_heading
      tooltip = lv_heading.
  gv_common_error_header_written = abap_true.

  CLEAR : lv_heading.

  WRITE: 'Fehlende Stammdaten am Selektionsstichtag'(h04) TO lv_heading.
  WRITE: pn-begda DD/MM/YYYY TO lv_date_begda.

  CONCATENATE lv_heading lv_date_begda INTO lv_heading
  SEPARATED BY space.

  CALL METHOD lr_grid->create_header_information
    EXPORTING
      row     = 4
      column  = 1
      text    = lv_heading
      tooltip = lv_heading.

  CLEAR : lv_heading.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_page_error

*&---------------------------------------------------------------------*
*&      Form  top_of_page_lock
*&---------------------------------------------------------------------*
*       Top of Page for lock table output
*----------------------------------------------------------------------*
FORM top_of_page_lock.                                      "#EC CALLED

  DATA : lr_grid         TYPE REF TO cl_salv_form_layout_grid,
         lr_abap         TYPE REF TO cl_salv_form_abap,
         lv_heading(200) TYPE        c.

  CREATE OBJECT lr_grid.
  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  IF gv_common_error_header_written IS INITIAL.
    gv_common_error_header_written = abap_true.

    WRITE: 'Liste der abgelehnten Mitarbeiter'(h10) TO lv_heading.

    CALL METHOD lr_grid->create_header_information
      EXPORTING
        row     = 3
        column  = 1
        text    = lv_heading
        tooltip = lv_heading.

    CLEAR : lv_heading.

    WRITE: 'Gesperrte Pesonalnummern:'(l01) TO lv_heading.
    CALL METHOD lr_grid->create_header_information
      EXPORTING
        row     = 4
        column  = 1
        text    = lv_heading
        tooltip = lv_heading.
  ELSE.
    WRITE: 'Gesperrte Pesonalnummern:'(l01) TO lv_heading.
    CALL METHOD lr_grid->create_header_information
      EXPORTING
        row     = 3
        column  = 1
        text    = lv_heading
        tooltip = lv_heading.
  ENDIF.

  CLEAR lv_heading.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_page_lock

*&---------------------------------------------------------------------*
*&      Form  top_of_page_apac
*&---------------------------------------------------------------------*
*       Top of Page for APAcount output
*----------------------------------------------------------------------*
FORM top_of_page_apac.                                      "#EC CALLED

  DATA : lr_grid          TYPE REF TO cl_salv_form_layout_grid,
         lr_abap          TYPE REF TO cl_salv_form_abap,
         lv_heading1(200) TYPE        c,
         lv_heading2(200) TYPE        c.

  CREATE OBJECT lr_grid.
  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  CASE t_code.
    WHEN 'XK01'.
      WRITE: 'Mitarbeiter, die bereits einen Kreditorenstamm'(l02)
                TO lv_heading2.
      WRITE: 'besitzen'(l03) TO lv_heading2+60.
      CONDENSE lv_heading2.
    WHEN 'XK02'.
      WRITE: 'Mitarbeiter, die noch keinen Kreditorenstamm'(l12)
             TO lv_heading2.
      WRITE: 'besitzen'(l03) TO lv_heading2+60.
      CONDENSE lv_heading2.
    WHEN 'XK05'.
      WRITE: 'Mitarbeiter, die noch keinen Kreditorenstamm'(l12)
             TO lv_heading2.
      WRITE: 'besitzen'(l03) TO lv_heading2+60.
      CONDENSE lv_heading2.
  ENDCASE.

  IF gv_common_error_header_written IS INITIAL.
    gv_common_error_header_written = abap_true.

    WRITE: 'Liste der abgelehnten Mitarbeiter'(h10) TO lv_heading1.

    CALL METHOD lr_grid->create_header_information
      EXPORTING
        row     = 3
        column  = 1
        text    = lv_heading1
        tooltip = lv_heading1.

    CLEAR : lv_heading1.
    CALL METHOD lr_grid->create_header_information
      EXPORTING
        row     = 4
        column  = 1
        text    = lv_heading2
        tooltip = lv_heading2.
  ELSE.
    CALL METHOD lr_grid->create_header_information
      EXPORTING
        row     = 3
        column  = 1
        text    = lv_heading2
        tooltip = lv_heading2.
  ENDIF.

  CLEAR : lv_heading1, lv_heading2.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_page_apac

*&---------------------------------------------------------------------*
*&      Form  top_of_page_apac_wo_pernr
*&---------------------------------------------------------------------*
*       Top of Page for ApAccount w/o PERNR table output
*----------------------------------------------------------------------*
FORM top_of_page_apac_wo_pernr.                             "#EC CALLED

  DATA : lr_grid         TYPE REF TO cl_salv_form_layout_grid,
         lr_abap         TYPE REF TO cl_salv_form_abap,
         lv_heading(200) TYPE        c,
         lv_next_row_no  TYPE        i.

  CREATE OBJECT lr_grid.
  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  IF gv_common_error_header_written IS INITIAL.
    gv_common_error_header_written = abap_true.
    WRITE: 'Liste der abgelehnten Mitarbeiter'(h10) TO lv_heading.

    CALL METHOD lr_grid->create_header_information
      EXPORTING
        row     = 3
        column  = 1
        text    = lv_heading
        tooltip = lv_heading.
    lv_next_row_no = 4.
    CLEAR : lv_heading.
  ELSE.
    lv_next_row_no = 3.
  ENDIF.

  WRITE: 'Mitarbeiter, die bereits einen Kreditorenstamm'(l02)
         TO lv_heading.
  WRITE: 'besitzen'(l03) TO lv_heading+60.
  CONDENSE lv_heading.

  CALL METHOD lr_grid->create_header_information
    EXPORTING
      row     = lv_next_row_no
      column  = 1
      text    = lv_heading
      tooltip = lv_heading.
  lv_next_row_no = lv_next_row_no + 1.
  CLEAR lv_heading.

  WRITE:
'Die Angabe der Personalnummer fehlt im Buchungskreissegment!'(l04)
  TO lv_heading.

  CALL METHOD lr_grid->create_header_information
    EXPORTING
      row     = lv_next_row_no
      column  = 1
      text    = lv_heading
      tooltip = lv_heading.

  CLEAR lv_heading.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_page_apac_wo_pernr

*&---------------------------------------------------------------------*
*&      Form  top_of_page_stats
*&---------------------------------------------------------------------*
*       Top of Page for Statistics table output
*----------------------------------------------------------------------*
FORM top_of_page_stats.                                     "#EC CALLED

  DATA : lr_grid TYPE REF TO cl_salv_form_layout_grid,
         lr_abap TYPE REF TO cl_salv_form_abap.

  CREATE OBJECT lr_grid.

  PERFORM prepare_common_top_of_page CHANGING lr_grid.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " top_of_page_stats

*&---------------------------------------------------------------------*
*&      Form  end_of_list
*&---------------------------------------------------------------------*
*       End of list
*----------------------------------------------------------------------*
FORM end_of_list.                                           "#EC CALLED

  PERFORM display_list_message USING gv_table_msg.
  PERFORM display_alv_list USING '2'. "Log table ALV display
  PERFORM display_list_message USING gv_log_fail_message.
  "Log fail message display.
  PERFORM display_alv_list USING '3'. "Error table ALV display
  PERFORM display_alv_list USING '4'. "Locked table ALV display
  PERFORM display_alv_list USING '5'. "APAccount table ALV display
  PERFORM display_alv_list USING '6'. "APAccount w/o PERNR ALV display
  PERFORM display_messages.           "Display PERNR messages using FM
  PERFORM display_alv_list USING '8'. "Statistics.

ENDFORM.                    " end_of_list
*&---------------------------------------------------------------------*
*&      Form  modify_fieldcat_file
*&---------------------------------------------------------------------*
*       Modify Fieldcat for File output
*----------------------------------------------------------------------*
*      <-->XT_FIELDCAT  Fieldcat
*----------------------------------------------------------------------*
FORM modify_fieldcat_file CHANGING xt_fieldcat TYPE slis_t_fieldcat_alv.

  DATA : ls_fieldcat TYPE slis_fieldcat_alv.

  LOOP AT xt_fieldcat INTO ls_fieldcat WHERE fieldname = 'STYPE'.
    ls_fieldcat-tech = gc_x.
    MODIFY xt_fieldcat FROM ls_fieldcat TRANSPORTING tech.
  ENDLOOP.

ENDFORM.                    " modify_fieldcat_file

*&---------------------------------------------------------------------*
*&      Form  modify_fieldcat_log
*&---------------------------------------------------------------------*
*       Modify Fieldcat for Log output
*----------------------------------------------------------------------*
*      <-->XT_FIELDCAT  Fieldcat
*----------------------------------------------------------------------*
FORM modify_fieldcat_log  CHANGING xt_fieldcat TYPE slis_t_fieldcat_alv.

  DATA : ls_fieldcat TYPE slis_fieldcat_alv.

  LOOP AT xt_fieldcat INTO ls_fieldcat.
    CASE ls_fieldcat-fieldname.
      WHEN 'PERNR'.
        ls_fieldcat-lzero = gc_x.
        ls_fieldcat-just  = 'L'.
      WHEN 'VENDOR_NO' OR 'BUKRS'.
        ls_fieldcat-tech = gc_x.
      WHEN 'NAME'.
        ls_fieldcat-seltext_s = TEXT-p02.
        ls_fieldcat-seltext_m = TEXT-p02.
        ls_fieldcat-seltext_l = TEXT-p02.
        ls_fieldcat-outputlen = 69.
    ENDCASE.

    MODIFY xt_fieldcat FROM ls_fieldcat TRANSPORTING tech lzero
                   just outputlen seltext_s seltext_m seltext_l.
  ENDLOOP.

ENDFORM.                    " modify_fieldcat_log

*&---------------------------------------------------------------------*
*&      Form  modify_fieldcat_error
*&---------------------------------------------------------------------*
*       Modify Fieldcat for Error table output
*----------------------------------------------------------------------*
*      <-->XT_FIELDCAT  Fieldcat
*----------------------------------------------------------------------*
FORM modify_fieldcat_error CHANGING xt_fieldcat TYPE slis_t_fieldcat_alv
.
  DATA : ls_fieldcat TYPE slis_fieldcat_alv.

  LOOP AT xt_fieldcat INTO ls_fieldcat.
    CASE ls_fieldcat-fieldname.
      WHEN 'PERNR'.
        ls_fieldcat-lzero = gc_x.
        ls_fieldcat-just  = 'L'.
      WHEN 'NAME'.
        ls_fieldcat-seltext_s = TEXT-p02.
        ls_fieldcat-seltext_m = TEXT-p02.
        ls_fieldcat-seltext_l = TEXT-p02.
        ls_fieldcat-outputlen = 24.
      WHEN 'ACTION'.
        CONCATENATE TEXT-p03 TEXT-p04 INTO ls_fieldcat-seltext_s
        SEPARATED BY space.
        CONCATENATE TEXT-p03 TEXT-p04 INTO ls_fieldcat-seltext_m
        SEPARATED BY space.
        CONCATENATE TEXT-p03 TEXT-p04 INTO ls_fieldcat-seltext_l
        SEPARATED BY space.
        ls_fieldcat-outputlen = 8.
      WHEN 'PERSON_DATA'.
        CONCATENATE TEXT-p05 TEXT-p06 INTO ls_fieldcat-seltext_s
        SEPARATED BY space.
        CONCATENATE TEXT-p05 TEXT-p06 INTO ls_fieldcat-seltext_m
        SEPARATED BY space.
        CONCATENATE TEXT-p05 TEXT-p06 INTO ls_fieldcat-seltext_l
        SEPARATED BY space.
        ls_fieldcat-outputlen = 8.
      WHEN 'PERM_RESI'.
        CONCATENATE TEXT-p07 TEXT-p08 INTO ls_fieldcat-seltext_s
        SEPARATED BY space.
        CONCATENATE TEXT-p07 TEXT-p08 INTO ls_fieldcat-seltext_m
        SEPARATED BY space.
        CONCATENATE TEXT-p07 TEXT-p08 INTO ls_fieldcat-seltext_l
        SEPARATED BY space.
        ls_fieldcat-outputlen = 8.
      WHEN 'BANK_DETAILS'.
        CONCATENATE TEXT-p09 TEXT-p10 INTO ls_fieldcat-seltext_s
        SEPARATED BY space.
        CONCATENATE TEXT-p09 TEXT-p10 INTO ls_fieldcat-seltext_m
        SEPARATED BY space.
        CONCATENATE TEXT-p09 TEXT-p10 INTO ls_fieldcat-seltext_l
        SEPARATED BY space.
        ls_fieldcat-outputlen = 8.
      WHEN 'HOUSE_BANK'.
        CONCATENATE TEXT-p11 TEXT-p12 INTO ls_fieldcat-seltext_s
        SEPARATED BY space.
        CONCATENATE TEXT-p11 TEXT-p12 INTO ls_fieldcat-seltext_m
        SEPARATED BY space.
        CONCATENATE TEXT-p11 TEXT-p12 INTO ls_fieldcat-seltext_l
        SEPARATED BY space.
        ls_fieldcat-outputlen = 8.
    ENDCASE.

    MODIFY xt_fieldcat FROM ls_fieldcat TRANSPORTING lzero outputlen
                         just seltext_s seltext_m seltext_l.
  ENDLOOP.
ENDFORM.                    " modify_fieldcat_error

*&---------------------------------------------------------------------*
*&      Form  modify_fieldcat_apac_wo_pernr
*&---------------------------------------------------------------------*
*       Modify Fieldcat for AP Account w/o PERNR output
*----------------------------------------------------------------------*
*      <-->XT_FIELDCAT  Fieldcat
*----------------------------------------------------------------------*
FORM modify_fieldcat_apac_wo_pernr CHANGING xt_fieldcat TYPE
slis_t_fieldcat_alv.

  DATA : ls_fieldcat TYPE slis_fieldcat_alv.

  LOOP AT xt_fieldcat INTO ls_fieldcat.
    CASE ls_fieldcat-fieldname.
      WHEN 'PERNR'.
        ls_fieldcat-lzero = gc_x.
        ls_fieldcat-just  = 'L'.
      WHEN 'NAME'.
        ls_fieldcat-seltext_s = TEXT-p02.
        ls_fieldcat-seltext_m = TEXT-p02.
        ls_fieldcat-seltext_l = TEXT-p02.
        ls_fieldcat-outputlen = 53.
    ENDCASE.

    MODIFY xt_fieldcat FROM ls_fieldcat TRANSPORTING lzero seltext_s
                           seltext_m seltext_l outputlen just.
  ENDLOOP.
ENDFORM.                    " modify_fieldcat_apac_wo_pernr

*&---------------------------------------------------------------------*
*&      Form  modify_fieldcat_stats
*&---------------------------------------------------------------------*
*       Modify Fieldcat for Statistics output
*----------------------------------------------------------------------*
*      <-->XT_FIELDCAT  Fieldcat
*----------------------------------------------------------------------*
FORM modify_fieldcat_stats CHANGING xt_fieldcat TYPE
slis_t_fieldcat_alv.

  DATA : ls_fieldcat TYPE slis_fieldcat_alv.

  LOOP AT xt_fieldcat INTO ls_fieldcat.
    CASE ls_fieldcat-fieldname.
      WHEN 'STTXT'.
        ls_fieldcat-outputlen = 65.
      WHEN 'STCNT'.
        ls_fieldcat-outputlen = 12.
    ENDCASE.

    MODIFY xt_fieldcat FROM ls_fieldcat TRANSPORTING outputlen.
  ENDLOOP.
ENDFORM.                    " modify_fieldcat_stats

*&---------------------------------------------------------------------*
*&      Form  display_list_message
*&---------------------------------------------------------------------*
*       Display List message
*       --> IV_MESSAGE Message text
*----------------------------------------------------------------------*
FORM display_list_message USING iv_message.

  DATA : lr_grid TYPE REF TO cl_salv_form_layout_grid,
         lr_abap TYPE REF TO cl_salv_form_abap.

  CHECK NOT iv_message IS INITIAL.

  CREATE OBJECT lr_grid.

  CALL METHOD lr_grid->create_text
    EXPORTING
      row     = 1
      column  = 1
      text    = iv_message
      tooltip = iv_message.

  CREATE OBJECT lr_abap.

  lr_abap->set_content( lr_grid ).
  lr_abap->display( ).

ENDFORM.                    " display_list_message
*&---------------------------------------------------------------------*
*&      Form  prepare_common_top_of_page
*&---------------------------------------------------------------------*
*       Common TOP OF PAGE Part
*----------------------------------------------------------------------*
*       <-->   XR_GRID  Grid
*----------------------------------------------------------------------*
FORM prepare_common_top_of_page
           CHANGING xr_grid TYPE REF TO cl_salv_form_layout_grid.

  CLEAR h_line.

  IF NOT msg IS INITIAL.
    sy-pagno = 1.
  ENDIF.

  CHECK sy-pagno <> gv_last_pagno.
  gv_last_pagno = sy-pagno.

  CASE t_code.
    WHEN 'XK01'.
      WRITE TEXT-h20 TO h_line CENTERED.
    WHEN 'XK02'.
      IF ref_a_p IS INITIAL.
        WRITE TEXT-h21 TO h_line CENTERED.
      ELSE.
        WRITE TEXT-h23 TO h_line CENTERED.
      ENDIF.
    WHEN 'XK05'.
      WRITE TEXT-h22 TO h_line CENTERED.
  ENDCASE.
  WRITE sy-datum DD/MM/YYYY TO h_line(10).
  WRITE: sy-pagno TO h_line+78(2).

  CALL METHOD xr_grid->create_header_information
    EXPORTING
      row     = 1
      column  = 1
      text    = h_line
      tooltip = h_line.

  CALL METHOD xr_grid->create_text
    EXPORTING
      row    = 2
      column = 1
      text   = sy-uline(80).

  CLEAR : h_line.

ENDFORM.                    " prepare_common_top_of_page
************* End ALV Coding C5056168 28/02/2005*******************
*&---------------------------------------------------------------------*
*&      Form  telnr
*&---------------------------------------------------------------------*
*       New with MAWK013477 [note 995726]
*       Due to a change of FORM telnr_pbo(sapfp5u0) in note  872791
*       we had to copy the form into RPRAPA00
*----------------------------------------------------------------------*
*      -->P_P0006_telnr  text
*      -->P_P0006_AREAC  text
*      -->P_P0006_telnr  text
*----------------------------------------------------------------------*
FORM telnr  USING    p_telnr
                     q_areac
                     q_telnr.

  CLEAR: q_areac, q_telnr.
  CHECK p_telnr NE space.

  MOVE: p_telnr(3)    TO q_areac(3),
        p_telnr+3(3)  TO q_telnr(3),
        '-'           TO q_telnr+3(1),
        p_telnr+6(4)  TO q_telnr+4(4).

ENDFORM.                    " telnr

*&---------------------------------------------------------------------*
*&      Form  STOP_OR_REJECT
*&---------------------------------------------------------------------*
*       New with MAWK022558
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM stop_or_reject .

  IF testrun IS INITIAL AND sw_stop IS NOT INITIAL. "GLW note 1989485
    STOP.
  ELSE.
    ADD 1 TO sel_with_error.  "GLW note 1989485
    DELETE logtable WHERE pernr EQ pernr-pernr.  "GLW note 2614599
    REJECT.
  ENDIF.

ENDFORM.                    " STOP_OR_REJECT
*&---------------------------------------------------------------------*
*&      Form  CHECK_EXTERNAL_ASSIGNMENT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM check_external_assignment .
  DATA lv_error TYPE i.
  DATA lv_lifnr TYPE lifnr.
* GLW note 2614599 begin
* when create mode: if external number assignment, then check if the vendor number already exists (in the company code):
  IF blf00-lifnr IS NOT INITIAL AND t_code = 'XK01'.

    CALL FUNCTION 'CONVERSION_EXIT_ALPHA_INPUT'
      EXPORTING
        input  = blf00-lifnr
      IMPORTING
        output = lv_lifnr.

    IF crea_cc IS INITIAL.
      SELECT COUNT( * ) FROM lfa1 WHERE lifnr = lv_lifnr.
      IF sy-dbcnt > 0.
        lv_error = 1.
      ENDIF.
    ELSE.
      SELECT COUNT( * ) FROM lfb1 WHERE lifnr = lv_lifnr AND bukrs = p0001-bukrs.
      IF sy-dbcnt > 0.
        lv_error = 2.
      ENDIF.
    ENDIF.
    CASE lv_error.
      WHEN 1.
        PERFORM fill_error_int USING pernr-pernr
                                   'F2'
                                   'E'
                                   '161'
                                   lv_lifnr
                                   space
                                   space
                                   space.
        PERFORM stop_or_reject.
      WHEN 2.
        PERFORM fill_error_int USING pernr-pernr
                                 'F2'
                                 'E'
                                 '162'
                                 lv_lifnr
                                 p0001-bukrs
                                 space
                                 space.
        PERFORM stop_or_reject.
    ENDCASE.
  ENDIF.
* GLW note 2614599 end
ENDFORM.
*&---------------------------------------------------------------------*
*&      Form  MOVE_STRUCT_TO_FILE
*&---------------------------------------------------------------------*
*       new with MAWH1492437
*----------------------------------------------------------------------*
*      -->P_BLFA1  text
*      -->P_0314   text
*      <--P_FILE_K  text
*----------------------------------------------------------------------*
FORM move_struct_to_file  USING    ps_struct      TYPE any
                                   pv_struct_name TYPE strukname
                          CHANGING pv_file        TYPE tv_file.

  DATA lo_typedescr       TYPE REF TO cl_abap_typedescr.
  DATA lo_structdescr     TYPE REF TO cl_abap_structdescr.
  DATA lt_ddfields        TYPE        ddfields.
  DATA lv_help            TYPE        c LENGTH 61.
  DATA lv_file            TYPE        string.
  FIELD-SYMBOLS <ls_ddfields> TYPE dfies.
  FIELD-SYMBOLS <lv_value>.

  CLEAR pv_file.

  CALL METHOD cl_abap_typedescr=>describe_by_name
    EXPORTING
      p_name      = pv_struct_name
    RECEIVING
      p_descr_ref = lo_typedescr.

  IF sy-subrc <> 0.
*   should not happen
  ENDIF.

  CASE lo_typedescr->kind .
    WHEN lo_typedescr->kind_struct.
      lo_structdescr ?= lo_typedescr.

      CALL METHOD lo_structdescr->get_ddic_field_list
        EXPORTING
          p_including_substructres = abap_true
        RECEIVING
          p_field_list             = lt_ddfields
        EXCEPTIONS
          not_found                = 1
          no_ddic_type             = 2
          OTHERS                   = 3.
      IF sy-subrc <> 0.
*   should not happen
      ENDIF.

    WHEN OTHERS.
*     should not happen
  ENDCASE.

  SORT lt_ddfields BY position ASCENDING.
  LOOP AT lt_ddfields ASSIGNING <ls_ddfields>.
    CONCATENATE 'PS_STRUCT' <ls_ddfields>-fieldname
           INTO lv_help SEPARATED BY '-'.
    ASSIGN (lv_help) TO <lv_value>.
    IF sy-subrc = 0.
* Begin MIVO2745831
  PERFORM REMOVE_CONTROL_CHARACTERS
              USING
                 <lv_value>
              CHANGING
                 <lv_value>.
* delete all line break signs - however they may have come to the infotype data
*      REPLACE ALL OCCURRENCES OF cl_abap_char_utilities=>newline IN <lv_value> WITH space.  "GLW note 2103710
* End MIVO2745831
      CONCATENATE lv_file <lv_value> INTO lv_file RESPECTING BLANKS.
    ENDIF.
  ENDLOOP.

  MOVE lv_file TO pv_file.

ENDFORM.                    " MOVE_STRUCT_TO_FILE
*&---------------------------------------------------------------------*
*&      Form  REMOVE_CONTROL_CHARACTERS
*&---------------------------------------------------------------------*
*       MIVO2745831
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM REMOVE_CONTROL_CHARACTERS
  USING i_text TYPE ANY
  CHANGING e_text TYPE ANY.

  DATA l_line TYPE string.
  DATA  l_hex(4)  TYPE x.
  DATA i TYPE i VALUE 0.
  FIELD-SYMBOLS <fs> TYPE any.

  l_line = i_text.

  WHILE i <= 31.
    l_hex = i * ( 16 ** 6 ).
    ASSIGN l_hex TO <fs> CASTING TYPE abap_char1.
    REPLACE ALL OCCURRENCES OF <fs> IN l_line  WITH '' IN CHARACTER MODE.
    i = i + 1.
    IF i = 32.
      l_hex = 127 * ( 16 ** 6 ).
      ASSIGN l_hex TO <fs> CASTING TYPE abap_char1.
      REPLACE ALL OCCURRENCES OF <fs> IN l_line  WITH '' IN CHARACTER MODE.
    ENDIF.
  ENDWHILE.

  e_text = l_line.

ENDFORM.
* Note 1555565 part 4 begin
*&---------------------------------------------------------------------*
*&      Form  DELETE_OLD_BANK_DATA_IBAN
*&---------------------------------------------------------------------*
FORM delete_old_bank_data_iban USING p_old_vendor_lfb1_lifnr
                                     p_iban TYPE iban.

  DATA lv_old_vendor_iban TYPE iban.

  PERFORM read_old_bank_data USING
                             p_old_vendor_lfb1_lifnr.
* first we have to delete all old bank data iban.
  LOOP AT old_vendor_lfbk.
    CLEAR lv_old_vendor_iban.

* Get iban of vendor
    CALL FUNCTION 'READ_IBAN'
      EXPORTING
        i_banks        = old_vendor_lfbk-banks
        i_bankl        = old_vendor_lfbk-bankl
        i_bankn        = old_vendor_lfbk-bankn
        i_bkont        = space
        i_bkref        = space
      IMPORTING
        e_iban         = lv_old_vendor_iban
      EXCEPTIONS
        iban_not_found = 1.

    IF sy-subrc NE 0.
      CONTINUE.
    ENDIF.

    CHECK p0009-banks NE old_vendor_lfbk-banks OR
          p0009-bankl NE old_vendor_lfbk-bankl OR
          p_iban NE lv_old_vendor_iban.

    CLEAR blfbk_iban.
    CLEAR file_k.
    PERFORM nodata_in_structure USING 'BLFBK_IBAN' nodata.
    blfbk_iban-stype = '2'.
    blfbk_iban-tbnam = 'BLFBK_IBAN'.
    blfbk_iban-xdele = 'X'.
    blfbk_iban-banks = old_vendor_lfbk-banks.
    blfbk_iban-bankl = old_vendor_lfbk-bankl.
*    blfbk_iban-bankn = old_vendor_lfbk-bankn.
    blfbk_iban-iban = lv_old_vendor_iban.
*   file_k = blfbk.                              "#EC ENHOK "MAWH1492437
    PERFORM move_struct_to_file USING blfbk_iban                 "MAWH1492437
                                      'BLFBK_IBAN'               "MAWH1492437
                             CHANGING file_k.                    "MAWH1492437
    PERFORM write_file USING '2' file_k space space.
    TRANSFER file_k TO file_o.
  ENDLOOP.
ENDFORM.                    "delete_old_bank_data_iban
*&---------------------------------------------------------------------*
*&      Form  CLEAR_BNKA_FIELDS
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      <--P_BLFBK  text
*----------------------------------------------------------------------*
FORM clear_bnka_fields  CHANGING p_blfbk TYPE blfbk.

* if the following fields are unequal no-data, RFBIKR00 will interprete this as a request to change
* master data of the bank in BNKA table! This is not desired when creating / updating vendors based on
* employee master data. New with GLW note 2174172

  MOVE nodata TO:

        p_blfbk-provz,
        p_blfbk-stras,
        p_blfbk-ort01,
        p_blfbk-swift,
        p_blfbk-bgrup,
        p_blfbk-xpgro,
        p_blfbk-bnklz.


ENDFORM.