
from pathlib import Path
import os
import secrets
import time
import threading
from functools import wraps

from flask import (
    Flask,
    jsonify,
    send_from_directory,
    Response,
    request,
    session
)

from werkzeug.security import check_password_hash

from src.backend.recognition_service import RecognitionService

from src.database.connection import conectar

from src.database.repository import (
    registrar_acesso_inicio,
    registrar_acesso_fim,
    obter_resumo_dashboard,
    obter_ranking_sinais,
    obter_evolucao_diaria,
    obter_reconhecimentos_recentes,
    obter_acessos_recentes,
)


# ==================================================
# CAMINHOS DO PROJETO
# ==================================================

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
FRONTEND_DIR = RAIZ_PROJETO / "frontend"


# ==================================================
# CONFIGURAÇÃO DO FLASK
# ==================================================

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)

app.secret_key = os.environ.get(
    "TRADULIB_SECRET_KEY"
) or secrets.token_hex(32)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=3600
)


# ==================================================
# SERVIÇO DE RECONHECIMENTO
# ==================================================

recognition_service = RecognitionService()


# ==================================================
# MONITORAMENTO DOS ACESSOS
# ==================================================

def monitorar_acesso(acesso_id):

    try:

        while recognition_service.get_state()["running"]:
            time.sleep(0.2)

        sucesso = registrar_acesso_fim(acesso_id)

        if sucesso:
            app.logger.info(
                "Acesso %s finalizado com sucesso.",
                acesso_id
            )
        else:
            app.logger.warning(
                "Não foi possível finalizar o acesso %s.",
                acesso_id
            )

    except Exception:
        app.logger.exception(
            "Erro ao monitorar o acesso %s.",
            acesso_id
        )


# ==================================================
# PROTEÇÃO DAS ROTAS ADMINISTRATIVAS
# ==================================================

def administrador_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "administrador_id" not in session:
            return jsonify({
                "erro": "Acesso não autorizado."
            }), 401

        return func(*args, **kwargs)

    return wrapper


# ==================================================
# PÁGINA INICIAL
# ==================================================

@app.route("/", methods=["GET"])
def inicio():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ==================================================
# STATUS DO SERVIDOR
# ==================================================

@app.route("/api/status", methods=["GET"])
def status():

    return jsonify({
        "servidor": "online",
        "sistema": "Tradulib"
    })


# ==================================================
# LOGIN ADMINISTRATIVO
# ==================================================

