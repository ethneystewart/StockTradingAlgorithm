import numpy as np
import FileStorage
import History
import holidays
import os
import datetime
import math
from scipy.stats import pearsonr

import X_Data, X_Model
import json

import maincontrol as MAIN
from maincontrol import FILEROOT

class GridData:
    # parsed training examples from stock history, return value for load_wide_data
    def __init__(self):
        self.stockname = ''
        self.tf_inputs = []  # inputs to the neural net
        self.prices = []  # adjusted close prices of target stock
        self.dates = []  # close date (or intraday date)
        self.labels = []  # labels for the training examples, i.e. the actual stock deltas
        self.volumes = []  # daily volumes (optional input to tf)
        self.openprices = []  # open prices of target stock
        self.highprices = []  # high prices of target stock
        self.lowprices = []  # low prices of target stock
        self.closeprices = []  # close (not adjusted) prices of target stock
        self.symbols = [] #names of primary stock
        self.dayofweek = []


    def AddMoreData(self, wd):
        self.tf_inputs.append(wd.tf_inputs)  # inputs to the neural net
        self.prices.append(wd.prices)  # close prices of target stock
        self.dates.append(wd.dates)  # close date (or intraday date)
        self.labels.append(wd.labels)  # labels for the training examples, i.e. the actual stock deltas
        self.volumes.append(wd.volumes)  # daily volumes (optional input to tf)
        self.openprices.append(wd.openprices)  # open prices of target stock
        self.highprices.append(wd.highprices)  # high prices of target stock
        self.lowprices.append(wd.lowprices)  # low prices of target stock
        self.closeprices.append(wd.lowprices)  # close prices of target stock
        self.dayofweek.append(wd.dayofweek)
        return self

def main():

    print("-------------------------------")
    print("### CORRELATE ###")


    Scanner("Scan")


def Scanner(maindir, deep=0, mincorr=0.15):

    targets = ["NFLX", "CRM", "NVDA", "INTC", "MSFT", "AMAT", "AMD", "GOOG", "FB", "TXN"]
    targets = ["GOOG", "TXN", "AMAT" , "AMD", "TSLA", "INTC", "OXY", "CVX", "FANG", "BXP", "CRM", "REGN", "HST", "EBAY", "FRT", "OKE", "DHI", "COP", "K", "KMI", "XOM",  "AMT", "KMB", "AMZN", "HRL", "MRO", "FB", "HAL", "VLO", "CHD", "WBA", "PRGO", "TFX", "VNO", "ETR", "INCY", "PHM", "NEM", "LMT", "FISV", "BKNG", "FIS", "HUM", "LVS", "DVN", "SPGI", "NOC", "REG", "MCO", "LEN", "SBAC", "OMC", "ED", "DISH", "CLX", "KSS", "DLR", "CCL", "MPC",  "NOV", "MA", "BSX", "CTAS", "EW", "T", "VRSK", "SRE", "EOG", "LKQ", "LHX", "ATO", "APA", "HP", "JKHY", "EFX", "AAP", "XEL", "MSFT", "O", "COTY", "PXD", "GIS", "KO", "CMS", "FLT", "CPB", "CCI", "KR", "LNT", "FTI", "HOG", "MMM", "RE", "ADBE", "DRE", "CI", "AKAM", "CL", "CTXS", "WMT", "PLD", "RCL", "ZION", "WY", "NFLX", "ALLE", "TSN", "BA", "PG", "PCAR", "ABT", "ABC", "NI", "IBM", "WMB", "WELL", "WEC", "AIV", "VRSN", "JBHT", "KHC", "PM", "HES", "GILD", "MAC", "ESS", "ARE", "MDT", "TRIP", "NVR", "HLT", "PEP", "EQIX", "GPC", "PEAK", "SJM", "SPG"]
    inputs =  ["DIA", "QQQ", "FVX.INDX", "RVX.INDX", "IRX.INDX"]
    inputs += X_Data.get_stock_group(1)
    model = X_Model.ModelSettings()
    model.UseIntradayPrice = 0
    model.MaxDataPoints = 300

    merge = list(set(inputs + targets))
    all_data = X_Data.get_stock_data(model, merge)

    tfdata = load_grid_data(model, all_data)
    corrs = []
    corrs.append({"Name":"Yesterday", "offset": 1, "var": "close", "subvar": "delta", "deepcount": deep, "mincorr" : mincorr, "inputfilter": 0.2})

    FindCorrelations(tfdata, maindir,  targets, merge, corrs)
    print("=============== Scan Complete =================")
    return


