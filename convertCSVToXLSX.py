import pandas as pd
import subprocess
import glob
import os


DPMULogRreader = r"C:\Users\gferreira\source\repos\DPMULogReader\x64\Release\DPMULogReader.exe"
DPMULogDir = r"C:\DPMU_LOG"
DPMUCsvDir = f"{DPMULogDir}\\csv"
DPMUXlsDir = f"{DPMULogDir}\\xls"

DPMULogHexFileList = glob.glob(f"C:\\DPMU_LOG\\*.hex")

l=len(DPMULogHexFileList)
print(f"Number of files {l}" )

for DPMULogHexFile in DPMULogHexFileList:
    DPMULogFileBaseName = os.path.basename(DPMULogHexFile)
    DPMULogFileBaseName = DPMULogFileBaseName.split('.')[0]
    print(f"********* Basename {DPMULogFileBaseName}")
    DPMULogCsvFile=f"{DPMUCsvDir}\\{DPMULogFileBaseName}.csv"
    print(f"Converting .hex to .csv cmd:{DPMULogRreader} {DPMULogHexFile}")

    # Custom executable program to convert DPMULogHex in CSV
    subprocess.check_call([DPMULogRreader, DPMULogHexFile])
    
    # Arrange csv file to change characters "." to ","
    with open(f"{DPMULogHexFile}.csv", "rt") as fin:
        with open(DPMULogCsvFile, "wt") as fout:
            for line in fin:
                fout.write(line.replace('.', ','))

    DPMULogXlsFile=f"{DPMUXlsDir}\\{DPMULogFileBaseName}.xlsx"
    read_file_product = pd.read_csv( DPMULogCsvFile, delimiter = '\t' )
    read_file_product.to_excel( DPMULogXlsFile, index = None, header=True )

    os.remove(f"{DPMULogHexFile}.csv")
    os.remove(DPMULogCsvFile)   
    try:
        os.system(f"start {DPMULogXlsFile}")
    except Exception as ex:
        print(f"Error {ex} trying to open excel file: {DPMULogXlsFile}")


#read_file_product = pd.read_csv (r'C:\DPMU_LOG\DPMU_CAN_LOG_DPMU_PROTO_FUNCTIONAL_SN000001_20241025_140842.hex.csv', delimiter = '\t')
#read_file_product.to_excel (r'C:\DPMU_LOG\xls\DPMU_CAN_LOG_DPMU_PROTO_FUNCTIONAL_SN000001_20241025_140842.xlsx', index = None, header=True)