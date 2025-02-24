import socket
import ssl
import json
import threading
import concurrent.futures

IP_RESOLVER = "speed.cloudflare.com"
PATH_RESOLVER = "/meta"
TIMEOUT_SECONDS = 20  # Define timeout value in seconds

def check(host, path, proxy):
    payload = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "User-Agent: Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240\r\n"
        "Connection: close\r\n\r\n"
    )
    ip = host if not proxy.get("ip") else proxy["ip"]
    port = 443 if not proxy.get("port") else proxy["port"]

    conn = None
    try:
        ctx = ssl.create_default_context()
        conn = socket.create_connection((ip, int(port) ), timeout=TIMEOUT_SECONDS) # Add timeout here
        conn = ctx.wrap_socket(conn, server_hostname=host)

        conn.send(payload.encode())

        resp = b""
        while True:
            data =  conn.recv(4096)
            if not data:
                break
            resp += data

        resp = resp.decode("utf-8")
        resp = resp.split("\r\n\r\n")

        if len(resp) < 2:
            return {}

        try:
            resp_json = json.loads(resp[1])
            return resp_json
        except json.JSONDecodeError: # Handle potential JSON decode errors
            print(f"Error: JSONDecodeError for proxy {proxy.get('ip')}:{proxy.get('port')}")
            return {}

    except socket.timeout: # Catch socket.timeout specifically
        print(f"Error: Connection timed out after {TIMEOUT_SECONDS} seconds for proxy {proxy.get('ip')}:{proxy.get('port')}")
        return {}
    except Exception as e:
        print(f"Error: {e} for proxy {proxy.get('ip')}:{proxy.get('port')}")
        return {}
    finally:
        if conn:
            conn.close()

def process_proxy(proxy_str):
    try:
        ipv4, port, negara, org = proxy_str.strip().split(",")
        proxy_dict = {"ip": ipv4, "port": port, "negara": negara, "org": org}
        ori = check(IP_RESOLVER, PATH_RESOLVER, {})
        pxy = check(IP_RESOLVER, PATH_RESOLVER, proxy_dict)

        if ori and pxy and ori.get("clientIp") != pxy.get("clientIp"):
            asn = pxy.get("asn", "N/A")
            org_proxy = pxy.get("asOrganization", "N/A")
            country = pxy.get("country", "N/A")
            city = pxy.get("city", "N/A")
            return f"CF PROXY LIVE!: {ipv4}:{port} | {org_proxy} | {country} | {city}"
        else:
            return f"CF PROXY DEAD!: {ipv4}:{port}"
    except ValueError:
        return f"Error parsing proxy line: {proxy_str.strip()}"
    except Exception as e:
        return f"Error processing proxy {proxy_str.strip()}: {e}"

if __name__ == "__main__":
    proxy_file = "/content/rawProxyList.txt" # Use the correct path for Colab
    active_proxy_file = "proxyactive.txt"
    max_workers = 50
    proxy_results = []
    live_proxies = [] # List to store live proxy results

    try:
        with open(proxy_file, "r") as f:
            proxies = f.readlines()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_proxy, proxy) for proxy in proxies]

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                proxy_results.append(result)
                if "CF PROXY LIVE!" in result: # Check if proxy is live
                    live_proxies.append(result) # Add live proxy result to list

        # Save live proxies to proxyactive.txt
        with open(active_proxy_file, "w") as f_active:
            for live_proxy_result in live_proxies:
                f_active.write(live_proxy_result + "\n")

        print("\n--- Proxy Check Results ---") # Separator for better readability
        for result in proxy_results:
            print(result)

        print(f"\nLive proxies saved to '{active_proxy_file}'")


    except FileNotFoundError:
        print(f"Error: File '{proxy_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
