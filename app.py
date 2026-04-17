from flask import Flask, jsonify, request
import random
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from flasgger import Swagger

load_dotenv()

app = Flask(__name__)
app.config['SWAGGER'] = {
    'openapi': '3.0.3'
}
swagger = Swagger(app, template_file='openapi.yaml')

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
CORS(app, origins="*")

ADM_USUARIO = os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")

try:
    from auth import token_obrigatorio, gerar_token
except ImportError:
    def token_obrigatorio(f):
        return f
    def gerar_token():
        return "token_dummy"

if os.getenv("VERCEL"):
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
else:
    cred = credentials.Certificate("firebase_academia.json")
    
firebase_admin.initialize_app(cred)
db = firestore.client()

# ====================
# FUNÇÕES AUXILIARES
# ====================

def buscar_usuario_cpf(cpf):
    usuarios_ref = db.collection("usuarios")
    query = usuarios_ref.where("cpf", "==", cpf).limit(1)
    resultados = list(query.stream())
    if resultados:
        return resultados[0]
    return None

def atualizar_contador():
    try:
        contador_ref = db.collection("contador").document("controle_id")
        contador = contador_ref.get()
        
        if contador.exists:
            dados = contador.to_dict()
            ultimo_id = dados.get("ultimo_id", 0)
            novo_id = ultimo_id + 1
            contador_ref.update({"ultimo_id": novo_id})
            return novo_id
        else:
            contador_ref.set({"ultimo_id": 1})
            return 1
    except Exception as e:
        print(f"Erro ao atualizar contador: {e}")
        return None

def obter_contador():
    try:
        contador_ref = db.collection("contador").document("controle_id")
        contador = contador_ref.get()
        if contador.exists:
            return contador.to_dict().get("ultimo_id", 0)
        return 0
    except Exception as e:
        print(f"Erro ao obter contador: {e}")
        return 0

# ====================
# ROTAS PÚBLICAS 
# ====================

