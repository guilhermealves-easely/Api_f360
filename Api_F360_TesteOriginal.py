import requests
import json

API_KEY = "3ae4f2ed-8e22-44f4-84a5-3d3b3d69a7f3"
BASE_URL = "https://financas.f360.com.br"

LOGIN_URL = f"{BASE_URL}/PublicLoginApi/DoLogin"
PACELAS_URL = F"{BASE_URL}/ParcelasDeTituloPublicAPI/ListarParcelasDeTitulos"

def extract_jwt(resp):
    """Tenta extrair o JWT do JSON do login (chaves comuns e containers)."""
    try:
        data = resp.json()
    except ValueError:
        return None

    if not isinstance(data, dict):
        return None

    # tenta direto
    for k in ("Token", "token", "token_jwt", "jwt", "access_token"):
        v = data.get(k)
        if isinstance(v, str) and v.count(".") == 2:
            return v

    # tenta aninhado
    for cont in ("data", "result", "content"):
        obj = data.get(cont)
        if isinstance(obj, dict):
            for k in ("Token", "token", "token_jwt", "jwt", "access_token"):
                v = obj.get(k)
                if isinstance(v, str) and v.count(".") == 2:
                    return v

    return None

with requests.Session() as s:
    # 1) Login → obter JWT
    r_login = s.post(
        LOGIN_URL,
        json={"token": API_KEY},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=60,
    )
    print("Login status:", r_login.status_code)
    if not r_login.ok:
        print("Corpo do login:", r_login.text)
        raise SystemExit("Falha no login. Verifique a chave/token ou a disponibilidade do serviço.")

    jwt_token = extract_jwt(r_login)
    if not jwt_token:
        # fallback específico p/ {"Token": "<jwt>"}
        try:
            jwt_token = r_login.json().get("Token")
        except ValueError:
            jwt_token = None

    if not (isinstance(jwt_token, str) and jwt_token.count(".") == 2):
        print("Resposta de login (não achei o JWT):", r_login.text[:600])
        raise SystemExit("Não encontrei o token JWT na resposta do login.")

    print("JWT (prefixo):", jwt_token[:16] + "...")

    # 2) Headers comuns com JWT (DENTRO do with)
    s.headers.update({
        "Accept": "application/json",
        "Authorization": f"Bearer {jwt_token}",
        "token_jwt": jwt_token,  # algumas instâncias exigem esse header também
    })

    # 3) Listar parcelas
    params = {
        "pagina": 1,
        "tipo": "Despesa",           # "Receita" ou "Ambos"
        "inicio": "2025-10-01",
        "fim": "2025-10-01",
        "tipoDatas": "Vencimento",   # Emissao/Competencia/Vencimento/Liquidacao/LiquidacaoSistema/Atualizacao
        "token_jwt": jwt_token,      # algumas instâncias exigem via querystring também
    }

    r = s.get(PACELAS_URL, params=params, timeout=60)
    print("URL chamada:", r.url)
    print("Parcelas status:", r.status_code)
    print(r.text)

    if r.status_code == 401:
        raise SystemExit("JWT expirado/inválido. Faça novo login e tente novamente.")
    r.raise_for_status()
