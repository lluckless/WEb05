import asyncio
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime, timedelta
import aiohttp
import platform

logging.basicConfig(level=logging.INFO)

class PrivatBankAPI:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates"

    async def fetch_exchange_rate(self, currency, date):
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}?json&date={date}"
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch data: {response.status}")
                data = await response.json()
                for rate in data['exchangeRate']:
                    if rate['currency'] == currency:
                        return rate['saleRateNB']
                raise ValueError(f"Currency {currency} not found for the specified date")


class CurrencyConverter:
    def __init__(self, api):
        self.api = api

    async def get_exchange_rate(self, currencies, days):
        exchange_rates = {}
        for currency in currencies:
            rates = {}
            for i in range(days):
                date = (datetime.today() - timedelta(days=i)).strftime('%d.%m.%Y')
                try:
                    rate = await self.api.fetch_exchange_rate(currency, date)
                    rates[date] = rate
                except ValueError as e:
                    print(f"Error fetching exchange rate for {currency} on {date}: {e}")
            exchange_rates[currency] = rates
        return exchange_rates


class Server:
    def __init__(self, converter:CurrencyConverter):
        self.clients = set()
        self.converter = converter

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

    async def exchange_command(self, currencies, days):
    # Fetch exchange rates for the specified number of days
        exchange_rates = await self.converter.get_exchange_rate(currencies, days)

    # Prepare response message
        response = f"Exchange rates for the last {days} days:\n"
        for currency, rates in exchange_rates.items():
            response += f"Exchange rates for {currency}:\n"
            for date, rate in rates.items():
                response += f"On {date}, 1 {currency} = {rate} UAH\n"
        return response

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            while True:
                message = await ws.recv()
                if message.startswith("exchange"):
                    parts = message.split()
                    if len(parts) > 1:  # Перевірка на наявність параметрів
                        days = int(parts[1])
                        currencies = parts[2:]
                        response = await self.exchange_command(currencies, days)
                        await ws.send(response)
                    else:
                        await ws.send("Error: Command format should be 'exchange <number of days> <currency1> <currency2> ...'")
                else:
                    await self.send_to_clients(f"{ws.name}: {message}")
        except websockets.exceptions.ConnectionClosedError:
            pass
        finally:
            await self.unregister(ws)

async def main():
    api = PrivatBankAPI()
    converter = CurrencyConverter(api)
    server = Server(converter)
       
    async with websockets.serve(server.ws_handler, 'localhost', 8765):
        await asyncio.Future() # run forever

    available_currencies = await api.get_available_currencies()

    # Запит користувача на введення валют
    input_currencies = input("Enter currency codes separated by comma (e.g., EUR,USD): ")
    currencies = [currency.strip().upper() for currency in input_currencies.split(',')]

    # Перевірка на наявність введених валют у списку доступних валют
    invalid_currencies = [currency for currency in currencies if currency not in available_currencies]
    if invalid_currencies:
        print(f"Error: Invalid currency codes: {', '.join(invalid_currencies)}")
        return

    days = min(int(input("Enter number of days (not more than 10): ")), 10)

    try:
        exchange_rates = await converter.get_exchange_rate(currencies, days)
        for currency, rates in exchange_rates.items():
            print(f"Exchange rates for {currency}:")
            for date, rate in rates.items():
                print(f"On {date}, 1 {currency} = {rate} UAH")
            print()
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

