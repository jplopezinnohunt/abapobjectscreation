class YCL_FM_BR_EXCHANGE_RATE_BL definition
  public
  final
  create public .

public section.

  types:
    BEGIN OF ty_avc_fund,
             gjahr TYPE gjahr,
             fikrs TYPE fikrs,
             fonds TYPE bp_geber,
           END OF ty_avc_fund .

  data:
    mt_avc_fund TYPE SORTED TABLE OF ty_avc_fund WITH UNIQUE KEY gjahr fikrs fonds .

  methods CHECK_BR_IS_ACTIVE
    returning
      value(RV_IS_OK) type XFELD .
  methods GET_BR_IMPACT
    importing
      !IV_BUKRS type BUKRS
      !IV_GJAHR type GJAHR
      !IV_FKBTRP type FM_FKBTRPY
      !IV_TRBTRP type FM_TRBTRPY
      !IV_TWAER type TWAER
      !IV_WRTTP type CO_WRTTP
      !IV_VRGNG type CO_VORGANG
      !IV_BTART type FM_BTART
      !IV_BUDAT type BUDAT
      !IV_KURSF type KURSF optional
      !IV_BSEG_BELNR type BELNR_D optional
      !IV_BSEG_GJAHR type GJAHR optional
      !IV_BSEG_BUZEI type BUZEI optional
      !IV_BSEG_DMBTR type DMBTR optional
      !IV_BSEG_SHKZG type SHKZG optional
      !IV_REFBN type CO_REFBN optional
      !IV_RFPOS type CC_RFPOS optional
      !IV_FINCODE type BP_GEBER
    exporting
      !EV_ZZBRIMPACTED type ZE_BRAFFECTED
      !EV_ZZAMOUNTBRLC type ZE_AMOUNTBR_LC
      !EV_ZZAMOUNTBRDIFF type ZE_AMOUNTBR_DIFF .
  methods GET_FM_AREA_FROM_COMPANY_CODE
    importing
      !IV_BUKRS type BUKRS
    returning
      value(RV_FIKRS) type FIKRS .
  methods GET_FUND_TYPE_FROM_FUND
    importing
      !IV_FIKRS type FIKRS
      !IV_FINCODE type BP_GEBER
    returning
      value(RV_FTYPE) type FM_FUNDTYPE .
  methods CHECK_CONDITIONS
    importing
      !IV_RLDNR type RLDNR optional
      !IV_BUKRS type BUKRS optional
      !IV_FIKRS type FIKRS optional
      !IV_GSBER type GSBER optional
      !IV_WAERS type WAERS optional
      !IV_FIPEX type FM_FIPEX optional
      !IV_VRGNG type CO_VORGANG optional
      !IV_FTYPE type FM_FUNDTYPE optional
    returning
      value(RV_IS_OK) type XFELD .
  methods CHECK_CONDITIONS_2
    importing
      !IV_RLDNR type RLDNR optional
      !IV_BUKRS type BUKRS optional
      !IV_FIKRS type FIKRS optional
      !IV_GSBER type GSBER optional
      !IV_WAERS type WAERS optional
      !IV_FIPEX type FM_FIPEX optional
      !IV_VRGNG type CO_VORGANG optional
      !IV_FTYPE type FM_FUNDTYPE optional
      !IV_HKONT type HKONT optional
    returning
      value(RV_IS_OK) type XFELD .
  methods CONVERT_TO_CURRENCY
    importing
      !IV_DATE type DATUM
      !IV_TYPE_OF_RATE type KURST_CURR default 'EURX'
      !IV_FOREIGN_AMOUNT type ANY
      !IV_FOREIGN_CURRENCY type WAERS
      !IV_LOCAL_CURRENCY type WAERS
    exporting
      !EV_LOCAL_AMOUNT type ANY
      !EV_SUBRC type SY-SUBRC .
  methods CONVERT_TO_CURRENCY_2
    importing
      !IV_DATE type DATUM
      !IV_TYPE_OF_RATE type KURST_CURR default 'EURX'
      !IV_FOREIGN_AMOUNT type ANY
      !IV_FOREIGN_CURRENCY type WAERS
      !IV_LOCAL_CURRENCY type WAERS
      !IV_TYPE_OF_RATE_UNORE type KURST_CURR default 'M'
    exporting
      !EV_LOCAL_AMOUNT type ANY
      !EV_SUBRC type SY-SUBRC .
  methods FMAVC_REINIT_ON_EVENT
    for event TRANSACTION_FINISHED of CL_SYSTEM_TRANSACTION_STATE
    importing
      !KIND .
  methods GET_EXCHANGE_RATE
    importing
      !IV_DATE type DATUM
      !IV_FOREIGN_CURRENCY type WAERS
      !IV_LOCAL_CURRENCY type WAERS
    exporting
      !EV_EXCHANGE_RATE type ANY
      !EV_SUBRC type SY-SUBRC .
  methods CONSTRUCTOR .
  class-methods GET_INSTANCE
    returning
      value(RO_INSTANCE) type ref to YCL_FM_BR_EXCHANGE_RATE_BL .
  methods CHECK_CONDITIONS_3
    importing
      !IV_RLDNR type RLDNR optional
      !IV_BUKRS type BUKRS optional
      !IV_FIKRS type FIKRS optional
      !IV_GSBER type GSBER optional
      !IV_WAERS type WAERS optional
      !IV_FIPEX type FM_FIPEX optional
      !IV_VRGNG type CO_VORGANG optional
      !IV_FTYPE type FM_FUNDTYPE optional
      !IV_HKONT type HKONT optional
    returning
      value(RV_IS_OK) type XFELD .