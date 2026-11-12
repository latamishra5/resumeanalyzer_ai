"""Utility functions for webdriver setup and management (UI-agnostic)."""

import logging
import os
import platform
import subprocess
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from backend.config.settings import SCRIPTS_DIR

logger = logging.getLogger(__name__)

# Try to import various webdriver managers with fallbacks
try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.utils import ChromeType
    webdriver_manager_available = True
except ImportError:
    webdriver_manager_available = False

try:
    import chromedriver_autoinstaller
    autoinstaller_available = True
except ImportError:
    autoinstaller_available = False


def _notify(on_status, level, message):
    if on_status is not None:
        on_status(level, message)
    elif level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)


def get_chrome_version():
    """Get the installed Chrome/Chromium version"""
    system = platform.system()

    if system == "Windows":
        try:
            import winreg
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for subkey in (
                    r"Software\Google\Chrome\BLBeacon",
                    r"Software\Wow6432Node\Google\Chrome\BLBeacon",
                ):
                    try:
                        with winreg.OpenKey(hive, subkey) as key:
                            version, _ = winreg.QueryValueEx(key, "version")
                            if version:
                                return str(version).split('.')[0]
                    except OSError:
                        continue
        except Exception:
            pass

        try:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ]

            for path in chrome_paths:
                if os.path.exists(path):
                    try:
                        output = subprocess.check_output(
                            [
                                'powershell',
                                '-NoProfile',
                                '-Command',
                                f"(Get-Item -LiteralPath '{path}').VersionInfo.ProductVersion",
                            ],
                            stderr=subprocess.STDOUT,
                        )
                        version_str = output.decode('utf-8').strip()
                        if version_str:
                            return version_str.split('.')[0]
                    except Exception:
                        try:
                            output = subprocess.check_output([path, '--version'], stderr=subprocess.STDOUT)
                            version = output.decode('utf-8').strip().split()[-1].split('.')[0]
                            return version
                        except Exception:
                            pass
        except Exception:
            pass
    else:
        try:
            for binary in ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser']:
                if os.path.exists(binary):
                    version = subprocess.check_output([binary, '--version'], stderr=subprocess.STDOUT)
                    version = version.decode('utf-8').strip().split()[-1].split('.')[0]
                    return version
        except Exception:
            pass

    return "120"


def run_setup_script(on_status=None):
    """Run the setup_chromedriver.py script to install the correct chromedriver"""
    try:
        setup_script = str(SCRIPTS_DIR / "setup_chromedriver.py")

        if os.path.exists(setup_script):
            _notify(on_status, "info", "Running chromedriver setup script...")
            result = subprocess.run([sys.executable, setup_script], capture_output=True, text=True)

            if result.returncode == 0:
                _notify(on_status, "success", "Chromedriver setup completed successfully!")
                for line in result.stdout.split('\n'):
                    if "Chromedriver path:" in line:
                        return line.split("Chromedriver path:")[1].strip()
            else:
                _notify(on_status, "warning", f"Chromedriver setup failed: {result.stderr}")
        else:
            _notify(on_status, "warning", f"Setup script not found at {setup_script}")
    except Exception as e:
        _notify(on_status, "warning", f"Error running setup script: {str(e)}")

    return None


def get_chromedriver_path():
    """Get the path to the chromedriver executable based on the platform"""
    system = platform.system()

    if system == "Windows":
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            chromedriver_path = os.path.join(local_app_data, "ChromeDriver", "chromedriver.exe")
            if os.path.exists(chromedriver_path):
                return chromedriver_path
    else:
        home_dir = os.path.expanduser("~")
        chromedriver_path = os.path.join(home_dir, ".chromedriver", "chromedriver")
        if os.path.exists(chromedriver_path):
            return chromedriver_path

    return None


def setup_webdriver(on_status=None):
    """
    Set up and configure Chrome webdriver with multiple fallback options

    Returns:
        webdriver.Chrome or None: Configured Chrome webdriver or None if setup fails
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )

    # Method 1: Try direct initialization first
    try:
        driver = webdriver.Chrome(options=options)
        _notify(on_status, "success", "Chrome webdriver initialized successfully!")
        return driver
    except Exception:
        pass

    # Method 2: Check if we already have a chromedriver installed
    chromedriver_path = get_chromedriver_path()
    if chromedriver_path:
        try:
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception:
            pass

    # Method 3: Try using webdriver-manager
    if webdriver_manager_available:
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception:
            pass

    # Method 4: Try platform-specific approaches
    system = platform.system()
    if system == "Windows":
        try:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ]

            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    try:
                        driver = webdriver.Chrome(options=options)
                        return driver
                    except Exception:
                        continue
        except Exception:
            pass
    elif system == "Linux":
        try:
            options.binary_location = "/usr/bin/chromium"
            try:
                driver = webdriver.Chrome(options=options)
                return driver
            except Exception:
                pass

            options.binary_location = "/usr/bin/google-chrome"
            try:
                driver = webdriver.Chrome(options=options)
                return driver
            except Exception:
                pass
        except Exception:
            pass

    _notify(on_status, "error", "Failed to initialize Chrome webdriver. Please make sure Chrome is installed.")
    return None
