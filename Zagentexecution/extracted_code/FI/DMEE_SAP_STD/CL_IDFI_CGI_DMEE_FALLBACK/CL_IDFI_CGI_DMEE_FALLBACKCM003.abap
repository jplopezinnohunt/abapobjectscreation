  METHOD GET_CREDIT.


    DATA:
      LS_DMEE_ITEM_TMP TYPE DMEE_PAYM_IF_TYPE,
      LT_DMEE_TAB_TMP  TYPE TABLE OF  DMEE_TREE_TYPE-IF_TAB,
      LV_NOT_FOUND     TYPE BOOLE_D,
      LV_CODE          TYPE STRING,
      LS_ADRC_TMP      TYPE ADRC,
      LS_T015L         TYPE T015L_D_BF,        "SCB information  "n2261341
      LV_AMT_DIS       TYPE WMTO_S-AMOUNT,                  "n2272412
      LV_AMT_INT       TYPE WMTO_S-AMOUNT.                  "n2272412

    CASE I_NODE_PATH.
*BEGIN*OF**********************<Document>*************************************
      WHEN '<Document><xmlns><ISO>'.                          "n2533796
*       Original ISO value
        IF I_EXTENSION-NODE_VALUES-REF_NAME = 'XMLNSV9'.    "n3159759
          C_VALUE = 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'.
        ELSE.
          C_VALUE = 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03'.
        ENDIF.

      WHEN '<Document><xmlns:xsi><ISO>'.                      "n2533796
*       Original ISO value
        C_VALUE = 'http://www.w3.org/2001/XMLSchema-instance'.

      WHEN '<Document><xsi:schemaLocation><schemaLocationExit>'. "n2533796
*       Original empty
        CLEAR C_VALUE.

      WHEN '<Document><CstmrCdtTrfInitn><Version>'.         "n3159759
        IF I_EXTENSION-NODE_VALUES-REF_NAME = 'V9'.
          MV_VERSION = '09'.
        ENDIF.

*BEGIN*OF**********************<GrpHdr>***************************************
      WHEN '<GrpHdr><MsgId>'.                               "n2283292
*       Originator’s unique identifier of the submitted file
        C_VALUE = I_FPAYHX-RENUM.

      WHEN '<GrpHdr><CreDtTm>'.
*       create ISO time stamp according time zone
        C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREATION_TIME_AND_DATE( ).

      WHEN '<GrpHdr><Authstn><Cd>'.                          "n2533796
*       Authorization Code, default empty, special handling for AE
        CLEAR C_VALUE.

      WHEN '<GrpHdr><Authstn><Prtry>'.                      "n3108984
*       Default empty, customers can use it in BADI
        CLEAR C_VALUE.

      WHEN '<GrpHdr><InitgPty><Nm>'.
*       First AUST1 and AUST2 then T001 (same as Dbtr Nm)   "n2960399
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

      WHEN '<GrpHdr><InitgPty><CtctDtls><Nm>'.               "n2350646
*       This node defines the Contact Details Name on Group Header
        CLEAR C_VALUE.

      WHEN '<GrpHdr><InitgPty><CtctDtls><Othr>'.             "n2350646
*       This node defines the Contact Details Other on Group Header
        CLEAR C_VALUE.

      WHEN '<GrpHdr><InitgPty><CtctDtls><Othr><ChanlTp>'.   "n3159759
*       This node defines the Contact Details Other on Group Header
        CLEAR C_VALUE.

      WHEN '<GrpHdr><InitgPty><CtctDtls><Othr><Id>'.        "n3159759
*       This node defines the Contact Details Other on Group Header
        CLEAR C_VALUE.

      WHEN '<GrpHdr><InitgPty><Id><PrvtId><Othr><Id>'.        "n2562701
*       This node defines special parameters for Portugal
        CLEAR C_VALUE.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><BICOrBEI>'
        OR '<PmtInf><Dbtr><Id><OrgId><BICOrBEI>'.
*       If the magic value is set to SWIFT so in this node CGIID should be used
        IF MV_CGIIR EQ GC_SWIFT.
          C_VALUE = MV_CGIID.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><AnyBIC>'
        OR '<PmtInf><Dbtr><Id><OrgId><AnyBIC>'.               "n2600590
*         Used in higher version than 03
        IF MV_VERSION = '09' AND MV_CGIIR EQ GC_SWIFT.      "n3159759
          C_VALUE = MV_CGIID.
        ELSE.
          CLEAR C_VALUE.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><-Othr>'
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr>'.
*       The other functionality is only for non-SWIFT Identification
*       Which can be done on the Company -> additional data
*       or on the house bank in field Customer Number
        IF MV_CGIIR EQ GC_SWIFT
          OR ( MV_CGIID IS INITIAL AND I_FPAYHX-DTKID IS INITIAL ) .   "n2800089
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><Othr><Id>'
        OR '<PmtInf><Dbtr><Id><OrgId><Othr><Id>'.
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
        OR '<PmtInf><Dbtr><Id><OrgId><Othr><SchmeNm><Prtry>'.
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
        OR '<PmtInf><Dbtr><Id><OrgId><Othr><SchmeNm><Cd>'.
*        This node refers to the node <GrpHdr><InitgPty><Id><OrgId><Othr><Id>
*        and its 2nd possible filling -> copied condition
*       In this casse Prtry tag has higher priority as Cd tag for SEPA payments
        IF MV_CGIIR NE GC_SWIFT.
          IF ( MV_IS_SEPA_PAYMENT EQ ABAP_FALSE )
              OR
             ( MV_IS_SEPA_PAYMENT EQ ABAP_TRUE
                AND
              MV_CGIID  IS INITIAL ).
            IF MV_CGIID IS NOT INITIAL
              OR I_FPAYHX-DTKID IS NOT INITIAL.
*             Fill only if the ID is filled
              IF MV_CGICD IS INITIAL.                       "n2893975
                C_VALUE = GC_BANK.
              ELSE.
                C_VALUE = MV_CGICD.
              ENDIF.
            ENDIF.
          ENDIF.
        ENDIF.

      WHEN '<GrpHdr><InitgPty><Id><OrgId><Othr><Issr>'
        OR '<PmtInf><Dbtr><Id><OrgId><Othr><Issr>'.
        IF MV_CGIIR NE GC_SWIFT.
          C_VALUE = MV_CGIIR.
        ENDIF.

      WHEN '<GrpHdr><FwdgAgt>'.                             "n2847996
        " Functionality for SK. Generally hidden.
        C_VALUE = ABAP_FALSE.

      WHEN '<GrpHdr><FwdgAgt><FinInstnId><Nm>'.             "n2847996
        " Functionality for SK. Generally not usede.
        CLEAR C_VALUE.

      WHEN '<GrpHdr><FwdgAgt><BrnchId><Nm>'.                "n2847996
        " Functionality for SK. Generally not used.
        CLEAR C_VALUE.

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
      WHEN '<PmtInf><PmtMtd>'.
*      This method indicates what kind of transfer it is
        CASE MV_IS_CHECK_PAYMENT.
          WHEN ABAP_TRUE.
            C_VALUE = GC_CHK.
          WHEN ABAP_FALSE.
            C_VALUE = GC_TRF.
        ENDCASE.

      WHEN '<PmtInf><BtchBookg>'.                             "n2600590
        C_VALUE = MS_FORMAT_PARAMS-BATCH_BOOKING.

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
        IF  MV_IS_SEPA_PAYMENT EQ ABAP_TRUE
          AND MV_IS_CHECK_PAYMENT NE ABAP_TRUE .
*         Dont hide for SEPA payments (w/o checks )
          C_VALUE = ABAP_FALSE.
          O_VALUE = ABAP_FALSE.
        ELSE.
          C_VALUE = ABAP_TRUE.
          O_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><PmtTpInf><InstrPrty>'.
*       This handles the Instruction property on the batch level HIGH/NORM
        IF I_FPAYHX-DTKZA EQ '01' OR I_FPAYHX-DTURG IS NOT INITIAL.
          C_VALUE = GC_INSTRPRTY_HIGH.
        ELSE."IF i_fpayhx-dtkza EQ '00'.
          C_VALUE = GC_INSTRPRTY_NORM.
        ENDIF.
