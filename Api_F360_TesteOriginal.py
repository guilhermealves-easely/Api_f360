import requests
import json

API_KEY = "3ae4f2ed-8e22-44f4-84a5-3d3b3d69a7f3"
BASE_URL = "https://financas.f360.com.br"

LOGIN_URL = f"{BASE_URL}/PublicLoginApi/DoLogin"
PACELAS_URL = F"{BASE_URL}/ParcelasDeTituloPublicAPI/ListarParcelasDeTitulos"

def extract_jwt(resp):
    """
    Extrai o token JWT da resposta do login.
    Procura chaves comuns e containers ('data', 'result', etc.).
    """
    try:
        data = resp.json()
    except ValueError:
        return None

    candidate_keys = ["token_jwt", "tokenJWT", "jwt", "TokenJWT", "access_token", "token"]
    containers = [None, "data", "result", "content"]

    for cont in containers:
        obj = data if cont is None else data.get(cont, {})
        if isinstance(obj, dict):
            for k in candidate_keys:
                v = obj.get(k)
                # JWT normalmente tem 2 pontos (header.payload.signature)
                if isinstance(v, str) and v.count(".") == 2:
                    return v
    return None

with requests.Session() as s:
     # 1) Login → recebe JWT
     r_login = s.post (
         LOGIN_URL,
         json={"Token": API_KEY},
         headers={"Accept": "application/json", "Content-Type": "application/json"},
         timeout=60
     )

print ("Login Status:", r_login.status_code)
if not r_login.ok:
    print("Corpo do Login:", r_login.text)
    raise SystemExit ("Não encontrei JWT na resposta do login")     
        
