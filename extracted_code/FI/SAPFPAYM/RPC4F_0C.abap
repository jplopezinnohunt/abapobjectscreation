***INCLUDE RPC4F_0C.
* constants definitions for cluster F* - Pay statement, ...
* 4.0A (ALR)
* VKIK059242 22.07.1997 now using structures from DDIC (direct way).

CONSTANTS:
  BEGIN OF F__LTYPE,                    "type of line
    CMD        LIKE PC408-LTYPE   VALUE '/:',    "command
    TXT        LIKE PC408-LTYPE   VALUE '  ',    "textline
  END OF F__LTYPE.

CONSTANTS:
  BEGIN OF F__CMD,                      "commands
    NEWPAGE   LIKE PC408-LINDA    VALUE '<NEW-PAGE>',
  END OF F__CMD.