*       Comment
*       Only two values are possible in this case. old solution used for NORM payment value from DTWS1 (EQ 11)
*       even if it would be empty this would mean that the priority is NORM (standard ISO20022 behaviour)

      WHEN '<PmtInf><PmtTpInf><SvcLvl><Cd>'.

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

      WHEN '<PmtInf><PmtTpInf><SvcLvl><Prtry>'.             "n2268668
*       This node defines the Service Level fot the payment  - Proprietary
        CLEAR C_VALUE.

      WHEN '<PmtInf><PmtTpInf><LclInstrm><Cd>'.
*       This node defines the Local instrument fot the payment
        CLEAR C_VALUE.

      WHEN '<PmtInf><PmtTpInf><LclInstrm><Prtry>'.          "n2268668
*       This node defines the Local Instrument fot the payment - Proprietary
        CLEAR C_VALUE.

      WHEN '<PmtInf><PmtTpInf><-CtgyPurp>'.
*       This node handles visibility of Category Purpose
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><PmtTpInf><CtgyPurp><Cd>'.
        IF MV_IS_HR_PAYMENT EQ ABAP_TRUE.
          C_VALUE = I_FPAYH-PURP_CODE.
        ELSE.
*         Check if the customized value for Application component CGI is customized
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
        ENDIF.

      WHEN '<PmtInf><PmtTpInf><CtgyPurp><Prtry>'.           "n2268668
*       This node defines the Category Purpose fot the payment - Proprietary
        CLEAR C_VALUE.

      WHEN '<PmtInf><ReqdExctnDt>'.                         "n2295642
*       Get RequestedExecutionDate from format parameters or from Due date
        IF NOT MS_FORMAT_PARAMS-DUEDATE_CGI CO ' 0'.        "n2387052
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

      WHEN '<PmtInf><ReqdExctnDt><Dt>'.                     "n3159759
*       Get RequestedExecutionDate from format parameters or from Due date
        IF NOT MS_FORMAT_PARAMS-DUEDATE_CGI CO ' 0'.
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

      WHEN '<PmtInf><Dbtr><Nm>'.
*       This node returns the debtor's name from AUST1 fiels defined on Payment method "n2261341
        IF I_FPAYHX-AUST1 IS NOT INITIAL
          AND MS_FORMAT_PARAMS-NATION IS INITIAL.           "n2261341
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

      WHEN '<PmtInf><Dbtr><-PstlAdr>'.                        "n2562701
*       This node handles visibility of the adress generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><Dbtr><PstlAdr><-PstlAdr_More_Nodes>'.
*       This node handles visibility of more additional nodes in the adress
*       generaly always shown
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.                 "n3108984
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.


      WHEN '<PmtInf><Dbtr><PstlAdr><Dept>'.           "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.
      WHEN '<PmtInf><Dbtr><PstlAdr><SubDept>'.           "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

*     begin of 2318961
      WHEN '<PmtInf><Dbtr><PstlAdr><StrtNm>'.
*       This node contains the Street Name of the debtor address
        C_VALUE = I_FPAYHX-REF01(60).
      WHEN '<PmtInf><Dbtr><PstlAdr><BldgNb>'.
*       This node contains the Building Number of the debtor address
        C_VALUE = I_FPAYHX-REF01+100(10).
      WHEN '<PmtInf><Dbtr><PstlAdr><PstCd>'.
*       This node contains the Postal code of the debtor address
        C_VALUE = I_FPAYHX-REF01+80(10).
      WHEN '<PmtInf><Dbtr><PstlAdr><TwnNm>'.
*       This node contains the Town name of the debtor address
        C_VALUE = I_FPAYHX-REF06+0(40).
      WHEN '<PmtInf><Dbtr><PstlAdr><CtrySubDvsn>'.
*       This node contains the Country Subdivision of the debtor address
        C_VALUE = I_FPAYHX-REF01+90(10).
*     end of of 2318961

      WHEN '<PmtInf><Dbtr><PstlAdr><Ctry>'.                   "n2562701
*       This node contains the Country of the debtor address
        C_VALUE = I_FPAYHX-LDISO.

      WHEN '<PmtInf><Dbtr><PstlAdr><AdrLine1>'.
*         This node holds the information about the street and house number
*         This is a technical node and it content will be used in the first ocurrence of the AdrLine
        IF I_FPAYHX-AUST3 IS NOT INITIAL
          AND I_FPAYHX-AUSTO IS NOT INITIAL.
          C_VALUE = I_FPAYHX-AUST3.
        ELSE.
*           concatenate values from FPAYHX-REF01 field which holds info about the address
          CONCATENATE I_FPAYHX-REF01(60) I_FPAYHX-REF01+100(10)
            INTO C_VALUE
              SEPARATED BY SPACE.
        ENDIF.

        IF MS_FORMAT_PARAMS-NATION IS INITIAL.              "2847996
*   replace strange characters                                    "2847996
          CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'               "2847996
            EXPORTING                                             "2847996
              INTEXT  = C_VALUE                                   "2847996
            IMPORTING                                             "2847996
              OUTTEXT = C_VALUE.                                  "2847996
        ENDIF.                                              "2847996

      WHEN '<PmtInf><Dbtr><PstlAdr><AdrLine2>'.
*         This node holds the information about the postal code
*         This is a technical node and it content will be used in the second ocurrence of the AdrLine
        IF I_FPAYHX-AUST3 IS NOT INITIAL
          AND I_FPAYHX-AUSTO IS NOT INITIAL.
          C_VALUE = I_FPAYHX-AUSTO.
        ELSE.
*           concatenate values from FPAYHX-REF01 field which holds info about the address
          CONCATENATE I_FPAYHX-REF01+80(10) I_FPAYHX-REF06+0(40) INTO C_VALUE
            SEPARATED BY SPACE.
        ENDIF.

        IF MS_FORMAT_PARAMS-NATION IS INITIAL.              "2847996
*   replace strange characters                                    "2847996
          CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'               "2847996
            EXPORTING                                             "2847996
              INTEXT  = C_VALUE                                   "2847996
            IMPORTING                                             "2847996
              OUTTEXT = C_VALUE.                                  "2847996
        ENDIF.                                              "2847996
**BEGIN*OF******************<PmtInf><Dbtr><Id>*************************************
***********************************************************************************
*
*!!!!! This functionality is the same like <GrpHdr><IniTyPty><Id> !!!!!!
*      So was moved to the corresponding when cases
***********************************************************************************
*      WHEN '<PmtInf><Dbtr><Id><OrgId><BICOrBEI>'.
**       If the magic value is set to SWIFT so in this node CGIID should be used
*
*
*      WHEN '<PmtInf><Dbtr><Id><OrgId><Othr><Id>'.
**        This node can be filled 2 ways.
**        1st parameter in the too1z CGIID
**        Information on this place (T001-PAVAL) has higher prio as 2nd location
*
*
*      WHEN '<PmtInf><Dbtr><Id><OrgId><Othr><SchmeNm><Prtry>'.
**       This node refers to the node <GrpHdr><InitgPty><Id><OrgId><Othr><Id>
**       and its 1st possible filling -> copied condition
*
*      WHEN '<PmtInf><Dbtr><Id><OrgId><Othr><SchmeNm><Cd>'.
**        This node refers to the node <GrpHdr><InitgPty><Id><OrgId><Othr><Id>
**        and its 2nd possible filling -> copied condition
**       In this casse Prtry tag has higher priority as Cd tag for SEPA payments
*
*      WHEN '<PmtInf><Dbtr><Id><OrgId><Othr><Issr>'.
*END*OF******************<PmtInf><Dbtr><Id>*************************************
      WHEN '<PmtInf><Dbtr><Id><OrgId><-Othr1>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr2>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr3>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr4>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr5>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr6>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr7>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr8>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-Othr9>' "N3159759
        OR '<PmtInf><Dbtr><Id><OrgId><-OthrA>'. "n3159759
