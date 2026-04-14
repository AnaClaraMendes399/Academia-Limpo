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
# Chamar o openapi para o código
swagger = Swagger(app, template_file='openapi.yaml')

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
CORS(app, origins="*")

ADM_USUARIO = os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")

# Import condicional do auth 
try:
    from auth import token_obrigatorio, gerar_token
except ImportError:
    # Função dummy para desenvolvimento
    def token_obrigatorio(f):
        return f
    def gerar_token():
        return "token_dummy"

if os.getenv("VERCEL"):
    # Online na Vercel
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
else:
    # Local
    cred = credentials.Certificate("firebase_academia.json")
    
# Carregar as credenciais do Firebase
firebase_admin.initialize_app(cred)

# Conectar ao Firestore
db = firestore.client()

# Função para buscar usuário por CPF
def buscar_usuario_cpf(cpf):
    usuarios_ref = db.collection("usuarios")
    query = usuarios_ref.where("cpf", "==", cpf).limit(1)
    resultados = list(query.stream())
    if resultados:
        return resultados[0]
    return None

# Rota principal 
@app.route('/', methods=['GET'])
@token_obrigatorio
def index():
    return jsonify({"mensagem": "Bem-vindo ao GreenFit!"})

# Rota cadastro de usuário
@app.route('/cadastro', methods=['POST'])
def cadastro():
    dados = request.get_json()
    if not dados:
        return jsonify({"error": "Envie os dados de cadastro"}), 400
    nome = dados.get("nome")
    cpf = dados.get("cpf")
    if not all([nome, cpf]):
        return jsonify({"erro": "Os campos 'nome' e 'cpf' são obrigatórios."}), 400
    if len(cpf) != 11 or not cpf.isdigit():
        return jsonify({"erro": "CPF inválido"}), 400
    # Verificar se o CPF já existe
    usuario_existente = buscar_usuario_cpf(cpf)
    if usuario_existente:
        return jsonify({"erro": "O CPF já está cadastrado."}), 400
    # Adicionar documento com CPF como ID
    db.collection("usuarios").document(cpf).set({
        "nome": nome,
        "cpf": cpf,
    })
    return jsonify({"mensagem": "Usuário cadastrado com sucesso!"}), 201

# Rota de consulta - Método GET
@app.route('/consulta', methods=['GET'])
@token_obrigatorio
def consulta():
    usuario_ref = db.collection("usuarios")
    usuarios = []
    for doc in usuario_ref.stream():
        usuarios.append(doc.to_dict())
    return jsonify({"usuarios": usuarios})

# Rota de consulta por CPF - Método GET
@app.route('/consulta/<cpf>', methods=['GET'])
@token_obrigatorio
def consulta_por_cpf(cpf):
    usuario_doc = db.collection("usuarios").document(cpf).get()
    if not usuario_doc.exists:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify(usuario_doc.to_dict())

# Rota de edição parcial - Método PATCH
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
    doc_ref.update(dados)
    return jsonify({"mensagem": "Usuário editado com sucesso!"})

# Rota de edição total - Método PUT
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
    doc_ref.set({
        "nome": nome,
        "cpf": cpf,
    })
    return jsonify({"mensagem": "Usuário substituído com sucesso!"})

# Rota de exclusão de alunos - Método DELETE
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

# Rota de login 
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
#  Rotas de tratamento de erros
# ====================
@app.errorhandler(404)
def erro404(error):
    return jsonify({"error": "URL não encontrada"}), 404

@app.errorhandler(500)
def erro500(error):
    return jsonify({"error": "Servidor interno com falhas. Tente mais tarde"}), 500

if __name__ == "__main__":
    app.run(debug=True)