@app.route("/api/admin/login", methods=["POST"])
def login_administrador():

    dados = request.get_json(silent=True) or {}

    usuario = dados.get("usuario", "").strip()
    senha = dados.get("senha", "")

    if not usuario or not senha:
        return jsonify({
            "erro": "Informe usuário e senha."
        }), 400

    conexao = conectar()

    if conexao is None:
        return jsonify({
            "erro": "Não foi possível conectar ao banco de dados."
        }), 503

    cursor = None

    try:

        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT id, usuario, senha_hash, ativo
            FROM administradores
            WHERE LOWER(usuario) = LOWER(%s)
            """,
            (usuario,)
        )

        administrador = cursor.fetchone()

        if administrador is None:
            return jsonify({
                "erro": "Usuário ou senha incorretos."
            }), 401

        admin_id, nome_usuario, senha_hash, ativo = administrador

        if not ativo:
            return jsonify({
                "erro": "Esta conta administrativa está desativada."
            }), 403

        if not check_password_hash(senha_hash, senha):
            return jsonify({
                "erro": "Usuário ou senha incorretos."
            }), 401

        session.clear()

        session["administrador_id"] = admin_id
        session["administrador_usuario"] = nome_usuario
        session.permanent = True

        return jsonify({
            "mensagem": "Login realizado com sucesso.",
            "administrador": {
                "id": admin_id,
                "usuario": nome_usuario
            }
        }), 200

    except Exception:

        app.logger.exception(
            "Erro durante a autenticação administrativa."
        )

        return jsonify({
            "erro": "Erro interno durante a autenticação."
        }), 500

    finally:

        if cursor:
            cursor.close()

        conexao.close()


# ==================================================
# VERIFICAR SESSÃO ADMINISTRATIVA
# ==================================================

@app.route("/api/admin/sessao", methods=["GET"])
@administrador_required
def verificar_sessao_admin():

    return jsonify({
        "autenticado": True,
        "administrador": {
            "id": session["administrador_id"],
            "usuario": session["administrador_usuario"]
        }
    }), 200


# ==================================================
# LOGOUT ADMINISTRATIVO
# ==================================================

@app.route("/api/admin/logout", methods=["POST"])
def logout_administrador():

    session.clear()

    return jsonify({
        "mensagem": "Sessão encerrada com sucesso."
    }), 200


# ==================================================
# DASHBOARD ADMINISTRATIVO
# ==================================================

@app.route("/api/admin/dashboard", methods=["GET"])
@administrador_required
def dashboard_administrativo():

    periodo_texto = request.args.get("periodo", "30")

    try:
        periodo = int(periodo_texto)

    except (TypeError, ValueError):
        return jsonify({
            "erro": "Período inválido."
        }), 400

    periodos_permitidos = [7, 30, 90, 365]

    if periodo not in periodos_permitidos:
        return jsonify({
            "erro": "Selecione um período de 7, 30, 90 ou 365 dias."
        }), 400

    try:

        resumo = obter_resumo_dashboard(periodo)
        ranking = obter_ranking_sinais(periodo)
        evolucao = obter_evolucao_diaria(periodo)
        recentes = obter_reconhecimentos_recentes(10)
        acessos = obter_acessos_recentes(10)

        resultados = [
            resumo,
            ranking,
            evolucao,
            recentes,
            acessos
        ]

        if any(resultado is None for resultado in resultados):

            return jsonify({
                "erro": "Não foi possível consultar os dados do dashboard."
            }), 503

        return jsonify({

            "periodo": periodo,

            "indicadores": resumo,

            "ranking_sinais": ranking,

            "evolucao_diaria": evolucao,

            "reconhecimentos_recentes": recentes,

            "acessos_recentes": acessos

        }), 200

    except Exception:

        app.logger.exception(
            "Erro ao carregar dashboard administrativo."
        )

        return jsonify({
            "erro": "Erro interno ao carregar o dashboard."
        }), 500


# ==================================================
# INICIAR RECONHECIMENTO
# ==================================================

@app.route("/api/reconhecimento/iniciar", methods=["POST"])
def iniciar_reconhecimento_api():

    acesso_id = registrar_acesso_inicio()

    iniciado = recognition_service.start()

    if not iniciado:

        if acesso_id is not None:
            registrar_acesso_fim(acesso_id)

        return jsonify({
            "mensagem": "O reconhecimento já está em execução."
        }), 409

    if acesso_id is not None:

        threading.Thread(
            target=monitorar_acesso,
            args=(acesso_id,),
            daemon=True
        ).start()

    else:

        app.logger.warning(
            "Reconhecimento iniciado sem registro de acesso no banco."
        )

    return jsonify({
        "mensagem": "Solicitação de reconhecimento recebida.",
        "acesso_registrado": acesso_id is not None
    }), 202


# ==================================================
# PARAR RECONHECIMENTO
# ==================================================

@app.route("/api/reconhecimento/parar", methods=["POST"])
def parar_reconhecimento_api():

    recognition_service.stop()

    return jsonify({
        "mensagem": "Solicitação de encerramento recebida."
    })


# ==================================================
# CONSULTAR ESTADO DO RECONHECIMENTO
# ==================================================

@app.route("/api/reconhecimento/estado", methods=["GET"])
def estado_reconhecimento_api():

    return jsonify(
        recognition_service.get_state()
    )


# ==================================================
# TRANSMISSÃO DA CÂMERA PARA O NAVEGADOR
# ==================================================

@app.route("/api/reconhecimento/video", methods=["GET"])
def video_reconhecimento_api():

    def gerar_frames():

        while True:

            frame = recognition_service.get_frame()

            if frame is None:

                if not recognition_service.get_state()["running"]:
                    break

                time.sleep(0.1)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )

            time.sleep(0.03)

    return Response(
        gerar_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==================================================
# EXECUÇÃO DO SERVIDOR
# ==================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