*       These nodes are relevant only for Norway, generally always hidden.
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><Dbtr><-CtryOfRes>'.
*       This node handles visibility of more additional nodes in the adress
*       generaly always shown
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.   "n3108984
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><Dbtr><-CtctDtls>'.
*       This node handles visibility of more additional nodes in the adress
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><Dbtr><CtctDtls><NmPrfx>'.                "n2484794
*       The Name Prefix of Debtor is generaly empty, as FPAYH-SALUT
*       contains values from view V_TSAD3T which is not expected as
*       DOCT, MIST, MISS, MADM
*       c_value = i_fpayh-salut.
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAcct><Id><IBAN>'.
*       This node holds the bank account in the IBAN form
        C_VALUE = I_FPAYHX-UIBAN.

      WHEN '<PmtInf><DbtrAcct><Id><Othr><Id>'.
*       This node holds the bank account if the IBAN is not known/used
        IF I_FPAYHX-UIBAN IS INITIAL.
          C_VALUE = I_FPAYHX-UBKNT.
        ENDIF.

      WHEN '<PmtInf><DbtrAcct><Id><Othr><SchmeNm><Cd>'.
*       This node holds the bank account type if the iban is not known/used
*       Standard value is BBAN                                            "2366540
        IF I_FPAYHX-UIBAN IS INITIAL.
          C_VALUE = GC_BBAN.                                              "2366540
        ENDIF.

      WHEN '<PmtInf><DbtrAcct><Id><Othr><SchmeNm><Prtry>'.    "n2387052
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAcct><Id><Othr><Issr>'.              "n2600590
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAcct><Tp><Cd>'.
*       This node is ued only for US no values in general class
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAcct><Tp><Prtry>'.                               "2366540
*       Proprietary type
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAcct><-Ccy>'.
*       This node handles visibility
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><DbtrAcct><Nm>'.                           "2533796
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAcct><-Prxy>'.                     "3310863
*       This node handles visibility of Proxy element
*       Currently only used for Sweden
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><BIC>'.
        IF I_FPAYHX-USWIF IS NOT INITIAL.
          C_VALUE = I_FPAYHX-USWIF.
        ENDIF.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><BICFI>'.             "2533796
*       Used in v9                                          "n3159759
        IF MV_VERSION = '09' AND I_FPAYHX-USWIF IS NOT INITIAL.
          C_VALUE = I_FPAYHX-USWIF.
        ELSE.
          CLEAR C_VALUE.
        ENDIF.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><-ClrSysMmbId>'.
*       This node handles visibility of the Clearing system member Id
*       generaly always shown
        IF I_FPAYHX-USWIF IS INITIAL.                         "n2600590
          C_VALUE = ABAP_FALSE.
        ELSE.
*         Do not use together with <FinInstnId><BIC>
          C_VALUE = ABAP_TRUE.                                "n2600590
        ENDIF.                                                "n2600590

      WHEN '<PmtInf><DbtrAgt><FinInstnId><ClrSysMmbId><ClrSysId><Cd>'. "n2768124
*       Main House Bank Segments - This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><ClrSysMmbId><ClrSysId><Prtry>'. "n2768124
*       Main House Bank Segments - This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
        C_VALUE = I_FPAYHX-UBNKL.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><-PstlAdr>'.
*       This node handles visibility of the Clearing system member Id
*       generaly always shown
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.   "n3108984
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><PstlAdr><AdrLine1>'. "n2768124
*       Debtor Agent (House Bank) Address Line 1: Street Name & Number
*       c_value = i_fpayhx-ubstr.
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><PstlAdr><AdrLine2>'. "n2768124
*       Debtor Agent (House Bank) Address Line 2: City Name
*       c_value = i_fpayhx-ubort.
        CLEAR C_VALUE.

      WHEN '<PmtInf><DbtrAgt><FinInstnId><Othr><Id>'.
*       Identification is not provided
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE
          AND I_FPAYHX-UBNKL IS INITIAL
          AND I_FPAYHX-USWIF IS INITIAL.
          C_VALUE = GC_NOTPROVIDED.
        ENDIF.

      WHEN '<PmtInf><DbtrAgt><BrnchId><Id>'.
*       Branch Identification
        C_VALUE = I_FPAYHX-UBRCH.

      WHEN '<PmtInf><-UltmtDbtr>'.                          "n2318961
*       This node handles visibility of UltimateDebtor on GroupLevel
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><UltmtDbtr><Nm>'.                       "n2318961
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><UltmtDbtr><Id><OrgId><Othr><Id>'.      "n2318961
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><ChrgBr>'.
*       This node is relevant only for SEPA payments
*       Returns SLEV value
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
          C_VALUE = GC_SLEV.
        ENDIF.

      WHEN '<PmtInf><-ChrgsAcct>'.
*       This node is relevant only for non-SEPA payments
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><ChrgsAcct><Id><IBAN>'.                    "n2800089
*       This not is provided to the customer
        CLEAR C_VALUE.

      WHEN: '<PmtInf><CdtTrfTxInf><PmtRef>'.
*       Batch Id - APPEND to global memory(batch Id + Documents)
        "we check ref06+40 first (BADI solution saved as DMEEX)
       IF I_FPAYHX-REF06+40(35) IS INITIAL.                 "n2942194
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

      WHEN '<PmtInf><CdtTrfTxInf><PmtId><InstrId>'.

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

      WHEN '<PmtInf><CdtTrfTxInf><PmtId><-EndToEndId>'.
*       This node handles visibility of the End to end ID
*       generaly always shown
        C_VALUE = ABAP_FALSE.                                 "n2387052

      WHEN '<PmtInf><CdtTrfTxInf><-PmtTpInf>'.
*       This node handles visibility of the Payment type info
*       isn't used in SEPA or Check payments
        IF MV_IS_SEPA_PAYMENT NE ABAP_TRUE
          AND MV_IS_CHECK_PAYMENT NE ABAP_TRUE.
          C_VALUE = ABAP_FALSE.
          O_VALUE = ABAP_FALSE.
        ELSE.
          C_VALUE = ABAP_TRUE.
          O_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Amt><InstdAmt><Ccy>'.     "n3229727
        C_VALUE = I_FPAYH-WAERS.

      WHEN '<PmtInf><CdtTrfTxInf><Amt><-EqvtAmt>'.
*       How to fill subnodes?
        C_VALUE = ABAP_TRUE. "remove

      WHEN '<PmtInf><CdtTrfTxInf><Amt><EqvtAmt><Amt>'.        "n2654933
*       Is this Eqivalent Amount correct?
        P_VALUE = I_FPAYP-WRBTR.

      WHEN '<PmtInf><CdtTrfTxInf><Amt><EqvtAmt><Amt><Ccy>'.   "n2654933
*       Is this Eqivalent Amount Currency correct?
        C_VALUE = I_FPAYP-WAERS.

      WHEN '<PmtInf><CdtTrfTxInf><Amt><EqvtAmt><CcyOfTrf>'.   "n2654933
*       Is this Eqivalent Amount Currency ot Transaction correct?
        C_VALUE = I_FPAYHX-WAERS.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><InstrPrty>'.
*       This handles the Instruction property on the batch level HIGH/NORM
        IF I_FPAYHX-DTKZA EQ '01' OR I_FPAYHX-DTURG IS NOT INITIAL.
          C_VALUE = GC_INSTRPRTY_HIGH.
        ELSE."IF i_fpayh-dtws1 EQ '11'.
          C_VALUE = GC_INSTRPRTY_NORM.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><SvcLvl><Cd>'.
*
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
*         When it is SEPA payment this node should be empty
          CLEAR C_VALUE.
        ELSE.
*         Check if the customized value for Application component CGI is customized
          CL_IDFI_CGI_DMEE_UTILS=>GET_SERVICE_LEVEL_CODE(
          EXPORTING
            IS_FPAYH = I_FPAYH
            IV_AREA  = MV_AREA
          IMPORTING
            EV_CODE = LV_CODE
            EV_NOT_FOUND = LV_NOT_FOUND
             ).

          IF LV_NOT_FOUND IS NOT INITIAL
            OR  LV_CODE IS INITIAL.
