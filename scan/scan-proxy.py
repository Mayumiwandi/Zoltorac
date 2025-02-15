import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
file_input = "rawProxyList.txt"

def Cek_proxy(ip, port, timeout=3):
    """dengan module socket kita memeriksa koneksi IP dan PORT"""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except(socket.timeout, socket.error):
        return False
    
def Cek_ip_port(line):
    parts = line.strip().split(',')
    if len (parts)>= 2:
        ip_addres = parts[0]
        try:
            port_number = int(parts[1])
        except ValueError:
            print(f"[ERROR] Port tidak valid : {parts[1]}")
            return
        
        country = parts[2] if len(parts) > 2 else "Unknown"
        organization = parts[3] if len(parts) > 3 else "Unknown"
        
        result = f"{ip_addres}, {port_number}, {country}, {organization}" 
        
        if Cek_proxy(ip_addres, port_number):
            Save_to_file('active.txt', result)
            print(f"[AKTIF] {result} ")
            
        else:
            Save_to_file('dead.txt', result)
            print(f"[TIDAK AKTIF],{result}")
            
def Save_to_file(filename, data):
    with open(filename, 'a') as f:
        f.write(data +'\n')
        
def Read_ip_port(filename, max_workers=50): # max_workers harus jangan terlalu banyak
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures =[executor.submit(Cek_ip_port, line) for line in lines]
            for future in as_completed(futures):
                future.result()
                #memastikan setiap tugas selesai
                
    except FileNotFoundError:
        print(f"File '{filename}' tidak di temukan.")
    except ValueError:
        print(f"Format data salah. Pastikan Ip dan Port dipisah dengan koma.")
        
Read_ip_port(file_input)