def FindCorrelations(data, maindir,  targetstks, inputstks,  corrs):

    for corr in corrs:
        print('=======================================================')
        print('{} correlation: min corr:{}  inputfilter:{}'.format(corr["Name"], corr["mincorr"], corr["inputfilter"]))
        path = FILEROOT + '/' + maindir + '/'

        for targetstk in targetstks:
            foundone = False

            if targetstk == "NOC":
                foundone = False

            with open(path + targetstk + ".txt" , "w+") as myfile:
                tHold = 0.0
                tProfit = 0.0
                tRatio = 0.0
                list = []
                for inputstk in inputstks:
                    idxTarget = GetStockIndex(data.symbols, targetstk)
                    idxInput = GetStockIndex(data.symbols, inputstk)
                    if idxTarget < 0 or idxInput < 0:
                        continue
                    data1 = np.asarray(data.labels[idxTarget].tolist()[int(corr["offset"]):])
                    data1np = data1 /  np.asarray([abs(ele)+0.0001 for ele in data1])
                    data2 = np.asarray(data.labels[idxInput].tolist()[:-1 * int(corr["offset"])])
                    data2np = data2 / np.asarray([abs(ele)+0.0001 for ele in data2])
                    data2np = data2np[:200]
                    data1np = data1np[:200]
                    correlation, _ = pearsonr(data1np, data2np)
                    if math.fabs(correlation) > corr["mincorr"]:
                        list.append({"symbol": targetstk, "corr": correlation})
                        out = TestTrade(data1, data2, int(corr["deepcount"]), correlation, corr["inputfilter"])
                        tHold += out["holdprofit"]
                        tProfit += out["profit"]
                        foundone = True
                        print('{}:{} Pearsons correlation: {:f}  profit:{:f}  win%:{:f} on {:d} samples  hold value:{:f}'.format( targetstk, inputstk, correlation, out["profit"], out["pctwin"], out["count"], out["holdprofit"]))

                        out["targetstk"] = targetstk
                        out["inputstk"] = inputstk
                        out["correlation"] = correlation
                        out["mincorr"] = corr["mincorr"]
                        out["runtime"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        out["deepcount"] = corr["deepcount"]
                        myfile.writelines(json.dumps(out) + "\n")
                if tHold != 0.0:
                    tRatio = tProfit/tHold
                if tProfit != 0.0:
                    print('{} - Total {} correlation: Profit:{}  Hold:{}  Ratio:{}'.format(targetstk, corr["Name"], tProfit, tHold, tRatio))
            if not foundone:
                os.remove(path + targetstk + ".txt")
    return list

def GetStockIndex(symbols, findstk):
    for i in range(len(symbols)):
        if findstk == symbols[i]:
            return i

    return -1

def TestTrade(targetlabel, inputdata, deep, corr, inputfilter):
    out = dict()
    out["profit"] = 0.0
    out["pctwin"] = 0.0
    out["holdprofit"] = 0.0
    out["count"] = 0
    out["deepwinpct"] = 0.0
    out["deepprofit"] = 0.0
    out["deepholdprofit"] = 0.0
    out["actualcount"] = 0
    out["tradescorearr"] = []
    out["inputdata"] = []
    out["targetlabel"] = []

    #should this run cumulatively, ie reinvest profit?
    #runs for 200
    for t in range(len(targetlabel) - deep):
        out["holdprofit"] = min(out["holdprofit"], 2)
        out["holdprofit"] = max(out["holdprofit"], -2)
        out["holdprofit"] += targetlabel[t]
        if corr * inputdata[t] > 0:
            dayprofit = targetlabel[t]
        elif corr * inputdata[t] < 0:
            dayprofit = -1 * targetlabel[t]
        else:
            dayprofit = 0

        #dont count very small changes
        if math.fabs(dayprofit) < inputfilter:
            dayprofit = 0

        out["profit"] += dayprofit
        if dayprofit > 0:
            out["pctwin"] += 1
            out["count"] += 1
        elif dayprofit < 0:
            out["count"] += 1


    if out["count"] > 0:
        out["pctwin"] = out["pctwin"]/out["count"]
    # for 100 days
    for t in range(len(targetlabel) - deep, len(targetlabel)):
        out["deepholdprofit"] += targetlabel[t]
        tradescore = corr * inputdata[t]
        out["tradescorearr"].append(tradescore)
        out["targetlabel"].append(targetlabel[t])
        out["inputdata"].append(inputdata[t])

        dayprofit = min(dayprofit, 2)
        dayprofit = max(dayprofit, -2)
        if corr * inputdata[t] > 0:
            dayprofit = targetlabel[t]
        elif corr * inputdata[t] < 0:
            dayprofit = -1 * targetlabel[t]
        else:
            dayprofit = 0

        out["deepprofit"] += dayprofit
        if dayprofit > 0:
            out["deepwinpct"] += 1
            out["actualcount"] += 1
        elif dayprofit < 0:
            out["actualcount"] += 1

    if out["actualcount"] > 0:
        out["deepwinpct"] = out["deepwinpct"] / out["actualcount"]
    return out


def ClearScanData(maindir):
    path = FILEROOT + '/Scan/'
    badfiles = ["Auto.txt", "Market.txt", "Settings.txt", "Indicators.txt", "Pods.txt", "totals.csv", "Picks"]
    if os.path.isdir(path):
        files = os.listdir(path)
        for f in files:
            if f not in badfiles:
                os.remove(path + "/" + f)

def CalcIndicators(maindir, minmodels = 1, maxmodels=6, mintradescore =0.1, sortkey = 'TradeScore', verbose=True , noUpdate=False):
    data = dict()
    data["Stocks"] = []
    path = FILEROOT + '/'+ maindir + '/'
    model = X_Model.ModelSettings()
    model.UseIntradayPrice = 1

    FILE = MAIN.FILEROOT + "NoUpdate.txt"
    if os.path.exists(FILE):
        noUpdate = True
        model.UseIntradayPrice = 0
        if verbose:
            print("NO UPDATE FOR INTRADAY")


    market = []


    badfiles = ["Auto.txt", "Market.txt", "Settings.txt", "Indicators.txt", "Pods.txt", "totals.csv"]
    if os.path.isdir(path):
        files = os.listdir(path)
        for f in files:
            if f in badfiles or ".txt" not in f:
                continue
            stk = dict()
            stk["Name"] = f.split('.')[0]
            stk["Symbol"] = f.split('.')[0]
            hist = History.GetEODIntradayJSON(stk["Symbol"], NoUpdate=noUpdate)
            market.append(stk["Symbol"])
            day = json.loads(hist)
            stk["Indicators"] = []
            stk["LastPrice"] = day["close"]
            stk["LastDelta"] = day["change"]
            stk["TradeScore"] = 0
            stk["NumOfIndicators"] = 0
            stk["AllTradeScore"] = []
            stk["TotalPercentWin"] = 0
            stk["TotalProfit"] = 0
            stk["ProfitArray"] = []
            stk["TotalDeepProfit"] = 0
            stk["InputData"]= []

            gridData = X_Data.get_stock_data(model, [stk["Symbol"]])
            stk["Graph"] = [d[gridData.closetag] for d in gridData.data[0]][-30:]

            pdate = datetime.datetime.now() + datetime.timedelta(days=1)
            while pdate.weekday() > 4 or pdate in holidays.UnitedStates():
                pdate = pdate + datetime.timedelta(days=1)
            stk["PredictDate"] = pdate.strftime("%Y-%m-%d")

            data["Stocks"].append(stk)


    for stk in data["Stocks"]:
        #This Assumes we are runnign a 1 day delay correlation, need to put this in a switchable function for other corr types
        alltradesc = []
        alltargetlab = []
        tradescore = 0
        listlinedata= []
        count = 0
        with open(path + "/" + stk["Name"] + ".txt", "r") as myfile:
            try:
                for line in myfile.readlines():
                    linedata = json.loads(line)
                    listlinedata.append(linedata)
                newlist = sorted(listlinedata, key=lambda d: math.fabs(d['correlation']), reverse=True)
                for linedata in newlist:
                    count += 1
                    ind = dict()
                    ind["Symbol"] = linedata["inputstk"]
                    hist = History.GetEODIntradayJSON(ind["Symbol"], NoUpdate=noUpdate)
                    market.append(ind["Symbol"])
                    day = json.loads(hist)
                    ind["Value"] = day["change"]
                    ind["Score"] = day["change_p"] * linedata["correlation"]
                    ind["LastPrice"] = day["close"]
                    ind["DayDelta"] = day["change"]
                    ind["Correlation"] = linedata["correlation"]
                    ind["PercentWin"] = linedata["pctwin"]
                    ind["Profit"] = linedata["profit"]
                    ind["DeepCount"] = linedata["deepcount"]
                    ind["ActualCount"] = linedata["actualcount"]
                    ind["DeepPercentWin"] = linedata["deepwinpct"]
                    ind["TargetLabel"] = linedata["targetlabel"]
                    ind["TradeScoreARR"] = linedata["tradescorearr"]
                    ind["DeepProfit"]= linedata["deepprofit"]
                    ind["DeepHoldProfit"] = linedata["deepholdprofit"]
                    stk["Indicators"].append(ind)
                    alltradesc.append(ind["TradeScoreARR"])
                    alltargetlab = ind["TargetLabel"]
                    if len(alltradesc) == maxmodels:
                        break
            except:
                pass

        length = len(alltargetlab)
        #print(stk["Name"])
        result = pctwintot_calc(mintradescore, maxmodels, length,alltradesc, alltargetlab)
        result2 = profit_total_calc(mintradescore, maxmodels,length,alltradesc, alltargetlab)
        stk["NumOfIndicators"] = count
        stk["TotalPercentWin"] = result[0]
        stk["ActualCount"] = result[1]
        stk["AllTradeScore"].extend(alltradesc)
        stk["AllTargetLabel"] = alltargetlab
        stk["TotalProfit"] = result2[0]
        stk["TotalDeepProfit"] = result2[1]
        stk["ProfitArray"] = get_dayprofit_array(mintradescore, maxmodels, length, alltradesc, alltargetlab)
        #insert total line here


        newlist2 = sorted(stk["Indicators"], key=lambda d: math.fabs(d['Correlation']), reverse=True)

        for i in range(len(newlist2)):
            if i < maxmodels:
                tradescore += newlist2[i]["Score"]

        div = max(maxmodels, len(newlist2))
        if div != 0:
            tradescore /= div

        if len(newlist2) < minmodels:
            tradescore = 0
        stk["Indicators"] = newlist2
        stk["TradeScore"] = tradescore

    #no market prices for now
    #np.savetxt(path + "/" + "Market.txt", market, delimiter=", ", fmt='% s')
    data["Stocks"] = sorted(data["Stocks"], key=lambda d: math.fabs(d[sortkey]), reverse=True)
    return data
#new subroutine that is going to calc pctwin

def pctwintot_calc(mintradescore, maxmodels,length, tclist=[], tllist=[]):
    totaltradesc = [0] * length   #will store add up all tradescores day by day
    totalpctwin = 0   #returned data
    pctwincnt = 0       #number of days total overall win
    dayprofit = 0
    temp = [0]*100
    count = 0

    if len(tclist) != 0:    #check that list is not empty
        for i in range(0, length):
            for j in range(len(tclist)):
                if j > maxmodels:
                    break
                temp = tclist[j]
                totaltradesc[i] += temp[i] #adds all day i of each stocks trade scores together
            div = max(maxmodels, len(tclist))
            if div != 0:
                totaltradesc[i] = totaltradesc[i] /div
        cntbeltrsc = 0
        for i in range(0, length):
            if abs(totaltradesc[i]) < mintradescore:
                cntbeltrsc+=1
                dayprofit = 0
            elif totaltradesc[i] == 0:
                dayprofit = 0
            elif totaltradesc[i] > 0:     #just reformatted from original pctwincode now with totaltradescore
                dayprofit = tllist[i]
            else:
                dayprofit = -1*tllist[i]

            if dayprofit > 0:
                pctwincnt += 1
                count += 1
            if dayprofit < 0:
                count +=1
        #print(cntbeltrsc)
        if count!= 0:
            totalpctwin = pctwincnt/count*100
    return totalpctwin, count


def profit_total_calc(mintradescore, maxmodels,length, tclist=[], tllist=[]):
    totaltradesc = [0] * length  # will store add up all tradescores day by day
    dayprofit = 0
    temp = [0] * 100
    totalprofit = 0
    totaldeepholdprofit = 0
    if len(tclist) != 0:  # check that list is not empty
        for i in range(0, length):
            for j in range(len(tclist)):
                if j > maxmodels:
                    break
                temp = tclist[j]
                totaltradesc[i] += temp[i]  # adds all day i of each stocks trade scores together

        for i in range(0, length):
            totaldeepholdprofit += tllist[i]
            if totaltradesc[i] == 0 or abs(totaltradesc[i]) < mintradescore:
                dayprofit = 0
            elif totaltradesc[i] > 0:  # just reformatted from original pctwincode now with totaltradescore
                dayprofit = tllist[i]
            else:
                dayprofit = -1 * tllist[i]
            totalprofit += dayprofit
    return totalprofit, totaldeepholdprofit


def get_dayprofit_array(mintradescore, maxmodels,length, tclist=[], tllist=[]):
    totaltradesc = [0] * length  # will store add up all tradescores day by day
    dayprofit = 0
    temp = [0] * 100
    profitarray = []

    if len(tclist) != 0:  # check that list is not empty
        for i in range(0, length):
            for j in range(len(tclist)):
                if j > maxmodels:
                    break
                temp = tclist[j]
                totaltradesc[i] += temp[i]  # adds all day i of each stocks trade scores together
            div = max(maxmodels, len(tclist))
            if div != 0:
                totaltradesc[i] = totaltradesc[i] / div
        for i in range(0, length):
            if totaltradesc[i] > 0:  # just reformatted from original pctwincode now with totaltradescore
                dayprofit = tllist[i]
            elif totaltradesc[i] == 0 or abs(totaltradesc[i]) < mintradescore:
                dayprofit = 0
            else:
                dayprofit = -1 * tllist[i]
            profitarray.append(dayprofit)
    return profitarray

def load_grid_data(model, target_data):
    # get labeled training examples from the stock data and model settings
    # the requested data is marked as "dirty" except for the last DeepOffset number that are reserved for blind testing

    # calc size of the training data
    num_lookforward = model.LookForwardDays  # not used in SolverWide2 version, it spoofs the last price deltas

    # stock history data
    # data[0] is the target stock
    # data[>0] are all the input stocks, including the target stock again

    closetag = target_data.closetag

    if not target_data.data or len(target_data.data[0]) == 0:
        return None

    # we want extra examples for the "deep" evaluation and the dates that don't have lookforward actuals available
    # only the first NumDataPoints of the examples are used in training
    model.NumDataPoints = model.MaxDataPoints  # this is how many data points are requested
    num_examples = model.NumDataPoints + model.DeepOffset + num_lookforward
    num_lookback = model.NumLookbackPeriods
    num_history_pts = len(target_data.data[0])

    num_available_examples = num_history_pts - num_lookback # need num_lookback + 1 points to get num_lookback deltas

    if (num_examples > num_available_examples):
        num_examples = num_available_examples
        model.NumDataPoints = num_examples - model.DeepOffset - num_lookforward

    if model.NumDataPoints < 0:
        print(f"Insufficient data points for {model.TargetStock}: {model.NumDataPoints}")
        return None

        # initialize return value object
    num_extra = 0
    has_sma10 = True if ("SMA10" in model.ExtraData or "sma10" in model.ExtraData or "all" in model.ExtraData) else False
    has_sma30 = True if ("SMA30" in model.ExtraData or "sma30" in model.ExtraData or "all" in model.ExtraData) else False
    has_volume = True if ("Volume" in model.ExtraData or "volume" in model.ExtraData or "all" in model.ExtraData) else False
    has_bband = True if ("BBand" in model.ExtraData or "bband" in model.ExtraData or "all" in model.ExtraData) else False
    has_rsi = True if ("RSI" in model.ExtraData or "rsi" in model.ExtraData or "all" in model.ExtraData) else False
    has_obv = True if ("OBV" in model.ExtraData or "obv" in model.ExtraData or "all" in model.ExtraData) else False
    has_hloc = True if ("HLOC" in model.ExtraData or "hloc" in model.ExtraData or "all" in model.ExtraData) else False

    num_extra += 1 if has_sma10 else 0
    num_extra += 1 if has_sma30 else 0
    num_extra += 1 if has_volume else 0
    num_extra += 2 if has_bband else 0
    num_extra += 1 if has_rsi else 0
    num_extra += 1 if has_obv else 0
    num_extra += 1 if has_hloc else 0

    wdall = GridData()
    for stk in range(len(target_data.symbols)):
        wd = GridData()
        wd.stockname = target_data.symbols[stk]
        wd.tf_inputs = np.zeros([num_examples, 1 + num_extra])  # inputs to the neural net

        wd.prices = np.zeros([num_examples])
        wd.openprices = np.zeros([num_examples])
        wd.lowprices = np.zeros([num_examples])
        wd.highprices = np.zeros([num_examples])
        wd.closeprices = np.zeros([num_examples])
        open = np.zeros([num_examples])
        high = np.zeros([num_examples])
        low = np.zeros([num_examples])
        close = np.zeros([num_examples])
        wd.dates = [""] * num_examples
        wd.dayofweek = np.zeros([num_examples])
        wd.labels = np.zeros([num_examples])  # labels for the training examples, actual delta price to predict
        wd.volumes = np.zeros([num_examples])  # optionally added as tf_inputs

        datetag = "date"
        volumetag = "volume"

        # starting index that we want from the history
        start_index = num_history_pts - num_examples

        #############################################
        # region MAIN LOOP
        #############################################
        sma10 = []
        sma30 = []
        for t in range(0, num_examples):  # (t + start_index) is "today's close" for example[t], trying to predict ahead
            data_index = t + start_index

            wd.prices[t] = target_data.data[stk][data_index][closetag]
            wd.openprices[t] = target_data.data[stk][data_index]["open"]
            wd.highprices[t] = target_data.data[stk][data_index]["high"]
            wd.lowprices[t] = target_data.data[stk][data_index]["low"]
            wd.closeprices[t] = target_data.data[stk][data_index]["close"]
            wd.dates[t] = target_data.data[stk][data_index][datetag]
            wd.dayofweek[t] = datetime.datetime.strptime(wd.dates[t], '%Y-%m-%d').weekday()
            #label for this input data, look ahead when possible
            if data_index + num_lookforward < len(target_data.data[stk]):
                this_stock_delta = target_data.data[stk][data_index + num_lookforward][closetag] - wd.prices[t]
                wd.labels[t] = 100.0 * (this_stock_delta / wd.prices[t])
            else:
                wd.labels[t] = 0.0


            if wd.prices[t] == 0.0 and t > 0:
                wd.prices[t] = wd.prices[t - 1]  # carry over missing data
                wd.openprices[t] = wd.openprices[t-1]
                open[t] = open[t - 1]
                high[t] = high[t - 1]
                low[t] = low[t - 1]
                close[t] = close[t - 1]

            if wd.prices[t] == 0.0:
                raise ValueError  # is this an error condition? will be a spike somewhere in the deltas if so

            if target_data.data[stk][data_index][volumetag] != 'NA':
                wd.volumes[t] = target_data.data[stk][data_index][volumetag]
            # neural net inputs, delta prices for each stock normalized to target stock price
            # moving averages
            if has_sma10:
                sma10.append(wd.prices[t])
                if len(sma10) > 10:
                    sma10.remove(sma10[0])

            if has_sma30:
                sma30.append(wd.prices[t])
                if len(sma30) > 30:
                    sma30.remove(sma30[0])

            # target data
            lb = 1 #number of days we do the delta price over
            cumCols = 0
            tf_index = cumCols
            if data_index < len(target_data.data[stk]) and data_index - lb - 1 >= 0:
                # % change from lookback day to this day
                lb_price = target_data.data[stk][data_index][closetag]
                prev_price = target_data.data[stk][data_index - lb][closetag]
                this_stock_delta = lb_price - prev_price

                if prev_price != 0.0:
                    wd.tf_inputs[t][tf_index] = 100.0 * (this_stock_delta / lb_price)
                else:
                    wd.tf_inputs[t][tf_index] = 0.0
            else:
                wd.tf_inputs[t][tf_index] = 0.0

            # cap
            if math.fabs(wd.tf_inputs[t][tf_index]) > model.CapDelta:
                wd.tf_inputs[t][tf_index] = model.CapDelta * np.sign(wd.tf_inputs[t][tf_index])


            # Simple Moving averages at the end of the stack of data
            cumCols += 1
            if has_sma30:
                wd.tf_inputs[t][cumCols] =  (wd.prices[t] / np.average(sma30)) - 1.0
                cumCols = cumCols + 1
            if has_sma10:
                wd.tf_inputs[t][cumCols] =  (wd.prices[t] / np.average(sma10)) - 1.0
                cumCols = cumCols + 1

        # Average the volume data down to something that does not cause scaling issues
        if has_volume:
            tVolAvg = np.average(wd.volumes)
            if tVolAvg != 0.0:
                for t in range(len(wd.volumes)):
                    wd.tf_inputs[t][cumCols] = (wd.volumes[t] / tVolAvg) - 1.0

            cumCols = cumCols + 1

        # Average the volume data down to something that does not cause scaling issues
        if has_hloc:
            for t in range(len(wd.volumes)):
                wd.tf_inputs[t][cumCols] = (2.0 * (wd.closeprices[t] / (wd.highprices[t] + wd.lowprices[t]))) - 1.0
            cumCols = cumCols + 1

        if has_bband or has_rsi:
            import pandas
            import ta
            df = pandas.DataFrame({"Price": wd.prices, "Volume": wd.volumes})

        if has_bband:
            bband = 20
            # Initialize Bollinger Bands Indicator
            indicator_bb = ta.volatility.BollingerBands(close=df["Price"], window=bband, window_dev=2)

            # Add Bollinger Bands features
            df['bb_bbh'] = indicator_bb.bollinger_hband_indicator()
            df['bb_bbl'] = indicator_bb.bollinger_lband_indicator()
            for i in range(bband):
                df['bb_bbh'][i] = 0.5
                df['bb_bbl'][i] = 0.5
            for t in range(len(wd.prices)):
                wd.tf_inputs[t][cumCols] = df['bb_bbh'][i]
                wd.tf_inputs[t][cumCols + 1] = df['bb_bbl'][i]
            cumCols = cumCols + 2

        if has_rsi:
            rsi = ta.momentum.StochRSIIndicator(close=df["Price"], window=14, smooth1=3, smooth2=3, fillna=True)
            df['rsi'] = rsi.stochrsi()
            for i in range(14):
                df['rsi'][i] = 0.5
            for t in range(len(wd.prices)):
                wd.tf_inputs[t][cumCols] = df['rsi'][i]  # / wd.prices[i]
            cumCols = cumCols + 1

        if has_obv:
            obv = ta.volume.VolumePriceTrendIndicator(close=df["Price"], volume=df["Volume"], fillna=True)
            df['obv'] = obv.volume_price_trend()
            o = np.array(df['obv'])  # value is based on volume -ve to +ve , needs to be scaled down
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            o = scaler.fit_transform(o.reshape(-1, 1))
            for t in range(len(wd.prices)):
                wd.tf_inputs[t][cumCols] = 2.0 * (o[i][0] - 0.5)
            cumCols = cumCols + 1


        #############################################
        # endregion MAIN LOOP
        #############################################
        wdall.AddMoreData(wd)
        wdall.symbols = target_data.symbols

    return wdall








# START PROGRAM
if __name__ == "__main__":
    exit(main())