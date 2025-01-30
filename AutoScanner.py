import json
import math
import schedule
import datetime
import os
import sys
import time
from maincontrol import FILEROOT

import maincontrol as MAIN

import Config
import IBClient
import csv

SettingTime = None
AutoFile = "pod1"


def main():
    global AutoFile
    print("-------------------------------")
    print("### AUTO STARTED ###")
    if len(sys.argv) > 1:
        AutoFile = str(sys.argv[1])
    else:
        print("NO WORKING DIRECTORY SPECIFIED as argument")
        quit()

    print("### Using " + AutoFile + " parameters")
    print("-------------------------------")

    global ib, AlreadyFilled, root, LastRunStatus, GotHistoryList
    GotHistoryList = []
    LastRunStatus = ""
    AlreadyFilled = []

    CheckForUpdates()

    BuildSchedule(verbose=True)

    Menu()

    print("-------------------")
    print("Running....")

    LOOP_ACTIVE = True
    while LOOP_ACTIVE:
        time.sleep(5)
        schedule.run_pending()


def Menu():
    settings = ReadSettings(False)
    print("---")
    print("(Enter) : Run AUTO and wait\r")
    print("(1) : Run Auto Scanner Trade (Scheduled at: " + settings["TradeTime"] + ")\r")
    print("(2) : Calculate Correlations ZERO DEEP (Scheduled at: " + settings["PredictTime"] + ")\r")
    print("(3) : Calculate Correlations 100 DEEP \r")
    print("(4) : Run Search \r")

    print("(7) : Close Trades(Scheduled at: " + settings["CloseTime"] + ")\r")

    print("(m) : Show Menu and Read Settings\r")
    print("(x) : Quit()\r")

    x = input()

    if x == "1":
        AutoScanTrade()
        Menu()
    elif x == "2":
        AutoScanTrain(0)
        Menu()
    elif x == "3":
        AutoScanTrain(100)
        Menu()
    elif x =="4":
        AutoSearch()
        Menu()

    elif x == "7":
        AutoScanTrade(None, justClose=True)
        Menu()
    elif x == "m":
        ReadSettings(True)
        Menu()
    elif x == "x":
        quit()


def BuildSchedule(verbose=False):
    settings = ReadSettings(False)
    schedule.clear()
    schedule.every(1).minutes.do(CheckForUpdates)

    if int(settings["Continuous"]) == 0:
        if settings["TradeTime"] != "25:00":
            if verbose:
                print("Trading at: " + settings["TradeTime"])
            schedule.every().day.at(settings["TradeTime"]).do(AutoScanTrade)

        if settings["CloseTime"] != "25:00":
            if verbose:
                print("Closing Trades at: " + settings["CloseTime"])
            schedule.every().day.at(settings["CloseTime"]).do(AutoScanTrade, justClose=True)

    if settings["TrainTime"] != "25:00":
        if verbose:
            print("Training Scanner at: " + settings["TrainTime"])
        schedule.every().day.at(settings["TrainTime"]).do(AutoScanTrain, 0)


    if "Continuous" in settings.keys() and int(settings["Continuous"]) > 0 and datetime.datetime.now().weekday() < 5 and datetime.datetime.now().hour >= 7 and datetime.datetime.now().hour < 14:
        schedule.every().hour.at(":55").do(AutoScanTrade)

    if "Continuous" in settings.keys() and int(settings["Continuous"]) > 1 and datetime.datetime.now().weekday() < 5 and datetime.datetime.now().hour >= 8 and datetime.datetime.now().hour < 14:
        schedule.every().hour.at(":25").do(AutoScanTrade)


def CheckForUpdates():
    ReadSettings(False)
    Heartbeat()
    BuildSchedule()
    return None


def ReadSettings(force, filename=""):
    global AutoFile
    global SettingTime
    if filename:
        FILE = MAIN.FILEROOT + "/" + filename
    else:
        FILE = MAIN.FILEROOT + AutoFile + "/Auto.txt"

    if os.path.isfile(FILE) and os.access(FILE, os.R_OK):
        with open(FILE, "r") as myfile:
            data = myfile.read()
            settings = json.loads(data)

    if os.path.getmtime(FILE) != SettingTime or force:
        print("-------------------------------")
        print(FILE)

        if "PodNames" in settings.keys():
            print("Pod: " + str(settings["PodNames"]))
        print("ENABLED: " + str(bool(settings["Enabled"])))
        print("FAKE TRADING: " + str(bool(settings["FakeTrading"])))
        print("Close TRADES: " + str(bool(settings["CloseTrades"])))
        print("ONLY LONG: " + str(bool(settings["OnlyLong"])))
        print("STOP LOSS: " + str(bool(settings["StopLoss"])))
        print("ORDER SIZE: " + str(int(settings["OrderSize"])))
        print("Min Trade Score: " + str(float(settings["MinTradeScore"])))
        print("Max Trades " + str(float(settings["MaxTrades"])))
        print("Train Time: " + str(settings["TrainTime"]))

        print("-------------------------------")
        if settings["Continuous"] == 0:
             print("Trade Time: " + str(settings["TradeTime"]) + "  Close: " + str(settings["CloseTime"]))
        else:
            print("Continuous Trading Active: " + str(settings["Continuous"]) + "@:50, :55")

        print("-------------------------------")
        if "DEBUG" in settings.keys() and bool(settings["DEBUG"]):
            print("DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG")

    SettingTime = os.path.getmtime(FILE)
    return settings


