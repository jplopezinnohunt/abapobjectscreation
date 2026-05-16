  METHOD GET_DEBIT.
* CGI Direct Debit default functionality

    DATA:
      LS_DMEE_ITEM_TMP TYPE DMEE_PAYM_IF_TYPE,
      LT_DMEE_TAB_TMP  TYPE TABLE OF  DMEE_TREE_TYPE-IF_TAB,
      LV_NOT_FOUND     TYPE BOOLE_D,
      LV_CODE          TYPE STRING,
      LS_ADRC_TMP      TYPE ADRC,
      LS_T015L         TYPE T015L_D_BF,
      LV_AMT_DIS       TYPE WMTO_S-AMOUNT,
      LV_AMT_INT       TYPE WMTO_S-AMOUNT.

    CASE I_NODE_PATH.
*BEGIN*OF**********************<Document>*************************************
      WHEN '<Document><xmlns><ISO>'.                          "n2533796
*       Original ISO value
        C_VALUE = 'urn:iso:std:iso:20022:tech:xsd:pain.008.001.02'.

      WHEN '<Document><xmlns:xsi><ISO>'.                      "n2533796
*       Original ISO value
        C_VALUE = 'http://www.w3.org/2001/XMLSchema-instance'.

      WHEN '<Document><xsi:schemaLocation><schemaLocationExit>'. "n2533796
*       Original empty
        CLEAR C_VALUE.

*BEGIN*OF**********************<GrpHdr>***************************************
      WHEN '<GrpHdr><MsgId>'.
*       Originator’s unique identifier of the submitted file
        C_VALUE = I_FPAYHX-RENUM.

      WHEN '<GrpHdr><CreDtTm>'.
*       Creation Date Time
        C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREATION_TIME_AND_DATE( ).

      WHEN '<GrpHdr><InitgPty><Nm>'.
*       First Aust1 and Aust2 then T001 (same as Cdtr Nm)        "n2960399
        IF I_FPAYHX-AUST1 IS NOT INITIAL
          AND MS_FORMAT_PARAMS-NATION IS INITIAL.
          CONCATENATE I_FPAYHX-AUST1 I_FPAYHX-AUST2
                 INTO C_VALUE SEPARATED BY SPACE.
        ELSE.
*         or it is taken in local language or from T001-BUTXT
          C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_DEBITOR_NAME(
              IV_NATION = MS_FORMAT_PARAMS-NATION
              IS_FPAYHX = I_FPAYHX
              IV_ZBUKR  = I_FPAYH-ZBUKR
          ).
        ENDIF.

      WHEN '<GrpHdr><InitgPty><-Id>'.
*       This node handles visibility of Node <GrpHdr><InitgPty><Id>              "n2508061
        C_VALUE = ABAP_FALSE.

      WHEN '<GrpHdr><InitgPty><Id><PrvtId><Othr><Id>'.        "n2562701
*       This node defines special parameters for Portugal
        CLEAR C_VALUE.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><BICOrBEI>'
        OR '<PmtInf><Cdtr><Id><OrgId><BICOrBEI>'.
*       If the magic value is set to SWIFT so in this node CGIID should be used
        IF MV_CGIIR EQ GC_SWIFT.
          C_VALUE = MV_CGIID.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><-Othr>'
        OR '<PmtInf><Cdtr><Id><OrgId><-Othr>'.
*       The other functionality is only for non-SWIFT Identification
*       Which can be done on the Company -> additional data
*       or on the house bank in field Customer Number
        IF MV_CGIIR EQ GC_SWIFT
          OR ( MV_CGIID IS INITIAL AND I_FPAYHX-DTKID IS INITIAL ) .   "n2800089
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><Othr><Id>'
        OR '<PmtInf><Cdtr><Id><OrgId><Othr><Id>'.
*       This node can be filled 2 ways.
*       1nd parameter on house bank -> Customer number FPAYHX-DTKID
        IF MV_CGIIR NE GC_SWIFT.
          IF I_FPAYHX-DTKID IS NOT INITIAL.                 "n2893975
            C_VALUE = I_FPAYHX-DTKID.

*         2st parameter in the too1z CGIID
*         Information on this place (T001-PAVAL) has lower prio as 1nd location
          ELSEIF MV_CGIID IS NOT INITIAL.
            C_VALUE = MV_CGIID.
          ENDIF.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><Othr><SchmeNm><Prtry>'
        OR '<PmtInf><Cdtr><Id><OrgId><Othr><SchmeNm><Prtry>'.
*       This node refers to the node <GrpHdr><InitgPty><Id><OrgId><Othr><Id>
*       and its 1st possible filling -> copied condition
        IF MV_CGIID IS NOT INITIAL
           AND MV_CGIIR NE GC_SWIFT.

          IF MV_CGIPRT IS NOT INITIAL.
*           Information for this node is taken from (T001Z-PAVAL with PARTY CGIPTR)
            C_VALUE = MV_CGIPRT.
          ENDIF.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><Othr><SchmeNm><Cd>'
        OR '<PmtInf><Cdtr><Id><OrgId><Othr><SchmeNm><Cd>'.
*       This node refers to the node <GrpHdr><InitgPty><Id><OrgId><Othr><Id>
*       and its 2nd possible filling -> copied condition
*       In this casse Prtry tag has higher priority as Cd tag for SEPA payments
        IF MV_CGIIR NE GC_SWIFT.
          IF ( MV_IS_SEPA_PAYMENT EQ ABAP_FALSE )
              OR
             ( MV_IS_SEPA_PAYMENT EQ ABAP_TRUE
                AND
              MV_CGIID  IS INITIAL ).
            IF MV_CGICD IS INITIAL.                         "n2893975
              C_VALUE = GC_BANK.
            ELSE.
              C_VALUE = MV_CGICD.
            ENDIF.
          ENDIF.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><Othr><Issr>'
        OR '<PmtInf><Cdtr><Id><OrgId><Othr><Issr>'.
        IF MV_CGIIR NE GC_SWIFT.
          C_VALUE = MV_CGIIR.
        ENDIF.

* Initiating Party - Contact Details
      WHEN '<GrpHdr><InitgPty><-CtctDtlsIP>'.
        C_VALUE = ABAP_TRUE.

*END*OF**********************<GrpHdr>***************************************

*BEGIN*OF**********************<PmtInf>*************************************

      WHEN '<PmtInf><PmtInfId>'.
*       Batch Id - CREATE ID for logical group of PmtInf
        "we check ref06+40 first (BADI solution saved as DMEEX)
       IF I_FPAYHX-REF06+40(35) IS NOT INITIAL.             "n2942194
         C_VALUE = I_FPAYHX-REF06+40(35).
       ELSE.

        LS_DMEE_ITEM_TMP-FPAYH  = I_FPAYH.
        LS_DMEE_ITEM_TMP-FPAYHX = I_FPAYHX.
        LS_DMEE_ITEM_TMP-FPAYP  = I_FPAYP.

        CALL FUNCTION 'DMEE_EXIT_SEPA_21'
          EXPORTING
            I_TREE_TYPE = I_TREE_TYPE
            I_TREE_ID   = I_TREE_ID
            I_ITEM      = LS_DMEE_ITEM_TMP
            I_PARAM     = I_PARAM
            I_UPARAM    = I_UPARAM
          IMPORTING
            C_VALUE     = C_VALUE
          TABLES
            I_TAB       = LT_DMEE_TAB_TMP.
       ENDIF.
      WHEN '<PmtInf><-NbOfTxs>'.
