private section.

  data MV_BUKRS type BUKRS .
  data MV_FIKRS type FIKRS .
  data MV_START_DATE type BEGDA .
  class-data MO_INSTANCE type ref to YCL_FM_BR_EXCHANGE_RATE_BL .
  data:
    mr_rldnr TYPE RANGE OF rldnr .
  data:
    mr_fikrs TYPE RANGE OF fikrs .
  data:
    mr_gsber TYPE RANGE OF gsber .
  data:
    mr_waers TYPE RANGE OF waers .
  data:
    mr_fipex TYPE RANGE OF fm_fipex .
  data:
    mr_vrgng TYPE RANGE OF co_vorgang .
  data:
    mr_bukrs TYPE RANGE OF bukrs .
  data:
    mr_fund_type TYPE RANGE OF fm_fundtype .
  data:
*Staff
    mr_vrgng2 TYPE RANGE OF co_vorgang .
  data:
    mr_waers2 TYPE RANGE OF waers .
  data:
    mr_hkont TYPE RANGE OF hkont .
  data:
*Revaluation
    mr_fund_type3 TYPE RANGE OF fm_fundtype .
  data:
    mr_fipex3 TYPE RANGE OF fm_fipex .
  data:
    mr_vrgng3 TYPE RANGE OF co_vorgang .