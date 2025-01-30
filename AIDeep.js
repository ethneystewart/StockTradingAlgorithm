var root = "";
var approot = "../";
var grid = null;
var stocks = null;
var settings = null;
var positions = null;
var orders = null;
var count = 10;
var AutoData = null;
var totalgrid = null;
var sortkey = 'TotalPercentWin';
var totalnumofstocks = 10;
function Init()
{
    root =  approot;

    StartMainUpdate();

    window.setTimeout(GetStatus,2000);
}

function GetStatus()
{
    $.ajax({
        url: root + 'GetStatus',
        type: 'GET',
        datatype: "text",
        success: GetStatusReturn
        });
}

function GetStatusReturn(data)
{
    return;

  document.getElementById("txtResults").innerHTML = data;

  count = count - 1;
  document.getElementById("txtCount").innerHTML = count;
  if (count == 0)
  {
    count = 10;
    SetCookie();
    StartMainUpdate();
  }

  if (count == 5)
  {
     $.ajax({
        url: root + 'GetIBStatus',
        type: 'GET',
        datatype: "text",
        success: GetIBStatusReturn
        });
  }

  window.setTimeout(GetStatus,2000);
}

function StartMainUpdate()
{

 //Daisy chain of calls to get stock positions, and then all the current predictions
    $.ajax({
        url: root + 'GetDeepDatabaseTables',
        type: 'GET',
        datatype: "text",
        success: GetDBTablesReturn
        });
}

function GetDBTablesReturn(data)
{
    try {
       GetTableReturn(data);
    }
    catch{}

    GetCookie();

    if (document.getElementById("ddTable").selectedIndex < 0)
        document.getElementById("ddTable").selectedIndex = 0;

    $.ajax({
        url: root + 'GetPositions',
        type: 'GET',
        datatype: "text",
        success: GetPositionsReturn
        });
}

function GetTableReturn(data) {
    //List of database tables available to read has been returned, add to dropdown
    document.getElementById("ddTable").innerHTML = '';
    var tbls = JSON.parse(data);
    tbls.forEach(AddTable);

    if (get("table")){
        document.getElementById("ddTable").value = get("table");
        GetResults();
        }

}

function GetPositionsReturn(data)
{
    try {
        positions = JSON.parse(data);
    }
    catch{}
    $.ajax({
        url: root + 'GetOrders',
        type: 'GET',
        datatype: "text",
        success: GetOrdersReturn
        });
}

function GetOrdersReturn(data)
{
  var maindir = document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;

    try {
    orders = JSON.parse(data);
    }
    catch{}

    $.ajax({
        url: root + 'GetTradeSettings?maindir=' + maindir,
        type: 'GET',
        datatype: "text",
        success: GetTradeSettingsReturn
        });


}

function GetTradeSettingsReturn(data)
{
    AutoData = JSON.parse(data);

    //document.getElementById("txtDMFilter").value = AutoData.FilterDM;
    //document.getElementById("txtRMSFilter").value = AutoData.FilterRMS;
    //document.getElementById("txtDeltaFilter").value = AutoData.FilterDelta;
    document.getElementById("txtTradeScore").value = AutoData.MinTradeScore;
    document.getElementById("txtMaxModels").value = AutoData.MaxModels;
    document.getElementById("txtMinModels").value = AutoData.MinModels;
    //document.getElementById("txtRepeats").value = AutoData.TrainRepeats;
    //document.getElementById("txtGlobalRepeats").value = AutoData.TrainGlobal;

    document.getElementById("txtEnabled").value =  AutoData.Enabled;
    document.getElementById("txtFakeTrading").value =   AutoData.FakeTrading;
    document.getElementById("txtOnlyLong").value =   AutoData.OnlyLong;
    document.getElementById("txtCloseTrades").value =   AutoData.CloseTrades;
    document.getElementById("txtStopLoss").value =   AutoData.StopLoss;
    document.getElementById("txtOrderSize").value =   AutoData.OrderSize.toFixed(0);
    document.getElementById("txtMaxTrades").value =   AutoData.MaxTrades.toFixed(0);
    document.getElementById("txtCloseTime").value =   AutoData.CloseTime;
    //document.getElementById("txtPredictTime").value =   AutoData.PredictTime;
    //document.getElementById("txtUpdateTime").value =   AutoData.UpdateTime;
    document.getElementById("txtTradeTime").value =   AutoData.TradeTime;
    document.getElementById("txtTrainTime").value =   AutoData.TrainTime;
    //document.getElementById("txtMarketPrices").value =   AutoData.MarketPrices;


    GetScannerData();
}

