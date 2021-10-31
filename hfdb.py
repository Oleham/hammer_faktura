"""
module HFDB (Hammer Faktura Database) contains all client-facing functions for adding to and retrieving from the database.
Functions are also used by the CLI tool.
"""

from . import sql_handler
from . import Invoice, Client, Bank, Generator, str_to_ts, ts_to_str
import time, uuid
from sqlite3 import IntegrityError

def addItem(values):
    """
    Adds an invoice item to the database.
    Arguments: dict = {"dato": int, "id": str, "beskrivelse": str, "netto": float, "client": int}
    Optional = {"vat": float}
    Returns None
    """
    values.setdefault("vat", None)

    sql = """
        INSERT INTO invoice_items (dato, id, beskrivelse, netto, vat, client)
        VALUES (:dato,:id,:beskrivelse,:netto,:vat,:client)

        """
    sql_handler.execute(sql, values)

    # Retrieve the new invoie item pk to return 
    sql = """
        SELECT pk FROM invoice_items WHERE dato=:dato AND id=:id;
        """

    return sql_handler.retrieve_one_wvalue(sql, {"dato": values["dato"], "id": values["id"]})

def addClient(navn, org_nr, adresse, vat, valuta):
    """
    Adds a client to the database.
    Arguments: navn str, org_nr str, adresse str, vat float, valuta str
    Returns primary key
    """
    values = {
        "navn": navn,
        "org_nr": org_nr,
        "adresse": adresse,
        "vat": vat,
        "valuta": valuta   
    }

    sql = """
        INSERT INTO clients (navn, org_nr, adresse, vat, valuta)
        VALUES (:navn,:org_nr,:adresse,:vat,:valuta);
        """

    sql_handler.execute(sql, values)

    # Retrieve the new client pk to return 
    sql = """
        SELECT pk FROM clients WHERE org_nr=:org_nr;
        """

    return sql_handler.retrieve_one_wvalue(sql, {"org_nr": org_nr})

def addBank(konto, iban, bic, bank):
    """
    Adds a bank to the database.
    Arguments: konto str, iban str, bic str, bank str
    Returns primary key
    """

    values = {"konto": konto,"iban": iban,"bic": bic,"bank": bank}

    sql = """
        INSERT INTO banks (konto, iban, bic, bank)
        VALUES (:konto,:iban,:bic,:bank);
        """
    sql_handler.execute(sql, values)

    sql = """
        SELECT pk FROM banks WHERE konto=:konto;
        """

    return sql_handler.retrieve_one_wvalue(sql, {"konto": konto})

def addInvoice(client, bank, dato=int(time.time()), frist=30, language="NO"):
    """
    Creates an empty invoice without any items.
    Arguments: client int, bank int, frist=30, language="NO"
    Returns invoice number
    """

    values = {"client": client, "bank": bank, "language": language, "dato": dato}

    values["id"] = uuid.uuid4().fields[1]

    values["forfall"] = int(values["dato"] + (86400 * frist))

    sql = """
        INSERT INTO invoices
        VALUES (:id,:dato,:forfall,:language,:client,:bank)
        """

    sql_handler.execute(sql, values)

    # Retrieve the new invoice number to return 
    sql = """
        SELECT id FROM invoices WHERE dato=(SELECT MAX(dato) FROM invoices) AND client=:client;
        """

    return sql_handler.retrieve_one_wvalue(sql, {"client": client})

def makeGenerator(id):
    """
    Returns all invoice information from database.
    Arguments: invoice id (str)
    Returns: (hammer_faktura.Generator)
    """

    # INVOICE!
    values = {"invoice": id}

    sql = f"""
        SELECT id, dato, forfall, language
        FROM invoices
        WHERE id=:invoice;
    """
    result = sql_handler.retrieve_multi_wvalue(sql, values)

    invoice = Invoice(result[0][0], result[0][1], result[0][2], result[0][3])
        
    # CLIENT!
    sql = f"""
        SELECT navn, org_nr, adresse, vat, valuta
        FROM clients
        WHERE pk=(SELECT client FROM invoices WHERE id=:invoice);
    """
    result = sql_handler.retrieve_multi_wvalue(sql, values)

    client = Client(result[0][0], result[0][1], result[0][2], result[0][3], result[0][4])

    # BANK!
    sql = f"""
        SELECT konto, iban, bic, bank
        FROM banks
        WHERE pk=(SELECT bank FROM invoices WHERE id=:invoice);
    """
    result = sql_handler.retrieve_multi_wvalue(sql, values)

    bank = Bank(result[0][0], result[0][1], result[0][2], result[0][3])

    # INVOICE ITEMS!
    sql = """
        SELECT dato, id, beskrivelse, netto, vat
        FROM invoice_items
        WHERE invoice=:invoice
        ORDER BY dato;
    """
    result = sql_handler.retrieve_multi_wvalue(sql, values)

    invoice_items = []
    for jobb in result:
        invoice_items.append({
            "dato": jobb[0],
            "id": jobb[1],
            "beskrivelse": jobb[2],
            "netto": jobb[3],
            "vat": jobb[4]
        })

    return Generator(invoice, client, bank, invoice_items)

