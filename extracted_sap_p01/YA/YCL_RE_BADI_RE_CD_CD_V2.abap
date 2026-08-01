* ==== CLASS POOL YCL_RE_BADI_RE_CD_CD_V2 ====
CLASS-POOL .
*"* class pool for class YCL_RE_BADI_RE_CD_CD_V2

*"* local type definitions
INCLUDE YCL_RE_BADI_RE_CD_CD_V2=======CCDEF.

*"* class YCL_RE_BADI_RE_CD_CD_V2 definition
*"* public declarations
  INCLUDE YCL_RE_BADI_RE_CD_CD_V2=======CU.
*"* protected declarations
  INCLUDE YCL_RE_BADI_RE_CD_CD_V2=======CO.
*"* private declarations
  INCLUDE YCL_RE_BADI_RE_CD_CD_V2=======CI.
ENDCLASS. "YCL_RE_BADI_RE_CD_CD_V2 definition

*"* macro definitions
INCLUDE YCL_RE_BADI_RE_CD_CD_V2=======CCMAC.
*"* local class implementation
INCLUDE YCL_RE_BADI_RE_CD_CD_V2=======CCIMP.

CLASS YCL_RE_BADI_RE_CD_CD_V2 IMPLEMENTATION.
*"* method's implementations
  INCLUDE METHODS.
ENDCLASS. "YCL_RE_BADI_RE_CD_CD_V2 implementation


* ---- YCL_RE_BADI_RE_CD_CD_V2=======CI ----
  PRIVATE SECTION.

    TYPES:
      BEGIN OF TY_PERIOD,
        DATE_FROM TYPE DATUM,
        DATE_TO   TYPE DATUM,
      END OF TY_PERIOD .
    TYPES:
      TY_PERIODS TYPE STANDARD TABLE OF TY_PERIOD WITH EMPTY KEY .
    TYPES:
*25/09/2025
      BEGIN OF TY_MONTH_CALC,
        VALUEVALIDFROM TYPE DATS,
        VALUEVALIDTO   TYPE DATS,
        MONTH_NO       TYPE N LENGTH 2,
        TOTAL_M2       TYPE REBDMEASVALUE,
        RENT_MOE       TYPE RECDUNITPRICE,
        PROV_PROV      TYPE RECDUNITPRICE,
      END OF TY_MONTH_CALC .
    TYPES:
      TY_MONTH_CALC_TAB TYPE STANDARD TABLE OF TY_MONTH_CALC WITH EMPTY KEY .

*  data CT_MESSAGE type RE_T_MSG .
    DATA MO_RULE TYPE REF TO CL_RECD_CALC_RULE_12 .             "CL_EXM_IM_RECD_CALC_RULE_DIFF
    DATA MV_COUNT TYPE INT2 VALUE 0 ##NO_TEXT.
    CLASS-DATA MT_MEAS_X TYPE RE_T_MEAS_X .
    DATA MO_PARENT TYPE REF TO IF_REBD_HAS_MEAS .
    DATA MV_TOTAL TYPE RECDUNITPRICE VALUE 0 ##NO_TEXT.
    DATA MV_PROVTOTAL TYPE RECDUNITPRICE VALUE 0 ##NO_TEXT.
    DATA ZMV_COUNT TYPE INT2 .
    DATA MV_PROVCOUNT TYPE INT2 .
    DATA MT_MONTH_CALC TYPE TY_MONTH_CALC_TAB .

*25/09/2025
    METHODS GET_CONFIG
      IMPORTING
        !I_CONTYPE       TYPE RECNCONTRACTTYPE
        !I_DATE          TYPE DATUM DEFAULT SY-DATUM
        !IO_OBJECT       TYPE REF TO OBJECT
        !IO_RO_OBJNR     TYPE RECAOBJNR
        !IO_RECNTYPE     TYPE RECNCONTRACTTYPE
        !IO_OFFICSIZE    TYPE REBDMEASVALUE
        !ID_ACTIVITY     TYPE RECAACTIVITY OPTIONAL
        !IO_AVGOFFICSIZE TYPE REBDMEASVALUE
        !IO_OFFICSIZETOT TYPE REBDMEASVALUE
        !LV_YEAR         TYPE GJAHR
      EXPORTING
        !ES_PROVCONS     TYPE RECDUNITPRICE
        !E_APPLNAME      TYPE FDT_APPLICATION_NAME
        !E_FUNCTION      TYPE FDT_FUNCTION_NAME
        !ES_UNITPRICE    TYPE RECDUNITPRICE
        !ES_MONTHREN     TYPE RECDUNITPRICE
        !ES_MONTHPROV    TYPE RECDUNITPRICE
      CHANGING
        !CT_MESSAGE      TYPE RE_T_MSG OPTIONAL .
    METHODS GET_BPTYPE
      IMPORTING
        !IO_OBJECT  TYPE REF TO OBJECT
      EXPORTING
        !E_BPKIND   TYPE BU_BPKIND
        !E_BP_GROUP TYPE BU_GROUP .
    METHODS WAS_CONDITION_POSTED
      IMPORTING
        !I_CONDITION     TYPE REF TO IF_RECD_CONDITION
      RETURNING
        VALUE(RV_POSTED) TYPE ABAP_BOOL .
