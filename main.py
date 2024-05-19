import aiohttp
import asyncio
from datetime import datetime, timedelta


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

    async def get_exchange_rate(self, currency, days):
        exchange_rates = {}
        for i in range(days):
            date = (datetime.today() - timedelta(days=i)).strftime('%d.%m.%Y')
            try:
                rate = await self.api.fetch_exchange_rate(currency, date)
                exchange_rates[date] = rate
            except ValueError as e:
                print(f"Error fetching exchange rate for {currency} on {date}: {e}")
        return exchange_rates

async def main():
    api = PrivatBankAPI()
    converter = CurrencyConverter(api)
    
    currency = input("Enter currency code (e.g., EUR, USD): ")
    days = min(int(input("Enter number of days (not more than 10): ")), 10)

    try:
        exchange_rates = await converter.get_exchange_rate(currency, days)
        for date, rate in exchange_rates.items():
            print(f"On {date}, 1 {currency} = {rate} UAH")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())