*       This node handles visibility of <PmtInf><NbOfTxs>
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><-CtrlSum>'.
*       This node handles visibility of <PmtInf><CtrlSum>
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><-PmtTpInf>'.
*       This node handles visibility of <PmtInf><PmtTpInf>
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
*         Dont hide for SEPA payments
          C_VALUE = ABAP_FALSE.
        ELSE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><BtchBookg>'.                             "n2600590
        C_VALUE = MS_FORMAT_PARAMS-BATCH_BOOKING.

      WHEN '<PmtInf><PmtTpInf><InstrPrty>'.
*       This handles the Instruction property on the batch level HIGH/NORM
        IF I_FPAYHX-DTKZA EQ '01' OR I_FPAYHX-DTURG IS NOT INITIAL.
          C_VALUE = GC_INSTRPRTY_HIGH.
        ELSE."IF i_fpayhx-dtkza EQ '00'.
          C_VALUE = GC_INSTRPRTY_NORM.
        ENDIF.
*       Comment
*       Only two values are possible in this case. old solution used
*       for NORM payment value from DTWS1 (EQ 11) even if it would be
*       empty this would mean that the priority is NORM (standard
*       ISO20022 behaviour)

      WHEN '<PmtInf><PmtTpInf><SvcLvl><Cd>'
        OR '<PmtInf><DrctDbtTxInf><PmtTpInf><SvcLvl><Cd>'.
*       Check if the customized value for Application component CGI is customized
        CL_IDFI_CGI_DMEE_UTILS=>GET_SERVICE_LEVEL_CODE(
        EXPORTING
          IS_FPAYH = I_FPAYH
          IV_AREA  = MV_AREA
        IMPORTING
          EV_CODE = LV_CODE
          EV_NOT_FOUND = LV_NOT_FOUND
           ).

        IF LV_NOT_FOUND IS NOT INITIAL
          OR LV_CODE IS INITIAL.
*         it is not customized (returned empty string)
          IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
*           When it is SEPA payment define the SEPA constant
            C_VALUE = GC_SEPA.
          ELSE.
*          decide according fallback logic via DTWS1
            CASE I_FPAYH-DTWS1.
              WHEN '11'.
                C_VALUE = GC_SVCLVL_CD_NURG.
              WHEN '12'.
                C_VALUE = GC_SVCLVL_CD_SDVA.
              WHEN '13'.
                C_VALUE = GC_SVCLVL_CD_URNS.
              WHEN '14'.
                C_VALUE = GC_SVCLVL_CD_URGP.
              WHEN '15'.
                C_VALUE = GC_SVCLVL_CD_BKTR.
              WHEN '16'.
                C_VALUE = GC_SVCLVL_CD_PRPT.
              WHEN '17'.
                C_VALUE = GC_SVCLVL_CD_NUGP.
            ENDCASE.
          ENDIF.
        ELSE.
          C_VALUE = LV_CODE.
        ENDIF.

      WHEN '<PmtInf><PmtTpInf><SvcLvl><Prtry>'.             "n2289247
* used in case of Swiss bank,..
        CLEAR C_VALUE.

      WHEN '<PmtInf><PmtTpInf><LclInstrm><Cd>'
        OR '<PmtInf><DrctDbtTxInf><PmtTpInf><LclInstrm><Cd>'.
*       This node defines the Local instrument fot the payment
        C_VALUE = I_FPAYHX-INST_CODE.                                   "n2414649

      WHEN '<PmtInf><PmtTpInf><LclInstrm><Prtry>'                       "n2330563
        OR '<PmtInf><DrctDbtTxInf><PmtTpInf><LclInstrm><Prtry>'.        "n2330563
*       Filled empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><PmtTpInf><SeqTp>'.                     "n2289247
        C_VALUE = I_FPAYHX-SEQ_TYPE.

      WHEN '<PmtInf><PmtTpInf><-CtgyPurp>'.                 "n2289247
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><PmtTpInf><CtgyPurp><Cd>'
        OR '<PmtInf><DrctDbtTxInf><PmtTpInf><CtgyPurp><Cd>'.
*       Check if the customized value for Application component CGI is customized
        CL_IDFI_CGI_DMEE_UTILS=>GET_CATEGORY_PURPOSE_CODE(
        EXPORTING
          IS_FPAYH = I_FPAYH
          IV_AREA  = MV_AREA
        IMPORTING
          EV_CODE = LV_CODE
          EV_NOT_FOUND = LV_NOT_FOUND
           ).

        IF LV_NOT_FOUND IS NOT INITIAL
          OR  LV_CODE IS INITIAL.
          CASE I_FPAYH-DTWS2.
            WHEN '01'.
              C_VALUE = GC_CTGYPURP_CD_DIVI.
            WHEN '02'.
              C_VALUE = GC_CTGYPURP_CD_INTC.
            WHEN '03'.
              C_VALUE = GC_CTGYPURP_CD_PENS.
            WHEN '04'.
              C_VALUE = GC_CTGYPURP_CD_SALA.
            WHEN '05'.
              C_VALUE = GC_CTGYPURP_CD_SUPP.
            WHEN '06'.
              C_VALUE = GC_CTGYPURP_CD_TREA.
            WHEN '07'.
              C_VALUE = GC_CTGYPURP_CD_CASH.
            WHEN OTHERS.
          ENDCASE.
        ELSE.
          C_VALUE = LV_CODE.
        ENDIF.

      WHEN '<PmtInf><PmtTpInf><CtgyPurp><Prtry>'
        OR '<PmtInf><DrctDbtTxInf><PmtTpInf><CtgyPurp><Prtry>'.          "n2893975
        CLEAR C_VALUE.

      WHEN '<PmtInf><ReqdColltnDt>'.                        "n2295642
*       Get RequestedCollectionDate from format parameters or from Due date
        IF NOT MS_FORMAT_PARAMS-DUEDATE_CGI CO ' 0'.          "n2508061
          CONCATENATE MS_FORMAT_PARAMS-DUEDATE_CGI(4)
                      MS_FORMAT_PARAMS-DUEDATE_CGI+4(2)
                      MS_FORMAT_PARAMS-DUEDATE_CGI+6(2)
                 INTO C_VALUE SEPARATED BY '-'.
        ELSE.
          CONCATENATE I_FPAYH-AUSFD(4)
                      I_FPAYH-AUSFD+4(2)
                      I_FPAYH-AUSFD+6(2)
                 INTO C_VALUE SEPARATED BY '-'.
        ENDIF.

      WHEN '<PmtInf><Cdtr><Nm>'.
*       This node returns the creditor's name from AUST1 fiels (HOUSE BANK SETTINGS)
        IF I_FPAYHX-AUST1 IS NOT INITIAL
          AND MS_FORMAT_PARAMS-NATION IS INITIAL.
          CONCATENATE I_FPAYHX-AUST1 I_FPAYHX-AUST2
                 INTO C_VALUE SEPARATED BY SPACE.             "n2484794
        ELSE.
