import numpy as np

import os
import datetime
import math
from scipy.stats import pearsonr

import X_Data, X_Model

import Scanner
import AutoScanner

import maincontrol as MAIN


def main():

    print("-------------------------------")
    print("### Indicators ###")
    settings = dict()
    settings["CorrType"] = "2Day"
    settings["deep"] = 100
    settings["minmodels"] = 0
    settings["maxmodels"] = 6
    settings["mincorr"] = 0.75
    settings["mintradescore"]= 0.25
    settings["inputfilter"] = 0.2
    FindCorrelations(settings)

def FindCorrelations(settings):
    targets = ["GOOG", "TXN", "AMAT", "AMD", "TSLA", "INTC", "OXY", "CVX", "FANG", "BXP", "CRM", "REGN", "HST", "EBAY",
               "FRT", "OKE", "DHI", "COP", "K", "KMI", "XOM", "AMT", "KMB", "AMZN", "HRL", "MRO", "FB", "HAL", "VLO",
               "CHD", "WBA", "PRGO", "TFX", "VNO", "ETR", "INCY", "PHM", "NEM", "LMT", "FISV", "BKNG", "FIS", "HUM",
               "LVS", "DVN", "SPGI", "NOC", "REG", "MCO", "LEN", "SBAC", "OMC", "ED", "DISH", "CLX", "KSS", "DLR",
               "CCL", "MPC", "NOV", "MA", "BSX", "CTAS", "EW", "T", "VRSK", "SRE", "EOG", "LKQ", "LHX", "ATO", "APA",
               "HP", "JKHY", "EFX", "AAP", "XEL", "MSFT", "O", "COTY", "PXD", "GIS", "KO", "CMS", "FLT", "CPB", "CCI",
               "KR", "LNT", "FTI", "HOG", "MMM", "RE", "ADBE", "DRE", "CI", "AKAM", "CL", "CTXS", "WMT", "PLD", "RCL",
               "ZION", "WY", "NFLX", "ALLE", "TSN", "BA", "PG", "PCAR", "ABT", "ABC", "NI", "IBM", "WMB", "WELL", "WEC",
               "AIV", "VRSN", "JBHT", "KHC", "PM", "HES", "GILD", "MAC", "ESS", "ARE", "MDT", "TRIP", "NVR", "HLT",
               "PEP", "EQIX", "GPC", "PEAK", "SJM", "SPG"]
    inputs = ["DIA", "QQQ", "FVX.INDX", "RVX.INDX", "IRX.INDX"]
    inputs += X_Data.get_stock_group(1)
    model = X_Model.ModelSettings()

    FILE = MAIN.FILEROOT + "NoUpdate.txt"
    verbose = 1
    if os.path.exists(FILE):
        noUpdate = True
        model.UseIntradayPrice = 0
        if verbose:
            print("NO UPDATE FOR INTRADAY")


    model.UseIntradayPrice = 0
    model.MaxDataPoints = 300

    merge = list(set(inputs + targets))
    all_data = X_Data.get_stock_data(model, merge)

    data = Scanner.load_grid_data(model, all_data)


    print('=======================================================')

    rtdata = dict()
    rtdata["Stocks"] = []

    rtdata["TotalData"]= []
    inputx = 0
    labels = 0
    for targetstk in targets:
        stk = dict()
        stk["Name"] = targetstk
        stk["Symbol"] = targetstk
        stk["AllTargetLabel"] = []
        stk["Indicators"] = []
        stk["TradeScore"] = 0
        stk["NumOfIndicators"] = 0
        stk["AllTradeScore"] = []
        stk["TotalPercentWin"] = 0
        stk["TotalProfit"] = 0
        stk["ProfitArray"] = []
        stk["TotalDeepProfit"] = 0


        tHold = 0.0
        tProfit = 0.0
        tRatio = 0.0
        alltradesc = []
        count = [0] * len(data.labels[0].tolist()[:-1])
        if settings["CorrType"] == "Trendy":
            for inputstk in inputs:
                idxInput = Scanner.GetStockIndex(data.symbols, inputstk)
                inputx = np.asarray(data.labels[idxInput].tolist()[:-1])
                for t in range(0, len(inputx)):
                    if data.labels[idxInput].tolist()[t]> 0:
                        count[t] += 1
                    elif data.labels[idxInput].tolist()[t] < 0:
                        count[t] -= 1

        for inputstk in inputs:

            idxTarget = Scanner.GetStockIndex(data.symbols, targetstk)
            idxInput = Scanner.GetStockIndex(data.symbols, inputstk)
            if idxTarget < 0 or idxInput < 0:
                continue

            #set the data arrays and do the correlation math

            #input is the input data we are hoping has a correlation
            daystotrim = 0
            if settings["CorrType"] == "1Day":
                inputx = np.asarray(data.labels[idxInput].tolist()[:-1])
            elif settings["CorrType"] == "2Day":
                daystotrim = 1
                inputx = np.asarray(data.labels[idxInput].tolist()[:-1])
                #do something fancy to combine more than one day
                for t in range(1,len(inputx)):
                    if inputx[t]*inputx[t-1] < 0:
                        inputx[t] = 0
                    else:
                        inputx[t] = (inputx[t] + inputx[t-1])/2
            elif settings["CorrType"] == "Trendy":
                inputx = np.asarray(data.labels[idxInput].tolist()[:-1])


            inputx = inputx[daystotrim:]#trim extra data if we are using more than one day for input


            #labels is the target labels (results) for the target stock [1:] pulled back one day
            labels = np.asarray(data.labels[idxTarget].tolist()[int(1):])
            labels = labels[daystotrim:] #trim extra data if we are using more than one day for input


            # apply any filters to zero our input value that are too small for instance
            if settings["CorrType"] == "Trendy":
                for t in range(0, len(inputx)):
                    if abs(count[t]) < 50:
                        inputx[t] = 0
            else:
                for t in range(0, len(inputx)):
                    if math.fabs(inputx[t]) < settings["inputfilter"]:
                        inputx[t] = 0



            # think we should rip out the inputs that are zero, to stop confusing the correlations
            inputcopy = inputx[:200]
            labelcopy = labels[:200]
            max = len(labelcopy)
            for dayx in range(max - 1, -1, -1):
                if inputx[dayx] == 0:
                    inputcopy = np.delete(inputcopy, dayx)
                    labelcopy = np.delete(labelcopy, dayx)

            #!! remove from both input and labels

            #convert to numpy arrays for the correlation math
            #inputnp = inputcopy / np.asarray([abs(ele) + 0.0001 for ele in inputcopy])
            labelsnp = labelcopy / np.asarray([abs(ele) + 0.0001 for ele in labelcopy])
            # do the correlation math
            correlation, _ = pearsonr(labelsnp, inputcopy)

            #record the results
            if math.fabs(correlation) > settings["mincorr"]:
                out = Scanner.TestTrade(labels, inputx, int(settings["deep"]), correlation, settings["inputfilter"])
                tHold += out["holdprofit"]
                tProfit += out["profit"]

                print('{}:{} Pearsons correlation: {:f}  profit:{:f}  win%:{:f} on {:d} samples  hold value:{:f}'.format( targetstk, inputstk, correlation, out["profit"], out["pctwin"], out["count"], out["holdprofit"]))

                out["targetstk"] = targetstk
                out["inputstk"] = inputstk
                out["correlation"] = correlation
                out["mincorr"] = settings["mincorr"]
                out["runtime"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                out["deepcount"] = settings["deep"]



                ind = dict()
                ind["Symbol"] = out["inputstk"]
                ind["Correlation"] = out["correlation"]

                ind["DeepCount"] = out["deepcount"]
                ind["ActualCount"] = out["actualcount"]
                ind["DeepPercentWin"] = out["deepwinpct"]
                ind["TargetLabel"] = out["targetlabel"]
                ind["TradeScoreARR"] = out["tradescorearr"]
                ind["DeepProfit"] = out["deepprofit"]
                ind["DeepHoldProfit"] = out["deepholdprofit"]
                ind["PercentWin"] = out["pctwin"]
                ind["Profit"] = out["profit"]
                stk["AllTargetLabel"] = ind["TargetLabel"]
                alltradesc.append(ind["TradeScoreARR"])

                stk["Indicators"].append(ind)
                length = len(stk["AllTargetLabel"])
                # print(stk["Name"])
                result = Scanner.pctwintot_calc(settings["mintradescore"], settings["maxmodels"], length, alltradesc, stk["AllTargetLabel"])
                result2 = Scanner.profit_total_calc(settings["mintradescore"], settings["maxmodels"], length, alltradesc, stk["AllTargetLabel"])
                ##stk["NumOfIndicators"] = count
                stk["TotalPercentWin"] = result[0]
                stk["ActualCount"] = result[1]
                stk["AllTradeScore"].extend(alltradesc)
                stk["AllTargetLabel"] = stk["AllTargetLabel"]
                stk["TotalProfit"] = result2[0]
                stk["TotalDeepProfit"] = result2[1]
                stk["ProfitArray"] = Scanner.get_dayprofit_array(settings["mintradescore"], settings["maxmodels"], length, alltradesc,stk["AllTargetLabel"])

                stk["AllTradeScore"].extend(alltradesc)
                if len(stk["Indicators"]) > 0:
                    rtdata["Stocks"].append(stk)
                if tHold != 0.0:
                    tRatio = tProfit/tHold
                if tProfit != 0.0:
                    print('{} - Total {} correlation: Profit:{}  Hold:{}  Ratio:{}'.format(targetstk, settings["CorrType"], tProfit, tHold, tRatio))

    tot = AutoScanner.SimulateTrades(rtdata, maxmodels=20, minmodels=0, mintradescore=0, totalnumofstocks=10)
    rtdata["TotalData"].append(tot)
    return rtdata




# START PROGRAM
if __name__ == "__main__":
    exit(main())