def Heartbeat():
    try:
        dstr = datetime.datetime.now().strftime("%b %d, %H:%M") + " : OK"

        with open(MAIN.FILEROOT + "AutoHeart.txt", "w") as myfile:
            myfile.write(dstr)
    except:
        return



def AutoScanTrain(deepcnt, group_path=""):
    import Scanner
    global AutoFile
    # Main Trading routine, called once a day from here, or from AITrader.html interface
    if not group_path:
        group_path = AutoFile
    else:
        AutoFile = group_path

    settings = ReadSettings(True)
    Scanner.ClearScanData(group_path)
    Scanner.Scanner(group_path, deep=deepcnt, mincorr=0.15)

def drange(start, stop, step):
    while start < stop:
            yield start
            start += step

def AutoSearch(group_path=""):

    global AutoFile
    # Main Trading routine, called once a day from here, or from AITrader.html interface
    if not group_path:
        group_path = AutoFile
    else:
        AutoFile = group_path
    settings = ReadSettings(True)
    path = FILEROOT + '/' + group_path + '/'
    filename = "Total"

    with open(path + 'totals.csv', 'w', newline='') as csvfile:
        headers = ['MinModels', 'MaxModels', 'MinTradeScore', 'ActualCount', 'AvgPctWin', 'AvgProfit']
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        totlist = []
        maxmodels = 6
        mintradescore = 0.1
        totalnumofstocks = 10

        runcount = 0
        minmodels = 1

        for mintradescore in drange(0, 1.0, 0.05):
            tot = SimulateTrades(group_path, maxmodels, minmodels, mintradescore,  totalnumofstocks)
            totlist.append(tot)
            runcount += 1
            print(f"{runcount}  Min Trade Score: {mintradescore}   Min Models: {minmodels}   Max Models: {maxmodels}  Avg Pct Win: {tot['AvgPctWin']}")

        writer.writerows(totlist)
        print("------ AUTO SCAN COMPLETE -------")


def SimulateCalcTrades(group_path, maxmodels, minmodels, mintradescore, totalnumofstocks):
    import Scanner
    mydata = Scanner.CalcIndicators(group_path, minmodels=minmodels, maxmodels=maxmodels, mintradescore=mintradescore,
                                    sortkey="TotalPercentWin", verbose=False)
    return SimulateTrades(mydata,maxmodels=maxmodels, minmodels=minmodels,  mintradescore=mintradescore, totalnumofstocks= totalnumofstocks)