*           if it is not customized (returned empty string) decide according fallback logic via DTWS1
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
          ELSE.
            C_VALUE = LV_CODE.
          ENDIF.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><SvcLvl><Prtry>'. "n2268668
*       This node defines the Service Level fot the payment - Proprietary
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><LclInstrm><Cd>'.
*       This node defines the Local instrument fot the payment
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><LclInstrm><Prtry>'. "n2268668
*       This node defines the Local Instrument fot the payment - Proprietary
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><-CtgyPurp>'.    "n2318961
*       This node handles visibility of <CdtTrfTxInf><PmtTpInf><CtgyPurp>
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><CtgyPurp><Cd>'.
        IF MV_IS_HR_PAYMENT EQ ABAP_TRUE.
          C_VALUE = I_FPAYH-PURP_CODE.
        ELSE.
*         Check if the customized value for Application component cgi is customized
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
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><CtgyPurp><Prtry>'. "n2257354
*       generaly hidden
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><ChrgBr>'.
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

      WHEN '<PmtInf><CdtTrfTxInf><-ChqInstr>'.
*       Only for check payments
        IF MV_IS_CHECK_PAYMENT EQ ABAP_FALSE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><ChqTp>'.
*       Check if the customized value for Application component CGI is customized
        CL_IDFI_CGI_DMEE_UTILS=>GET_CHECK_TYPE(
        EXPORTING
          IS_FPAYH = I_FPAYH
          IV_AREA  = MV_AREA
        IMPORTING
          EV_CODE = LV_CODE
          EV_NOT_FOUND = LV_NOT_FOUND
           ).

        IF LV_NOT_FOUND IS NOT INITIAL
          OR  LV_CODE IS INITIAL.
          CASE I_FPAYH-DTWS1.
            WHEN '07'.
              C_VALUE = GC_CHQTP_BCHQ.
            WHEN '08'.
              C_VALUE = GC_CHQTP_CCHQ.
            WHEN '09'.
              C_VALUE = GC_CHQTP_DRFT.
            WHEN OTHERS.
          ENDCASE.
        ELSE.
          C_VALUE = LV_CODE.
        ENDIF.

        GVS_CHECK_TYPE_TMP = C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><-ChqNb>'.          "2533796
