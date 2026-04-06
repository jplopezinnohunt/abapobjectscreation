FUNCTION z_wf_fi_bseg_event_paym_method.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(CHANGEDOCUMENT_HEADER) TYPE  CDHDR OPTIONAL
*"     VALUE(OBJECT_POR) TYPE  SIBFLPORB OPTIONAL
*"     VALUE(EVENT) TYPE  SWECDEXIT-EVENT OPTIONAL
*"     VALUE(EVENT_CONTAINER) TYPE
*"EF TO IF_SWF_IFS_PARAMETER_CONTAINER OPTIONAL
*"  TABLES
*"      CHANGEDOCUMENT_POSITION STRUCTURE  CDPOS OPTIONAL
*"--------------------------------------------------------------------
* This is the template-FB to fill the event-container before raising
* the event from a change-document.
* This Template does replace the previous Interface of
* SWE_CD_TEMPLATE_CONTAINER_FB to be able to handle BOR-References as
* well as References of Business-classes
* Use the interface of this template to implement the exit.
  SKIP.
ENDFUNCTION.