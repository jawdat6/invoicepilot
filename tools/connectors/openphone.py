from datetime import date
from pathlib import Path

from .base import BaseConnector, ConnectorResult

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


class OpenPhoneConnector(BaseConnector):
    name = "OpenPhone"
    stable = False  # Playwright-based, may break on login flow changes

    def is_configured(self) -> bool:
        return self._is_set("email", "password")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")

        try:
            pw = sync_playwright()
        except (ImportError, TypeError, Exception) as e:
            if sync_playwright is None or "not installed" in str(e).lower() or isinstance(e, ImportError):
                return ConnectorResult(
                    connector=self.name, files=[], count=0, skipped=0,
                    error="Playwright not installed",
                    hint="Run: pip install playwright && playwright install chromium",
                )
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None)

        try:
            return self._download_with_playwright(pw, start, end, out_dir, period)
        except TimeoutError:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error="OpenPhone timed out after 120s",
                hint="Try again or download invoices manually from openphone.com/settings/billing",
            )
        except Exception as e:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error=str(e),
                hint="If login failed, check email/password or complete 2FA in the browser window",
            )

    def _download_with_playwright(self, pw, start: date, end: date, out_dir: Path, period: str) -> ConnectorResult:
        import os
        import shutil
        import time

        files = []
        with pw as p:
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/usr/bin/google-chrome",
                shutil.which("google-chrome") or "",
                shutil.which("chromium") or "",
            ]
            executable = next((path for path in chrome_paths if path and os.path.exists(path)), None)
            launch_kwargs = {"headless": False}
            if executable:
                launch_kwargs["executable_path"] = executable

            browser = p.chromium.launch(**launch_kwargs)
            ctx = browser.new_context(accept_downloads=True)
            page = ctx.new_page()
            page.set_default_timeout(120_000)

            page.goto("https://app.openphone.com/sign-in")
            page.wait_for_load_state("networkidle")

            page.fill('input[type="email"], input[name="email"]', self.config["email"])
            page.keyboard.press("Tab")
            time.sleep(0.5)
            page.fill('input[type="password"]', self.config["password"])
            page.click('button[type="submit"]')

            try:
                page.wait_for_url("**/app.openphone.com/**", timeout=15_000)
            except Exception:
                pass

            if "verify" in page.url or "2fa" in page.url:
                input("  2FA detected — complete it in the browser, then press Enter...")

            page.goto("https://app.openphone.com/settings/billing")
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            links = page.query_selector_all(
                'a[href*="invoice"], a[href*="receipt"], button:has-text("Download"), a:has-text("PDF")'
            )

            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    if "invoice" in href.lower() or "receipt" in href.lower():
                        with ctx.expect_download(timeout=30_000) as dl_info:
                            link.click()
                        dl = dl_info.value
                        filename = out_dir / (dl.suggested_filename or f"OpenPhone_{period}_{len(files) + 1}.pdf")
                        dl.save_as(str(filename))
                        files.append(filename)
                except Exception:
                    continue

            browser.close()

        return ConnectorResult(
            connector=self.name,
            files=files,
            count=len(files),
            skipped=0,
            error=None,
            hint=None,
        )
