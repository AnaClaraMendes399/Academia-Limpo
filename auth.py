import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app


# ==========================
# FUNÇÃO PARA GERAR TOKEN JWT
# ==========================
def gerar_token(usuario=None):
    """
    Gera um token JWT para o usuário autenticado
    
    Args:
        usuario (str, optional): Nome do usuário. Se não fornecido, usa 'admin'
    
    Returns:
        str: Token JWT
    """
    # Se não receber usuário, usa um padrão
    if usuario is None:
        usuario = "admin"
    
    payload = {
        "usuario": usuario,
        "perfil": "adm",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc)  # Adicionado issued at time
    }

    token = jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return token


# ==========================
# DECORATOR PARA PROTEGER ROTAS
# ==========================
def token_obrigatorio(func):
    """
    Decorator que exige um token JWT válido para acessar a rota.

    Uso:
    @app.route('/rota-privada')
    @token_obrigatorio
    def minha_rota():
        ...
    """
    @wraps(func)
    def verificar_token(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        # Verifica se o cabeçalho foi enviado
        if not auth_header:
            return jsonify({"erro": "Token ausente. Faça login."}), 401

        partes = auth_header.split()

        # Verifica se o formato está correto: Bearer SEU_TOKEN
        if len(partes) != 2 or partes[0] != "Bearer":
            return jsonify({"erro": "Cabeçalho Authorization inválido. Use: Bearer <token>"}), 401

        token = partes[1]

        try:
            # Tenta decodificar o token usando a chave secreta
            dados_token = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )

            # Armazena os dados do token na requisição para uso nas rotas
            request.usuario_logado = dados_token

        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado. Faça login novamente."}), 401

        except jwt.InvalidTokenError as e:
            return jsonify({"erro": f"Token inválido: {str(e)}"}), 401

        return func(*args, **kwargs)

    return verificar_token