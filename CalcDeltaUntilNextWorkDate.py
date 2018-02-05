import sys
import os
import datetime
import subprocess as subp

def commandExecuter(commandToExecute):
    try:
        ctmpsmOutput = subp.Popen(commandToExecute, stdout=subp.PIPE, shell=True)
        out, err = ctmpsmOutput.communicate()
        splittedLines = out.splitlines()
        return splittedLines
    except Exception as e:
        raise Exception("Error : Something went wrong with the command : \n" + str(commandToExecute) + "\n" +
                        str(e.args[0]) + "\nExiting with code 9 !", 9)

def calcDelta(firstDate, secondDate):
    if isinstance(firstDate, datetime.date) and isinstance(secondDate, datetime.date):
        datesDiff = abs(firstDate - secondDate)
        return(datesDiff.days)
    else:
        raise ValueError("one or more of the inputs isn't datetime format! exiting with code 2", 2)

def getNeededOrderID(jobName, dateOfOrderTosearch):
    ctmpsmCommand = ['ctmpsm', '-listall', '-sort', 'ORDERID']
    try:
        splittedLines = commandExecuter(ctmpsmCommand)
        splittedLines = splittedLines[4:-2]
        jobsTable = []
        isFound = False
        numOfFoundJobs = 0
        for line in splittedLines:
            try:
                line = line.decode('ascii').split()
            except:
                print("Warning: Something wrong with the line:\n{}".format(line))
                continue
            jobsTable.append(line)
            firstPart = line[0].split("|")
            if(jobName == firstPart[1]):
                thirdPart = line[2].split("|")
                orderDate = thirdPart[1]
                orderDate = datetime.datetime.strptime(orderDate, '%Y%m%d').date()
                if orderDate == dateOfOrderTosearch:
                    isFound = True
                    numOfFoundJobs += 1
                    print("Found the following line : " + str(line))
                    orderID = firstPart[0]
                else:
                    continue
        if not isFound:
            print("Something went wrong! no matching found...\nFollowing the ctmpsm table :\n")
            for line in jobsTable:
                print(line)
            raise Exception("Exiting with code 6!", 6)
        else:
            if numOfFoundJobs == 1:
                return(orderID)
            else:
                raise Exception("There are more than 1 job with the same name and from the current OrderID!!!\n"
                                "Exiting with code 10",10)
    except Exception as e:
        raise

def getNeededVarExpr(varName):
    ctmvarCommand = ['ctmvar', '-action', 'list']
    try:
        splittedLines = commandExecuter(ctmvarCommand)
        splittedLines = splittedLines[5:-3]
        varsTable = []
        isFound = False
        for line in splittedLines:
            try:
                line = line.decode('ascii').split()
            except:
                print("Warning: Something wrong with the line:\n{}".format(line))
                continue
            varsTable.append(line)
            if varName == line[0]:
                isFound = True
                print("Found the following line : " + str(line))
                neededVarExpr = line[1]
                pass

        if not isFound:
            print("Something went wrong! no matching found...\nFollowing the global variables table :\n")
            for line in varsTable:
                try:
                    print(line.decode('ascii'))
                except:
                    print("Warning: Something wrong with the line:\n{}".format(line))
                    continue
            raise Exception("Exiting with code 4!", 4)
        else:
            return(neededVarExpr)
    except Exception as e:
        raise

def updateJob(orderID, dictOfVarsAndExprs, inCondNames):
    ctmpsmUpdateCommand = ['ctmpsm', '-fullupdate', orderID]
    for key, value in dictOfVarsAndExprs.items():
        varName = key
        varExpr = value
        variableString =  ["-variable", key, value]
        ctmpsmUpdateCommand.extend(variableString)
    for condition in inCondNames:
        inCondString = ["-incond", condition, "ODAT", "AND"]
        ctmpsmUpdateCommand.extend(inCondString)
    splittedLines = commandExecuter(ctmpsmUpdateCommand)
    for line in splittedLines:
        try:
            line = line.decode('ascii')
            print(line)
        except:
            print("Warning: Something wrong with the line:\n{}".format(line))
            continue

if __name__ == "__main__":
    bimJobName = os.environ['BimJobName']
    inCondNames = os.environ['InCondNames'].split(",")
    nextWorkDateVarName = "%%NextWorkDate"
    #bimJobName = "BIM-Night-Run"
    bimJobOrderIdVariable =  "%%" + bimJobName + "OrderID"
    today = datetime.date.today()
    print("Today is :" + str(today))
    try:
        print("Going to search for existence of " + nextWorkDateVarName + " in ctmvar output...")
        nextWorkDate = getNeededVarExpr(nextWorkDateVarName)
        #nextWorkDate = "2017109"
        nextWorkDate = datetime.datetime.strptime(nextWorkDate, '%Y%m%d').date()
        print("Next WorkDate is : " + str(nextWorkDate))
        if nextWorkDate > today:
            dateDiff = calcDelta(today, nextWorkDate)
            print("Number of days until next working date is  : " + str(dateDiff))
            if dateDiff > 5:
                raise ValueError("Error : Dates diff cannot be more than 5! Exiting with code 5", 5)
        else:
            raise ValueError("Error : Next work date should be bigger then today's date! Exiting with code 3", 3)
        print("Going to search for the relevant Order ID of JobName : " + bimJobName)
        bimJobOrderId = getNeededOrderID(bimJobName, today)
        print("The OrderID of the BIM job " + bimJobName + " is : " + bimJobOrderId)
        print("Going to update job with Order ID " + bimJobOrderId)
        dueTimeString = "07:05," + str(dateDiff)
        dictOfVarsAndValues = {
            "%%BIM-SENSITIVITY" :  "3sigma",
            "%%BIM-SERVICE_NAME" : bimJobName,
            "%%BIM-SERVICE_PRIORITY" : "3",
            "%%BIM-DUE_TIME" : dueTimeString
        }
        updateJob(bimJobOrderId, dictOfVarsAndValues, inCondNames)
    except Exception as e:
        exception = e.args[0]
        print(exception)
        if len(e.args) > 1 :
            exitCode = e.args[1]
            exit(exitCode)
        else:
            raise
