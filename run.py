#!/usr/bin/env python3
"""Extract expenses and invoices from freshbooks and print summary."""
from csv import DictWriter
from decimal import Decimal
from os import environ
from pathlib import Path
from argparse import ArgumentParser

from dotenv import find_dotenv, load_dotenv

from lxml import objectify
from lxml.etree import XMLSyntaxError
from refreshbooks import api


def friendly_pdf_decoder(*args, **kwargs):
    """Blabla."""
    try:
        return objectify.fromstring(*args, **kwargs)
    except XMLSyntaxError:
        return args[0]


def retrieve_invoices(date_range, c, path='Einnahmen'):
    """Retrieve all invoice, dl pdf and create csv overview."""
    def _iter():
        for invoice in invoice_response.invoices.invoice:
            def _sum_taxes():
                for line in invoice.lines.line:
                    yield (Decimal(str(line.amount)) / 100 *
                           Decimal(str(line.tax1_percent)))
            total = Decimal(str(invoice.amount))
            tax_sum = round(sum(_sum_taxes()), 2)
            date = invoice.date
            company = invoice.organization
            yield {'Datum': date,
                   'Rechnungsnummer': invoice.number,
                   'Firma': company,
                   'Betrag (Brutto)': total,
                   'Betrag (Netto)': total - tax_sum,
                   'USt 19%': tax_sum,
                   'Währung': invoice.currency_code,
                   'Empfängerland': invoice.p_country}

            pdf = c.invoice.getPDF(invoice_id=invoice.invoice_id)
            with open('{}/{}-{}.pdf'.format(path, date, company), 'wb') as fd:
                fd.write(pdf)

    invoice_response = c.invoice.list(**date_range)
    fieldnames = ('Datum', 'Rechnungsnummer', 'Firma',
                  'Betrag (Netto)', 'Betrag (Brutto)', 'USt 19%',
                  'Währung', 'Empfängerland')
    Path(path).mkdir(exist_ok=True)
    with open('{}/Übersicht.csv'.format(path), 'w') as fd:
        writer = DictWriter(fd, fieldnames=fieldnames)
        writer.writeheader()
        for line in _iter():
            writer.writerow(line)


def retrieve_expenses(date_range, c, path="Ausgaben"):
    """."""
    def _iter():
        for expense in expense_response.expenses.expense:
            total = Decimal(str(expense.amount))
            tax_sum = Decimal(str(expense.tax1_amount) or 0)
            date = expense.date
            vendor = expense.vendor
            yield {'Datum': date,
                   'Firma': vendor,
                   'Betrag (Brutto)': total,
                   'Betrag (Netto)': total - tax_sum,
                   'USt 19%': tax_sum}

            pdf = c.receipt.get(expense_id=int(str(expense.expense_id)))
            with open('{}/{}-{}.pdf'.format(path, date, vendor), 'wb') as fd:
                fd.write(pdf)

    Path(path).mkdir(exist_ok=True)
    expense_response = c.expense.list(**date_range)
    fieldnames = ('Datum',
                  'Firma',
                  'Betrag (Brutto)',
                  'Betrag (Netto)',
                  'USt 19%')
    with open('{}/Übersicht.csv'.format(path), 'w') as fd:
        writer = DictWriter(fd, fieldnames=fieldnames)
        writer.writeheader()
        for line in _iter():
            writer.writerow(line)


def main(**kwargs):
    """Go over nvoices and do stuff."""
    year = kwargs.pop('year')
    date_range = {'date_from': '{}-01-01'.format(year),
                  'date_to': '{}-12-31'.format(year)}
    try:
        c = api.TokenClient(
            environ['FRESHBOOKS_DOMAIN'],
            environ['FRESHBOOKS_TOKEN'],
            response_decoder=friendly_pdf_decoder,
            user_agent='plreport')
    except KeyError as e:
        raise ValueError(
            "FRESHBOOKS_DOMAIN and FRESHBOOKS_TOKEN must be supplied as "
            "environment variables") from e
    retrieve_invoices(date_range, c)
    retrieve_expenses(date_range, c)


if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument('--year', type=int)
    args = vars(argparser.parse_args())
    load_dotenv(find_dotenv())
    main(**args)
