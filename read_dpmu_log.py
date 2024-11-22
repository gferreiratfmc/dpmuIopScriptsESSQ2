import struct
import sys

NUMBER_OF_CELLS = 30
MAGIC_NUMBER = 0xDEADFACE

class DebugLog:
    def __init__(self, data):
        unpacked_data = struct.unpack('<I18hH30hhHIH', data)
        self.MagicNumber = unpacked_data[0]
        self.ISen1 = unpacked_data[1]
        self.ISen2 = unpacked_data[2]
        self.IF_1 = unpacked_data[3]
        self.I_Dab2 = unpacked_data[4]
        self.I_Dab3 = unpacked_data[5]
        self.Vbus = unpacked_data[6]
        self.VStore = unpacked_data[7]
        self.AvgVbus = unpacked_data[8]
        self.AvgVStore = unpacked_data[9]
        self.BaseBoardTemperature = unpacked_data[10]
        self.MainBoardTemperature = unpacked_data[11]
        self.MezzanineBoardTemperature = unpacked_data[12]
        self.PowerBankBoardTemperature = unpacked_data[13]
        self.RegulateAvgInputCurrent = unpacked_data[14]
        self.RegulateAvgOutputCurrent = unpacked_data[15]
        self.RegulateAvgVStore = unpacked_data[16]
        self.RegulateAvgVbus = unpacked_data[17]
        self.RegulateIRef = unpacked_data[18]
        self.ILoop_PiOutput = unpacked_data[19]
        self.cellVoltage = unpacked_data[20:50]
        self.CurrentState = unpacked_data[50]
        self.counter = unpacked_data[51]
        self.CurrentTime = unpacked_data[52]
        self.elapsed_time = unpacked_data[53]

def create_csv_line(dblog, first_time_read):
    csv_line = f"{dblog.CurrentTime:08}\t{(dblog.CurrentTime - first_time_read) / 10.0:.2f}\t{dblog.Vbus / 10:.2f}\t{dblog.AvgVbus / 10:.2f}\t{dblog.VStore / 10:.2f}\t{dblog.AvgVStore / 10:.2f}\t{dblog.IF_1 / 10:.2f}\t{dblog.ISen1 / 10:.2f}\t{dblog.ISen2 / 10:.2f}\t{dblog.ILoop_PiOutput / 100:.2f}\t{dblog.I_Dab2 / 100:.2f}\t{dblog.I_Dab3 / 100:.2f}\t{dblog.RegulateAvgVStore / 10:.2f}\t{dblog.RegulateAvgVbus / 10:.2f}\t{dblog.RegulateAvgInputCurrent / 10:.2f}\t{dblog.RegulateAvgOutputCurrent / 10:.2f}\t{dblog.RegulateIRef / 100:.2f}\t{dblog.BaseBoardTemperature:02}\t{dblog.MainBoardTemperature:02}\t{dblog.MezzanineBoardTemperature:02}\t{dblog.PowerBankBoardTemperature:02}\t{dblog.counter:05}\t{dblog.CurrentState:02}\t{dblog.elapsed_time:08}"
    for voltage in dblog.cellVoltage:
        csv_line += f"\t{voltage / 100:.2f}"
    csv_line += "\n"
    return csv_line

def convertHexToCSV(fileName):

    csv_file_name = fileName
    try:
        file_csv = open(csv_file_name, "w+")
    except IOError:
        print(f"Error opening file {csv_file_name}")
        return -2

    print(f"Output file csv: {csv_file_name}")

    try:
        file = open(sys.argv[1], "rb")
    except IOError:
        print(f"Error opening file {sys.argv[1]}")
        return -2

    csv_header = "DPMUTime\tTime\tVBus\tAvgVbus\tVStore\tAvgVStore\tInputCurrent\tOutputCurrent\tSupercapCurrent\tILoopPiOutput\tLLC1_Current\tLLC2_Current\tRegAvgVStore\tRegAvgVbus\tRegAvgInputCurrent\tRegAvgOutputCurrent\tRegIref\tTBase\tTMain\tTMezz\tTPWRBank\tCounter\tCurrentState\tElapsed_time"
    for i in range(NUMBER_OF_CELLS):
        csv_header += f"\tCEL_{i:02d}"
    csv_header += "\n"
    file_csv.write(csv_header)

    count = 0
    end_of_file_reached = False
    first_time_read = -1
    magic_number_count = 0

    while not end_of_file_reached:
        sizeOfStruct = struct.calcsize('<I18hH30hhHIH')
        data = file.read(sizeOfStruct)
        if len(data) < struct.calcsize('<I18hH30hhHIH'):
            end_of_file_reached = True
            break

        dblog = DebugLog(data)
        if dblog.MagicNumber != MAGIC_NUMBER:
            continue
        else:
            magic_number_count = magic_number_count + 1

        if first_time_read == -1:
            first_time_read = dblog.CurrentTime

        csv_line = create_csv_line(dblog, first_time_read)
        file_csv.write(csv_line)
        count += 1

    print(f"Number of lines: {count} - Magic Number Count: {magic_number_count}")
    file.close()
    file_csv.close()

if __name__ == "__main__":
    main()

#This Python code replicates the functionality of the provided C code, including reading binary data, processing it, and writing it to a CSV file. 
#Adjustments were made to handle file operations and data unpacking in Python.