*      RETURNING
*        VALUE(result) TYPE recdcalcrule.
*      ev_condtype TYPE recdcondtype.
    METHODS GET_FORMULA_FOR_OBJECT
      IMPORTING
        !IS_CONTRACT  TYPE REF TO IF_RECN_CONTRACT
        !IS_OBJECT    TYPE RECAOBJNR
      RETURNING
        VALUE(RESULT) TYPE RECDCALCRULE .
    METHODS GET_CONTRACT_TOTALS
      IMPORTING
        !I_DATE             TYPE DATUM DEFAULT SY-DATUM
        !IT_OBJECT_CONTRACT TYPE BAPI_RE_T_OBJECT_REL_INT
        !LO_CONTRACT        TYPE REF TO CL_RECN_CONTRACT
      EXPORTING
        !V_OFFICES          TYPE REBDMEASVALUE
        !V_OFFICSIZETOT     TYPE REBDMEASVALUE
        !ID_ACTIVITY        TYPE RECAACTIVITY
        !V_AVGOFFSIZE       TYPE REBDMEASVALUE .
    METHODS SET_CONDITIONS
      IMPORTING
        !V_OFFICES      TYPE REBDMEASVALUE OPTIONAL
        !V_OFFICSIZETOT TYPE REBDMEASVALUE OPTIONAL
        !ID_ACTIVITY    TYPE RECAACTIVITY OPTIONAL
        !V_AVGOFFSIZE   TYPE REBDMEASVALUE
        !IS_CONDITION   TYPE RECD_CONDITION
        !V_MONTHREN     TYPE RECDUNITPRICE
        !LT_COND        TYPE RE_T_IF_RECD_CONDITION
        !LS_DET         TYPE RECN_CONTRACT
        !LV_YEAR        TYPE GJAHR
        !V_MONTHPROV    TYPE RECDUNITPRICE
      CHANGING
        !V_UNITPRICE    TYPE RECDUNITPRICE
        !V_PROVECONS    TYPE RECDUNITPRICE .

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM001 ----
  METHOD CONSTRUCTOR.
    CREATE OBJECT MO_RULE.
  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM002 ----
  METHOD GET_BPTYPE.
** 1 Get Vendor Type
    DATA LO_CONTRACT TYPE REF TO CL_RECN_CONTRACT.
    DATA: LT_BUT000 TYPE BUT000.
    LO_CONTRACT ?= IO_OBJECT.
    IF LO_CONTRACT IS BOUND.
      DATA: LT_PARTNERS TYPE RE_T_BP_OBJREL.
      LO_CONTRACT->GET_PARTNER_MNGR( )->GET_LIST(
        IMPORTING
          ET_LIST = LT_PARTNERS
        EXCEPTIONS
          ERROR   = 1
          OTHERS  = 2
      ).
      IF SY-SUBRC <> 0.
        RETURN.
      ENDIF.
    ENDIF.

    LOOP AT LT_PARTNERS INTO DATA(LT_PARTNERS2)
      WHERE ( ROLE = 'FLCU00' OR ROLE = 'TR0600' ) .
      SELECT SINGLE BPKIND, BU_GROUP
        INTO CORRESPONDING FIELDS OF  @LT_BUT000
        FROM BUT000
        WHERE PARTNER = @LT_PARTNERS2-PARTNER.

      IF SY-SUBRC <> 0.
        MESSAGE I004(ZRE) WITH LT_PARTNERS2-PARTNER.

      ENDIF.

    ENDLOOP.
    E_BPKIND = LT_BUT000-BPKIND.
    E_BP_GROUP = LT_BUT000-BU_GROUP.
  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM003 ----
  METHOD GET_CONFIG.
    "tables YRE_CN_PRICECALC  YRE_CN_TARIFF
    DATA: LT_CONFIG TYPE FMCA_PT_BRFPLUS_T.
    DATA: LT_CONFIG2 TYPE YRE_CN_TARIFF.
    DATA: LT_BUT000 TYPE BUT000.
    FIELD-SYMBOLS: <FS> LIKE LINE OF LT_CONFIG.
    DATA LO_CONTRACT TYPE REF TO CL_RECN_CONTRACT.
    DATA: LT_CN_PRICECALC TYPE YRE_CN_PRICECALC.
    DATA MO TYPE REF TO CL_REBD_MEAS_MNGR_RO.
    DATA: LT_MEAS_CN TYPE RE_T_MEASUREMENT_CN.

    DATA: V_UNITPRICE TYPE RECDUNITPRICE,
          V_PROVECONS TYPE RECDUNITPRICE,
          V_OFFICSIZE TYPE REBDMEASVALUE,
          V_BPKIND    TYPE BU_BPKIND,
          V_FACTOR(2) TYPE N.
    DATA: P_DEC TYPE P DECIMALS 2.
    DATA LV_VALUE TYPE P.

** 1 Get Vendor Type
    LO_CONTRACT ?= IO_OBJECT.
    GET_BPTYPE(
                EXPORTING IO_OBJECT   = IO_OBJECT
                IMPORTING E_BPKIND =  V_BPKIND
                                    ).

***3 get object usage type and Office Size to calcutate rent using AVG M2
    DATA:
      LS_RODETAIL       TYPE BAPI_RE_RENTAL_OBJECT_INT,
      LT_ROMEASUREMENT  TYPE BAPI_RE_T_MEASUREMENT_INT,
      LS_ET_SUB_OBJECTS TYPE RE_T_OBJNR,
      IV_SNUNR          TYPE REBDUSAGETYPE.
***3.1 get Individual office size
    CALL FUNCTION 'API_RE_RO_GET_DETAIL'
      EXPORTING
