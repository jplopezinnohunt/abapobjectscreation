"""Read Y_FMKU_0050_CREATE_WITH_COMMIT interface (read-only) from P01 via RFC."""
import os
from dotenv import load_dotenv
from pyrfc import Connection
load_dotenv()
cp={'ashost':os.getenv('SAP_P01_ASHOST'),'sysnr':os.getenv('SAP_P01_SYSNR'),
    'client':os.getenv('SAP_P01_CLIENT'),'user':os.getenv('SAP_P01_USER'),'lang':'EN',
    'snc_mode':'1','snc_partnername':os.getenv('SAP_P01_SNC_PARTNERNAME'),'snc_qop':'9'}
conn=Connection(**cp)
FM='Y_FMKU_0050_CREATE_WITH_COMMIT'
def rt(tab,opts,fields,n=400):
    r=conn.call('RFC_READ_TABLE',QUERY_TABLE=tab,DELIMITER='|',ROWCOUNT=n,
        OPTIONS=[{'TEXT':opts}],FIELDS=[{'FIELDNAME':f} for f in fields])
    return [row['WA'] for row in r['DATA']]
print("== TFDIR ==");      [print(' ',x) for x in rt('TFDIR',"FUNCNAME = '%s'"%FM,['FUNCNAME','PNAME','FMODE'])]
print("== ENLFDIR (func group) =="); [print(' ',x) for x in rt('ENLFDIR',"FUNCNAME = '%s'"%FM,['FUNCNAME','AREA'])]
print("== FUPARAREF (interface params) ==")
for x in rt('FUPARAREF',"FUNCNAME = '%s'"%FM,['PARAMETER','PARAMTYPE','TYP','STRUCTURE','KIND','PASSVALUE','OPTIONAL','DEFAULTVAL']):
    print(' ',x)