function GetScannerData()
{
    var maindir = document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;
    //Get the list of available data base tables
    var minmodels = document.getElementById("txtMinModels").value;
    var maxmodels =  document.getElementById("txtMaxModels").value;
    var mintradescore = document.getElementById("txtTradeScore").value;
    $.ajax({
        url: root + 'GetScannerData?maindir=' + maindir + "&minmodels=" + minmodels + "&maxmodels=" + maxmodels +"&mintradescore=" + mintradescore + "&sortkey=" + sortkey ,
        type: 'GET',
        datatype: "text",
        success: GetScannerDataReturn
        });
}

function GetScannerDataReturn(data)
{
    data = data.replace("NaN", "0.0");
    grid = JSON.parse(data);

    var maindir = document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value; // should i be changing this line??
    //Get the list of available data base tables
    var minmodels = document.getElementById("txtMinModels").value;
    var maxmodels =  document.getElementById("txtMaxModels").value;
    var mintradescore = document.getElementById("txtTradeScore").value;
    $.ajax({
        url: root + 'GetTotalData?maindir=' + maindir + "&minmodels=" + minmodels + "&maxmodels=" + maxmodels +"&mintradescore=" + mintradescore + "&totalnumofstocks=" + totalnumofstocks,
        type: 'GET',
        datatype: "text",
        success: GetTotalDataReturn
        });
}
function GetTotalDataReturn(data)
{
    data = data.replace("NaN", "0.0");
    totalgrid = JSON.parse(data);

    UpdateTraderTable();

}


function GetIBStatusReturn(data)
{
    document.getElementById("tdStatus").innerHTML = data;
}