*       This node handles visibility of the Check Number
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><DlvryMtd><Cd>'.
*       Check if the customized value for Application component CGI is customized
        CL_IDFI_CGI_DMEE_UTILS=>GET_CHECK_DELIVERY_METHOD(
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
            WHEN '10'.
              C_VALUE = GC_DLVRYMTD_MLDB.
            WHEN '14'.
              C_VALUE = GC_DLVRYMTD_MLCD.
            WHEN OTHERS.
          ENDCASE.
        ELSE.
          C_VALUE = LV_CODE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><-DlvrTo>'.        "n2699168
*       Cheque Payments in Malaysia
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Nm>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><AdrTp>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><Dept>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><SubDept>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><StrtNm>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><BldgNb>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><PstCd>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><TwnNm>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><CtrySubDvsn>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><Ctry>'
        OR '<PmtInf><CdtTrfTxInf><ChqInstr><DlvrTo><Adr><AdrLine'. "n2699168
*       Cheque Payments in Malaysia
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><DlvryMtd><Prtry>'. "n2387052
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><InstrPrty>'.
*       This handles the Instruction property on the batch level HIGH/NORM
        IF I_FPAYHX-DTKZA EQ '01' OR I_FPAYHX-DTURG IS NOT INITIAL.
          C_VALUE = GC_INSTRPRTY_HIGH.
        ELSE."IF i_fpayh-dtws1 EQ '11'.
          C_VALUE = GC_INSTRPRTY_NORM.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><-ChqMtrtyDt>'.
*       allowed if <ChqTp> EQ DRFT or ELDR.
        IF GVS_CHECK_TYPE_TMP NE GC_CHQTP_DRFT
          AND GVS_CHECK_TYPE_TMP NE GC_CHQTP_ELDR.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><FrmsCd>'.         "n2387052
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><ChqInstr><PrtLctn>'.
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-UltmtDbtr>'.
*       This node handles visibility of Ultimate Debtor
*       it is shown when FPAYP  BNAME   <>  FPAYHX  NAMEZ
        IF I_FPAYP-BNAME  EQ I_FPAYHX-NAMEZ.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtDbtr><-Id>'.         "n2318961
*       This node handles visibility of UltimateDebtor Id
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtDbtr><Id><OrgId><Othr><Id>'. "n2318961
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtDbtr><PstlAdr><-PstlAdr_More_Nodes_UltmtDbtr>'.
*       This node handles visibility of more postal address subnodes
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtDbtr><-PstlAdr>'.    "n2322683
*       This node handles visibility UltmtDbtr's Postal Address
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtDbtr><PstlAdr><Dept>'.    "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtDbtr><PstlAdr><SubDept>'.    "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtDbtr><-CtryOfRes>'.
*       This node handles visibility UltmtDbtr's Country of residence
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><-IntrmyAgt1>'.
*       This node handles visibility Intermediatory Agent 1
*       generaly always shown
*       but for SEPA payments it is not allowed
        IF  MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1><BrnchId><Id>'.    "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1><FinInstnId><-ClrSysMmbId>'. "n2600590
*       Do not display <BIC> together with <ClrSysMmbId>
        IF I_FPAYH-BSWIFT1 IS NOT INITIAL.    "n2847996
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1><FinInstnId><ClrSysMmbId><MmbId>'. "n2800089
        CALL FUNCTION 'GET_BANKCODE'
          EXPORTING
            I_BANKS  = I_FPAYH-BNKS1
            I_BANKL  = I_FPAYH-BNKL1
          IMPORTING
            E_ECSIC  = C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-IntrmyAgt1Acct>'.
        "This node handles visibility Intermediatory Agent 1, generaly always shown
        "but for SEPA payments it is not allowed                 "n2847996
        IF  MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Id><IBAN>'. "n2847996
        C_VALUE = I_FPAYH-IBAN1.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Id><Othr><Id>'. "n2847996
        "not with IBAN
        IF I_FPAYH-IBAN1 IS INITIAL.
          C_VALUE = I_FPAYH-BNKN1.
        ELSE.
          CLEAR C_VALUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtTr><Id><OrgId><Othr><SchmeNm><Prtry>'. "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Id><Othr><SchmeNm><Cd>'. "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Id><Othr><SchmeNm><Prtry>'. "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Id><Othr><Issr>'. "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Tp><Cd>'. "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Tp><Prtry>'. "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Ccy>'.    "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><IntrmyAgt1Acct><Nm>'.     "n2847996
        " This node is provided to customers
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-CdtrAgt>'.
*       This node handes the visibility of Creditor Agent
*       It is not used when it is a internal bank or
*       if it is a check payment
        DATA: LV_IS_INTERNAL_BANK TYPE BOOLE_D.
        LV_IS_INTERNAL_BANK = CL_IDFI_CGI_DMEE_UTILS=>IS_INTERNAL_BANK(
                     IV_ZBNKS  = I_FPAYH-ZBNKS
                     IV_ZIBAN  = I_FPAYH-ZIBAN
                     IV_ZSWIFT = I_FPAYH-ZSWIF
                     IV_ZBNKL  = I_FPAYH-ZBNKL
                 ).

        IF LV_IS_INTERNAL_BANK EQ ABAP_TRUE
          OR MV_IS_CHECK_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE. "remove node
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><BIC>'. "n2414649
*       This node is generaly provided                    "n2847996
        C_VALUE = I_FPAYH-ZSWIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><BICFI>'. "n2600590
*       Used in v9                                        "n3159759
        IF MV_VERSION = '09' AND I_FPAYH-ZSWIF IS NOT INITIAL.
          C_VALUE = I_FPAYH-ZSWIF.
        ELSE.
          CLEAR C_VALUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><-ClrSysMmbId>'.
*       This node handles visibility Clearing system member ID              "n2375987
*       not shown in case <ClrSysId><Cd> is empty                           "n2375987
        IF I_FPAYHX-REF07+110(5) IS INITIAL                                 "n2375987"n2441982
          OR MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.               "n3108984
          C_VALUE = ABAP_TRUE.                                              "n2375987
        ELSE.                                                               "n2375987
          C_VALUE = ABAP_FALSE.
        ENDIF.                                                              "n2375987

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><ClrSysId><Cd>'. "n2508061
        C_VALUE = I_FPAYHX-REF07+110(5).

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><ClrSysId><Prtry>'. "n2600590
*       Empty value - mandatory for Malaysia
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
*       this node holds the value of the Clearing system member ID
        IF I_FPAYH-ZBNKL IS NOT INITIAL.
          C_VALUE = I_FPAYH-ZBNKL.
        ELSE.
          C_VALUE = I_FPAYH-ZBNKY.
        ENDIF.


      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><-Nm>'.
*       This node handles visibility Name of the Creditor's bank
*       generaly always shown
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.   "n3108984
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><Nm>'.

        C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_NATION_BANK_NAME(
          IV_ZBNKS = I_FPAYH-ZBNKS
          IV_ZBNKY = I_FPAYH-ZBNKY
          IV_ZBNKA = I_FPAYH-ZBNKA
          IV_NATION = MS_FORMAT_PARAMS-NATION
          ).

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><-PstlAdr>'.
*       This node handles visibility address of the Creditor's bank
*       generaly always shown
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.   "n3108984
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><PstlAdr><AdrLine1>'. "n2311029
*       Creditor Agent Address Line 1: Street Name & Number
*       c_value = i_fpayh-zbstr.
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><PstlAdr><AdrLine2>'. "n2311029
*       Creditor Agent Address Line 2: City Name
*       c_value = i_fpayh-zbort.
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><-BrnchId>'.
*       This node handles visibility Branch info of the Creditor's bank
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><BrnchId><Id>'.     "n2508061
*       Branch info/Code of the Creditor's bank
        C_VALUE = I_FPAYH-ZBRCH.

      WHEN '<PmtInf><CdtTrfTxInf><-CdtrAgtAcct>'.
*       This node handes the visibility of Creditor Agent Account
*       This is used as far as I know only in UK.
*       removed
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgtAcct><Id><Othr><Id>'.
        C_VALUE = I_FPAYH-BKREF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Nm>'.
*       This node fills the creditor name
        IF  I_FPAYH-KOINH IS INITIAL
         OR I_FPAYH-KOINH EQ I_FPAYH-ZNME1.
*         the Account holder is empty or the Same as in the ZNAM1
          IF MV_IS_HR_PAYMENT EQ ABAP_TRUE  .
*          cond1: payment comes from HR
            C_VALUE = I_FPAYH-ZNME1.
          ELSE.
*           cond2: non-HR payment
            C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_NAME(
              IV_DOC2R   = I_FPAYP-DOC2R
              IV_GPA1T   = I_FPAYH-GPA1T
              IV_NATION  = MS_FORMAT_PARAMS-NATION
              IV_DORIGIN = I_FPAYH-DORIGIN
              IV_DOC2T   = I_FPAYP-DOC2T
              IV_ZADNR   = I_FPAYH-ZADNR
              IV_ZNAME1  = I_FPAYH-ZNME1
              IV_ZNAME2  = I_FPAYH-ZNME2
               ).
          ENDIF.
        ELSE.
*         cond3: take the name form accouny holder name
          C_VALUE = I_FPAYH-KOINH.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><-PstlAdr>'.           "n2533796
*       This node handles visibility of Postal Address of Creditor
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><Dept>'.             "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.
      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><SubDept>'.         "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.


      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><-PstlAdr_More_Nodes_Cdtr>'.
*       This node handles visibility of more postal address subnodes
*       generaly always shown
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.   "n3108984
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><PstCd>'.
*       This node fills the Postal Creditor's code
        IF I_FPAYHX-XSCHK EQ ABAP_TRUE
          OR I_FPAYH-ZPSTL IS INITIAL.
          C_VALUE = I_FPAYH-ZPST2.
        ENDIF.
*       When the first option was not executed or the result is empty
        IF C_VALUE IS INITIAL.
          C_VALUE = I_FPAYHX-REF02+80(10).              "n2942194
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
*       This node holds the Creditor Street name
        C_VALUE = I_FPAYHX-REF09+70(60).                "n2942194
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

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><BldgNb>'.  "n2484794
*       This node holds the Creditor Building number - Empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><TwnNm>'.
*       This node holds the Creditor Town Name
        IF I_FPAYHX-XSCHK EQ ABAP_TRUE.
*         This node holds the Creditor's POBOX
          C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_PO_CITY(
              IV_DOC2R   = I_FPAYP-DOC2R
              IV_GPA1T   = I_FPAYH-GPA1T
              IV_NATION  = MS_FORMAT_PARAMS-NATION
              IV_DORIGIN = I_FPAYH-DORIGIN
              IV_DOC2T   = I_FPAYP-DOC2T
              IV_ZPFOR   = I_FPAYH-ZPFOR
              IV_ZADNR   = I_FPAYH-ZADNR
          ).
        ENDIF.
*       When the first option was not executed or the result is empty
        IF C_VALUE IS INITIAL.
*         This node holds the Creditor's City
          C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_CITY(
              IV_DOC2R   = I_FPAYP-DOC2R
              IV_GPA1T   = I_FPAYH-GPA1T
              IV_NATION  = MS_FORMAT_PARAMS-NATION
              IV_DORIGIN = I_FPAYH-DORIGIN
              IV_DOC2T   = I_FPAYP-DOC2T
              IV_ZORT1   = I_FPAYH-ZORT1
              IV_ZADNR   = I_FPAYH-ZADNR
          ).
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><CtrySubDvsn>'.
*       This node holds the Creditor's Regoin
        C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_REGION(
           IV_DOC2R   = I_FPAYP-DOC2R
           IV_GPA1T   = I_FPAYH-GPA1T
           IV_NATION  = MS_FORMAT_PARAMS-NATION
           IV_DORIGIN = I_FPAYH-DORIGIN
           IV_DOC2T   = I_FPAYP-DOC2T
           IV_ZREGI   = I_FPAYH-ZREGI
           IV_ZADNR   = I_FPAYH-ZADNR
           IV_ZLAND   = I_FPAYH-ZLAND
           IV_ZREGX   = I_FPAYHX-ZREGX              "n2375987
           ).

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><Ctry>'.    "n2960399
*       This node holds the Creditor's Country
        C_VALUE = I_FPAYHX-ZLISO.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><AdrLine1>'.
*       This node holds the Customer's street name
*       for SEPA payments it contains also house number
        IF MV_IS_HR_PAYMENT EQ ABAP_FALSE.
          C_VALUE = I_FPAYHX-REF09+70(60).                "n2942194
*          c_value = cl_idfi_cgi_dmee_utils=>get_creditor_street(
*              iv_doc2r   = i_fpayp-doc2r
*              iv_gpa1t   = i_fpayh-gpa1t
*              iv_nation  = ms_format_params-nation
*              iv_dorigin = i_fpayh-dorigin
*              iv_doc2t   = i_fpayp-doc2t
*              iv_zstra   = i_fpayh-zstra
*              iv_zadnr   = i_fpayh-zadnr
*              iv_zpfac   = i_fpayh-zpfac                    "n2394966
*          ).
        ELSE.
          C_VALUE = I_FPAYHX-ZPFST.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><AdrLine2>'.
*        This node holds Customer's Postal code
        IF MV_IS_HR_PAYMENT EQ ABAP_TRUE.
          C_VALUE = I_FPAYHX-ZPLOR.
        ELSE.
          C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_CITY(
              IV_DOC2R   = I_FPAYP-DOC2R
              IV_GPA1T   = I_FPAYH-GPA1T
              IV_NATION  = MS_FORMAT_PARAMS-NATION
              IV_DORIGIN = I_FPAYH-DORIGIN
              IV_DOC2T   = I_FPAYP-DOC2T
              IV_ZORT1   = I_FPAYH-ZORT1
              IV_ZADNR   = I_FPAYH-ZADNR
          ).

          CONCATENATE I_FPAYHX-REF02+80(10) C_VALUE         "n2942194
            INTO C_VALUE
            SEPARATED BY SPACE.
        ENDIF.
      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><-Id>'.
*       This node handles visibility of Creditor Id
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><-OrgId>'.
*       This node handles visibility of Organization Id
*       it is hidden for HR payments
        IF MV_IS_HR_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><OrgId><BICOrBEI>'. "n2600590
*       Generaly it is empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><OrgId><AnyBIC>'.  "n2600590
*       Used in higher version than 03
*       Generaly it is empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><OrgId><Othr><Id>'.
*       This node holds the Organization Id
*       for non HR payments
        IF I_FPAYH-GPA1T NE GC_ONE_TIME_VENDOR OR
           I_FPAYP-GPA2R IS INITIAL.                        "n2330563
          C_VALUE = I_FPAYH-GPA1R.
        ELSE.
          C_VALUE = I_FPAYP-GPA2R.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><OrgId><Othr><SchmeNm><Cd>'.
*       This node holds the Scheme name for orgID
*       Generaly it is empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><OrgId><Othr><SchmeNm><Prtry>'. "n3043741
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><OrgId><Othr><Issr>'.      "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><-PrvtId>'.
*       This node handles visibility of Private Id
*       it is hidden for non HR payments
        IF MV_IS_HR_PAYMENT NE ABAP_TRUE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><DtAndPlcOfBirth><BirthDt>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><DtAndPlcOfBirth><PrvcOfBirth>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><DtAndPlcOfBirth><CityOfBirth>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><DtAndPlcOfBirth><CtryOfBirth>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><Othr><Id>'.
*       This node holds the Private Id
*       used only for HR payments already checked on parent's parent
        C_VALUE = I_FPAYP-SGTXT.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><Othr><SchmeNm><Cd>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><Othr><SchmeNm><Prtry>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Id><PrvtId><Othr><Issr>'.       "n2800089
*       This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><CtryOfRes>'.        "n2699168
*       used only in Indonesia
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><CtctDtls><Nm>'.
*       This node holds the name of the creditor
*       used only in TW
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><CtctDtls><EmailAdr>'. "n2654933
*       This node holds the e-mail of the creditor
*       used only in TW, Korea
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><CtctDtls><Othr>'.  "n2893975
        " we are providing this node to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-CdtrAcct>'.
*       This node handles visibility of Private Id
*       it is hidden for check payments
        IF  MV_IS_CHECK_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Id><IBAN>'.
*       This node fills the value for IBAN
        C_VALUE = I_FPAYH-ZIBAN.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Id><-Othr>'.
*       This node handles visibility of Other section
*       it is hidden if iban is filled
        IF  I_FPAYH-ZIBAN IS NOT INITIAL.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Id><Othr><Id>'. "2350646
*       for supplement 1 - Switzerland, iban isn't filled
        C_VALUE = I_FPAYHX-ZBNKN_EXT.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Id><Othr><SchmeNm><Cd>'.
*        This node holds the value for the proprietary
*        in general contains constant BBAN                   "2366540
*        CLEAR c_value.                                      "2366540
         C_VALUE = GC_BBAN.                                  "2366540

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Id><Othr><SchmeNm><Prtry>'.
*        This node holds the value for the proprietary
*        in general it is empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Id><Othr><Issr>'. "n2600590
*       in general it is empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Tp><Cd>'.
*        This node holds the value for the proprietary
*        in general it is empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Tp><Prtry>'.       "2533796
*       This node is generaly empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><Nm>'.
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.                 "n3108984
          CLEAR C_VALUE.
        ELSE.
          C_VALUE = I_FPAYH-KOINH.

          IF MS_FORMAT_PARAMS-NATION IS INITIAL.              "n2253924
*         replace strange characters

          CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
            EXPORTING
              INTEXT  = C_VALUE
            IMPORTING
              OUTTEXT = C_VALUE.
          ENDIF.
        ENDIF.                                         "n2253924

      WHEN '<PmtInf><CdtTrfTxInf><CdtrAcct><-Prxy>'.   "3310863
*       This node handles visibility of Proxy element
*       Currently only used for Sweden
*       generaly always hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtTrfTxInf><-UltmtCdtr>'.
*       This node handles visibility of Ultimate Creditor
*       It is not displayed when the name on the item si the same as the header
        IF I_FPAYP-NAME1 EQ I_FPAYH-ZNME1.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><-PstlAdr_More_Nodes_UltmtCdtr>'.
*       This node handles visibility of more postal address subnodes
*       generaly always shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><Dept>'.           "n2800089
*   This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><SubDept>'.           "n2800089
*   This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><StrtNm>'.
* Ultimate Creditor - Street
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-STREET.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><BldgNb>'.
* Ultimate Creditor - Building Number
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        IF LS_ADRC_TMP-HOUSE_NUM1 IS NOT INITIAL.
          C_VALUE =  LS_ADRC_TMP-HOUSE_NUM1.
        ELSE.
          C_VALUE =  LS_ADRC_TMP-HOUSE_NUM2.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><PstCd>'.
* Ultimate Creditor - Post Code
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

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><TwnNm>'.
* Ultimate Creditor - Town
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-CITY1.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><CtrySubDvsn>'.
* Ultimate Creditor - Region
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-REGION.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><Ctry>'.
* Ultimate Creditor - Country
        CALL METHOD CL_DMEE_PAYM_UT=>ADRC_CONVERT_TO_ADRLINES
          EXPORTING
            IV_ADDRNUM      = I_FPAYP-ADRNR
            IV_NATION       = MS_FORMAT_PARAMS-NATION
            IV_BANK_COUNTRY = FLT_VAL_COUNTRY
          IMPORTING
            ES_ADRC         = LS_ADRC_TMP.

        C_VALUE =  LS_ADRC_TMP-COUNTRY.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr><AdrLine>'.           "n2800089
*   This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><UltmtCdtr><CtryOfRes>'.           "n2800089
*   This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-InstrForCdtrAgt>'.
*       This node handles visibility instruction for Cdtr agent
*       it is not used for SEPA payments and non-SEPA
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE. "remove
        ELSE.                                                 "n2699168
          C_VALUE = ABAP_TRUE. "remove                        "n2699168
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><-InstrForCdtrAgtUETR>'.     "n2699168
*       SWIFT gpi UETR - Unique End-to-End Transaction Reference
        IF MV_IS_UETR_SWITCHED EQ ABAP_FALSE.
          C_VALUE = ABAP_TRUE. "remove
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><InstrForCdtrAgt><Cd>'.      "n2699168
*       filled empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><InstrForCdtrAgt><InstrInf>'."n2699168
*       Instruction Information for Creditor, can also hold
*       SWIFT gpi UETR - Unique End-to-End Transaction Reference
        CONCATENATE 'UETR/' MV_UETR INTO C_VALUE.              "n2800089

      WHEN '<PmtInf><CdtTrfTxInf><-InstrForDbtrAgt>'.
*       This node handles visibility instruction for Dbtr agent
*       it is not used for sepa payments
        IF MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE. "remove
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><InstrForDbtrAgt>'.        "n2330563
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-Purp>'.
*       This node handles visibility Purpose
*       it is not used for check payments
        IF MV_IS_CHECK_PAYMENT EQ ABAP_TRUE.
          C_VALUE = ABAP_TRUE. "remove
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Purp><-Cd>'.
*       This node handles visibility Purpose code
*       generaly shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><Purp><Cd>'.
*       This node holds the value for Purpose Code
        C_VALUE = I_FPAYP-XREF3.

      WHEN '<PmtInf><CdtTrfTxInf><Purp><-Prtry>'.
*       This node handles visibility Purpose code - Proprietary
*       generaly hidden
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtTrfTxInf><Purp><Prtry>'.              "n2768124
*       This node holdes the value for Purpose Code - Proprietary
        C_VALUE = I_FPAYP-STRFR. "I know that this will be hidden in the generic implementation but this is general filling for countries which use this node.

      WHEN '<PmtInf><CdtTrfTxInf><-RgltryRptg>'.
*       This node handles visibility regulatory reporting
*       generaly hidden
        C_VALUE = ABAP_TRUE. "display in all SAP country implementations

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><DbtCdtRptgInd>'.
*       this node is used only in IT
*       filled empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><Authrty><Nm>'.      "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><Authrty><Ctry>'.
        C_VALUE = I_FPAYP-LANDL.

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Tp>' OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Dt>' OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Ctry>'.   "n2654933
*       This node holds values for Indonesia crossborder payments
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Cd>'.   "n2261341
*       This note contains the code which is assigned to the SCB Indicator
        IF I_FPAYP-LZBKZ NE SPACE.
          CALL FUNCTION 'FI_SCBINDICATOR_GETDETAIL'
            EXPORTING
              SCBINDICATOR = I_FPAYP-LZBKZ
            IMPORTING
              T015L_DATA   = LS_T015L
            EXCEPTIONS
              NOT_FOUND    = 1.                               "n2375987

          IF SY-SUBRC EQ 0 AND LS_T015L-LVAWV IS NOT INITIAL.
            C_VALUE = LS_T015L-LVAWV.
          ELSE.
            C_VALUE = I_FPAYP-LZBKZ.                          "n2375987
          ENDIF.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Amt>'.        "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Amt><Ccy>'.        "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Inf>'.  "n2261341
*       this node contains the text value assigned to the SCB indicator
        IF I_FPAYP-LZBKZ NE SPACE.
          CALL FUNCTION 'FI_SCBINDICATOR_GETDETAIL'
            EXPORTING
              SCBINDICATOR = I_FPAYP-LZBKZ
            IMPORTING
              T015L_DATA   = LS_T015L
            EXCEPTIONS
              NOT_FOUND    = 1.                               "n2375987

          IF SY-SUBRC EQ 0.
            C_VALUE = LS_T015L-ZWCK1.
          ENDIF.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><-RgltryRptg2>'.             "n2768124
*       This node handles visibility regulatory reporting 2 for Russia
*       generaly hidden
        C_VALUE = ABAP_TRUE. "display in all SAP country implementations


      WHEN '<PmtInf><CdtTrfTxInf><RgltryRptg><DbtCdtRptgInd2>' OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Authrty><Ctry2>' OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Tp2>'      OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Dt2>'      OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Ctry2>'    OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Cd2>'      OR
           '<PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Inf2>'.   "n2768124
*       Those nodes holds values for Russia
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-Tax>'.
*       This node handles visibility Tax
*       Shown for non HR payments
        IF MV_IS_HR_PAYMENT EQ ABAP_TRUE                    "2366540
          OR MV_IS_SEPA_PAYMENT EQ ABAP_TRUE.               "n3108984
          C_VALUE = ABAP_TRUE.                                         "2366540
        ELSE.                                                          "2366540
          C_VALUE = ABAP_FALSE.                                        "2366540
        ENDIF.                                                         "2366540

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Cdtr><TaxId>'.
*         This node holds the value for creditor TAX ID
        C_VALUE = CL_IDFI_CGI_DMEE_UTILS=>GET_CREDITOR_TAXID(
                      IV_GPA1R = I_FPAYH-GPA1R
                     ).

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Cdtr><RegnId>'.      "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Cdtr><TaxTp>'.       "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.


      WHEN '<PmtInf><CdtTrfTxInf><Tax><Dbtr><TaxId>'.
*       This node holds the value for Debtor's TAX ID
        C_VALUE = I_FPAYHX-STCEG.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Dbtr><RegnId>'.      "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Dbtr><TaxTp>'.       "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Dbtr><Authstn><Titl>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Dbtr><Authstn><Nm>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><AdmstnZn>'.    "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Mtd>'.
*       This node holds the Tax Method
        DATA LV_TAX_METHOD TYPE WITHT.

       IF I_FPAYP-QSTEU IS NOT INITIAL.
        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_METHOD     = LV_TAX_METHOD
        ).

        C_VALUE = LV_TAX_METHOD.
       ELSE.
         CLEAR C_VALUE.
       ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><TtlTaxblBaseAmt>'.   "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><TtlTaxblBaseAmt><Ccy>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><TtlTaxAmt>'.         "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><TtlTaxAmt><Ccy>'.    "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><SeqNb>'.
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

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><Ctgy>'.
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

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><CtgyDtls>'.
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

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><DbtrSts>'.     "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><CertId>'.      "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><FrmsCd>'.
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

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><Prd><Yr>'.     "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><Prd><Tp>'.     "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><Prd><FrToDt><FrDt>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><Prd><FrToDt><ToDt>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><Rate>'.
*       This node holds the Tax forms
        DATA LV_TAX_AMT_RATE TYPE WT_QSATZ.

        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_AMT_RATE   = LV_TAX_AMT_RATE
        ).

        IF LV_TAX_AMT_RATE IS NOT INITIAL.                  "n2330563
          C_VALUE = LV_TAX_AMT_RATE.
          SHIFT C_VALUE LEFT DELETING LEADING SPACE.        "n2330563
        ENDIF.                                              "n2330563

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TaxblBaseAmt>'. "n2600590
*       In this node amount is returned in currency form p_value
*        p_value = abs( i_fpayp-dmbtr ).

        DATA LV_TAX_BASE_AMT_IN_LOC_CURR TYPE WT_BS.        "n2960399