*         or it is taken in local language or from T001-BUTXT
          C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_DEBITOR_NAME(
              IV_NATION = MS_FORMAT_PARAMS-NATION
              IS_FPAYHX = I_FPAYHX
              IV_ZBUKR  = I_FPAYH-ZBUKR
          ).
        ENDIF.

      WHEN '<PmtInf><Cdtr><PstlAdr><-PstlAdr_More_Nodes>'.
*       This node handles visibility of more additional nodes in the adress
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><Cdtr><PstlAdr><Dept>'.                 "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><Cdtr><PstlAdr><SubDept>'.              "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><Cdtr><PstlAdr><StrtNm>'.               "n2562701
*       Creditor's Postal Address - Street Name
        C_VALUE = I_FPAYHX-REF01+0(60).

      WHEN '<PmtInf><Cdtr><PstlAdr><BldgNb>'.                 "n2562701
*       Creditor's Postal Address - Building Number
        C_VALUE = I_FPAYHX-REF01+60(20).

      WHEN '<PmtInf><Cdtr><PstlAdr><CtrySubDvsn>'.            "n2562701
*       Creditor's Postal Address - Country Sub-Division
        C_VALUE = I_FPAYHX-REF01+90(10).

      WHEN '<PmtInf><Cdtr><PstlAdr><AdrLine1>'.
*       This node holds the information about the street and house number
*       This is a technical node and it content will be used in the first ocurrence of the AdrLine
        IF I_FPAYHX-AUST3 IS NOT INITIAL
          AND I_FPAYHX-AUSTO IS NOT INITIAL.
          C_VALUE = I_FPAYHX-AUST3.
        ELSE.
*         Concatenate values from FPAYHX-REF01 field which holds info about the address
          CONCATENATE I_FPAYHX-REF01(60) I_FPAYHX-REF01+60(20)
            INTO C_VALUE
              SEPARATED BY SPACE.
        ENDIF.

      WHEN '<PmtInf><Cdtr><PstlAdr><AdrLine2>'.
*       This node holds the information about the postal code
*       This is a technical node and it content will be used in the second ocurrence of the AdrLine
        IF I_FPAYHX-AUST3 IS NOT INITIAL
          AND I_FPAYHX-AUSTO IS NOT INITIAL.
          C_VALUE = I_FPAYHX-AUSTO.
        ELSE.
*         Concatenate values from FPAYHX-REF01 field which holds info about the address
          CONCATENATE I_FPAYHX-REF01+80(10) I_FPAYHX-ORT1Z INTO C_VALUE
            SEPARATED BY SPACE.
        ENDIF.

      WHEN '<PmtInf><Cdtr><-Id>'.                           "n2289247
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><Cdtr><-CtryOfRes>'.
*       This node handles visibility of more additional nodes in the adress
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><Cdtr><-CtctDtls>'.
*       This node handles visibility of more additional nodes in the adress
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><Cdtr><CtctDtls><NmPrfx>'.                "n2484794
*       The Name Prefix of Debtor is generaly empty, as FPAYH-SALUT
*       contains values from view V_TSAD3T which is not expected as
*       DOCT, MIST, MISS, MADM
*       c_value = i_fpayh-salut.
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtrAcct><Id><IBAN>'.
*       This node holds the bank account in the IBAN form
        C_VALUE = I_FPAYHX-UIBAN.

      WHEN '<PmtInf><CdtrAcct><Id><Othr><Id>'.
*       This node holds the bank account if the IBAN is not known/used
        IF I_FPAYHX-UIBAN IS INITIAL.
          C_VALUE = I_FPAYHX-UBKNT.
        ENDIF.

      WHEN '<PmtInf><CdtrAcct><Tp><Cd>'.
*       This node is ued only for US no values in general class
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtrAcct><Tp><Prtry>'.
*       This node is ued only for US no values in general class
        CLEAR C_VALUE.                                        "n2394966

      WHEN '<PmtInf><CdtrAcct><-Ccy>'.
*       This node handles visibility
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtrAgt><FinInstnId><BIC>'.
        C_VALUE = I_FPAYHX-USWIF.

      WHEN '<PmtInf><CdtrAgt><FinInstnId><-ClrSysMmbId>'.
*       This node handles visibility of the Clearing system member Id
*       generaly always shown
        IF I_FPAYHX-USWIF IS INITIAL.                         "n2600590
          C_VALUE = ABAP_FALSE.
        ELSE.
*         Do not use together with <FinInstnId><BIC>
          C_VALUE = ABAP_TRUE.                                "n2600590
        ENDIF.                                                "n2600590

      WHEN '<PmtInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
        C_VALUE = I_FPAYHX-UBNKL.

      WHEN '<PmtInf><CdtrAgt><FinInstnId><-PstlAdr>'.
*       This node handles visibility of the Postal Adress
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtrAgt><FinInstnId><Othr><Id>'.
*       Identification is not provided
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE
          AND I_FPAYHX-UBNKL IS INITIAL
          AND I_FPAYHX-USWIF IS INITIAL.
          C_VALUE = GC_NOTPROVIDED.
        ENDIF.

      WHEN '<PmtInf><CdtrAgt><-BrnchId>'.
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtrAgt><BrnchId><Id>'.
*       Branch Identification
        C_VALUE = I_FPAYHX-UBRCH(35).

      WHEN '<PmtInf><-UltmtCdtr>'.
*       This node handles visibility of Ultimate Creditor on the B-level
*       In general nodes related to Ultimate Creditor are shown if
*       fpayp-bname <> fpayhx-namez
*       Because this information can be included either on B-level
*       or on C-level (not on both of them) then by default on the B-level
*       it is hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><UltmtCdtr><-PstlAdr>'.
*       This node handles visibility of Ultimate Creditor's Postal Address on the B-level
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><UltmtCdtr><PstlAdr><Dept>'.            "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><UltmtCdtr><PstlAdr><SubDept>'.         "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><UltmtCdtr><PstlAdr><StrtNm>'.          "n2562701
*       Ultimate Creditor's Postal Address - Street Name
        C_VALUE = I_FPAYP-REF01+0(60).

      WHEN '<PmtInf><UltmtCdtr><PstlAdr><BldgNb>'.          "n2562701n3043741
*       Ultimate Creditor's Postal Address - Building Number
        C_VALUE = I_FPAYP-REF01+100(10).

      WHEN '<PmtInf><UltmtCdtr><PstlAdr><CtrySubDvsn>'.       "n2562701
*       Ultimate Creditor's Postal Address - Country Sub-Division
        C_VALUE = I_FPAYP-REGIO.

      WHEN '<PmtInf><UltmtCdtr><-CtryOfRes>'.
*       This node handles visibility UltmtCdtr's Country of residence
*       (on the B-level)
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><ChrgBr>'.
*       This node is relevant only for SEPA payments
*       Returns SLEV value
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
          C_VALUE = GC_SLEV.
        ENDIF.

      WHEN '<PmtInf><-ChrgsAcct>'.
