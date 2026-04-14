

import asyncio

async def main():
    print("Hello, world!")
    await asyncio.sleep(1)
    print("Goodbye, world!")
    print("Current event loop:", id(loop))

# Create a new event loop
loop = asyncio.new_event_loop()
print("loop:", id(loop))
# Do not set default event loop; run async function directly using loop
print("Running without setting default event loop:")
loop.run_until_complete(main())

# # Try to get the current event loop; this may cause issues
# try:
#     current_loop = asyncio.get_event_loop()
#     print("Current event loop without setting:", current_loop)
# except RuntimeError as e:
#     print("Error when getting event loop without setting:", e)
#
# # The correct approach is to set the default event loop
# asyncio.set_event_loop(loop)
# print("\nRunning with setting default event loop:")
# loop.run_until_complete(main())
#
# # Now getting the current event loop is correct
# current_loop = asyncio.get_event_loop()
# print("Current event loop after setting:", current_loop)
#
# # Finally, close the event loop
# loop.close()