function UpdateTraderTable()
{
    //Pods should already be set
    var maxcol = 9;
    var dmodels = parseInt(document.getElementById("txtMinModels").value);
    var justActive = document.getElementById("chkJustActive").checked;
    var tradeScoreThresh = parseFloat(document.getElementById("txtTradeScore").value);
    var sheader = "<table class='pTable'>";
    //s += "<tr><td>Stock</td>";

    //for (var i=0; i < maxcol; i++)
       //s += "<td style='color:blue' title='" + "indicator" + "'>" + i.toFixed(0) +"</td>" ;
    sheader += "<td style='color:blue'>" + "STOCKS" + "</td>";
    sheader += "<td style='color:blue'>" + "INDICATORS" + "</td>";
    sheader += "<td style='color:blue'>" + "CORRELATION" + "</td>";
    sheader += "<td style='color:blue'>" + "PERCENT WIN (%)" + "</td>";
    sheader += "<td style='color:blue'>" + "PROFIT($)" + "</td>";
    sheader += "<td style='color:blue'>" + "DEEP COUNT" + "</td>";
    sheader += "<td style='color:blue'>" + "ACTUAL COUNT" + "</td>";
    sheader += "<td style='color:blue'>" + "SIMULATE COUNT" + "</td>";
    sheader += "<td style='color:blue'>" + "DEEP PERCENT WIN(%)" + "</td>";
    sheader += "<td style='color:blue'>" + "DEEP PROFIT($)" + "</td>";
    sheader += "<td style='color:blue'>" + "DEEP HOLD PROFIT ($)" + "</td>";
    //s += "<td style='color:'>" + "Actions<br/>"
    //s += "<span class='smallstock' style='margin-left: 4px;; font-size: 15px'   id='btnTradeAll' onclick='TradeAll();'>&nbsp;Trade Now</span><span class='smallstock' style='margin-left: 4px;' onclick='CloseAll();'>Close ALL</span>" + "</td>";
    sheader += "</tr>";





    var srs = new Array();

    for (var stk=0; stk < grid.Stocks.length; stk++)
    {
        if (grid.Stocks[stk].Indicators.length < dmodels)
        {
            continue
        }
        if( grid.Stocks[stk].TotalPercentWin <= 50)
        {
            clr = "red"
        }
        else if (grid.Stocks[stk].TotalPercentWin >= 60 && grid.Stocks[stk].TotalPercentWin < 70)
        {
            clr = "green"
        }
        else if (grid.Stocks[stk].TotalPercentWin < 60 && grid.Stocks[stk].TotalPercentWin > 50)
        {
            clr = "#FF7D33"
        }
        else
        {
            clr = "#9700FF"
        }
         clr2 = grid.Stocks[stk].TotalProfit< 0.0 ? "red" : "green";
         clr2 = grid.Stocks[stk].TotalProfit == 0.0 ? "black" : clr2;
         name = grid.Stocks[stk].Symbol;
         var sr = "";
         sr += "<td style='text-decoration:underline; color:#F60077' onclick='ClickStock(\"" + grid.Stocks[stk].Symbol + "\");'>" + grid.Stocks[stk].Symbol + "</td>";
         sr += "</td><td>" + grid.Stocks[stk].NumOfIndicators + "</td><td></td><td></td><td></td><td></td><td>" + grid.Stocks[stk].ActualCount + "</td>";
         if (totalgrid.StkCount[name] != undefined){
         sr += "<td>" + totalgrid.StkCount[name] + "</td>";
         }
         else{
          sr += "<td></td>";
         }
         sr += "<td style='color:" + clr + "'>"+ grid.Stocks[stk].TotalPercentWin.toFixed(2)  + "</td><td style='color:" +clr2 + "'>" + grid.Stocks[stk].TotalProfit.toFixed(2) + "</td><td>";
         sr += grid.Stocks[stk].TotalDeepProfit.toFixed(2) + "</td></tr>";

        for (var key=0; key < maxcol; key++)
        {

            if (document.getElementById("chkJustActive").checked)
            {
                continue;
            }
            if (key < grid.Stocks[stk].Indicators.length)
            {
                 sr += "<tr><td></td><td>";
                 sr += grid.Stocks[stk].Indicators[key].Symbol
                 sr += "</td><td>" + grid.Stocks[stk].Indicators[key].Correlation.toFixed(3) + "</td><td>"
                 sr += grid.Stocks[stk].Indicators[key].PercentWin.toFixed(2) +"</td><td>"
                 sr += grid.Stocks[stk].Indicators[key].Profit.toFixed(2) +"</td><td>"
                 sr += grid.Stocks[stk].Indicators[key].DeepCount.toFixed(2) +"</td><td>"
                 sr += grid.Stocks[stk].Indicators[key].ActualCount +"</td><td></td><td>"
                 sr += grid.Stocks[stk].Indicators[key].DeepPercentWin.toFixed(2) +"</td><td>"
                 sr += grid.Stocks[stk].Indicators[key].DeepProfit.toFixed(2) +"</td><td>"
                 sr += grid.Stocks[stk].Indicators[key].DeepHoldProfit.toFixed(2) +"</td>"
                 //sr += grid.Stocks[stk].Indicators[key].TradeScore.toFixed(3) +"</td>"
                 sr += "</tr>";



            }
        }

        var obsr = new Object();
        obsr.Score = totalgrid.StkCount[name] ;
        obsr.Row = sr;
        srs.push(obsr);

    }

  //Sort the rows by score and add to ui
    if (srs){
        srs.sort((a, b) => (a.Score > b.Score) ? -1 : 1)

    }

    var st = "";
    st += "<tr style = 'background-color:#CECECE;'><td><strong>"+ "SIMULATE:" + "</td></strong><td></td><td></td><td>";
    st += "</td><td></td><td></td><td></td><td>" + totalgrid.ActualCount + "</td><td>";
    st += totalgrid.AvgPctWin.toFixed(2) + "</td><td>";
    st += totalgrid.AvgProfit.toFixed(2) + "</td><td>";
    st += totalgrid.AvgDeepProfit.toFixed(2) + "</td></tr>";
    sheader += st;
    srs.forEach(function(entry) {
        sheader += entry.Row;
    });
    sheader += "</table>";
    document.getElementById("tableResults").innerHTML = sheader;
    }


