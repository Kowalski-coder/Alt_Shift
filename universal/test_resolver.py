import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import main

def test_language_pairs():
    print("=== Testing User Language Scenarios ===")

    # Scenario 1: User with US + RU
    main.active_user_layouts = ["us", "ru"]
    assert main.resolve_character('H')[0] == 'us'
    assert main.resolve_character('П')[0] == 'ru'
    print("[+] PASS: Scenario 1 (US + RU)")

    # Scenario 2: User with US + ES
    main.active_user_layouts = ["us", "es"]
    assert main.resolve_character('ñ')[0] == 'es'
    assert main.resolve_character('¿')[0] == 'es'
    assert main.resolve_character('h')[0] == 'us'
    print("[+] PASS: Scenario 2 (US + ES)")

    # Scenario 3: User with US + DE
    main.active_user_layouts = ["us", "de"]
    assert main.resolve_character('ä')[0] == 'de'
    assert main.resolve_character('ß')[0] == 'de'
    print("[+] PASS: Scenario 3 (US + DE)")

    # Scenario 4: User with US + FR
    main.active_user_layouts = ["us", "fr"]
    assert main.resolve_character('é')[0] == 'fr'
    assert main.resolve_character('ç')[0] == 'fr'
    print("[+] PASS: Scenario 4 (US + FR)")

    # Scenario 5: User with US + UA
    main.active_user_layouts = ["us", "ua"]
    assert main.resolve_character('і')[0] == 'ua'
    assert main.resolve_character('ї')[0] == 'ua'
    assert main.resolve_character('ґ')[0] == 'ua'
    print("[+] PASS: Scenario 5 (US + UA)")

    # Scenario 6: User with US + PL
    main.active_user_layouts = ["us", "pl"]
    assert main.resolve_character('ą')[0] == 'pl'
    assert main.resolve_character('ż')[0] == 'pl'
    print("[+] PASS: Scenario 6 (US + PL)")

    # Scenario 7: User with 3 layouts: US + RU + ES
    main.active_user_layouts = ["us", "ru", "es"]
    assert main.resolve_character('й')[0] == 'ru'
    assert main.resolve_character('ñ')[0] == 'es'
    assert main.resolve_character('k')[0] == 'us'
    print("[+] PASS: Scenario 7 (US + RU + ES)")

    print("\nAll multi-language scenario tests passed!")

if __name__ == "__main__":
    test_language_pairs()