*       This node is relevant only for non-SEPA payments
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
*         hidden
          C_VALUE = ABAP_TRUE .
        ENDIF.

      WHEN '<PmtInf><ChrgsAcct><Id><IBAN>'.                 "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><-CdtrSchmeId>'.
*       This node handles visibility of Creditor Scheme Identification
*       by default hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtrSchmeId><Id><PrvtId><Othr><Id>'.   "n2289247
        C_VALUE = I_FPAYHX-REC_CRDID.

      WHEN '<PmtInf><CdtrSchmeId><Id><PrvtId><Othr><-SchmeNm>'.
*       This node handles visibility of SchmeNm
*       by default hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtrSchmeId><Id><PrvtId><Othr><SchmeNm><Prtry>'. "n2289247
        C_VALUE = 'SEPA'.

      WHEN: '<PmtInf><DrctDbtTxInf><PmtRef>'.
*       Batch Id - APPEND to global memory(batch Id + Documents)
        "we check ref06+40 first (BADI solution saved as DMEEX)
       IF I_FPAYHX-REF06+40(35) IS INITIAL.                           "n2942194
        LS_DMEE_ITEM_TMP-FPAYH  = I_FPAYH.
        LS_DMEE_ITEM_TMP-FPAYHX = I_FPAYHX.
        LS_DMEE_ITEM_TMP-FPAYP  = I_FPAYP.

        CALL FUNCTION 'DMEE_EXIT_SEPA_31'
          EXPORTING
            I_TREE_TYPE = I_TREE_TYPE
            I_TREE_ID   = I_TREE_ID
            I_ITEM      = LS_DMEE_ITEM_TMP
            I_PARAM     = I_PARAM
            I_UPARAM    = I_UPARAM
          TABLES
            I_TAB       = LT_DMEE_TAB_TMP.

       ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><PmtId><InstrId>'.

        LS_DMEE_ITEM_TMP-FPAYH  = I_FPAYH.
        LS_DMEE_ITEM_TMP-FPAYHX = I_FPAYHX.
        LS_DMEE_ITEM_TMP-FPAYP  = I_FPAYP.

        CALL FUNCTION 'DMEE_EXIT_SEPA_GET_INSTRID'
          EXPORTING
            I_TREE_TYPE = I_TREE_TYPE
            I_TREE_ID   = I_TREE_ID
            I_ITEM      = LS_DMEE_ITEM_TMP
            I_PARAM     = I_PARAM
            I_UPARAM    = I_UPARAM
          IMPORTING
            C_VALUE     = C_VALUE
          TABLES
            I_TAB       = LT_DMEE_TAB_TMP.

      WHEN '<PmtInf><DrctDbtTxInf><-PmtTpInf>'.
*       This node handles visibility of the Payment type info isn't used in SEPA
*       by default hidden
        C_VALUE = ABAP_TRUE.
        IF MV_IS_SEPA_PAYMENT EQ ABAP_FALSE.
*         for non-SEPA shown
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><PmtTpInf><InstrPrty>'.
*       This handles the Instruction property on the batch level HIGH/NORM
        IF I_FPAYHX-DTKZA EQ '01' OR I_FPAYHX-DTURG IS NOT INITIAL.
          C_VALUE = GC_INSTRPRTY_HIGH.
        ELSE."IF i_fpayh-dtws1 EQ '11'.
          C_VALUE = GC_INSTRPRTY_NORM.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><PmtTpInf><SeqTp>'.
*       Sequence Type
        C_VALUE = I_FPAYHX-SEQ_TYPE.

      WHEN '<PmtInf><DrctDbtTxInf><ChrgBr>'.
**      This node should be filled when it is not sepa payment
        IF MV_IS_SEPA_PAYMENT EQ ABAP_FALSE.
          CASE I_FPAYHX-DTKVS.
            WHEN '00'.
              C_VALUE = GC_CHRGBR_SHAR.
            WHEN '01'.
              C_VALUE = GC_CHRGBR_DEBT.
            WHEN '02'.
              C_VALUE = GC_CHRGBR_CRED.
            WHEN OTHERS.
          ENDCASE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><-DrctDbtTx>'.            "n2289247
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><MndtId>'. "n2533796
*       Mandant ID
        C_VALUE = I_FPAYHX-MNDID.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><DtOfSgntr>'.
*       Date of signature
        IF I_FPAYHX-SIGN_DATE NE '00000000'.
          CONCATENATE I_FPAYHX-SIGN_DATE(4) '-'
                      I_FPAYHX-SIGN_DATE+4(2) '-'
                      I_FPAYHX-SIGN_DATE+6(2) INTO C_VALUE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInd>'.
*       Indicator notifying whether the underlying mandate is amended
        IF I_FPAYHX-AMEND_IND IS INITIAL OR I_FPAYHX-SEQ_TYPE EQ 'FRST'.
          C_VALUE = 'false'.
        ELSE.
          C_VALUE = 'true'.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><-AmdmntInfDtls>'.
*       Amendment Information Details
        IF I_FPAYHX-AMEND_IND IS NOT INITIAL AND I_FPAYHX-SEQ_TYPE NE 'FRST'.
*         shown
          C_VALUE = ABAP_FALSE.
        ELSE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Nm>'.
*       Name of Original Creditor Scheme ID
        C_VALUE = I_FPAYHX-ORIG_REC_NAME1.
        IF C_VALUE IS INITIAL.
          C_VALUE = I_FPAYHX-ORIG_REC_NAME2.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><-OrgId>'.
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><OrgId><BICOrBEI>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><OrgId><Othr><Id>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><OrgId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><OrgId><Othr><SchmeNm><Prtry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><PrvtId><Othr><SchmeNm><-Cd>'.
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><PrvtId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><Id><PrvtId><Othr><SchmeNm><Prtry>'. "2533796
*       Empty value
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlCdtrSchmeId><-Id>'.
*       This node handles visibility of Identification of Original Creditor Scheme ID
*       by default shown
        C_VALUE = ABAP_FALSE. "n2893975

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlDbtr><-Id>'. "n2893975
*       This node handles visibility of Identification of Original Debtor ID
*       by default hidden
        C_VALUE = ABAP_TRUE.
        IF MV_CGIIR EQ GC_SWIFT.
          IF MV_CGIID IS NOT INITIAL.
*           shown
            C_VALUE = ABAP_FALSE.
          ENDIF.
        ELSE.
          IF MV_CGIID IS NOT INITIAL OR I_FPAYHX-DTKID IS NOT INITIAL.
*           shown
            C_VALUE = ABAP_FALSE.
          ENDIF.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><-OrgnlDbtr>'.
*       This node handes visibility of Original Debtor
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlDbtr><Id><PrvtId><Othr><Id>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlDbtr><Id><PrvtId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlDbtr><Id><CtryOfRes>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><-OrgnlDbtrAcct>'.
*       This node handes visibility of Original Debtor Account
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><-OrgnlDbtrAgt>'.
*       This node handes visibility of Original Debtor Account
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlDbtrAgt><FinInstnId><BIC>'.
*       BIC of Financial Institution Identification of Original Debtor Agent
        C_VALUE = I_FPAYHX-ORIG_BIC.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlDbtrAgt><FinInstnId><Othr><Id>'.
