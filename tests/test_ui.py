import os
import subprocess
import time
import requests
import pytest
from playwright.sync_api import sync_playwright

HEADLESS = os.getenv("TEST_UI_HEADLESS", "1") != "0"
SLOW_MO = 0 if HEADLESS else 150

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture(autouse=True)
def reset_game(server):
    res = requests.post(f"{BASE_URL}/reset", timeout=1.0)
    res.raise_for_status()    


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        yield browser
        browser.close()

@pytest.fixture(scope="session")
def page(browser):
    page = browser.new_page()
    yield page
    page.close()

@pytest.fixture(scope="session")
def server():
    # Start Flask server
    p = subprocess.Popen(["python", "webapp.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to respond
    for _ in range(80):
        try:
            requests.get(f"{BASE_URL}/state", timeout=0.25)
            break
        except Exception:
            time.sleep(0.1)
    else:
        p.terminate()
        raise RuntimeError("Server did not start in time")

    yield
    p.terminate()


def _click_hand_card(page, player_index: int, card_index: int) -> None:
    page.locator(".hand").nth(player_index).locator(".card").nth(card_index).click()


def _finish_setup(page) -> None:
    # Alice flips 0 and 3
    _click_hand_card(page, 0, 0)
    _click_hand_card(page, 0, 3)
    # Bob flips 1 and 4
    _click_hand_card(page, 1, 1)
    _click_hand_card(page, 1, 4)

    page.wait_for_function(
        "document.getElementById('statusLine').innerText.includes('Phase: play')"
    )


def test_loads(server, page):
    page.goto(f"{BASE_URL}/")

    page.wait_for_selector("#hands")
    assert page.locator(".hand").count() == 2

    page.wait_for_selector("#statusLine")
    page.wait_for_function("document.getElementById('statusLine').textContent.trim().length > 0")

    status = page.locator("#statusLine").text_content() or ""
    assert "Phase:" in status
    assert "setup" in status  # or "Phase: setup" if you want exact

def test_setup_to_play(server, page):
    page.goto(f"{BASE_URL}/")

    page.wait_for_selector(".hand")
    page.wait_for_function(
        "document.getElementById('statusLine').innerText.includes('Phase: setup')"
    )

    _finish_setup(page)

    # Deck pile should be enabled: not have class "disabled"
    cls = page.locator("#deckPile").get_attribute("class") or ""
    assert "disabled" not in cls

    # Drawn card should still be none
    # Either placeholder visible or drawn image hidden/empty
    placeholder = page.locator("#drawnPlaceholder")
    assert placeholder.is_visible()


def test_draw_and_swap_updates_drawn_and_discard(server, page):
    page.goto(f"{BASE_URL}/")

    page.wait_for_selector(".hand")
    _finish_setup(page)

    # Capture discard image src (may be back.png if empty; usually a face-up discard)
    discard_img = page.locator("#discardImg")
    before_discard_src = discard_img.get_attribute("src")

    # Click Deck to draw
    page.locator("#deckPile").click()

    # Drawn image should now be visible with src set
    page.wait_for_function(
        """
        () => {
            const img = document.getElementById('drawnImg');
            const ph  = document.getElementById('drawnPlaceholder');
            const src = img?.getAttribute('src') || '';
            // src should be set and placeholder hidden
            const imgVisible = img && getComputedStyle(img).display !== 'none';
            const phHidden = ph && getComputedStyle(ph).display === 'none';
            return src.includes('/static/cards/') && imgVisible && phHidden;
        }
        """
    )

    drawn_src = page.locator("#drawnImg").get_attribute("src") or ""
    assert "/static/cards/" in drawn_src

    # Now swap into Alice slot 1 (Alice is active first in play)
    _click_hand_card(page, 0, 1)

    # After swap, drawn should be cleared (placeholder visible again)
    page.wait_for_function("""
    () => {
    const ph  = document.getElementById('drawnPlaceholder');
    const img = document.getElementById('drawnImg');
    const phVisible = ph && getComputedStyle(ph).display !== 'none';
    const src = img?.getAttribute('src') || '';
    // accept either "src cleared" OR "placeholder visible" as cleared state
    return phVisible && (src === '' || !src.includes('/static/cards/'));
    }
    """)

    # Discard image should have changed (outgoing card placed on discard)
    after_discard_src = discard_img.get_attribute("src")
    assert after_discard_src != before_discard_src


def test_draw_from_discard(server, page):
    page.goto(f"{BASE_URL}/")

    page.wait_for_selector(".hand")
    _finish_setup(page)

    # Ensure we have a discard top (your game always seeds discard with 1 revealed card)
    discard_img = page.locator("#discardImg")
    before_discard_src = discard_img.get_attribute("src") or ""
    assert "/static/cards/" in before_discard_src

    # Click discard pile to draw from discard
    page.locator("#discardPile").click()

    # Drawn should show the discard card image we just took
    page.wait_for_function(
        """
        () => {
            const img = document.getElementById('drawnImg');
            const ph  = document.getElementById('drawnPlaceholder');
            const src = img?.getAttribute('src') || '';
            const imgVisible = img && getComputedStyle(img).display !== 'none';
            const phHidden = ph && getComputedStyle(ph).display === 'none';
            return src.includes('/static/cards/') && imgVisible && phHidden;
        }
        """
    )

    drawn_src = page.locator("#drawnImg").get_attribute("src") or ""
    assert drawn_src == before_discard_src, "Expected drawn card to come from discard pile"


def test_click_discard_discards_pending(server, page):
    page.goto(f"{BASE_URL}/")

    page.wait_for_selector(".hand")
    _finish_setup(page)

    # Draw from deck first to create a pending drawn card
    page.locator("#deckPile").click()

    page.wait_for_function(
        """
        () => {
            const img = document.getElementById('drawnImg');
            const ph  = document.getElementById('drawnPlaceholder');
            const src = img?.getAttribute('src') || '';
            const imgVisible = img && getComputedStyle(img).display !== 'none';
            const phHidden = ph && getComputedStyle(ph).display === 'none';
            return src.includes('/static/cards/') && imgVisible && phHidden;
        }
        """
    )

    # Capture what card is currently drawn
    drawn_src = page.locator("#drawnImg").get_attribute("src") or ""
    assert "/static/cards/" in drawn_src

    # Click discard pile while pending => should discard that drawn card
    page.locator("#discardPile").click()

    # Drawn should clear (placeholder visible again)
    page.wait_for_function(
        """
        () => {
            const img = document.getElementById('drawnImg');
            const ph  = document.getElementById('drawnPlaceholder');
            const imgHidden = img && getComputedStyle(img).display === 'none';
            const phVisible = ph && getComputedStyle(ph).display !== 'none';
            return imgHidden && phVisible;
        }
        """
    )

    # Discard top should now be the card we discarded (matches drawn_src)
    discard_src = page.locator("#discardImg").get_attribute("src") or ""
    assert discard_src == drawn_src, "Expected discard top image to become the discarded drawn card"