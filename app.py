from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import logging
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='ativo')
    endereco = db.relationship('Endereco', backref='usuario', uselist=False, cascade="all, delete")


class Endereco(db.Model):
    __tablename__ = 'enderecos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cep = db.Column(db.String(8), nullable=False)
    logradouro = db.Column(db.String(100), nullable=False)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)


def consultar_cep(cep):
    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
    if response.status_code == 200:
        dados = response.json()
        if "erro" in dados:
            return None
        return {
            "logradouro": dados.get("logradouro"),
            "bairro": dados.get("bairro"),
            "cidade": dados.get("localidade"),
            "estado": dados.get("uf"),
        }
    return None


@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    try:
        dados = request.json

        nome = dados.get('nome')
        email = dados.get('email')
        cep = dados.get('cep')
        if not all([nome, email, cep]):
            return jsonify({"erro": "Campos 'nome', 'email' e 'cep' são obrigatórios."}), 400

        if len(cep) != 8 or not cep.isdigit():
            return jsonify({"erro": "CEP inválido."}), 400

        endereco_data = consultar_cep(cep)
        if not endereco_data:
            return jsonify({"erro": "CEP não encontrado."}), 404

        usuario = Usuario(nome=nome, email=email)
        db.session.add(usuario)
        db.session.flush()

        endereco = Endereco(
            usuario_id=usuario.id,
            cep=cep,
            **endereco_data
        )
        db.session.add(endereco)
        db.session.commit()

        return jsonify({"mensagem": "Usuário criado com sucesso.", "usuario_id": usuario.id}), 201
    except Exception as e:
        logging.error(f"Erro ao criar usuário: {e}")
        return jsonify({"erro": "Erro interno no servidor."}), 500


@app.route('/usuarios/<int:id>', methods=['GET'])
def obter_usuario(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404

    endereco = usuario.endereco
    return jsonify({
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "data_criacao": usuario.data_criacao,
        "status": usuario.status,
        "endereco": {
            "cep": endereco.cep,
            "logradouro": endereco.logradouro,
            "bairro": endereco.bairro,
            "cidade": endereco.cidade,
            "estado": endereco.estado,
        }
    })


@app.route('/usuarios/<int:id>', methods=['PUT'])
def atualizar_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        dados = request.json
        usuario.nome = dados.get('nome', usuario.nome)
        usuario.email = dados.get('email', usuario.email)
        usuario.status = dados.get('status', usuario.status)
        db.session.commit()

        return jsonify({"mensagem": "Usuário atualizado com sucesso."})
    except Exception as e:
        logging.error(f"Erro ao atualizar usuário: {e}")
        return jsonify({"erro": "Erro interno no servidor."}), 500


@app.route('/usuarios/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"mensagem": "Usuário deletado com sucesso."})
    except Exception as e:
        logging.error(f"Erro ao deletar usuário: {e}")
        return jsonify({"erro": "Erro interno no servidor."}), 500


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