*       Identification of Financial Institution Identification of Original Debtor Agent
*       By default empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><MndtRltdInf><AmdmntInfDtls><OrgnlDbtrAgt><FinInstnId><Othr><SchmeNm><Prtry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><-CdtrSchmeId>'.
*       This node handles visibility of Creditor Scheme Identification
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><-OrgId>'.
*       This node handles visibility of Org. Identification of Creditor Scheme Identification
*       by hidden shown
*       Private ID is used instead
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><OrgId><BICOrBEI>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><OrgId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><OrgId><Othr><SchmeNm><Prtry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><-PrvtId>'.
*       This node handles visibility of Org. Identification of Creditor Scheme Identification
*       by default shown
*       !!!FROM SEPA RULE BOOK !!!!
*       Private Identification is used to identify either an
*       organisation or a private person.
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><PrvtId><Othr><Id>'
        OR '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><OrgId><Othr><Id>'.
*       By default following value is used
        C_VALUE = I_FPAYHX-REC_CRDID.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><PrvtId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DrctDbtTx><CdtrSchmeId><Id><PrvtId><Othr><SchmeNm><Prtry>'.
*       Proprietary of Scheme Name in Creditor Scheme Identification
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
*         When it is SEPA payment define the SEPA constant
          C_VALUE = GC_SEPA.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><-UltmtCdtr>'.
*       This node handles visibility of Ultimate Creditor on the C-level
*       In general it is shown if fpayp-bname <> fpayhx-namez
*       Here - on the C-level - it is checked if the condition is fulfilled,
*       if so then nodes are shown in the output
        IF I_FPAYP-BNAME  EQ I_FPAYHX-NAMEZ.
*         Values are the same -> hide
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><-PstlAdr>'.
*       This node handles visibility of Ultimate Creditor's Postal Address on the C-level
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><PstlAdr><-Unstructured_Adrlines_only>'.
*       generaly, structured(StrtNm,...) and unstructured(Adrline) tags shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><PstlAdr><Dept>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><PstlAdr><SubDept>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><PstlAdr><StrtNm>'. "n2562701
*       Ultimate Creditor's Postal Address - Street Name
        C_VALUE = I_FPAYP-REF01+0(60).

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><PstlAdr><BldgNb>'. "n2562701n3043741
*       Ultimate Creditor's Postal Address - Building Number
        C_VALUE = I_FPAYP-REF01+100(10).

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><PstlAdr><CtrySubDvsn>'. "n2562701
*       Ultimate Creditor's Postal Address - Country Sub-Division
        C_VALUE = I_FPAYP-REGIO.


      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><-CtryOfRes>'.
*       This node handles visibility UltmtCdtr's Country of residence
*       (on the C-level)
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><-Id>'.                    "n2508061
*       This node handles visibility UltmtCdtr's Country of residence
*       (on the B-level)
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><-OrgId>'.             "n2508061
*       This node handles visibility UltmtCdtr's Country of residence
*       (on the B-level)
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><OrgId><BICOrBEI>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><OrgId><Othr><Id>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><OrgId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><OrgId><Othr><SchmeNm><Prtry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><-PrvtId>'. "n2508061
*       This node handles visibility UltmtCdtr's Country of residence
*       (on the B-level)
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><PrvtId><Othr><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><Id><PrvtId><Othr><Prtry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtCdtr><CtryOfRes>'.  "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><-DbtrAgt>'.
*       This node handles visibility of Debtor Agent
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><FinInstnId><BIC>'. "n2289247

        C_VALUE = I_FPAYH-ZSWIF.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><FinInstnId><-ClrSysMmbId>'.
*       This node handles visibility Clearing system member ID              "n2375987
*       not shown in case <ClrSysId><Cd> is empty                           "n2375987
        IF I_FPAYHX-REF07+110(5) IS INITIAL OR I_FPAYH-ZSWIF IS NOT INITIAL."n2375987&n2441382&2600590
*         Do not use together with <BIC>
          C_VALUE = ABAP_TRUE.                                              "n2375987
        ELSE.                                                               "n2375987
          C_VALUE = ABAP_FALSE.
        ENDIF.                                                              "n2375987

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><FinInstnId><ClrSysMmbId><-ClrSysId>'. "n2289247
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
*       This node holds the value of the Clearing system member ID
        IF I_FPAYH-ZBNKL IS NOT INITIAL.
          C_VALUE = I_FPAYH-ZBNKL.
        ELSE.
          C_VALUE = I_FPAYH-ZBNKY.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><FinInstnId><-PstlAdr>'.
*       This node handles visibility of Postal Address of Debtor Agent
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><FinInstnId><Othr><Id>'. "n2562701
*       This node defines special parameters for Portugal
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><-BrnchId>'.
*       This node handles visibility of Branch info of the Debtor Agent
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAgt><BrnchId><Id>'.     "n2508061
*       Branch info/Code of the Debtor's Agent
        C_VALUE = I_FPAYH-ZBRCH.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Nm>'.                "n2654933
*       This node holds Debtor name
        C_VALUE = I_FPAYH-KOINH.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><-PstlAdr>'.
*       This node handles visibility of Postal Address of Debtor
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><-PstlAdr_More_Nodes>'.
*       This node handles visibility of more additional nodes in the adress
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><Dept>'.   "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><SubDept>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><StrtNm>'.
* Get street without House number
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYH-ZADNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-STREET.

      WHEN  '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><BldgNb>'.
* Get house number
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYH-ZADNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        IF LS_ADRC_TMP-HOUSE_NUM1 IS NOT INITIAL.
          C_VALUE =  LS_ADRC_TMP-HOUSE_NUM1.
        ELSE.
          C_VALUE =  LS_ADRC_TMP-HOUSE_NUM2.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><PstCd>'.
*       This node fills the Postal Debtor's code
        IF I_FPAYHX-XSCHK EQ ABAP_TRUE
          OR I_FPAYH-ZPSTL IS INITIAL.
          C_VALUE = I_FPAYH-ZPST2.
        ENDIF.
*       When the first option was not executed or the result is empty
        IF C_VALUE IS INITIAL.
          C_VALUE = I_FPAYHX-REF02+80(10).                      "n2942194
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><TwnNm>'.
*       This node fills the Debtor's Town name
        "first POBOX
          C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_PO_CITY(
              IV_DOC2R   = I_FPAYP-DOC2R
              IV_GPA1T   = I_FPAYH-GPA1T
              IV_NATION  = MS_FORMAT_PARAMS-NATION
              IV_DORIGIN = I_FPAYH-DORIGIN
              IV_DOC2T   = I_FPAYP-DOC2T
              IV_ZPFOR   = I_FPAYH-ZPFOR
              IV_ZADNR   = I_FPAYH-ZADNR
          ).                                                    "n2942194
        "then city
        IF C_VALUE IS INITIAL.
          C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_CITY(
              IV_DOC2R   = I_FPAYP-DOC2R
              IV_GPA1T   = I_FPAYH-GPA1T
              IV_NATION  = MS_FORMAT_PARAMS-NATION
              IV_DORIGIN = I_FPAYH-DORIGIN
              IV_DOC2T   = I_FPAYP-DOC2T
              IV_ZORT1   = I_FPAYH-ZORT1
              IV_ZADNR   = I_FPAYH-ZADNR
          ).                                                    "n2942194
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><CtrySubDvsn>'. "n2562701
*       Debtor's Postal Address - Country Sub-Division
        C_VALUE = I_FPAYH-ZREGI.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><AdrLine1>'.
