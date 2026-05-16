************************************************************************
* Program ZSAPFPAYM_REPLAY                                              *
* Payment Medium Creation Tool — REPLAY MODE (no checks, ROLLBACK end)  *
*                                                                       *
* Source: copia controlada de SAPFPAYM con CHECKs removidos para        *
*         re-procesar runs F110 ya consolidados en DFPAYG sin alterar   *
*         REGUV.STATUS / DFPAYG.ANZ_ERL.                                *
*                                                                       *
* Target: re-generar el output DMEE de un run existente en D01,         *
*         escribir XML a path local o pantalla, debug en mapping.       *
*                                                                       *
* Origen extracted Sesión #072 (P01 RFC RPY_PROGRAM_READ).              *
* Wrapper construido manualmente (no inventado).                        *
************************************************************************

INCLUDE zfpaym_top.               "Global Data Declarations
INCLUDE zfpaym_ini.               "Initialization
INCLUDE zfpaym_sel.               "Selection Screen
INCLUDE zfpaym_sta.               "Start Of Selection (CHECKs removed)
INCLUDE zfpaym_get.               "Get Payment Data (FI_REF_DOC_CHECK removed + BREAK-POINT)
INCLUDE zfpaym_end.               "End Of Selection (+ ROLLBACK WORK)
INCLUDE zfpaym_lns.               "Line Selection
INCLUDE zfpaym_sub.               "Subroutines
