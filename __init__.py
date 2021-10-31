import os, time, datetime

# Constant
HF_PATH = os.path.dirname(__file__)

class Client():

	def __init__(self, navn, org_nr, adresse, vat, valuta):
		self.navn = navn
		self.org_nr = org_nr
		self.adresse = adresse
		self.vat = vat
		self.valuta = valuta

class Bank():

	def __init__(self, konto, iban, bic, bank):
		self.konto = konto
		self.iban = iban
		self.bic = bic
		self.bank = bank

class Invoice():

	def __init__(self, id, dato, forfall, language):
		self.id = id
		self.dato = dato
		self.forfall = forfall
		self.language = language

class Generator():

	def __init__(self, invoice, client, bank, invoice_items):
		self.invoice = invoice
		self.client = client
		self.bank = bank
		self.invoice_items = invoice_items

		# The standard table row. Use it to populate the tr_elem_list
		with open(os.path.join(HF_PATH, "maler", "tr_elem_mal.html")) as f:
			self.tr_elem_mal = f.read()

		self.tr_elem_list = []
		self.netto_total = 0
		self.brutto_total = 0

		self.table = ""

		# Stylesheet
		self.css = "/".join(["..", "hammer_faktura", "maler","faktura.css"])

	def makeInvoiceBody(self):
		"""
		Creates makes item list, creates table and returns body.
		"""
		self.add_to_invoice()
		self.generate_table()
		return self.generate_body()


	def generate_body(self):
		"""
		Returns the invoice body.
		"""
		language_code = self.invoice.language.lower()

		with open(os.path.join(HF_PATH, "maler", f"fakturamal_{language_code}.html")) as f:
			fakturamal = f.read()

		with open(os.path.join(HF_PATH, "maler", "style.html")) as f:
			style = f.read()


		return fakturamal.format(
								# CSS
								style=style,
								# Client inforamsjon
								navn=self.client.navn,
								org_nr=self.client.org_nr,
								adresse=self.client.adresse,
								# Invoice information
								id=self.invoice.id, 
								dato=ts_to_str(self.invoice.dato), 
								forfall=ts_to_str(self.invoice.forfall), 
								# Table
								table=self.table,
								# Bank details
								konto=self.bank.konto,
								iban=self.bank.iban,
								bic=self.bank.bic,
								bank=self.bank.bank
								)

	def add_to_invoice(self):
		for t in self.invoice_items:
			if t["vat"]:
				vat = t["vat"]
			else:
				vat = self.client.vat

			brutto = t["netto"] * (vat + 1)

			self.tr_elem_list.append(self.tr_elem_mal\
				.format(leveringsdato=ts_to_str(t["dato"]), 
										id=t["id"], 
										beskrivelse=t["beskrivelse"], 
										netto=t["netto"], 
										vat=vat, 
										brutto=brutto))
			self.netto_total += t["netto"]
			self.brutto_total += brutto
		return

	def generate_table(self):
		"""
		Generate the table.
		"""
		language_code = self.invoice.language.lower()

		with open(os.path.join(HF_PATH, "maler", f"tabellmal_{language_code}.html")) as f:
			tabellmal = f.read()

		tabell = "\n".join(self.tr_elem_list)

		totalMVA = self.brutto_total - self.netto_total

		self.table = tabellmal.format(tabell=tabell, 
									netto=self.netto_total, 
									totalMVA=totalMVA, 
									brutto=self.brutto_total,
									valuta=self.client.valuta)

		return

def ts_to_str(timestamp):
	"""
	Converts timestamp to string.
	"""
	return  datetime.datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y")

def str_to_ts(str, endOfDay=False):
	"""
	Converts string to timestamp.
	if endOfDay, the timestamp is set to 23:59:59 of that day.
	Else, 00.00.00
	"""
	strlist = str.split(".")

	if endOfDay:
		dobj = datetime.datetime(int(strlist[2]), int(strlist[1]), int(strlist[0]), 23, 59 , 59)
	else:
		dobj = datetime.datetime(int(strlist[2]), int(strlist[1]), int(strlist[0]), 0, 0, 0)

	return int(time.mktime(dobj.timetuple()))
		


	




