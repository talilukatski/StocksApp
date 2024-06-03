from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from .models import Investor
from .models import Company
from .models import Stock
from .models import Buying
from .models import Transactions
from django.db import connection
from datetime import datetime

def dictfetchall(cursor):
    # Returns all rows from a cursor as a dict '''
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def index(request):
    return render(request, 'index.html')

def query_results(request):
    with connection.cursor() as cursor:
        cursor.execute("""
                        SELECT I.Name, D.TotalSum
                        FROM Investor I INNER JOIN DiversEInvestors D ON I.ID = D.ID
                        ORDER BY D.TotalSum DESC;
                        """)
        sql_res1 = dictfetchall(cursor)
        cursor.execute("""
                        SELECT I.Name, S.Symbol, S.AmountOfStocks
                        FROM StocksBuyers S INNER JOIN Investor I ON S.ID = I.ID
                        WHERE AmountOfStocks = (
                            SELECT MAX(S1.AmountOfStocks)
                            FROM StocksBuyers S1
                            WHERE S.Symbol = S1.Symbol
                            GROUP BY S1.Symbol
                        )
                        ORDER BY S.Symbol, I.Name;
                        """)
        sql_res2 = dictfetchall(cursor)
        cursor.execute("""
                        SELECT P.Symbol, COUNT(B.ID) AS AmountOfInvestors
                        FROM ProfitableCompany P LEFT OUTER JOIN Buying B ON B.tDate = P.FirsttDate AND
                                B.Symbol = P.Symbol
                        GROUP BY P.Symbol
                        ORDER BY P.Symbol;
                        """)
        sql_res3 = dictfetchall(cursor)
    return render(request, 'query_results.html', {'sql_res1': sql_res1,
                                                  'sql_res2': sql_res2, 'sql_res3': sql_res3})


def add_transaction(request):
    idErrorFlag = False
    dateErrorFlag = False

    if request.method == 'POST' and request.POST:
        id = request.POST["id"]
        idExists = Investor.objects.filter(id=id).exists()

        if idExists == False:
            idErrorFlag = True

        else:
            idErrorFlag = False
            today = Stock.objects.order_by('tdate').last().tdate
            lastDate = Transactions.objects.filter(tdate=today, id=id).exists()

            if lastDate == True:
                dateErrorFlag = True
            else:
                dateErrorFlag = False
                transaction_sum = int(request.POST["transaction_sum"])
                investorid = Investor.objects.get(id=id)
                Investor.objects.filter(id=id).update(amount=transaction_sum+investorid.amount)
                Transactions.objects.create(tdate=today, id=investorid, tamount=transaction_sum)

    with connection.cursor() as cursor:
        cursor.execute("""
                        SELECT TOP 10 T.tDate, T.ID, T.TAmount
                        FROM Transactions T
                        ORDER BY T.tDate DESC, T.ID DESC;       
                                """)
        sql_res = dictfetchall(cursor)

    return render(request, 'add_transaction.html', {"idErrorFlag": idErrorFlag, "dateErrorFlag": dateErrorFlag,
                                                    "sql_res": sql_res})


def buy_stocks(request):
    idErrorFlag = False
    dateErrorFlag = False
    companyErrorFlag = False
    sufficientFundsErrorFlag = False

    if request.method == 'POST' and request.POST:
        id = request.POST["id"]
        quantity = int(request.POST["quantity"])
        symbol = request.POST["company"]

        idExists = Investor.objects.filter(id=id).exists()
        companyExists = Stock.objects.filter(symbol=symbol).exists()

        if idExists == False:
            idErrorFlag = True
        if companyExists == False:
            companyErrorFlag = True
        if idErrorFlag == False and companyErrorFlag == False:
            today = Stock.objects.order_by('tdate').last().tdate
            lastDate = Buying.objects.filter(tdate=today, id=id, symbol=symbol).exists()
            currentFunds = Investor.objects.get(id=id).amount
            currentPrice = quantity * Stock.objects.get(tdate=today, symbol=symbol).price
            if currentPrice > currentFunds:
                sufficientFundsErrorFlag = True
            if lastDate == True:
                dateErrorFlag = True
            if sufficientFundsErrorFlag == False and dateErrorFlag == False:
                investorid = Investor.objects.get(id=id)
                Investor.objects.filter(id=id).update(amount=investorid.amount - currentPrice)
                with connection.cursor() as cursor:
                    cursor.execute("""
                                     INSERT INTO Buying(tDate, ID, Symbol, BQuantity) VALUES (%s,%s,%s, %s);
                                    """, (today.strftime('%Y-%m-%d'), id, symbol, quantity))

    with connection.cursor() as cursor:
        cursor.execute("""
                        SELECT TOP 10 B.tDate, B.ID, B.Symbol, B.BQuantity
                        FROM Buying B 
                        ORDER BY B.tDate DESC, B.ID DESC, B.symbol;       
                                """)
        sql_res = dictfetchall(cursor)
    return render(request, 'buy_stocks.html', {"idErrorFlag": idErrorFlag,
                                                                    "companyErrorFlag": companyErrorFlag,
                                                                    "dateErrorFlag": dateErrorFlag,
                                                                    "sufficientFundsErrorFlag": sufficientFundsErrorFlag,
                                                                    "sql_res": sql_res})