*
        CL_IDFI_CGI_DMEE_UTILS=>GET_TAX_INFO(
          EXPORTING
            IV_DOC2R          = I_FPAYP-DOC2R
            IV_ZLAND          = I_FPAYH-ZLAND
            IV_SPRAS          = I_FPAYH-ZSPRA
          IMPORTING
            EV_TAX_BASE_AMT_IN_LOC_CURR = LV_TAX_BASE_AMT_IN_LOC_CURR
        ).

*       we need to transform the currency in the display form
        IF LV_TAX_BASE_AMT_IN_LOC_CURR IS NOT INITIAL.
          LV_AMT_INT = LV_TAX_BASE_AMT_IN_LOC_CURR.
          CALL FUNCTION 'CURRENCY_AMOUNT_SAP_TO_DISPLAY'
            EXPORTING
              CURRENCY        = I_FPAYP-WAERS
              AMOUNT_INTERNAL = LV_AMT_INT
            IMPORTING
              AMOUNT_DISPLAY  = LV_AMT_DIS.

*         absolute value needs to be returned
          P_VALUE = ABS( LV_AMT_DIS ).
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TtlAmt>'. "n2600590
*       In this node amount is returned in currency form p_value
        P_VALUE = ABS( I_FPAYP-QSTEU ).

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><AddtlInf><Dtls><Prd><Yr>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><AddtlInf><Dtls><Prd><Tp>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><AddtlInf><Dtls><Prd><FrToDt><FrDt>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><AddtlInf><Dtls><Prd><FrToDt><ToDt>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><Tax><Rcrd><AddtlInf><Dtls><Amt>'. "n2800089
*     This node is provided to the customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><-RltdRmtInf>'.
*       This node handles visibility
*       generaly shown
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtId>'.      "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnMtd>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnElctrncAdr>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Nm>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><Dept>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><SubDept>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><StrtNm>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><BldgNb>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><PstCd>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><TwnNm>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><CtrySubDvsn>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><Ctry>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RltdRmtInf><RmtLctnPstlAdr><Adr><AdrLine>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><-Ustrd>'.
*       This node handles visibility Structured remmitence information
*       Hidden when format parameter is set to 'X'/NOT INITIAL
        IF MS_FORMAT_PARAMS-STRD IS NOT INITIAL.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Ustrd>'.          "n2322683
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

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><-Strd>'.
*       This node handles visibility Structured remmitence information
*       Which can have multiple occurences
*       Hidden when format parameter is set to ' '/INITIAL
        IF MS_FORMAT_PARAMS-STRD IS INITIAL.
          C_VALUE = ABAP_TRUE.
        ENDIF.
