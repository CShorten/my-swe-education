import asyncio

async def fetch_data():
    print("Fetching data...")
    await asyncio.sleep(2)  # Simulates a network operation
    return "Data received"

async def main():
    result = await fetch_data()  # Wait for fetch_data to complete
    print(result)

# Run the coroutine
asyncio.run(main())