*       This node holds the Debtor's street name
        C_VALUE = I_FPAYHX-REF09+70(60).                     "n2942194
*        c_value = cl_idfi_cgi_dmee_utils=>get_creditor_street(
*            iv_doc2r   = i_fpayp-doc2r
*            iv_gpa1t   = i_fpayh-gpa1t
*            iv_nation  = ms_format_params-nation
*            iv_dorigin = i_fpayh-dorigin
*            iv_doc2t   = i_fpayp-doc2t
*            iv_zstra   = i_fpayh-zstra
*            iv_zadnr   = i_fpayh-zadnr
*            iv_zpfac   = i_fpayh-zpfac                      "n2394966
*        ).

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><AdrLine2>'.
*       This node holds Debtor's Postal code
        C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_CITY(
            IV_DOC2R   = I_FPAYP-DOC2R
            IV_GPA1T   = I_FPAYH-GPA1T
            IV_NATION  = MS_FORMAT_PARAMS-NATION
            IV_DORIGIN = I_FPAYH-DORIGIN
            IV_DOC2T   = I_FPAYP-DOC2T
            IV_ZORT1   = I_FPAYH-ZORT1
            IV_ZADNR   = I_FPAYH-ZADNR
        ).

        CONCATENATE I_FPAYHX-REF02+80(10) C_VALUE            "n2942194
          INTO C_VALUE
          SEPARATED BY SPACE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><-Id>'.
*       This node handles visibility of Identification of Debtor
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><-OrgId>'.
*       This node handles visibility of Org. Identification of Debtor
        IF I_FPAYH-EIKTO IS INITIAL.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><OrgId><Othr><Id>'. "n2508061
        C_VALUE = I_FPAYH-EIKTO.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><OrgId><Othr><Issr>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><OrgId><-BICORBEI>'.               "n2508061
*       This node handles visibility of Org. Identification of BIC or BEI
          C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><-PrvtId>'.
*       This node handles visibility of Private Identification of Debtor
        IF I_FPAYHX-SND_DEBTOR_ID IS INITIAL OR I_FPAYH-EIKTO IS NOT INITIAL.
*         hidden
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><-DtAndPlcOfBirth>'.       "n2508061
*       This node handles visibility of Date and Birth of Private I.
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><DtAndPlcOfBirth><BirthDt>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><DtAndPlcOfBirth><PrvcOfBirth>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><DtAndPlcOfBirth><CityOfBirth>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><DtAndPlcOfBirth><CtryOfBirth>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><-Othr>'. "n2508061
*       This node handles visibility of Othr information of Private I.
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><Othr><SchmeNm><Prtry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><Id><PrvtId><Othr><Issr>'. "n2600590
*       This node holds Identification of Issurer
        C_VALUE = I_FPAYH-ZSWIF.

      WHEN '<PmtInf><DrctDbtTxInf><Dbtr><CtryOfRes>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAcct><Id><IBAN>'.
*       This node holds the bank account in the IBAN form
        C_VALUE = I_FPAYH-ZIBAN.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAcct><Id><Othr><Id>'.
*       This node holds Identification of Debtors Account
        IF I_FPAYH-ZIBAN IS INITIAL.
          C_VALUE = I_FPAYHX-ZBNKN_EXT.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAcct><Nm>'.
*       This node holds Name of Debtors Accont
        C_VALUE = I_FPAYH-KOINH.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAcct><Ccy>'.
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAcct><-Tp>'.                            "n2508061
*       This node handles visibility of Name od Debtor Account
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><DbtrAcct><Tp><Cd>'.       "n2330563
*       Filled empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><-UltmtDbtr>'.
*       This node handles visibility of Ultimate Debtor
*       it is shown when  FPAYP-NAME1 <> FPAYH-ZNME1
        IF I_FPAYP-NAME1 EQ I_FPAYH-ZNME1.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><-PstlAdr>'.
*       This node handles visibility of Postal Address of Ultimate Debtor
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><Dept>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><SubDept>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><StrtNm>'. "n2295642
*       Ultimate Debtor - Street
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-STREET.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><BldgNb>'. "n2295642
*       Ultimate Debtor - BldgNb
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-HOUSE_NUM1.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><PstCd>'.
*       Ultimate Debtor - Post Code
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        IF LS_ADRC_TMP-POST_CODE1 IS NOT INITIAL.
          C_VALUE =  LS_ADRC_TMP-POST_CODE1.
        ELSE.
          C_VALUE =  LS_ADRC_TMP-POST_CODE2.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><TwnNm>'.
*       Ultimate Debtor - Town
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-CITY1.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><CtrySubDvsn>'.
*       Ultimate Debtor - Region
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-REGION.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><Ctry>'.
*       Ultimate Debtor - Country
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-COUNTRY.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><AdrLine>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN  '<PmtInf><DrctDbtTxInf><UltmtDbtr><-Id>'.       "n2508061
*       This node handles visibility of Identification of Ultimate Debtor
*       by default shown
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><Id><-OrgId>'.                        "n2508061
*       This node handles visibility of Organizational Identification of Ultimate Debtor
*       by default shown
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><Id><OrgId><BICOrBEI>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><Id><OrgId><Othr><Id>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><Id><OrgId><Othr><-SchmeNm>'. "n2508061
*       This node handles visibility of Scheme Name
*       by default shown
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><Id><OrgId><Othr><SchmeNm><Cd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><Id><OrgId><Othr><SchmeNm><Prtry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><Id><OrgId><Othr><Issr>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><UltmtDbtr><CtryOfRes>'.  "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><InstrForCdtrAgt>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><-Purp>'.
*       This node handles visibility Purpose
*       it is not used for check payments
        IF MV_IS_CHECK_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE. "remove
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Purp><-Cd>'.              "n2893975
*       This node handles visibility Purpose code
*       generaly shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Purp><Cd>'.
*       This node holds the value for Purpose Code
        C_VALUE = I_FPAYP-XREF3.

      WHEN '<PmtInf><DrctDbtTxInf><Purp><-Prtry>'.           "n2893975
*       This node handles visibility Purpose code - Proprietary
*       generaly hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><Purp><Prtry>'.            "n2893975
*       This node holdes the value for Purpose Code - Proprietary
        C_VALUE = I_FPAYP-STRFR.

      WHEN '<PmtInf><DrctDbtTxInf><-RgltryRptg>'.
