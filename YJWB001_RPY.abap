************************************************************************
*                             INCLUDE YJWB001                          *
************************************************************************
* --> YUSR00, YUSR01, YUSR02, YUSR03, YUSR04                           *
*                                                                      *
************************************************************************
*                                                                      *
*                                                                      *
************************************************************************
* Declaration of tables used in matchcodes.
TABLES: YUSR00, "ID for user fields USR00PRPS (Region/inteR/G)
        YUSR01, "ID for user fields USR01PRPS (Subreg/country)
        YUSR02, "ID for user fields USR02PRPS (Sector)
        YUSR03, "ID for user fields USR03PRPS (Division/FO)
        YUSR04. "ID for user fields USR04PRPS (Code CCAQ)




* Region/inteR/G is initial
IF SAP_PRPS-USR00 IS INITIAL.
ELSE.
* Select values of region/inteR/G
  SELECT SINGLE * FROM  YUSR00
         WHERE  USR00  = SAP_PRPS-USR00.
* Check value entered is contained in the list of values region/InterR/G
  IF SY-SUBRC NE 0.
    MESSAGE E398(00) WITH TEXT-001.
    EXIT.
  ENDIF.
ENDIF.

* Subreg/country is initial
IF SAP_PRPS-USR01 IS INITIAL.
ELSE.
* Select values of Subreg/country
  SELECT SINGLE * FROM  YUSR01
         WHERE  USR01  = SAP_PRPS-USR01.
* Check value entered is contained in the list of values Subreg/country
  IF  SY-SUBRC NE 0.
    MESSAGE E398(00) WITH TEXT-001.
    EXIT.
  ENDIF.
ENDIF.

* Sector is initial
IF SAP_PRPS-USR02 IS INITIAL.
ELSE.
* Select values of Sector
  SELECT SINGLE * FROM  YUSR02
         WHERE  USR02  = SAP_PRPS-USR02.
* Check value entered is contained in the list of values Sector
  IF  SY-SUBRC NE 0.
    MESSAGE E398(00) WITH TEXT-001.
    EXIT.
  ENDIF.
ENDIF.

* Division/FO is initial
IF SAP_PRPS-USR03 IS INITIAL.
ELSE.
* Select values of Division/FO
  SELECT SINGLE * FROM  YUSR03
         WHERE  USR03  = SAP_PRPS-USR03.
* Check value entered is contained in the list of values Division/FO
  IF  SY-SUBRC NE 0.
    MESSAGE E398(00) WITH TEXT-001.
    EXIT.
  ENDIF.
ENDIF.

* Code CCAQ is initial
IF SAP_PRPS-USR04 IS INITIAL.
ELSE.
* Select values of Code CCAQ
  SELECT SINGLE * FROM  YUSR04
         WHERE  USR04  = SAP_PRPS-USR04.
* Check value entered is contained in the list of values Code CCAQ
  IF  SY-SUBRC NE 0.
    MESSAGE E398(00) WITH TEXT-001.
    EXIT.
  ENDIF.
ENDIF.

IF SAP_PRPS-USE04 IS INITIAL.
  SAP_USR-USE04 = 'ST'.
ENDIF.

IF SAP_PRPS-USE05 IS INITIAL.
  SAP_USR-USE05 = 'ST'.
ENDIF.

IF SAP_PRPS-USE06 IS INITIAL.
  SAP_USR-USE06 = 'USD'.
ENDIF.