def assignItemsByDate(invoice, _from, to):
    """
    Assigns all items matching the date range and client to the invoice.
    Arguments: invoice int, to str, from str. Format strings like this: "01.01.1990"
    """

    # Turn strings into timestamps
    from_ts = str_to_ts(_from)
    to_ts = str_to_ts(to, endOfDay=True)

    # Retrieve the client from the invoice
    sql = """
        SELECT client
        FROM invoices
        WHERE id = ?;
        """
    client = sql_handler.retrieve_one_wvalue(sql, (invoice,))

    # Assign all invoice items matching client and date range to the invoice.
    values = {
        "invoice": invoice,
        "from": from_ts,
        "to": to_ts,
        "client": client
    }

    sql = """
    UPDATE invoice_items
    SET invoice = :invoice
    WHERE dato BETWEEN :from AND :to AND client = :client;
    """
    sql_handler.execute(sql, values)

def assignItemByPk(invoice, pk):
    """
    Assigns a item matching the pk to the invoice.
    """

    values = {
        "invoice": invoice,
        "pk": pk
    }

    sql = """
    UPDATE invoice_items
    SET invoice = :invoice
    WHERE pk = :pk;
    """
    sql_handler.execute(sql, values)
    
def quickGeneratorFromList(items, client, bank):
    """
    Create a fast generator from a list"
    Arguments: items list, client int, bank int
    items={"dato": timestamp, "id": str, "beskrivelse": str, "netto": float}
    Returns hammer_faktura.Generator object
    """
    keys = ("dato", "id", "beskrivelse", "netto")

    for i in items:
        i["client"] = client
        for k in keys:
            if not k in i.keys():
                raise KeyError(f"The key: {k} is missing from: {i}")

    invoice = addInvoice(client, bank)
    for item in items:
        try: 
            pk = addItem(item)
            assignItemByPk(invoice, pk)
        except IntegrityError:
            print(f"Invoice item {item['id']} already exists. Skipped.")

    return makeGenerator(invoice)

def quickGeneratorFromItem(dato, id, beskrivelse, netto, client, bank):
    """
    Create a fast generator from a single item"
    Arguments: dato str, id str, beskrivelse str, netto float, client int, bank int
    Returns hammer_faktura.Generator
    """
    item = {
        "id": id,
        "beskrivelse": beskrivelse,
        "netto": netto,
        "client": client,
    }
    item["dato"] = str_to_ts(dato)

    pk = addItem(item)
    invoice = addInvoice(client, bank)
    assignItemByPk(invoice, pk)

    return makeGenerator(invoice)

def invoices(_from, to):
    """
    Retrieves the invoices between the set dates.
    Arguments: from str, to str. Format strings like this: "01.01.1990"
    """

    sql = """
    select 
        invoices.id, 
        clients.navn, 
        clients.valuta, 
        clients.vat, 
        round(sum(invoice_items.netto),2) as "netto", 
        round(sum(invoice_items.netto) * (1 + clients.vat),2) as "brutto"
    from invoices, invoice_items
    join clients on clients.pk = invoices.client
    where invoices.id = invoice_items.invoice 
    and invoices.dato between :from and :to
    group by invoice_items.invoice
    order by invoices.client
    """

    # Turn strings into timestamps
    from_ts = str_to_ts(_from)
    to_ts = str_to_ts(to, endOfDay=True)

    values = {
        "to": to_ts,
        "from": from_ts
    }

    result = sql_handler.retrieve_multi_wvalue(sql, values)

    ntotal = 0.0
    btotal = 0.0

    for i, res in enumerate(result):


        # Veldig stygg løsning for å bytte ut tuplene med EUR med tupler som har rundet opp euroen til tilnærmet kroner.
        if res[2] == "EUR":
            ny = (res[0], res[1], "EUR (* 10)", res[3], round(res[4] * 10, 2), round(res[5]*10, 2))

            res = ny
            result[i] = res
        if res[2] == "USD":
            ny = (res[0], res[1], "USD (* 8)", res[3], round(res[4] * 8, 2), round(res[5]*8, 2))

            res = ny
            result[i] = res

        ntotal += res[4]
        btotal += res[5]

    result.insert(0, ("Invoice", "Client", "Currency", "VAT", "NETTO", "BRUTTO\n")) # <-- Merk linjeskift
    result.append(("", "", "", "", "", ""))
    result.append(("TOTAL", " ", " ", " ", round(ntotal, 2), round(btotal, 2)))

    prettyPrinter(result)

def table(table):
    """
    Prints a pretty list of the named table to stdout.
    Is invoked by the "-l" flag on the CLI.
    """
    sql = f"""SELECT * FROM {table};"""
    
    prettyPrinter(sql_handler.retrieve(sql))
    

def prettyPrinter(values):
    """
    prettyPrinter prints a nice table in the CL.
    Used by the CLI.
    """
    maxwidth = [0] * (len(values[0]))

    for v in values:
        for i, l in enumerate(v):
            if len(str(l)) > maxwidth[i]:
                maxwidth[i] = len(str(l))

    for v in values:
        print(str(v[0]).ljust(maxwidth[0] + 5), end="")
        for i, l in enumerate(v[1:-1]):
            print(str(l).ljust(maxwidth[i+1] + 5), end="")
        print(str(v[-1]).rjust(maxwidth[-1] + 5))