def SimulateTrades(mydata, maxmodels, minmodels, mintradescore, totalnumofstocks):
    tot = dict()
    tot["StkCount"] = {}
    for stk in mydata["Stocks"]:
        stk["AllDailyScore"] = [0] * len(stk["AllTargetLabel"])
        for day in range(len(stk["AllTargetLabel"])):
            if len(stk["AllTradeScore"]) < minmodels:
                stk["AllDailyScore"][day] = 0
                continue
            for m in range(maxmodels + 1):
                if m < len(stk["AllTradeScore"]):
                    stk["AllDailyScore"][day] += stk["AllTradeScore"][m][day]
            div = max([maxmodels, (len(stk["AllTradeScore"]))])
            if div != 0.0:
                stk["AllDailyScore"][day] /= float(div)
    pctwincnt = 0
    count = 0
    totalprofit = 0
    avgpctwin = 0
    totaldeepprofit = 0
    for day in range(len(stk["AllTargetLabel"])):
        daysort = sorted(mydata["Stocks"], key=lambda d: math.fabs(d['AllDailyScore'][day]), reverse=True)
        countstocks = 0
        daycount = 0
        totaldayprofit = 0

        for stk in daysort:
            if countstocks < totalnumofstocks:

                # add to profit, add to win percent
                if stk["AllDailyScore"][day] == 0 or abs(stk["AllDailyScore"][day]) < mintradescore:
                    dayprofit = 0
                elif stk["AllDailyScore"][day] > 0:
                    dayprofit = stk["AllTargetLabel"][day]
                else:
                    dayprofit = -1 * stk["AllTargetLabel"][day]

                totaldayprofit += dayprofit
                totaldeepprofit += stk["TotalDeepProfit"]
                if dayprofit > 0:
                    pctwincnt += 1
                    count += 1
                    daycount += 1
                if dayprofit < 0:
                    count += 1
                    daycount += 1
                if stk["Name"] in tot["StkCount"].keys():
                    tot["StkCount"][stk["Name"]] += 1
                else:
                    tot["StkCount"][stk["Name"]] = 1
            countstocks += 1
        for stk in daysort:
            stocks = dict()
            stocks["Name"] = stk["Name"]
        if daycount != 0:
            totaldayprofit = totaldayprofit * totalnumofstocks / daycount

        totalprofit += totaldayprofit
    if count != 0:
        avgpctwin = pctwincnt / count * 100
    if totalnumofstocks != 0:
        avgprofit = totalprofit / totalnumofstocks
        totaldeepprofit = totaldeepprofit/ totalnumofstocks

    tot["MinModels"] = minmodels
    tot["MaxModels"] = maxmodels
    tot["MinTradeScore"] = mintradescore
    tot["ActualCount"] = count
    tot["AvgPctWin"] = avgpctwin
    tot["AvgProfit"] = avgprofit
    tot["AvgDeepProfit"] = totaldeepprofit
    return tot


def AutoScanTrade(group_path="", modeltype="", maxTrades=0, orderSize=0, justClose=False):
    global AutoFile
    # Main Trading routine, called once a day from here, or from AITrader.html interface
    if not group_path:
        group_path = AutoFile
    else:
        AutoFile = group_path

    settings = ReadSettings(True)

    now = datetime.datetime.now()
    if orderSize == 0:
        orderSize = float(ReadSettings(False)["OrderSize"])
    if maxTrades == 0:
        maxTrades = float(ReadSettings(False)["MaxTrades"])

    if not bool(settings["Enabled"]) and not bool(settings["FakeTrading"]):
        print("AUto Trading Stopped: Not Enabled  " + str(now))
        return
    if datetime.datetime.today().weekday() > 4 and not bool(settings["FakeTrading"]):
        print("AUto Trading Stopped: Weekend  " + str(now))
        return
    print("AUto Trading Started..." + str(now))
    rt = ""
    trades = []
    hasTrade = {}
    positions = json.loads(IBClient.Positions())
    import Scanner
    scans = []
    if not modeltype or modeltype == "CORR1":
        scans = Scanner.CalcIndicators(group_path, minmodels=settings["MinModels"], maxmodels=settings["MaxModels"], verbose=False)["Stocks"]

    # use the first pods stock list to control them all
    for ii in range(len(scans)):
        sym = scans[ii]["Symbol"]
        tradeScore = scans[ii]["TradeScore"]
        con = tradeScore
        lastprice = scans[ii]["LastPrice"]
        # No trade List
        if tradeScore != 0.0 and "NoTrade" in settings.keys() and sym in settings["NoTrade"]:
            tradeScore = 0.0
            print("NO TRADE:" + sym)

        if math.fabs(tradeScore) >= float(settings["MinTradeScore"]):
            trades.append(
                {"Symbol": sym, "Score": tradeScore, "Delta": con, "LastPrice": lastprice, "PredictDate": scans[ii]["PredictDate"], "Indicators": scans[ii]["Indicators"]})
            hasTrade[sym] = con

    trades = sorted(trades, key=lambda x: x['Score'], reverse=True)
    tcount = 0

    #Close positions that are not on our list
    if bool(settings["CloseTrades"]):
        allsymbols = [d['Symbol'] for d in scans]
        for pos in positions:
            if pos not in allsymbols:
                if not bool(settings["FakeTrading"]):
                    IBClient.ClosePositions([pos])
                    print("TRADING CLOSE: " + pos)
                else:
                    print("FAKE TRADING CLOSE: " + pos)



    # Do Trades on Existing positions
    madetrades = []
    for ii in range(len(scans)):
        sym = scans[ii]["Symbol"]
        if sym in positions and positions[sym]["position"] != 0.0 and bool(settings["CloseTrades"]):  # have postion, should we bail (opposite position or < 90% of min score
            if sym not in hasTrade.keys() or (positions[sym]["position"] * hasTrade[sym] < 0.0):  # opposite from current position

                if not bool(settings["FakeTrading"]):
                    IBClient.ClosePositions([sym])
                    print("TRADING CLOSE: " + sym)
                else:
                    print("FAKE TRADING CLOSE: " + sym)
            else:
                print("TRADING HOLD POSITION: " + sym)
                for trd in trades:
                    if trd["Symbol"] == sym:
                        madetrades.append(trd)
                        break
                if sym in hasTrade.keys():
                    del hasTrade[sym]

                tcount += 1

    # Now do the new trades
    if not justClose:
        for trade in trades:
            if trade["Symbol"] not in hasTrade.keys():
                continue  # we have removed it above

            if tcount >= maxTrades:
                print("Maximum Trades Reached: " + str(maxTrades))
                break

            multiplier = 1.0
            if min(len(trades), maxTrades) > 0:
                multiplier = int(maxTrades / min(len(trades), maxTrades))
            multiplier = max(multiplier, 1.0)
            multiplier = min(multiplier, 3.0)

            quant = round(((float(orderSize) / trade["LastPrice"]) / 20.0), 0) * 20
            if quant == 0: quant = 10
            quant = quant * multiplier
            if math.fabs(trade["Score"]) >= float(settings["MinTradeScore"]):
                # new positions
                sym = trade["Symbol"]
                if trade["Delta"] < 0 and bool(settings["OnlyLong"]):
                    print(sym + " SHORT TRADE NOT TRADED (OnlyLong)" + " : " + str(trade["Score"]))
                    continue

                tcount = tcount + 1
                if trade["Delta"] < 0.0:
                    quant *= -1

                rt = rt + "TRADE:" + sym + ":" + str(quant) + "\r\n"

                if not bool(settings["FakeTrading"]):
                    print("TRADING: " + sym + " : " + str(quant) + " : " + str(trade["Score"]) + " @MULT:" + str(
                        multiplier))

                    IBClient.OpenPositions([sym], quant)
                    RecordTradeToWeb(sym, trade["Score"], trade["LastPrice"], trade["PredictDate"], group_path, trade["Indicators"], ActualTrade=True)
                    madetrades.append(trade)
                else:
                    print("FAKE TRADING: " + sym + " : " + str(quant) + " Score:" + str(
                        round(trade["Score"], 2)) + " @" + str(trade["LastPrice"]) + " @MULT:" + str(multiplier))
                    RecordTradeToWeb(sym, trade["Score"], trade["LastPrice"], trade["PredictDate"], group_path, trade["Indicators"], ActualTrade=True)

        if not bool(settings["FakeTrading"]):
            madetrades.append({"Symbol": "TOTAL", "Score": 0, "Delta": 0, "LastPrice": GetAccount(),
                               "ResultsDate": datetime.datetime.now()})
            #MAIN.SendMail(group_path, madetrades)
        print("Trading Complete @ " + str(datetime.datetime.now()))
    return rt


