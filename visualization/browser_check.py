"""Check the static UI with installed Chrome and optional local aiohttp tooling.

python3 -m visualization.browser_check --chrome '/path/to/Google Chrome'
"""
import argparse
import asyncio
import base64
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


async def check(command, profile, screenshot, width):
    # Optional local QA tooling already installed on this machine; not an app dependency.
    import aiohttp

    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with asyncio.timeout(40):
            port_file = profile / "DevToolsActivePort"
            while not port_file.exists():
                if process.poll() is not None:
                    raise RuntimeError(f"Chrome exited before startup: {process.returncode}")
                await asyncio.sleep(.05)
            port = port_file.read_text().splitlines()[0]
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{port}/json/list") as response:
                    pages = await response.json()
                page = next(page for page in pages if page["type"] == "page")
                async with session.ws_connect(page["webSocketDebuggerUrl"]) as socket:
                    sequence = 0

                    async def cdp(method, params):
                        nonlocal sequence
                        sequence += 1
                        await socket.send_json({"id": sequence, "method": method, "params": params})
                        async for message in socket:
                            result = json.loads(message.data)
                            if result.get("id") == sequence:
                                if "error" in result:
                                    raise RuntimeError(str(result["error"]))
                                return result["result"]
                        raise RuntimeError("Browser disconnected")

                    await cdp("Emulation.setDeviceMetricsOverride", {"width": width, "height": 1600, "deviceScaleFactor": 1, "mobile": False})
                    expression = "JSON.stringify({status:document.getElementById('browser-check-results')?.dataset.status,report:document.getElementById('browser-check-results')?.textContent})"
                    while True:
                        result = await cdp("Runtime.evaluate", {"expression": expression, "returnByValue": True})
                        value = json.loads(result["result"].get("value", "{}"))
                        if value.get("status"):
                            print(value["report"])
                            break
                        await asyncio.sleep(.1)
                    if screenshot:
                        await cdp("Runtime.evaluate", {"expression": "document.getElementById('browser-check-results').hidden=true;window.scrollTo(0,0)"})
                        result = await cdp("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
                        screenshot.write_bytes(base64.b64decode(result["data"]))
                    await cdp("Browser.close", {})
                    return value["status"] == "passed"
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="spider-browser-check-") as directory:
        temp = Path(directory)
        source = (ROOT / "visualization" / "experiments.html").read_text()
        base = (ROOT / "visualization").as_uri() + "/"
        source = source.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><base href="{base}">')
        script = (ROOT / "visualization" / "tests" / "browser_checks.js").as_uri()
        source = source.replace('</head>', f'<script defer src="{script}"></script></head>')
        page = temp / "check.html"
        page.write_text(source)
        profile = temp / "profile"
        command = [str(args.chrome), "--headless=new", "--no-first-run", "--no-default-browser-check",
                   "--disable-background-networking", "--disable-extensions", "--allow-file-access-from-files",
                   "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
                   f"--user-data-dir={profile}", f"--window-size={args.width},1600"]
        command.append(page.as_uri())
        if not asyncio.run(check(command, profile, args.screenshot, args.width)):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
