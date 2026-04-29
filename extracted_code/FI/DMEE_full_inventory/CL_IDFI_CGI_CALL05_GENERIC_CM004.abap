METHOD country_specific_call.
* This method is used to return Country-Specific changes to Reference
* fields in structure FPAYHX and table FPAYP for DMEE(x) transaction in
* function module FI_PAYMEDIUM_DMEE_CGI_05.

* It is not allowed to change values set in Generic Call of this class,
* all such changes will be ignored and warinig message will be stored
* in F110/FBPM transaction

* To create Country-Specific version, find ISO Country Key not used and
* in SE24 display class CL_IDFI_CGI_CALL05_GENERIC, click on menu
* Edit -> Create Subclass or press [Shift+F1] and use your ISO code to
* create new class e.g. CL_IDFI_CGI_CALL05_DE.

* In your class redefine method COUNTRY_SPECIFIC_CALL by pressing
* button in menu near Filter checkbox

ENDMETHOD.