*       io_object        = io_object
        ID_OBJNR         = IO_RO_OBJNR
      IMPORTING
        ES_RENTAL_OBJECT = LS_RODETAIL
        ET_MEASUREMENT   = LT_ROMEASUREMENT
      EXCEPTIONS
        ERROR            = 1
        OTHERS           = 2.

    CHECK SY-SUBRC = 0.
    IF SY-SUBRC = 0.
      LOOP AT LT_ROMEASUREMENT INTO DATA(LO_ROMEASUREMENT) WHERE MEAS = 'M2'.
        V_OFFICSIZE = LO_ROMEASUREMENT-MEASVALUE.
      ENDLOOP.
    ENDIF.

***3.1 get Usage type as Parameter to access Table with Scales.
    IV_SNUNR = LS_RODETAIL-SNUNR.

***4 Get Configuration for BP type YRE_CN_PRICECALC
*Using BP TYPE and Office Size
*PROVCONS ALGORYTHM

    SELECT SINGLE
                  TOTAL,
                  PROVCONS,
                  ALGORYTHM,
                  DISCOUNT
*                  GJAHR
      FROM YRE_CN_PRICECALC
      INTO ( @LT_CN_PRICECALC-TOTAL,
             @LT_CN_PRICECALC-PROVCONS,
             @LT_CN_PRICECALC-ALGORYTHM,
             @LT_CN_PRICECALC-DISCOUNT )

*       CORRESPONDING FIELDS OF  @lt_cn_pricecalc

      WHERE
      USAGETYPE = @IV_SNUNR                 " Usage Type
      AND BPKIND =  @V_BPKIND               " Vendor Kind
      AND M2CHECK >=  @IO_OFFICSIZETOT    " range for Total Offices Size
      AND M2CHECK_FROM <=  @IO_OFFICSIZETOT " range for Total offices Size
      AND GJAHR = @LV_YEAR.

    IF SY-SUBRC = '0'. " CONFIGURATION SELECTED


* For Office
**5 Formulas ALGORYTHM 1 and 2
***5.1 Algoritm 1 Get m2 price from Rental Scale table only for algorithm 1
      IF LT_CN_PRICECALC-ALGORYTHM = '1'.
        SELECT  SINGLE
                ANNRATE, "Annual Rent
                MORATE   "Monthly Rent
                 FROM YRE_CN_TARIFF
                 INTO  ( @LT_CONFIG2-ANNRATE,
                         @LT_CONFIG2-MORATE )
                 WHERE
                 SPACE_TO >=  @IO_OFFICSIZETOT
                 AND SPACE_FROM <=   @IO_OFFICSIZETOT
                 AND GJAHR = @LV_YEAR.

        ES_MONTHREN = LT_CONFIG2-MORATE.
        ES_MONTHPROV = LT_CN_PRICECALC-PROVCONS / 12 * IO_OFFICSIZETOT.
        LT_CONFIG2-MORATE =  LT_CONFIG2-MORATE / IO_OFFICSIZETOT * V_OFFICSIZE.
        IF SY-SUBRC = 0.
*6 Set Unit Price and Provcons For alg USING SCALE
          ES_UNITPRICE = LT_CONFIG2-MORATE
                * ( 1 - ( LT_CN_PRICECALC-DISCOUNT / '100' ) ).

          ES_PROVCONS = LT_CN_PRICECALC-PROVCONS / 12 * V_OFFICSIZE.
        ELSE.
          MESSAGE I002(ZRE) WITH IO_OFFICSIZETOT.
*          APPEND VALUE #( msgid = 'ZRE'
*                    msgno = '002'
*                    msgty = 'I'
*                    msgv1 = io_officsizetot ) TO ct_message.
        ENDIF.

