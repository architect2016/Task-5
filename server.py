import asyncio
import logging
import httpx
import websockets
import names
import json
from datetime import datetime, timedelta
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


async def request(url: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code == 200:
            result = r.json()
            return result
        else:
            return "Не вийшло в мене взнати курс. Приват не відповідає:)"


async def get_exchange():
    response = await request(f'https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5')
    return str(response)


#------------------------------------------------------------------------------------------------------------------

async def get_exchange_per_day(index_day):
    try:
        d = datetime.now() - timedelta(days=int(index_day))
        shift = d.strftime("%d.%m.%Y")
        response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}')
        return response
    except Exception as e:
        return f"Помилка отримання курсу за день {index_day}: {str(e)}"


async def list_currency(r):
    list_currency_name = ["EUR", "USD"]
    currency_exchange_name = {}
    for currency_name in list_currency_name:
        for currency in r['exchangeRate']:
            if currency_name in currency["currency"]:
                currency_exchange = {'sale': currency["saleRateNB"], 'purchase': currency["purchaseRateNB"]}
                currency_exchange_name[currency_name] = currency_exchange
                break
    return str(currency_exchange_name)

    # for i in range(index):
    #     r = asyncio.run(get_exchange_per_day(i))
    #     now = datetime.now()
    #     a = {r["date"]: list_currency(new_currency_name)}
    #     print(a)

#------------------------------------------------------------------------------------------------------------------

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "exchange":
                exchange = await get_exchange()
                await self.send_to_clients(exchange)
            elif message == "Hello server":
                await self.send_to_clients("Привіт мої карапузи!")
            elif message.startswith("exchange "):
                index_day = message.split()[1]
                t = int(index_day)
                lst = []
                for i in range(t):
                    r = await get_exchange_per_day(str(i))
                    if isinstance(r, str):
                        await self.send_to_clients(r)  # Повідомлення про помилку
                    else:
                        a = {r["date"]: await list_currency(r)}
                        lst.append(a)
                await self.send_to_clients(str(lst))





            # elif message.startswith("exchange "):
            #     index_day = message.split()[1]
            #     t = int(index_day)
            #     lst = []
            #     for i in range(t):
            #         r = await get_exchange_per_day(str(i))
            #         a = {r["date"]: await list_currency(r)}
            #         lst.append(a)
            #     await self.send_to_clients(str(lst))






                # r = await get_exchange_per_day(index_day)
                # a = {r["date"]: await list_currency(r)}
                # await self.send_to_clients(str(a))
            else:
                await self.send_to_clients(f"{ws.name}: {message}")



async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