function GroupPredict(){
     var group_path =  document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;

     document.getElementById("txtResults").innerHTML = "Predict Started";
     $.ajax({
            url: root + 'ScannerTrain?maindir=' + group_path ,
            type: 'GET',
            datatype: "text",
            success: GroupPredictReturn
            });

}

function GroupPredictReturn(data)
{
    GetScannerData();
}

function TradeAll()
{
     var group_path =  document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;

     document.getElementById("txtResults").innerHTML = "Trade Started";
     $.ajax({
            url: root + 'ScannerTrade?maindir=' + group_path ,
            type: 'GET',
            datatype: "text",
            success: GroupTradeReturn
            });
}

function GroupTradeReturn(data)
{
    GetScannerData();
}


function get(name){
   if(name=(new RegExp('[?&]'+encodeURIComponent(name)+'=([^&]*)')).exec(location.search))
      return decodeURIComponent(name[1]);
}

function AddTable(t)
{   //after reading a DB table , put it on the list
        select = document.getElementById("ddTable");
        var opt = document.createElement('option');
        opt.value = t;
        opt.innerHTML = t;
        select.appendChild(opt);
}
function CreateStripChart(ctx, ctxdata, symbol){

    var ctxlabels = new Array();
     for (var stk=0; stk < ctxdata.length; stk++)
        ctxlabels[stk] = stk;

        var myChart = new Chart(ctx, {
    type: 'line',
    data: {
    labels: ctxlabels,
    datasets: [{
        data: ctxdata,
        label: symbol,
        borderColor: "#3e95cd",
        fill: false
      }
    ]
  },
  options: {
    title: {
      display: false,
      text: 'World population per region (in millions)'
    }
  }
      });
}
function UpdateAutoData()
{

    //AutoData.FilterDM = parseFloat(document.getElementById("txtDMFilter").value);
    //AutoData.FilterRMS = parseFloat(document.getElementById("txtRMSFilter").value);
    //AutoData.FilterDelta = parseFloat(document.getElementById("txtDeltaFilter").value);
    AutoData.MinTradeScore = parseFloat(document.getElementById("txtTradeScore").value);
    AutoData.MaxModels = parseInt(document.getElementById("txtMaxModels").value);
    AutoData.MinModels = parseInt(document.getElementById("txtMinModels").value);
    //AutoData.TrainRepeats = parseInt(document.getElementById("txtRepeats").value);
    //AutoData.TrainGlobal = parseInt(document.getElementById("txtGlobalRepeats").value);

    AutoData.Enabled = parseInt(document.getElementById("txtEnabled").value);
    AutoData.FakeTrading = parseInt(document.getElementById("txtFakeTrading").value);
    AutoData.OnlyLong = parseInt(document.getElementById("txtOnlyLong").value);
    AutoData.CloseTrades = parseInt(document.getElementById("txtCloseTrades").value);
    AutoData.StopLoss = parseInt(document.getElementById("txtStopLoss").value);
    AutoData.OrderSize = parseInt(document.getElementById("txtOrderSize").value);
    AutoData.MaxTrades = parseInt(document.getElementById("txtMaxTrades").value);
    AutoData.CloseTime = document.getElementById("txtCloseTime").value;
    //AutoData.PredictTime = document.getElementById("txtPredictTime").value;
    //AutoData.UpdateTime = document.getElementById("txtUpdateTime").value;
    AutoData.TradeTime =document.getElementById("txtTradeTime").value;
    AutoData.TrainTime =document.getElementById("txtTrainTime").value;
    //AutoData.MarketPrices =document.getElementById("txtMarketPrices").value;
    var maindir = document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;

    var autoJson = JSON.stringify(AutoData);
    $.ajax({
        url: root + 'UpdateTradeSettings?maindir=' + maindir,
        type: 'POST',
        datatype: "text",
        data: autoJson,
        contentType: "text/plain",
        success: GetScannerData
    });

}