def GetAccount():
    # reads IB account data from the Account.txt file written by IBServer.py
    cash = 0
    try:
        acct = json.loads(IBClient.GetAccount().replace("'", '"'));
        cash = acct["NetLiquidation"]


    except:
        print("Error reading account data")
        pass
    return cash


def RecordTradeToWeb(sym, score, lastprice, pdate, group_path, inputstks, ActualTrade=False):
    # Send the pick to the Picks table for long term tracking
    try:
        for stk in inputstks:
            stk["TargetLabel"] = []
            stk["TradeScoreARR"] = []

        rundate = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
        predict = {"Symbol": sym,
                   "RunDate": rundate,
                   "PredictDate": pdate,
                   "Score": score,
                   "LastPrice": lastprice,
                   "ActualDelta0": 0,
                   "ActualDelta1": 0,
                   "ActualDelta2": 0,
                   "GroupPath": group_path,
                   "InputStocks": inputstks
                   }
        if ActualTrade:
            FileAppend(group_path, Config.DBPicks, "ActualTrade", predict)
        else:
            FileAppend(group_path, Config.DBPicks, sym, predict)


    except:
        print("Error Writing trade to web")
        pass
    return


def FileAppend(maindir, folder, key, obj, extension=".txt"):
    rt = False
    DIR = MAIN.FILEROOT + maindir + "/" + folder + "/"
    FILE = DIR + key + extension

    if not os.path.isdir(DIR):
        os.mkdir(DIR)

    if obj:
        try:
            with open(FILE, "a") as myfile:
                rt = myfile.write(json.dumps(obj, indent=4) + ",\n")
        except:
            print("FAILED: to write file blob: " + folder + "/" + key + extension)
            pass
    return rt


# START PROGRAM
if __name__ == "__main__":
    exit(main())

# ExportPairs()
# CombinePairs()