@app.route('/cadastro', methods=['POST'])
def cadastro():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"error": "Envie os dados de cadastro"}), 400
        
        nome = dados.get("nome")
        cpf = dados.get("cpf")
        status = dados.get("status", "Pendente")
        
        if not all([nome, cpf]):
            return jsonify({"erro": "Os campos 'nome' e 'cpf' são obrigatórios."}), 400
        
        if len(cpf) != 11 or not cpf.isdigit():
            return jsonify({"erro": "CPF inválido"}), 400
        
        if status not in ["Ativo", "Inativo", "Pendente"]:
            return jsonify({"erro": "Status inválido. Use: Ativo, Inativo ou Pendente"}), 400
        
        usuario_existente = buscar_usuario_cpf(cpf)
        if usuario_existente:
            return jsonify({"erro": "O CPF já está cadastrado."}), 400
        
        novo_id = atualizar_contador()
        
        db.collection("usuarios").document(cpf).set({
            "id_contador": novo_id,
            "nome": nome,
            "cpf": cpf,
            "status": status,
            "data_cadastro": firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({
            "mensagem": "Usuário cadastrado com sucesso!",
            "id": novo_id,
            "status": status
        }), 201
        
    except Exception as e:
        print(f"Erro no cadastro: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/consulta', methods=['GET'])
def consulta():
    usuario_ref = db.collection("usuarios")
    usuarios = []
    for doc in usuario_ref.stream():
        data = doc.to_dict()
        usuarios.append({
            "id": data.get("id_contador"),
            "nome": data.get("nome"),
            "cpf": data.get("cpf"),
            "status": data.get("status", "Pendente")
        })
    
    usuarios.sort(key=lambda x: x["id"] if x["id"] is not None else 999999)
    
    total = len(usuarios)
    contador = obter_contador()
    
    ativos = sum(1 for u in usuarios if u["status"] == "Ativo")
    inativos = sum(1 for u in usuarios if u["status"] == "Inativo")
    pendentes = sum(1 for u in usuarios if u["status"] == "Pendente")
    
    return jsonify({
        "usuarios": usuarios,
        "total": total,
        "contador": contador,
        "status_count": {
            "Ativo": ativos,
            "Inativo": inativos,
            "Pendente": pendentes
        }
    })

@app.route('/consulta/<cpf>', methods=['GET'])
def consulta_por_cpf(cpf):
    usuario_doc = db.collection("usuarios").document(cpf).get()
    if not usuario_doc.exists:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    dados = usuario_doc.to_dict()
    status = dados.get("status", "Pendente")
    
    if status != "Ativo":
        return jsonify({
            "erro": f"Acesso negado. Status do usuário: {status}",
            "status": status,
            "mensagem_status": "Apenas usuários ATIVOS podem acessar a academia."
        }), 403
    
    return jsonify({
        "nome": dados.get("nome"),
        "cpf": dados.get("cpf"),
        "status": status,
        "acesso": "liberado"
    }), 200

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Envie as credenciais"}), 400
    usuario = dados.get("usuario")
    senha = dados.get("senha")
    if usuario == ADM_USUARIO and senha == ADM_SENHA:
        token = gerar_token(usuario)
        return jsonify({
            "token": token, 
            "mensagem": "Login realizado com sucesso!",
            "usuario": usuario
        })
    else:
        return jsonify({"erro": "Credenciais inválidas"}), 401

# ====================
# ROTAS PRIVADAS 
# ====================

@app.route('/', methods=['GET'])
@token_obrigatorio
def index():
    return jsonify({"mensagem": "Bem-vindo ao GreenFit!"})

@app.route('/contador', methods=['GET'])
@token_obrigatorio
def get_contador():
    valor = obter_contador()
    return jsonify({"ultimo_id": valor}), 200

@app.route('/alterar-status/<cpf>', methods=['PATCH'])
@token_obrigatorio
def alterar_status(cpf):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Envie o novo status"}), 400
    
    novo_status = dados.get("status")
    if not novo_status:
        return jsonify({"erro": "O campo 'status' é obrigatório."}), 400
    
    if novo_status not in ["Ativo", "Inativo", "Pendente"]:
        return jsonify({"erro": "Status inválido. Use: Ativo, Inativo ou Pendente"}), 400
    
    if len(cpf) != 11 or not cpf.isdigit():
        return jsonify({"erro": "CPF inválido"}), 400
    
    doc_ref = db.collection("usuarios").document(cpf)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    doc_ref.update({
        "status": novo_status,
        "data_atualizacao": firestore.SERVER_TIMESTAMP
    })
    
    doc_atualizado = doc_ref.get()
    dados_atualizados = doc_atualizado.to_dict()
    
    return jsonify({
        "mensagem": f"Status do usuário alterado para {novo_status} com sucesso!",
        "usuario": {
            "id": dados_atualizados.get("id_contador"),
            "nome": dados_atualizados.get("nome"),
            "cpf": cpf,
            "status": novo_status
        }
    }), 200

@app.route('/editar/<cpf>', methods=['PATCH'])
@token_obrigatorio
def editar(cpf):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Envie os dados para edição"}), 400
    if len(cpf) != 11 or not cpf.isdigit():
        return jsonify({"erro": "CPF inválido"}), 400
    
    doc_ref = db.collection("usuarios").document(cpf)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    if "cpf" in dados:
        return jsonify({"erro": "Não é permitido alterar o CPF"}), 400
    if "status" in dados:
        return jsonify({"erro": "Para alterar status, use a rota /alterar-status"}), 400
    
    doc_ref.update(dados)
    return jsonify({"mensagem": "Usuário editado com sucesso!"})

@app.route('/substituir/<cpf>', methods=['PUT'])
@token_obrigatorio
def substituir(cpf):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Envie os dados para substituição"}), 400
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório."}), 400
    if len(cpf) != 11 or not cpf.isdigit():
        return jsonify({"erro": "CPF inválido"}), 400
    
    doc_ref = db.collection("usuarios").document(cpf)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    status_original = doc.to_dict().get("status", "Pendente")
    novo_status = dados.get("status", status_original)
    
    doc_ref.set({
        "nome": nome,
        "cpf": cpf,
        "status": novo_status,
        "data_atualizacao": firestore.SERVER_TIMESTAMP
    })
    return jsonify({"mensagem": "Usuário substituído com sucesso!"})

@app.route("/excluir/<cpf>", methods=['DELETE'])
@token_obrigatorio
def excluir(cpf):
    if len(cpf) != 11 or not cpf.isdigit():
        return jsonify({"erro": "CPF inválido"}), 400
    doc_ref = db.collection("usuarios").document(cpf)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    doc_ref.delete()
    return jsonify({"mensagem": "Usuário excluído com sucesso!"})

@app.route('/resetar-contador', methods=['POST'])
@token_obrigatorio
def resetar_contador():
    try:
        contador_ref = db.collection("contador").document("controle_id")
        contador_ref.set({"ultimo_id": 0})
        return jsonify({"mensagem": "Contador resetado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ====================
# TRATAMENTO DE ERROS
# ====================

@app.errorhandler(404)
def erro404(error):
    return jsonify({"error": "URL não encontrada"}), 404

@app.errorhandler(500)
def erro500(error):
    return jsonify({"error": "Servidor interno com falhas. Tente mais tarde"}), 500

if __name__ == "__main__":
    app.run(debug=True)