*       HINT: See below when you are looking for single occucence

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><-StrdLevel3>'.
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

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><-StrdLv3CZ1>' OR
           '<PmtInf><CdtTrfTxInf><RmtInf><-StrdLv3CZ2>' OR
           '<PmtInf><CdtTrfTxInf><RmtInf><-StrdLv3CZ3>'.      "n2768124
*       Group of Nodes used in CZ/SK specific solution with Variable/
*       Specific/Constant Symbol, it is not used in other countries
        C_VALUE = ABAP_TRUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><Strd_Ref_CZ1>' OR
           '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><Strd_Ref_CZ2>' OR
           '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><Strd_Ref_CZ3>'. "n2768124
*       Group of Nodes used in CZ/SK specific solution with Variable/
*       Specific/Constant Symbol, it is not used in other countries
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocInf><Tp><CdOrPrtry><Cd>'.
        IF I_FPAYP-WRBTR GT 0.
          C_VALUE = GC_CINV.
        ELSEIF I_FPAYP-WRBTR LT 0.
          C_VALUE = GC_CREN.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocInf><Tp><CdOrPrtry><Prtry>'. "n2768124
*       in general it is empty
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocInf><Nb>'.
        C_VALUE = I_FPAYP-XBLNR.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocInf><-RltdDt>'.
