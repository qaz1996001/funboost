import asyncio


async def my_coroutine():
    try:
        print("Coroutine started")
        await asyncio.sleep(10)  # Simulate a long-running task
        print("Coroutine completed")
    except asyncio.CancelledError:
        print("Coroutine was cancelled")
    finally:
        print("Cleaning up resources")


async def main():
    # Create coroutine task
    task = asyncio.create_task(my_coroutine())

    await asyncio.sleep(1)  # Wait a moment to ensure the coroutine has started
    print("Preparing to cancel coroutine")

    # Cancel coroutine
    task.cancel()

    try:
        await task  # Wait for the task to be cancelled
    except asyncio.CancelledError:
        print("Task has been cancelled")


# Run main program

asyncio.run(main())

