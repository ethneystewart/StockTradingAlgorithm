var root = "";
var approot = "../";
var stkGroup = 0
function Init()
{
    root =  approot;
    var sym = get("symbol");
    if (sym)
        document.getElementById("txtSymbol").value = sym;
    GetStockHistory(document.getElementById("txtSymbol").value);
    GetStockList(stkGroup);
}

function get(name){
   if(name=(new RegExp('[?&]'+encodeURIComponent(name)+'=([^&]*)')).exec(location.search))
      return decodeURIComponent(name[1]);
}

function ddStockGraph_onchange()
{
    var grp =  eval(document.getElementById("ddStockGraph").options[document.getElementById("ddStockGraph").selectedIndex].value);
    GetStockList(grp)
}

function UpdateGraph()
{
    var stk =  document.getElementById("txtSymbol").value;
    GetStockHistory(stk);
}

function UpdateGraphIntra()
{
    var stk =  document.getElementById("txtSymbol").value;
    GetStockHistoryIntra(stk);
}

function GetStockList(group)
{
      $.ajax({
        url: root + 'GetStocks?score=' + group,
        type: 'POST',
        contentType: "text/plain",
        success: UpdateStockList
    });
}

function ClickStock(stk)
{
    document.getElementById("txtSymbol").value = stk;
    GetStockHistory(stk);
}


function UpdateStockList(data)
{
    var tbl = "";
    data.sort();
    data.forEach(function(s)
    {
        tbl += "<span style='margin:10px' onclick='ClickStock(\"" + s + "\");'>" + s + "</span><br/>";

     });

    tbl += "";
    document.getElementById("stkList").innerHTML = tbl;
}

function GetGridData(symbol)
{
     var stk =  document.getElementById("txtSymbol").value;
     $.ajax({
             url: root + 'GetStockHistory?symbol=' + stk,
             type: 'GET',
             success: GetGridReturn
            });
}
function GetGridReturn(data)
{
   if(data)
        var parts = data.split("|");
        var jdata = JSON.parse(parts[0]);
        GridData(jdata);
}

function GetStockHistory(symbol)
{
     $.ajax({
             url: root + 'GetStockHistory?symbol=' + symbol,
             type: 'GET',
             success: GetStockHistoryReturn
            });
}

function GetStockHistoryReturn(data)
{
    var parts = data.split("|");
    var jdata = JSON.parse(parts[0]);
    CreatePriceChart(document.getElementById("chart"), document.getElementById("txtSymbol").value, jdata);
    document.getElementById("grid").innerHTML = "";
    var rtime = JSON.parse(parts[1]);
    document.getElementById("quote").innerHTML = rtime.close + " (" + (rtime.close - rtime.previousClose).toFixed(2) + ")";
}

function GetStockHistoryIntra(symbol)
{
     $.ajax({
             url: root + 'GetStockHistoryIntra?symbol=' + symbol,
             type: 'GET',
             success: GetStockHistoryIntraReturn
            });
}

function GetStockHistoryIntraReturn(data)
{
    var jdata = JSON.parse(data);
    CreatePriceChartIntra(document.getElementById("chart"), document.getElementById("txtSymbol").value, jdata);
    document.getElementById("grid").innerHTML = "";
   // var rtime = JSON.parse(parts[1]);
    //document.getElementById("quote").innerHTML = rtime.close + " (" + (rtime.close - rtime.previousClose).toFixed(2) + ")";
}

function GridData(data)
{
    var dl = data.length;
    var s = "<br/><hr/><table>";
    s += "<tr><th></th><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>AdjClose</th></tr>";
    for (var i=dl - 1; i >= 0; i--){
        s += "<tr>";
        s += "<td>"  +  (dl - i) + "</td>";
        s += "<td>"  +  data[i].date + "</td>";
        s += "<td>"  +  data[i].open.toFixed(2) + "</td>";
        s += "<td>"  +  data[i].high.toFixed(2) + "</td>";
        s += "<td>"  +  data[i].low.toFixed(2) + "</td>";
        s += "<td>"  +  data[i].close.toFixed(2) + "</td>";
        s += "<td>"  +  data[i].adjusted_close.toFixed(2) + "</td>";
        s += "</tr>"
    }
    s += "</table>";
    document.getElementById("grid").innerHTML = s;
}

function CreatePriceChartIntra(target, symbol,  data) {

    if (!data)
        return;

    var ohlc = [];
    //var dl = data.open.keys.length;
    var i = 0;
    for (key in data.open){

        ohlc.push([
            data.date[i],
            data.open[i],
            data.high[i],
            data.low[i],
            data.close[i]

        ])
        i += 1;
    }



    Highcharts.stockChart(target, {
        chart: {
            zoomType: 'x',
        },
        rangeSelector: {
            selected: 1
        },
        xAxis: {
            type: 'datetime',
        },
        yAxis: {
            title: {
                text: symbol
            }
        },
         title: {
        text: symbol
        },
        legend: {
            enabled: false
        },
        series: [
            {
                type: 'ohlc',
                name: symbol,
                data: ohlc,

            }

        ]
    });

}

function CreatePriceChart(target, symbol,  data) {

    if (!data)
        return;

    var ohlc = [];
    var dl = data.length;
    for (var i=0; i < dl; i++){
        ohlc.push([
            new Date(data[i].date).getTime(),
            data[i].open,
            data[i].high,
            data[i].low,
            data[i].close,
            data[i].adjusted_close
        ])
    }



    Highcharts.stockChart(target, {
        chart: {
            zoomType: 'x',
        },
        rangeSelector: {
            selected: 1
        },
        xAxis: {
            type: 'datetime',
        },
        yAxis: {
            title: {
                text: symbol
            }
        },
         title: {
        text: symbol
        },
        legend: {
            enabled: false
        },
        series: [
            {
                type: 'ohlc',
                name: symbol,
                data: ohlc,

            }

        ]
    });

}