*******************
      ELSEIF LT_CN_PRICECALC-ALGORYTHM = '2'.
        """"Desactivat rounding.
        ES_MONTHREN = LT_CN_PRICECALC-TOTAL / 12 * IO_OFFICSIZETOT.
        ES_MONTHPROV =  LT_CN_PRICECALC-PROVCONS / 12 * IO_OFFICSIZETOT.

***6 Set Unit price and Prov cons for alg 2 USING FIX VALUE TABLES and factor depending on contract type
*DEFINE factor to divide master data price.
        IF  IO_RECNTYPE = 'OFFI' . "    Data Price in year condion Price Semester
*Set price and Prov
*        es_unitprice = ( lt_cn_pricecalc-total  / 2 )
*          es_unitprice = ( lt_cn_pricecalc-total  * io_avgofficsize )
          ES_UNITPRICE = ( LT_CN_PRICECALC-TOTAL / 12  * V_OFFICSIZE )
         * ( 1 - ( LT_CN_PRICECALC-DISCOUNT / '100' ) ) .
*          es_provcons =  lt_cn_pricecalc-provcons /  * v_officsize.
          ES_PROVCONS =  LT_CN_PRICECALC-PROVCONS /  12 * V_OFFICSIZE.  " As reference value was changed to Monthly
        ELSEIF IO_RECNTYPE = 'PARK'. "  Data Price in Year condition Price Month
*         es_unitprice = ( lt_cn_pricecalc-total )
          ES_UNITPRICE = ( LT_CN_PRICECALC-TOTAL ) / 12  " As reference value was changed to Monthly
          * ( 1 - ( LT_CN_PRICECALC-DISCOUNT / '100' ) ) .

        ENDIF.

      ELSE. " No cONGIGURATION SELECTED
**Add error message
        MESSAGE I001(ZRE) WITH IV_SNUNR V_BPKIND IO_OFFICSIZETOT.
*         APPEND VALUE #( msgid = 'ZRE'
*                    msgno = '001'
*                    msgty = 'I'
*                    msgv1 = iv_snunr
*                    msgv2 = v_bpkind
*                    msgv3 = io_officsizetot
*                     ) TO ct_message.
      ENDIF.
    ENDIF.
    "Round

  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM004 ----
  METHOD GET_FORMULA_FOR_OBJECT.


    DATA: LT_CONDITIONS TYPE TABLE OF RECD_CONDITION,
          LS_CONDITION  TYPE RECD_CONDITION,
          LO_COND_MNGR  TYPE REF TO IF_RECD_CONDITION_MNGR,
          CONDT         TYPE RECD_CONDITION-CONDTYPE.
    RESULT = ''.

    IF IS_CONTRACT IS BOUND.

      LO_COND_MNGR = IS_CONTRACT->GET_CONDITION_MNGR( ).

      LO_COND_MNGR->GET_LIST(
        EXPORTING
          IF_IGNORE_FILTER          = ABAP_TRUE
          IF_INCL_MODIFY_FLAG       = ABAP_FALSE
          IF_INCL_DELETED_CONDITION = ABAP_FALSE
          IF_FULL_LIST              = ABAP_FALSE
        IMPORTING
          ET_DETAIL                 = LT_CONDITIONS ).



      LOOP AT LT_CONDITIONS INTO LS_CONDITION
        WHERE OBJNR = IS_OBJECT
        AND CONDTYPE = 'MOE'.
        RESULT = LS_CONDITION-CALCRULE.
        CONDT = LS_CONDITION-CONDTYPE.
*          read table lt_conditions with key condtype = 'PROV'
*                    objnr = is_object INTO data(ls_condition2).
*          if   ls_condition-calcrule <> ls_condition2-calcrule.
*                 MESSAGE i004(zre) WITH is_object.
*          endif.
        EXIT.
      ENDLOOP.


    ENDIF.

  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM005 ----
  METHOD WAS_CONDITION_POSTED.
    DATA: LV_POSTED TYPE ABAP_BOOL.

    CALL METHOD I_CONDITION->IS_BOOKED
      IMPORTING
        ED_BOOKED = LV_POSTED.

    RV_POSTED = LV_POSTED.
  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM006 ----
  METHOD IF_EX_RECD_CALC_RULE~GET_FLEXIBLE.
    "BREAK a_vinca.
*    IF io_object IS BOUND.
*      DATA lo_contract TYPE REF TO cl_recn_contract.
*      lo_contract ?= io_object.
*      IF lo_contract IS BOUND.
*        DATA: lt_partners TYPE re_t_bp_objrel.
*        lo_contract->get_partner_mngr( )->get_list(
*          IMPORTING
*            et_list = lt_partners
*          EXCEPTIONS
*            error   = 1
*            OTHERS  = 2
*        ).
*        IF sy-subrc <> 0.
*          RETURN.
*        ENDIF.
*
*
*        DATA(lo_cond_mngr)   = lo_contract->get_condition_mngr( ).
*        DATA(lo_object_mngr) = lo_cond_mngr->get_object_mngr( ).
*        DATA lt_object TYPE re_t_obj_assign.
*
*        CALL METHOD lo_object_mngr->get_list
*          EXPORTING
*            if_fix_periods = abap_false
*          IMPORTING
*            et_list        = lt_object.
*
*      ENDIF.
*    ENDIF.
    CHECK ID_CALCRULEEXT = 'U'.


    CF_FLEXIBLE      = ABAP_FALSE.
    CD_FLEXIBLE_FROM = RECA0_DATE-MIN.
    CD_FLEXIBLE_TO   = RECA0_DATE-MIN.

    MO_RULE->GET_FLEXIBLE(
      EXPORTING
        "ID_CALCRULEEXT = ID_CALCRULEEXT
        IO_OBJECT        = IO_OBJECT                 " Object with Conditions
        IS_CONDITION     = IS_CONDITION                 " Condition
      CHANGING
        CF_FLEXIBLE      = CF_FLEXIBLE                 " Does Rule Support Flexible Intervals?
        CD_FLEXIBLE_FROM = CD_FLEXIBLE_FROM                 " Start of Flexible Interval
        CD_FLEXIBLE_TO   = CD_FLEXIBLE_TO                 " End of Flexible Interval
    ).
  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM007 ----
  METHOD IF_EX_RECD_CALC_RULE~GET_VALUES.
    DATA: V_UNITPRICE    TYPE RECDUNITPRICE,
          V_MONTHREN     TYPE RECDUNITPRICE,
          V_MONTHPROV    TYPE RECDUNITPRICE,
          V_PROVECONS    TYPE RECDUNITPRICE,
          V_OFFICSIZETOT TYPE REBDMEASVALUE,
          V_OFFICSIZE    TYPE REBDMEASVALUE,
          V_AVGOFFSIZE   TYPE REBDMEASVALUE,
          V_OFFICES      TYPE REBDMEASVALUE.
    DATA: P_DEC TYPE P DECIMALS 5.
    DATA LV_VALUE TYPE P DECIMALS 2.
    DATA LV_VALUE0 TYPE P DECIMALS 0.
    DATA : LS_CONFIG   TYPE TFMCA_PT_BRFPLUS,
           LS_CONTYPE  TYPE BAPI_RE_CONTRACT_TYPE_INT,
           LV_END_DATE TYPE RECDVALIDTO.
    DATA: LT_MEASUREMENT   TYPE BAPI_RE_T_MEAS_CN_INT,
          LT_ROMEASUREMENT TYPE BAPI_RE_T_MEASUREMENT_INT.
*Get Conditions
    DATA LO_CONTRACT TYPE REF TO CL_RECN_CONTRACT.

*22/05/2025
    DATA LS_COND TYPE RECD_CONDITION.
    DATA LT_COND  TYPE RE_T_IF_RECD_CONDITION.
    DATA LT_COND2 TYPE RE_T_RECD_CONDITION.
    DATA: LT_PERIODS      TYPE TY_PERIODS,
          LT_MEASUREMENTS TYPE BAPI_RE_T_MEASUREMENT_INT,
          LV_SQM_PERIOD   TYPE REBDMEASVALUE,
          LO_CONDITION    TYPE REF TO IF_RECD_CONDITION,
          LT_CONDITIONS   TYPE RE_T_IF_RECD_CONDITION.

*Check if condition is custom Bapi calculation Rule Unesco
    CHECK ID_CALCRULEEXT = 'U'.
    " *** Old, incorrect logic: wrapped in an always-false condition to be ignored ***
    IF  IO_OBJECT IS BOUND.
      LO_CONTRACT ?= IO_OBJECT.

      CLEAR: CT_CALC_VALUES,
             CT_DIST_VALUES,
             CT_CALC_USED_OBJECTS,
             CT_DIST_USED_OBJECTS,
             CD_OBJNRPARA.


      DATA(LO_CONDITION_MNGR) = LO_CONTRACT->GET_CONDITION_MNGR( ).

**Use of helper Class
**Using Helper Class 30/05/2025
*        DATA(lo_helper) = zrefx_tariff_helper=>get_instance( ).
*        DATA(lv_date) = lv_end_date.
*        lo_helper->init(
*          EXPORTING
*            io_contract =  lo_contract
*            it_measurements = lt_romeasurement
**            iv_date         = lv_date
*            iv_date         = id_abs_to " ENDOFTERM
*          IMPORTING
*            zh_condition    = lt_cond2 ).
*
*        DATA(ev_moe_sl) = lo_helper->get_booked_value_moes1( ).
*        DATA(ev_prov_sl) = lo_helper->get_booked_value_provs1( ).
*        DATA(lv_price_per_m2) = lo_helper->get_unit_price_per_m2( ).
*        DATA(lv_total_m2)     = lo_helper->get_total_m2( ).
*        DATA(lv_offices)      = lo_helper->get_totaloffices( ).
**END OF Using Helper Class 30/05/2025
**End use of helper class


      IF LO_CONTRACT IS BOUND.

*      DATA(ls_det1) = lo_contract->get_detail( ).
*get_contract_totals Determine Offices and SQM for the contract. It will be used to get the scale.
*V_OFFICES Office in the contract
*v_officsizetot Total SQM for all offices
*v_avgoffsize Average size of office to calculat M2 value based on Anual Rent

        GET_CONTRACT_TOTALS( EXPORTING IT_OBJECT_CONTRACT  = IT_OBJECT_CONTRACT
                                       LO_CONTRACT = LO_CONTRACT
                             IMPORTING  V_OFFICES = V_OFFICES
                                        V_OFFICSIZETOT = V_OFFICSIZETOT
                                        V_AVGOFFSIZE = V_AVGOFFSIZE   ).


*Get Contract details
        DATA(LS_DET) = LO_CONTRACT->GET_DETAIL( ).

*Get_COnfig Get the values from the configuration
****The year is important to set the Condition validity
        DATA(LV_YEAR) = ID_ABS_TO+0(4).
*        DATA(lv_year) = LS_DET-RECNEND1ST+0(4).

        GET_CONFIG( EXPORTING I_CONTYPE  = LS_CONTYPE-RECNTYPE
                                    I_DATE     = LV_END_DATE
                                    IO_OBJECT = LO_CONTRACT
                                    IO_RO_OBJNR  = IS_CONDITION-OBJNR " Rental Object
                                    IO_RECNTYPE = LS_DET-RECNTYPE " Contract Type OFFICE or PARK
                                    IO_OFFICSIZE = V_OFFICSIZE
                                    IO_AVGOFFICSIZE = V_AVGOFFSIZE
                                    IO_OFFICSIZETOT = V_OFFICSIZETOT
                                    LV_YEAR = LV_YEAR
                          IMPORTING
                                    ES_MONTHREN = V_MONTHREN
                                    ES_MONTHPROV = V_MONTHPROV
                                    ES_UNITPRICE =  V_UNITPRICE
                                    ES_PROVCONS = V_PROVECONS ).


**Get Contract Conditions
        LO_CONDITION_MNGR->GET_LIST(
              IMPORTING
                ETO_CONDITION = LT_COND
            ).
**Analize each condition

        SET_CONDITIONS( EXPORTING V_OFFICES = V_OFFICES
                                  V_AVGOFFSIZE = V_AVGOFFSIZE
                                  IS_CONDITION = IS_CONDITION
                                  V_MONTHREN = V_MONTHREN
                                  V_MONTHPROV = V_MONTHPROV
                                  LT_COND = LT_COND
                                  LS_DET = LS_DET
                                  LV_YEAR = LV_YEAR
                        CHANGING
                                  V_UNITPRICE = V_UNITPRICE
                                  V_PROVECONS = V_PROVECONS
                        ).
      ENDIF.
    ENDIF.


*update Calculated Value after change
    CALL METHOD MO_RULE->GET_VALUES
      EXPORTING
        "ID_CALCRULEEXT = ID_CALCRULEEXT
        ID_PARA_1            = ID_PARA_1
        ID_PARA_2            = ID_PARA_2
        ID_ABS_FROM          = ID_ABS_FROM
        ID_ABS_TO            = ID_ABS_TO
        IO_OBJECT            = IO_OBJECT
        IS_CONDITION         = IS_CONDITION
        IT_OBJECT_CONTRACT   = IT_OBJECT_CONTRACT
        IT_OBJECT_CONDITION  = IT_OBJECT_CONDITION
      CHANGING
        CT_CALC_VALUES       = CT_CALC_VALUES
        CT_DIST_VALUES       = CT_DIST_VALUES
        CT_CALC_USED_OBJECTS = CT_CALC_USED_OBJECTS
        CT_DIST_USED_OBJECTS = CT_DIST_USED_OBJECTS
        CD_OBJNRPARA         = CD_OBJNRPARA
      EXCEPTIONS
        ERROR                = 1
        OTHERS               = 2.
    IF SY-SUBRC <> 0.
      MESSAGE ID      SY-MSGID
              TYPE    SY-MSGTY
              NUMBER  SY-MSGNO
              WITH    SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4
              RAISING ERROR.
    ELSE.
      DATA LV_AMOUNT TYPE RECDCALCVALUE.


      CLEAR: CT_DIST_VALUES, CT_DIST_USED_OBJECTS.

    ENDIF.
    " *** End of Old Logic ***



*update Calculated Value after change
  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM008 ----
  METHOD IF_EX_RECD_CALC_RULE~GET_UNITS.
    CHECK ID_CALCRULEEXT = 'U'.


** call method of rule
    CALL METHOD MO_RULE->GET_UNITS
      EXPORTING
        "ID_CALCRULEEXT = ID_CALCRULEEXT
        IO_OBJECT         = IO_OBJECT
        IS_CONDITION      = IS_CONDITION
      CHANGING
        CD_UNIT_UNITPRICE = CD_UNIT_UNITPRICE
        CD_UNIT_CALCVALUE = CD_UNIT_CALCVALUE.

    CD_UNIT_UNITPRICE = 'Unit Price Test'.
    CD_UNIT_CALCVALUE = 'Calculation Factor Test'.

  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM009 ----
  METHOD IF_EX_RECD_CALC_RULE~GET_PARAMETER.

    CHECK ID_CALCRULEEXT = 'U'.


** call method of rule
    CALL METHOD MO_RULE->GET_PARAMETER
      EXPORTING
        "ID_CALCRULEEXT = ID_CALCRULEEXT
        ID_PARA_NO     = ID_PARA_NO
        IO_OBJECT      = IO_OBJECT
        IS_CONDITION   = IS_CONDITION
      CHANGING
        CT_PARA_VALUES = CT_PARA_VALUES
        CD_PARA_INFO   = CD_PARA_INFO
        CF_PARA_CHECK  = CF_PARA_CHECK.

  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM00A ----
  METHOD IF_EX_RECD_CALC_RULE~GET_ATTRIBUTES.

* Only for calculation rule type 'U':
    CHECK ID_CALCRULEEXT = 'U'.
*    IF id_calcruleext <> 'U'.
*      RETURN.
*    ENDIF.
* local data
    DATA :
      LO_RULE TYPE REF TO CL_RECD_CALC_RULE_12.

* create rule
    CREATE OBJECT LO_RULE.

** call method of rule
*   CALL METHOD mo_rule->get_attributes
    CALL METHOD LO_RULE->GET_ATTRIBUTES
*    EXPORTING
*      ID_CALCRULEEXT = ID_CALCRULEEXT
      CHANGING
        CF_DISTRIBUTE        = CF_DISTRIBUTE
        CF_ADJUSTABLE        = CF_ADJUSTABLE
        CF_UNITPRICE_HIDE    = CF_UNITPRICE_HIDE
        CF_DEPEND_CONDITION  = CF_DEPEND_CONDITION
        CF_DEPEND_OBJECT     = CF_DEPEND_OBJECT
        CD_INFO_IDENT        = CD_INFO_IDENT
        CD_GUI_FM_PARA_PBO   = CD_GUI_FM_PARA_PBO
        CD_GUI_FM_PARA_PAI   = CD_GUI_FM_PARA_PAI
        CF_CERULE_ABSOLUTE   = CF_CERULE_ABSOLUTE
        CF_CERULE_PERCENTAGE = CF_CERULE_PERCENTAGE.

    CD_INFO_IDENT          = 'UN_Rental calculation'.
    CF_DEPEND_CONDITION = ABAP_TRUE.

*    cf_distribute          = abap_true.
*    cf_adjustable          = abap_true.
*    cf_unitprice_hide      = abap_true.
*    cf_depend_condition    = abap_false.
*    cf_depend_object       = abap_true.
*    cf_unique_values       = abap_false.
*    cf_unique_values_multi = abap_false.
*    cf_use_buffer          = abap_false.

  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM00B ----
  METHOD GET_CONTRACT_TOTALS.
    DATA: LT_MEASUREMENT   TYPE BAPI_RE_T_MEAS_CN_INT,
          LT_ROMEASUREMENT TYPE BAPI_RE_T_MEASUREMENT_INT.
*    DATA(lo_helper) = zrefx_tariff_helper=>get_instance( ).

    LOOP AT IT_OBJECT_CONTRACT INTO DATA(LO_OBJECT_CONTRACT).

      CALL FUNCTION 'API_RE_RO_GET_DETAIL'
        EXPORTING
          ID_OBJNR       = LO_OBJECT_CONTRACT-OBJNR
*         id_objnr       = is_condition-objnr
        IMPORTING
          ET_MEASUREMENT = LT_ROMEASUREMENT
        EXCEPTIONS
          ERROR          = 1
          OTHERS         = 2.

      CHECK SY-SUBRC = 0.


      " 30052025🔸 Get the formula dynamically for this object
      DATA(LV_CALCRULE) = ME->GET_FORMULA_FOR_OBJECT(
                             IS_CONTRACT = LO_CONTRACT
                             IS_OBJECT   = LO_OBJECT_CONTRACT-OBJNR ).

      "Get Total Offices size and calculate average office size.

      LOOP AT  LT_ROMEASUREMENT INTO DATA(LO_ROMEASUREMENT)
        WHERE MEASUNIT ='M2'.
*            IF is_condition-CALCRULE = 'U'.
        IF  LV_CALCRULE = 'U'.
          V_OFFICES = V_OFFICES + 1.
          V_OFFICSIZETOT = V_OFFICSIZETOT + LO_ROMEASUREMENT-MEASVALUE. "Total office size
          V_AVGOFFSIZE = V_OFFICSIZETOT / V_OFFICES.
        ENDIF.
      ENDLOOP.
    ENDLOOP.
*    DATA(lv_total_m2)     = lo_helper->get_total_m2( ).

  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CM00C ----
  METHOD SET_CONDITIONS.

    DATA LO_CONTRACT TYPE REF TO CL_RECN_CONTRACT.
    DATA: P_DEC TYPE P DECIMALS 5.
    DATA LV_VALUE0 TYPE P DECIMALS 0.
    DATA LV_VALUE TYPE P DECIMALS 2.
*    DATA v_provecons TYPE recdunitprice.
*    DATA v_monthprov    TYPE recdunitprice.
    DATA: LV_DATE_FROM TYPE D,
          LV_DATE_TO   TYPE D.

    " Build the first day of the year (01.01.<year>)
    CONCATENATE LV_YEAR '0101' INTO LV_DATE_FROM.
    " Build the last day of the year (31.12.<year>)
    CONCATENATE LV_YEAR '1231' INTO LV_DATE_TO.


**Analize each condition
    LOOP AT LT_COND INTO DATA(LO_COND).
      DATA(LV_CONDGUID) = LO_COND->GET_CONDGUID( ).
      IF LV_CONDGUID = IS_CONDITION-CONDGUID.
        IF LS_DET-RECNTYPE = 'OFFI'. " If contract type is Office
          IF IS_CONDITION-CONDTYPE = 'MOE' " CONDITION TYPE RENT OFFICE
             AND IS_CONDITION-CONDVALIDFROM >= LV_DATE_FROM
             AND IS_CONDITION-CONDVALIDTO <= LV_DATE_TO.
            """
            " For Rounding we need to Adjust values using the last office
            " IN THE LAST OFFICE COMPARE THE DIFFERENCE AND ASSAIGN TO THE LAST ITEM
            " MV_Count contains the total number of offices and is reduced in each loop.
            """
            IF MV_COUNT = 0 OR LO_COND->MD_NUMBER = '0001'. " We set the value in the first loop
              MV_COUNT = V_OFFICES.
              MV_TOTAL =  V_MONTHREN.
              P_DEC = MV_TOTAL.

              CALL FUNCTION 'ROUND' " ROUNDING TOTAL RENT
                EXPORTING
                  DECIMALS      = 0
                  INPUT         = P_DEC
*                 SIGN          = ' '
                IMPORTING
                  OUTPUT        = LV_VALUE0
                EXCEPTIONS
                  INPUT_INVALID = 1
                  OVERFLOW      = 2
                  TYPE_INVALID  = 3
                  OTHERS        = 4.
              MV_TOTAL = LV_VALUE0.
            ENDIF.
            P_DEC = V_UNITPRICE.

            CALL FUNCTION 'ROUND' " ROUNDING MONTLY RENT
              EXPORTING
                DECIMALS      = 0
                INPUT         = P_DEC
*               SIGN          = ' '
              IMPORTING
                OUTPUT        = LV_VALUE0
              EXCEPTIONS
                INPUT_INVALID = 1
                OVERFLOW      = 2
                TYPE_INVALID  = 3
                OTHERS        = 4.

            V_UNITPRICE = LV_VALUE0.
            MV_COUNT = MV_COUNT - 1.           " Reduce the Office counter to get the last office.
            MV_TOTAL = MV_TOTAL - V_UNITPRICE.

            IF MV_COUNT = 0.
              V_UNITPRICE = V_UNITPRICE + MV_TOTAL.
            ENDIF.

**** Condition Posted.
            " If condition was posted we should not update
            IF ME->WAS_CONDITION_POSTED(
                        I_CONDITION =  LO_COND
                       )
                        = ABAP_FALSE.
              LO_COND->SET_UNITPRICE( ID_UNITPRICE = V_UNITPRICE ).
            ENDIF.

          ELSEIF IS_CONDITION-CONDTYPE = 'PROV' " IF CONDITION IS PROVISION
             AND IS_CONDITION-CONDVALIDFROM >= LV_DATE_FROM
             AND IS_CONDITION-CONDVALIDTO <= LV_DATE_TO.

            P_DEC = V_PROVECONS.
            CALL FUNCTION 'ROUND'
              EXPORTING
                DECIMALS      = 2
                INPUT         = P_DEC
                SIGN          = ' '
              IMPORTING
                OUTPUT        = LV_VALUE
              EXCEPTIONS
                INPUT_INVALID = 1
                OVERFLOW      = 2
                TYPE_INVALID  = 3
                OTHERS        = 4.
            V_PROVECONS = LV_VALUE.

            IF MV_PROVCOUNT = 0.             " Last Line Control Offices provision same logic as total offics
              MV_PROVCOUNT = V_OFFICES.
              MV_PROVTOTAL =  V_MONTHPROV.

              P_DEC = MV_PROVTOTAL.
              CALL FUNCTION 'ROUND'
                EXPORTING
                  DECIMALS      = 2
                  INPUT         = P_DEC
                  SIGN          = ' '
                IMPORTING
                  OUTPUT        = LV_VALUE "variable define the decimal place lv_value has 2  lv_value0 has 0
                EXCEPTIONS
                  INPUT_INVALID = 1
                  OVERFLOW      = 2
                  TYPE_INVALID  = 3
                  OTHERS        = 4.
              MV_PROVTOTAL = LV_VALUE.
            ENDIF.
            MV_PROVTOTAL = MV_PROVTOTAL - V_PROVECONS.
            MV_PROVCOUNT = MV_PROVCOUNT - 1.

            IF MV_PROVCOUNT = 0. " Last Line here we adjust the difference
              V_PROVECONS = V_PROVECONS + MV_PROVTOTAL.

            ENDIF.

**** Control Condition posted IF condition was posted is not required to UPDATE
                        IF ME->WAS_CONDITION_POSTED(
                                    I_CONDITION =  LO_COND
                                   )
                                    = ABAP_FALSE.
            LO_COND->SET_UNITPRICE( ID_UNITPRICE = V_PROVECONS ).
          ENDIF.

"            "****11122025 REMOVED ADDED
"          ELSEIF is_condition-condtype = 'PROV'.
"            p_dec = v_provecons.

"            " 1. Redondeo del valor mensual a 2 decimales (v_provecons)
"            CALL FUNCTION 'ROUND'
"              EXPORTING
"                decimals      = 2
"                input         = p_dec
"              IMPORTING
"                output        = lv_value
"              EXCEPTIONS
"                input_invalid = 1
"                overflow      = 2
"                type_invalid  = 3
"                OTHERS        = 4.
"            v_provecons = lv_value. " V_PROVECONS: Monthly Value Rounded

"            "... --- INSERTION: Calculation of the ANNUAL Contribution for this Line --
"            lv_annual_contribution = v_provecons * 12.
"            " -----------------------------------------------------------------

"            IF mv_provcount = 0.
"              "Initialization: It is only executed the first time."
"              mv_provcount = v_offices.
"              mv_provtotal = v_monthprov. " v_monthprov: "Unrounded ANNUAL Total."

"              "Round the ANNUAL total to the desired level (e.g., 0 decimals)"
"              p_dec = mv_provtotal.
"              CALL FUNCTION 'ROUND'
"                EXPORTING
"                  decimals      = 0
"                  input         = p_dec
"                IMPORTING
"                  output        = lv_value0
"                EXCEPTIONS
"                  input_invalid = 1
"                  overflow      = 2
"                  type_invalid  = 3
"                  OTHERS        = 4.
"              mv_provtotal = lv_value0. " MV_PROVTOTAL:Total annual target
"            ENDIF.

"            "... --- KEY MODIFICATION 1: Subtract contribution A"
"            mv_provtotal = mv_provtotal - lv_annual_contribution.
"            mv_provcount = mv_provcount - 1.

"            IF mv_provcount = 0.
"              "... --- KEY MODIFICATION 2: Apply the MONTHLY adjustment ---"
"              "1. Calculate the MONTHLY adjustment (divide the ANNUAL difference by 12)"
"              lv_adjustment_monthly = mv_provtotal / 12.

"              "2. Apply the MONTHLY adjustment to the MONTHLY value of the Line (y_provecons)."
"              v_provecons = v_provecons + lv_adjustment_monthly.
"            ENDIF.

"            "****11122025 REMOVED ADDED


        ENDIF.

        ELSEIF LS_DET-RECNTYPE = 'PARK'. "Parking contract

          IF IS_CONDITION-CONDTYPE = 'PROV'.
            LO_COND->SET_UNITPRICE( ID_UNITPRICE = '0' ).
          ELSEIF IS_CONDITION-CONDTYPE = 'AUTM'  " Car
              OR IS_CONDITION-CONDTYPE = 'MOTM'. " Moto
****Control Condition Posted
            IF ME->WAS_CONDITION_POSTED(
                        I_CONDITION =  LO_COND
                       )
                        = ABAP_FALSE.

              LO_COND->SET_UNITPRICE( ID_UNITPRICE = V_UNITPRICE ).
            ENDIF.
          ENDIF.

          IF MV_COUNT = 99.
            "BADI_RE_CN_CN
            MESSAGE 'Formula UN_Rental only for Office rental contract!'(001)
              TYPE 'W'.
          ELSE.
            MV_COUNT = 0.
          ENDIF.
        ENDIF.
      ENDIF.
    ENDLOOP.
  ENDMETHOD.

* ---- YCL_RE_BADI_RE_CD_CD_V2=======CO ----
  PROTECTED SECTION.

    DATA MT_LIST TYPE RE_T_REBD_MEAS .
    DATA MT_LIST_LAST_OK TYPE RE_T_REBD_MEAS .
    DATA MF_INVALID_MODE TYPE ABAP_BOOL .



* ---- YCL_RE_BADI_RE_CD_CD_V2=======CU ----
CLASS YCL_RE_BADI_RE_CD_CD_V2 DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

  PUBLIC SECTION.

    INTERFACES IF_BADI_INTERFACE .
    INTERFACES IF_EX_RECD_CALC_RULE .

    METHODS CONSTRUCTOR .