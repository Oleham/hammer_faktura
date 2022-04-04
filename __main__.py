import sys
from .hfdb import invoicesToCSV, table, printInvoices, addBank, addClient, addItem
from sqlite3 import IntegrityError, OperationalError
from . import str_to_ts

ARGS = sys.argv[1:]

def confirm_add(ARGS):
    inp = input(f"Type Y to add {ARGS[0]} (Y)\n")
    if inp == "y" or inp == "Y":
        try:
            if ARGS[0] == "client":
                addClient(ARGS[1],ARGS[2],ARGS[3],ARGS[4],ARGS[5])
            elif ARGS[0] == "bank":
                addBank(ARGS[1], ARGS[2], ARGS[3], ARGS[4])
            elif ARGS[0] == "item":
                addItem(ARGS[1])
            try:                       
                print("Added new " + str(ARGS[0]) + ": " + ", ".join(ARGS[1:]))
            # Or if there is no list, just the item dict
            except TypeError:                            
                print("Added new " + str(ARGS[0]) + ": " + str(ARGS[1]))
        except IntegrityError:
            print(f"{ARGS[0]} already exists (UNIQUE CONSTRAINT)")
    else:
        print(f"Did not add {ARGS[0]}.")



def list(tabell):
    try:
        table(tabell)
    except OperationalError:
        print(f"No table named {tabell}")

def add(ARGS):
    # CLIENT
    if ARGS[0] == "client" and len(ARGS) == 6:
            
        print(f"""
        Name: {ARGS[1]}
        Org_nr: {ARGS[2]}
        Adresse: {ARGS[3]}
        VAT rate: {ARGS[4]}
        Valuta: {ARGS[5]}
        """)
        confirm_add(ARGS)
            
    # BANK     
    elif ARGS[0] == "bank" and len(ARGS) == 5:
        print(f"""
            Konto: {ARGS[1]}
            IBAN: {ARGS[2]}
            BIC: {ARGS[3]}
            Bank: {ARGS[4]}
            """)
        confirm_add(ARGS)

    # ITEM
    elif ARGS[0] == "item" and len(ARGS) == 6 or len(ARGS) == 7:
        
        try:
            ts = str_to_ts(ARGS[1])
        except:
            print("Ikke gyldig dato. Bruk: '01.01.2001'")
            sys.exit()
        
        # Logic for optional VAT:
        if len(ARGS) == 6:
            print(f"""
            Leveringsdato: {ARGS[1]} ({ts})
            Id: {ARGS[2]}
            Beskrivelse: {ARGS[3]}
            Netto: {ARGS[4]}
            VAT: None
            Client: {ARGS[5]}
            """)
            dic = {
                "dato": ts,
                "id": ARGS[2],
                "beskrivelse": ARGS[3],
                "netto": float(ARGS[4]),
                "client": ARGS[5]
            }
            confirm_add(("item", dic))
        else:
            print(f"""
            Leveringsdato: {ARGS[1]} ({ts})
            Id: {ARGS[2]}
            Beskrivelse: {ARGS[3]}
            Netto: {ARGS[4]}
            VAT: {ARGS[5]}
            Client: {ARGS[6]}
            """)

            dic = {
                "dato": ts,
                "id": ARGS[2],
                "beskrivelse": ARGS[3],
                "netto": float(ARGS[4]),
                "vat": float(ARGS[5]),
                "client": ARGS[6]
            }
            confirm_add(("item", dic))

    else:
        print("""
        Something went wrong. Did you use the right arguments?
        python -m hammer_faktura -a bank <konto> <iban> <bic> <name>
        python -m hammer_faktura -a client <name> <org_nr> <adress> <vat> <valuta>
        python -m hammer_faktura -a item <dato> <id> <beskrivelse> <netto> [vat] <client>
        """)

def invo(args):
    if len(args) != 2:
        print("""Usage: python -m hammer_faktura -inv '01.01.2021' '31.01.2021'""")
    else:
        printInvoices(args[0], args[1])

def csv(args):
    if len(args) != 3:
        print("""Usage: python -m hammer_faktura -csv '01.01.2021' '31.01.2021' 'filename.csv'""")
    else:
        invoicesToCSV(args[0], args[1], args[2])


# Start here

if  len(ARGS) < 2 or len(ARGS) > 8:

    print("""Usage: python3 -m hammer_faktura [-l/-a] <args>

        list: -l or --list (table name in plural, i.e. "invoices")
        add: -a or --add (item, bank, client or invoice)
        print invoices: -inv or --invoices (specify time span, e.g. "01.01.2021" "02.01.2021")
        """)
else:
    if ARGS[0] == "-l" or ARGS[0] == "--list":
        list(ARGS[1])

    elif ARGS[0] == "-inv" or ARGS[0] == "--invoices":
        invo(ARGS[1:])
    
    elif ARGS[0] == "-csv" or ARGS[0] == "--csv":
        csv(ARGS[1:])

    elif ARGS[0] == "-a" or ARGS[0] == "--add":
        add(ARGS[1:])
        
        


