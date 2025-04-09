# Rabbit/test_agent.py  


import asyncio
import signal
from rabbit_sdk import RabbitAgent
from rabbit_sdk.utils import wait_for_enter


async def main():
    agent = RabbitAgent(
        browser_type="chromium",
        headless=False,
        profile_dir=".rabbit_profile"
    )

    try:
        results = await agent.run_task(
            session_id="test_session",
            task="Scrape OpenAI Homepage",
            urls=["https://www.ycombinator.com/jobs"] 
        )

        for url, data in results.items():
            print(f"\n=== {url} ===")
            if "error" in data:
                print("Error:", data["error"])
            else:
                print("Title:", data["title"])
                print("Content preview:", data["html"][:300])

        await wait_for_enter()

    except Exception as e:
        print("❌ Error occurred during scraping:", e)


def run_main():
    """Safe entry point for VSCode/Linux with proper event loop cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))

    try:
        loop.run_until_complete(main())
    finally:
        if not loop.is_closed():
            loop.run_until_complete(asyncio.sleep(0.1))
            loop.close()


async def shutdown(loop):
    """Cleanly shut down async tasks and event loop."""
    tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


if __name__ == "__main__":
    run_main()
