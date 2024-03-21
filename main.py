import aiohttp
import asyncio
import platform
from datetime import datetime, timedelta


class HttpError(Exception):
    pass


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))


async def main(index_day):
    d = datetime.now() - timedelta(days=int(index_day))
    shift = d.strftime("%d.%m.%Y")
    try:
        response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}')
        return response
    except HttpError as err:
        print(err)
        return None


def list_currency(new_currency):
    list_currency_name = ["EUR", "USD",new_currency]
    currency_exchange = {'sale': None, 'purchase': None}
    currency_exchange_name = {}
    for currency_name in list_currency_name:
        for currency in r['exchangeRate']:
            if currency_name in currency["currency"]:
                currency_exchange['sale'] = currency["saleRateNB"]
                currency_exchange['purchase'] = currency["purchaseRateNB"]
                currency_exchange_name[currency_name] = currency_exchange
                break
    return currency_exchange_name


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    index = int(input("Введіть протягом скількох останніх днів вас цікавить курс: "))
    if 0 <= index <=10:
        is_new_currency = input("Чи хочете ви дізнатись курс валют крім EUR та USD (Y/N): ")
        if is_new_currency == "Y":
            new_currency_name = input("Виберіть з наявних CHF, GBP, PLZ, SEK, CAD: ")
        else:
            new_currency_name = "_"

        for i in range(index):
            r = asyncio.run(main(i))
            now = datetime.now()
            a = {r["date"]: list_currency(new_currency_name)}
            # lst.append(a)
            print(a)
    else:
        print("Майте совість введіть значення від 0 до 10")