*       This node handles visibility of regulatory reporting
*       shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><DbtCdtRptgInd>'.
*       this node is used only in IT
*       filled empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><Authrty><Nm>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><Authrty><Ctry>'.
        C_VALUE = I_FPAYP-LANDL.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><Dtls><Tp>'.  "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><Dtls><Dt>'.  "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><Dtls><Ctry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><Dtls><Cd>'.
        IF I_FPAYP-LZBKZ NE SPACE.
          CALL FUNCTION 'FI_SCBINDICATOR_GETDETAIL'
            EXPORTING
              SCBINDICATOR = I_FPAYP-LZBKZ
            IMPORTING
              T015L_DATA   = LS_T015L.

          C_VALUE = LS_T015L-LVAWV.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><RgltryRptg><Dtls><Inf>'.
        IF I_FPAYP-LZBKZ NE SPACE.
          CALL FUNCTION 'FI_SCBINDICATOR_GETDETAIL'
            EXPORTING
              SCBINDICATOR = I_FPAYP-LZBKZ
            IMPORTING
              T015L_DATA   = LS_T015L.

          C_VALUE = LS_T015L-ZWCK1.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><-Tax>'.
*       This node handles visibility of Tax
*       generaly shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Cdtr><TaxId>'.
*       This node holds the value for creditor TAX ID
        C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_TAXID(
                      IV_GPA1R = I_FPAYH-GPA1R
                     ).

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Cdtr><RegnId>'.     "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Cdtr><TaxTp>'.      "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Dbtr><TaxId>'.
*       This node holds the value for Debtor's TAX ID
        C_VALUE = I_FPAYHX-STCEG.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Dbtr><RegnId>'.     "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Dbtr><TaxTp>'.      "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Dbtr><Authstn><Titl>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Dbtr><Authstn><Nm>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><AdmstnZn>'.         "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Mtd>'.
*       This node holds the Tax Method
        DATA LV_TAX_METHOD TYPE WITHT.

        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_METHOD     = LV_TAX_METHOD
        ).

        C_VALUE = LV_TAX_METHOD.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><TtlTaxblBaseAmt>'.  "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><TtlTaxAmt>'.        "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><SeqNb>'.
*       This node holds the Tax sequence number
        DATA LV_TAX_CTNUMBER TYPE CTNUMBER.

        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_CTNUMBER   = LV_TAX_CTNUMBER
        ).

        C_VALUE = LV_TAX_CTNUMBER.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><Ctgy>'.
*       This node holds the Tax Category
        DATA LV_TAX_CATEGORY TYPE WT_WITHCD.

        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_CATEGORY   = LV_TAX_CATEGORY
        ).

        C_VALUE = LV_TAX_CATEGORY.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><CtgyDtls>'.
*       This node holds the Tax Category Details
        DATA LV_TAX_CTGRY_DTLS TYPE TEXT40.

        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_CTGRY_DTLS = LV_TAX_CTGRY_DTLS
        ).

        C_VALUE = LV_TAX_CTGRY_DTLS.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><DbtrSts>'.    "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><CertId>'.     "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><FrmsCd>'.
*       This node holds the Tax forms
        DATA LV_TAX_FORMS_CODE TYPE QSREC.

        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_FORMS_CODE = LV_TAX_FORMS_CODE
        ).

        C_VALUE = LV_TAX_FORMS_CODE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><Prd><Yr>'.    "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><Prd><Tp>'.    "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><Prd><FrToDt><FrDt>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><Prd><FrToDt><ToDt>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><Rate>'.
*       This node holds the Tax Rate
        DATA LV_TAX_AMT_RATE TYPE WT_QSATZ.

        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_AMT_RATE   = LV_TAX_AMT_RATE
        ).

        IF LV_TAX_AMT_RATE IS NOT INITIAL.
          C_VALUE = LV_TAX_AMT_RATE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><TaxblBaseAmt>'.
        P_VALUE = ABS( I_FPAYP-DMBTR ).                              "2533796
**       In this node amount is returned in currency form p_value
*        DATA lv_tax_base_amt_in_loc_curr TYPE wt_bs.
*
*        cl_idfi_cgi_dmee_utils=>get_tax_info(
*          EXPORTING
*            iv_doc2r          = i_fpayp-doc2r
*            iv_zland          = i_fpayh-zland
*            iv_spras          = i_fpayh-zspra
*          IMPORTING
*            ev_tax_base_amt_in_loc_curr = lv_tax_base_amt_in_loc_curr
*        ).
*
**       we need to transform the currency in the display form
*        IF lv_tax_base_amt_in_loc_curr IS NOT INITIAL.
*          lv_amt_int = lv_tax_base_amt_in_loc_curr.
*          CALL FUNCTION 'CURRENCY_AMOUNT_SAP_TO_DISPLAY'
*            EXPORTING
*              currency        = i_fpayp-waers
*              amount_internal = lv_amt_int
*            IMPORTING
*              amount_display  = lv_amt_dis.
*
**         absolute value needs to be returned
*          p_value = abs( lv_amt_dis ).
*        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><TtlAmt>'.
        P_VALUE = ABS( I_FPAYP-QSTEU ).                              "2533796
**       In this node amount is returned in currency form p_value
*        DATA lv_tax_amt_in_loc_curr TYPE wt_wt.
*
*        cl_idfi_cgi_dmee_utils=>get_tax_info(
*          EXPORTING
*            iv_doc2r          = i_fpayp-doc2r
*            iv_zland          = i_fpayh-zland
*            iv_spras          = i_fpayh-zspra
*          IMPORTING
*            ev_tax_amt_in_loc_curr = lv_tax_amt_in_loc_curr
*        ).
*
**       we need to transform the currency in the display form
*        IF lv_tax_amt_in_loc_curr IS NOT INITIAL.
*          lv_amt_int = lv_tax_amt_in_loc_curr.
*          CALL FUNCTION 'CURRENCY_AMOUNT_SAP_TO_DISPLAY'
*            EXPORTING
*              currency        = i_fpayp-waers
*              amount_internal = lv_amt_int
*            IMPORTING
*              amount_display  = lv_amt_dis.
*
**         absolute value needs to be returned
*          p_value = abs( lv_amt_dis ).
*        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><Dtls><Prd><Yr>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><Dtls><Prd><Tp>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><Dtls><Prd><FrToDt><FrDt>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><Dtls><Prd><FrToDt><ToDt>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><Dtls><Amt>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><Tax><Rcrd><AddtlInf>'.   "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><-RltdRmtInf>'.
*       This node handles visibility
*       generaly shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Nm>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><Dept>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><SubDept>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><StrtNm>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><BldgNb>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><PstCd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><TwnNm>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><CtrySubDvsn>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><Ctry>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><AdrLine>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><-Ustrd>'.
*       This node handles visibility Structured remmitence information
*       Hidden when format parameter is set to 'X'/NOT INITIAL
        IF MS_FORMAT_PARAMS-STRD IS NOT INITIAL.
*         hidden
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Ustrd>'.           "n2508061
*       Unstructured tag is created with BAdI exit from NoteToPayee as
*       a concateneted Type 3 + Type 1
        CLEAR C_VALUE.
        CALL METHOD CL_IDFI_CGI_DMEE_UTILS=>GET_NOTE2PAYEE_BY_TYPE
          EXPORTING
            IM_TYPE = '3'
          IMPORTING
            EX_NOTE = C_VALUE.
        CALL METHOD CL_IDFI_CGI_DMEE_UTILS=>GET_NOTE2PAYEE_BY_TYPE
          EXPORTING
            IM_TYPE = '1'
          IMPORTING
            EX_NOTE = C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><-Strd>'.