function ClickStock(sym)
{
    window.open("AIStock.html?symbol=" + sym)
}

function GridTrain()
{
    if (r > pods.length)
        return;

     var maindir =  document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;
     var pod_name = pods[r].Name;
     $.ajax({
            url: root + 'GridTrain?maindir=' + maindir ,
            type: 'GET',
            datatype: "text",
            success: GridTrainReturn
            });

}

function GridTrainReturn(data)
{
    document.getElementById("txtResults").innerHTML = "Training Started: " +  data;
}


function GridTrade()
{
    var group_path = document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;

    document.getElementById("txtResults").innerHTML = "Trade All Started";
     $.ajax({
            url: root + 'GridTrade?maindir=' + group_path,
            type: 'GET',
            datatype: "text",
            success: GridTradeReturn
            });
}
function GridTradeReturn(data)
{
    document.getElementById("txtResults").innerHTML = "Trade All Started: " +  data;
}

function CloseAll()
{
    $.ajax({
            url: root + 'ClosePosition?symbol=' + "ALLSTOCKS",
            type: 'GET',
            datatype: "text",
            success: DoNothing
            });
    document.getElementById("txtResults").innerHTML = "Close Position Sent: " + "ALLSTOCKS";

}

function OpenPosition(symbol, lastprice,  con)
{
    var quant = eval(document.getElementById("txtOrderSize").value);

    if (lastprice == 0.0)
    {
        document.getElementById("txtResults").innerHTML = "NO LAST PRICE FOR " + symbol + ": NO TRADE";
        return;
    }

    quant = Math.round((quant / lastprice)/50.0) * 50
    if (quant == 0)
        quant = 20;
    if (con < 0.0)
         quant *= -1;

    $.ajax({
            url: root + 'OpenPosition?symbol=' + symbol + "&quant=" + quant,
            type: 'GET',
            datatype: "text",
            success: DoNothing
            });
    document.getElementById("txtOpenClose_" + symbol).innerHTML = "Opening...";
    document.getElementById("txtResults").innerHTML = "Open Position Sent: " + symbol;
}

function ClosePosition(symbol)
{

    $.ajax({
            url: root + 'ClosePosition?symbol=' + symbol,
            type: 'GET',
            datatype: "text",
            success: DoNothing
            });
    document.getElementById("txtOpenClose_" + symbol).innerHTML = "Closing...";
    document.getElementById("txtResults").innerHTML = "Close Position Sent: " + symbol;
}

function DoNothing(data){}


function GridPredict(){
     var group_path =  document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;

     document.getElementById("txtResults").innerHTML = "Predict Started";
     $.ajax({
            url: root + 'GridPredict?maindir=' + group_path,
            type: 'GET',
            datatype: "text",
            success: StartPredictReturn
            });

}

function GridPredictReturn(data)
{
 document.getElementById("txtResults").innerHTML = "Predict Finished";
}


function RunCancel()
{
    $.ajax({
        url: root + 'Cancel',
        type: 'GET',
        datatype: "text",
        success: CancelReturn
        });
}
function CancelReturn(data)
{
    document.getElementById("txtResults").innerHTML = data;
    ScanPods();
}


function GetCookie()
{
    if (getCookie("traderdata"))
    {
        ck = JSON.parse(getCookie("traderdata"));
        document.getElementById("ddTable").value = ck.MainDir;
        if (ck.JustActive)
            document.getElementById("chkJustActive").checked = ck.JustActive;

    }
}

function SetCookie()
{
    ck = new Object();
    ck.MainDir =  document.getElementById("ddTable").options[document.getElementById("ddTable").selectedIndex].value;
    //ck.DMFilter = document.getElementById("txtDMFilter").value;
    //ck.RMSFilter = document.getElementById("txtRMSFilter").value;
    //ck.DeltaFilter = document.getElementById("txtDeltaFilter").value;
    ck.JustActive = document.getElementById("chkJustActive").checked;
    ck.TradeScore = document.getElementById("txtTradeScore").value;
    jck = JSON.stringify(ck)
    setCookie("traderdata", jck, 10);
}

function setCookie(cname, cvalue, exdays) {
  var d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  var expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}


function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}


