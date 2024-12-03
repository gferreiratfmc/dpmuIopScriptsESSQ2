
import sys

def ReadCmdLineSequence(arglist):

    return arglist[2:]


if __name__ == "__main__":
    listOfStates = ReadCmdLineSequence(sys.argv)
    if( len(listOfStates)<1):
        print("No list of arguments.")
    else:
        print(f"states {listOfStates}")