*       This node handles visibility Structured remmitence information
*       Hidden when format parameter is set to ' '/INITIAL
        IF MS_FORMAT_PARAMS-STRD IS INITIAL.
*         hidden
          C_VALUE = ABAP_TRUE.
        ENDIF.
*       HINT: See below when you are looking for single occucence

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><-StrdLevel3>'.      "2533796
*       This node handles visibility Structured remmitence information
*       Which can have only one occurence
*       This is the exact copy of the multi <Strd> but with different level assigned to it
*       ALLWAYS Hidden
*       Must be allowed in SAP Country implementation or in the Customer implementation
        C_VALUE = ABAP_TRUE.
**       Example implementation:
*        FIELD-SYMBOLS:
*          <fs_ref>  TYPE dmee_node_if_aba.
*
**       Only in case where the <Strd> is requested
*        IF ms_format_params-strd IS INITIAL.
**         Check whether the Multipleoccurence's Strd is set
*          READ TABLE i_extension-ref_table WITH KEY ref_name = '-STRD' o_value = abap_true
*          ASSIGNING <fs_ref>.
*
*          IF sy-subrc EQ 0.
**           Strd with multiple occurence is allowed. This mustn't be populated!!!
**           You need to set as abap_false to allow this single occurence <Strd>
*            c_value = abap_true.
*          ELSE.
**           Allow the single occurence of the <Strd>
*            c_value = abap_false.
*          ENDIF.
*        ENDIF.
*
*       HINT: this influence also the content of the <Ref> Field

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><-StrdLv3CZ1>' OR
           '<PmtInf><DrctDbtTxInf><RmtInf><-StrdLv3CZ2>' OR
           '<PmtInf><DrctDbtTxInf><RmtInf><-StrdLv3CZ3>'.    "n2800089
*       Group of Nodes used in CZ/SK specific solution with Variable/
*       Specific/Constant Symbol, it is not used in other countries
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><Strd_Ref_CZ1>' OR
           '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><Strd_Ref_CZ2>' OR
           '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><Strd_Ref_CZ3>'. "n2800089
*       Group of Nodes used in CZ/SK specific solution with Variable/
*       Specific/Constant Symbol, it is not used in other countries
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><-RfrdDocInf>'.
*       This node handles visibility of Referred Document Information
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocInf><Tp><CdOrPrtry><Cd>'.
*       Document type in a coded form.
        IF I_FPAYP-WRBTR GT 0.
          C_VALUE = GC_CINV.
        ELSEIF I_FPAYP-WRBTR LT 0.
          C_VALUE = GC_CREN.
        ENDIF.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocInf><Nb>'.
        C_VALUE = I_FPAYP-XBLNR.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><-RfrdDocAmt>'.
*       This node handles visibility of Referred Document Amount
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><-DuePyblAmt>'.
*       This node handles visibility of Amount due and payable
        IF I_FPAYP-WRBTR EQ 0.
*         hidden
          C_VALUE = ABAP_TRUE.
        ENDIF.
      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><DuePyblAmt>'.
*       This node holds the value Amount due and payable
        P_VALUE = I_FPAYP-WRBTR.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><-DscntApldAmt>'.
*       This node handles visibility of Discount Amount
        IF I_FPAYP-WSKTO EQ 0.
*         hidden
          C_VALUE = ABAP_TRUE.
        ENDIF.
      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><DscntApldAmt>'.
*       This node holds the value for Discount Amount
        P_VALUE = I_FPAYP-WSKTO.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><-CdtNoteAmt>'.
*       This node handles visibility of Credit Note Amount
        IF I_FPAYP-WRBTR GE 0.
*         hidden
          C_VALUE = ABAP_TRUE.
        ENDIF.
      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><CdtNoteAmt>'.
*       This node holds the value for Credit Note Amount
        P_VALUE = I_FPAYP-WRBTR.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><-TaxAmt>'.
*       This node handles visibility of Tax Amount
        IF I_FPAYP-WQSTE EQ 0.
*         hidden
          C_VALUE = ABAP_TRUE.
        ENDIF.
      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><TaxAmt>'.
*       This node holds the value for Tax Amount
        P_VALUE = I_FPAYP-WQSTE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><AdjstmntAmtAndRsn><CdtDbtInd>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><AdjstmntAmtAndRsn><Rsn>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><AdjstmntAmtAndRsn><AddtlInf>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><-RmtdAmt>'.
*       This node handles visibility of Remitted Amount
        IF I_FPAYP-WRBTR LE 0.
          C_VALUE = ABAP_TRUE.
        ENDIF.
      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><RfrdDocAmt><RmtdAmt>'.
*       This node holds the value for Remitted Amount
        P_VALUE = I_FPAYP-WNETT.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><-CdtrRefInf>'.
*       This node handles visibility
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><-Tp>'.
*       This node handles visibility of Type
*       by default shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><Tp><CdOrPrtry><Cd>'. "n2508061
*       Always fill SCOR
        C_VALUE = 'SCOR'.                                   "#EC NOTEXT

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><Tp><CdOrPrtry><Prtry>'. "n2508061
*       Always empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><Tp><Issr>'.
*       This node holds value for Issuer
        C_VALUE = 'ISO'.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><CdtrRefInf><Ref>'.
        C_VALUE = I_FPAYP-STRFR.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><-Invcr>'.
*       generaly displayed                                     1
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><Invcr><Nm>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><-Invcee>'.
*       generaly displayed                                     1
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><Invcee><Nm>'. "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><-AddtlRmtInf>'.
*       This node handles visibility
*       generaly displayed
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><RmtInf><Strd><AddtlRmtInf>'. "n2295642
        C_VALUE = I_FPAYP-SGTXT.

      WHEN '<PmtInf><DrctDbtTxInf><PmtId><EndToEndId_Exit>'. "n2847996
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DrctDbtTxInf><PmtId><EndToEndId><EXIT>'. "n2847996
        C_VALUE = ABAP_FALSE.

      WHEN '<Document><CstmrDrctDbtInitn><PmtTrailer>'.
*       Batch Id - Save Documents from Global memory to db
        "we check ref06+40 first (BADI solution saved as DMEEX)
       IF I_FPAYHX-REF06+40(35) IS INITIAL.                           "n2942194
        LS_DMEE_ITEM_TMP-FPAYH  = I_FPAYH.
        LS_DMEE_ITEM_TMP-FPAYHX = I_FPAYHX.
        LS_DMEE_ITEM_TMP-FPAYP  = I_FPAYP.

        CALL FUNCTION 'DMEE_EXIT_SEPA_41'
          EXPORTING
            I_TREE_TYPE = I_TREE_TYPE
            I_TREE_ID   = I_TREE_ID
            I_ITEM      = LS_DMEE_ITEM_TMP
            I_PARAM     = I_PARAM
            I_UPARAM    = I_UPARAM
          TABLES
            I_TAB       = LT_DMEE_TAB_TMP.

       ENDIF.

      WHEN OTHERS.
        IF CL_IDFI_CGI_DMEE_UTILS=>IS_SAP_SYSTEM( ) EQ ABAP_TRUE.
          ASSERT 1 = 0. "no implementation in this method for the given field
        ENDIF.

    ENDCASE. " i_node_path

  ENDMETHOD.