*       This node handles visibility for referenced document date in struct data
*       generaly displayed
        IF I_FPAYP-BLDAT CO ' 0'.                               "2533796
*         Do no output 0000-00-00 in RltdDt node, it couses file rejection
          C_VALUE = ABAP_TRUE.
        ELSE.
          C_VALUE = ABAP_FALSE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocInf><RltdDt>'.
*       This node holds the value for RltdDt!?
        IF NOT I_FPAYP-BLDAT CO ' 0'.
          CONCATENATE I_FPAYP-BLDAT(4)
                      I_FPAYP-BLDAT+4(2)
                      I_FPAYP-BLDAT+6(2)
                      INTO C_VALUE SEPARATED BY '-'.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><-RfrdDocInf>'. "n2533796
*       This node handles visibility for referenced document Information
*       in struct data. Generaly displayed
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><-RfrdDocAmt>'.
*       This node handles visibility for referenced document amount in struct data
*       generaly displayed
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><-DuePyblAmt>'. "n2272412
*       This node handles visibility
        IF I_FPAYP-WRBTR EQ 0.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><DuePyblAmt>'.
*        This node holds the value for!?
        IF I_FPAYP-WRBTR NE 0.
          P_VALUE = I_FPAYP-WRBTR.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><-DscntApldAmt>'. "n2272412
*       This node handles visibility
        IF I_FPAYP-WSKTO EQ 0.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><DscntApldAmt>'.
*        This node holds the value for!?
        IF I_FPAYP-WSKTO NE 0.
          P_VALUE = I_FPAYP-WSKTO.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><-CdtNoteAmt>'.
*       This node handles visibility
        IF I_FPAYP-WRBTR GT 0.
          C_VALUE = ABAP_TRUE.
        ENDIF.
      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><CdtNoteAmt>'.
*        This node holds the value for!?
        IF I_FPAYP-WRBTR LT 0.
          P_VALUE = I_FPAYP-WNETT.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><-TaxAmt>'. "n2272412
*       This node handles visibility
        IF I_FPAYP-WQSTE EQ 0.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><TaxAmt>'.
*        This node holds the value for!?
        IF I_FPAYP-WQSTE NE 0.
          P_VALUE = I_FPAYP-WQSTE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><-AdjstmntAmtAndRsn>'. "n2272412
*       This node handles visibility - displayed if there is WHT    n3043741
        IF I_FPAYP-QSTEU IS NOT INITIAL.
          C_VALUE = ABAP_FALSE.
        ELSE.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><AdjstmntAmtAndRsn><Amt>'.
        P_VALUE = ABS( I_FPAYP-QSTEU ).                                         "2533796
**       In this node amount is returned in currency form p_value
*        DATA: lv_tax_amt_in_loc_curr TYPE wt_wt.
*
*        cl_idfi_cgi_dmee_utils=>get_tax_info(
*          EXPORTING
*            iv_doc2r          = i_fpayp-doc2r
*            iv_zland          = i_fpayh-zland
*            iv_spras          = i_fpayh-zspra
*          IMPORTING
*            ev_tax_amt_in_loc_curr = lv_tax_amt_in_loc_curr
*        ).
**       we need to transform the currency in the display form
*        IF lv_tax_amt_in_loc_curr IS NOT INITIAL.
*          lv_amt_int = lv_tax_amt_in_loc_curr.              "n2272412
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

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><AdjstmntAmtAndRsn><CdtDbtInd>'.
*       This node holds the value for!?
        IF I_FPAYP-WRBTR LT 0
          OR I_FPAYP-VOR1R EQ GC_DR.
          C_VALUE = GC_CDTDBTIND_CRDT.
        ELSEIF I_FPAYP-WRBTR GT 0
           OR I_FPAYP-VOR1R EQ GC_KR.
          C_VALUE = GC_CDTDBTIND_DBIT.
        ENDIF.

*      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><Helper_TaxblBaseAmt>'.
*      removed with note 2600590

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><AdjstmntAmtAndRsn><AddtlInf>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><-RmtdAmt>'.
*       This node holds the value for!?
        IF I_FPAYP-WRBTR LT 0.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><RmtdAmt>'.
*       This node holds the value for!?
        IF I_FPAYP-WRBTR GT 0.
          P_VALUE = I_FPAYP-WNETT.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><-CdtrRefInf>'.
*       This node handles visibility
*       displayed if additional information are filled
        IF I_FPAYP-STRFR IS INITIAL
          AND I_FPAYP-SGTXT IS INITIAL.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><-Tp>'.
*       This node handles visibility
*       displayed if additional information are filled
        IF I_FPAYP-STRFR IS INITIAL.
          C_VALUE = ABAP_TRUE.
        ENDIF.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><Tp><Issr>'.
        C_VALUE = GC_ISO.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><Tp><CdOrPrtry><Cd>'. "n2699168
        C_VALUE = GC_SCOR.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><Tp><CdOrPrtry><Prtry>'. "n2847996
        " This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><CdtrRefInf><Ref>'.
        C_VALUE = I_FPAYP-STRFR.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><-Invcr>'.
*       This node handles visibility
*       generaly displayed
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><Invcr><Nm>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><-Invcee>'.
*       This node handles visibility
*       generaly displayed
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><Invcee><Nm>'. "n2800089
*       This node is provided to customer
        CLEAR C_VALUE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><-AddtlRmtInf>'.
*       This node handles visibility
*       generaly displayed
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><RmtInf><Strd><AddtlRmtInf>'. "n2295642
        C_VALUE = I_FPAYP-SGTXT.

      WHEN '<PmtInf><CdtTrfTxInf><PmtId><EndToEndId_Exit>'.    "n2847996
        C_VALUE = ABAP_FALSE.

      WHEN '<PmtInf><CdtTrfTxInf><PmtId><EndToEndId><EXIT>'.   "n2847996
        C_VALUE = ABAP_FALSE.

      WHEN '<Document><CstmrCdtTrfInitn><PmtTrailer>'.
        "we check ref06+40 first (BADI solution saved as DMEEX)
       IF I_FPAYHX-REF06+40(35) IS INITIAL.                    "n2942194
*       Batch Id - Save Documents from Global memory to db
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
*END*OF**********************<PmtInf>***************************************
      WHEN OTHERS.
        IF CL_IDFI_CGI_DMEE_UTILS=>IS_SAP_SYSTEM( ) EQ ABAP_TRUE.
          ASSERT 1 = 0. "no implementation in this method for the given field
        ENDIF.
    ENDCASE.
  ENDMETHOD.