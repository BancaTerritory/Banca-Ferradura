from flask import Blueprint, render_template

game_blueprint = Blueprint("games", __name__)

import os
import sys # ESTA LINHA DEVE VIR AQUI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # DON'T CHANGE THIS !!!

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import random

from src.routes.auth_routes import users_db # Using global for prototype simplicity



# Jogo do Bicho Configuration (Simplified)
GRUPOS_BICHO = {
    1: {"nome": "Avestruz", "dezenas": ["01", "02", "03", "04"]}, 2: {"nome": "Águia", "dezenas": ["05", "06", "07", "08"]},
    3: {"nome": "Burro", "dezenas": ["09", "10", "11", "12"]}, 4: {"nome": "Borboleta", "dezenas": ["13", "14", "15", "16"]},
    5: {"nome": "Cachorro", "dezenas": ["17", "18", "19", "20"]}, 6: {"nome": "Cabra", "dezenas": ["21", "22", "23", "24"]},
    7: {"nome": "Carneiro", "dezenas": ["25", "26", "27", "28"]}, 8: {"nome": "Camelo", "dezenas": ["29", "30", "31", "32"]},
    9: {"nome": "Cobra", "dezenas": ["33", "34", "35", "36"]}, 10: {"nome": "Coelho", "dezenas": ["37", "38", "39", "40"]},
    11: {"nome": "Cavalo", "dezenas": ["41", "42", "43", "44"]}, 12: {"nome": "Elefante", "dezenas": ["45", "46", "47", "48"]},
    13: {"nome": "Galo", "dezenas": ["49", "50", "51", "52"]}, 14: {"nome": "Gato", "dezenas": ["53", "54", "55", "56"]},
    15: {"nome": "Jacaré", "dezenas": ["57", "58", "59", "60"]}, 16: {"nome": "Leão", "dezenas": ["61", "62", "63", "64"]},
    17: {"nome": "Macaco", "dezenas": ["65", "66", "67", "68"]}, 18: {"nome": "Porco", "dezenas": ["69", "70", "71", "72"]},
    19: {"nome": "Pavão", "dezenas": ["73", "74", "75", "76"]}, 20: {"nome": "Peru", "dezenas": ["77", "78", "79", "80"]},
    21: {"nome": "Touro", "dezenas": ["81", "82", "83", "84"]}, 22: {"nome": "Tigre", "dezenas": ["85", "86", "87", "88"]},
    23: {"nome": "Urso", "dezenas": ["89", "90", "91", "92"]}, 24: {"nome": "Veado", "dezenas": ["93", "94", "95", "96"]},
    25: {"nome": "Vaca", "dezenas": ["97", "98", "99", "00"]}
}
MULTIPLIERS_BICHO = {"grupo": 18, "milhar": 4000, "centena": 600, "dezena": 60}

# Bet Sports Futebol Configuration (Simplified)
PARTIDAS_FUTEBOL = [
    {"id": 1, "casa": "Flamengo", "fora": "Palmeiras", "odds": {"casa": 2.10, "empate": 3.30, "fora": 3.50}},
    {"id": 2, "casa": "Corinthians", "fora": "São Paulo", "odds": {"casa": 2.50, "empate": 3.00, "fora": 2.90}},
    {"id": 3, "casa": "Real Madrid", "fora": "Barcelona", "odds": {"casa": 1.90, "empate": 3.80, "fora": 3.90}},
    {"id": 4, "casa": "Manchester City", "fora": "Liverpool", "odds": {"casa": 1.80, "empate": 4.00, "fora": 4.20}}
]

def get_grupo_from_milhar(milhar_str):
    dezena_sorteada = milhar_str[2:]
    for grupo_num, detalhes in GRUPOS_BICHO.items():
        if dezena_sorteada in detalhes["dezenas"]: return grupo_num
    return None

@game_bp.route("/jogo-do-bicho", methods=["GET"])
def jogo_do_bicho():
    if "user_phone" not in session:
        flash("Você precisa estar logado para jogar.", "error"); return redirect(url_for("auth.login"))
    return render_template("jogo_do_bicho_v2.html")

@game_bp.route("/jogo-do-bicho/apostar", methods=["POST"])
def fazer_aposta_bicho():
    if "user_phone" not in session:
        flash("Sessão expirada. Faça login novamente.", "error"); return redirect(url_for("auth.login"))
    phone_number = session["user_phone"]; user_data = users_db.get(phone_number)
    if not user_data: flash("Usuário não encontrado.", "error"); return redirect(url_for("auth.login"))
    try:
        tipo_aposta = request.form.get("tipo_aposta"); aposta_valor_input = request.form.get("aposta_valor_input"); valor_aposta_str = request.form.get("valor_aposta")
        if not tipo_aposta or not aposta_valor_input or not valor_aposta_str:
            flash("Todos os campos da aposta são obrigatórios.", "error"); return redirect(url_for("games.jogo_do_bicho"))
        valor_aposta = float(valor_aposta_str)
        if valor_aposta <= 0: flash("O valor da aposta deve ser positivo.", "error"); return redirect(url_for("games.jogo_do_bicho"))
        if user_data["credits"] < valor_aposta: flash("Saldo insuficiente para esta aposta.", "error"); return redirect(url_for("games.jogo_do_bicho"))
        
        if tipo_aposta == "grupo":
            if not (aposta_valor_input.isdigit() and 1 <= int(aposta_valor_input) <= 25):
                flash("Para aposta em grupo, insira um número de 1 a 25.", "error"); return redirect(url_for("games.jogo_do_bicho"))
            aposta_numero = int(aposta_valor_input)
        elif tipo_aposta == "milhar":
            if not (aposta_valor_input.isdigit() and len(aposta_valor_input) == 4):
                flash("Para aposta na milhar, insira um número de 4 dígitos (0000-9999).", "error"); return redirect(url_for("games.jogo_do_bicho"))
            aposta_numero = aposta_valor_input
        elif tipo_aposta == "centena":
            if not (aposta_valor_input.isdigit() and len(aposta_valor_input) == 3):
                flash("Para aposta na centena, insira um número de 3 dígitos (000-999).", "error"); return redirect(url_for("games.jogo_do_bicho"))
            aposta_numero = aposta_valor_input
        elif tipo_aposta == "dezena":
            if not (aposta_valor_input.isdigit() and len(aposta_valor_input) == 2):
                flash("Para aposta na dezena, insira um número de 2 dígitos (00-99).", "error"); return redirect(url_for("games.jogo_do_bicho"))
            aposta_numero = aposta_valor_input
        else: flash("Tipo de aposta inválido.", "error"); return redirect(url_for("games.jogo_do_bicho"))
        
        user_data["credits"] -= valor_aposta; session["user_credits"] = user_data["credits"]
        milhar_sorteada = f"{random.randint(0,9999):04d}"; centena_sorteada = milhar_sorteada[1:]; dezena_sorteada = milhar_sorteada[2:]
        grupo_sorteado_numero = get_grupo_from_milhar(milhar_sorteada)
        grupo_sorteado_nome = GRUPOS_BICHO[grupo_sorteado_numero]["nome"] if grupo_sorteado_numero else "N/A"
        descricao_sorteio = f"Milhar: {milhar_sorteada}, Centena: {centena_sorteada}, Dezena: {dezena_sorteada}, Grupo: {grupo_sorteado_numero} ({grupo_sorteado_nome})"
        premio = 0.0; mensagem_resultado = "Não premiado."
        
        if tipo_aposta == "grupo" and aposta_numero == grupo_sorteado_numero:
            premio = valor_aposta * MULTIPLIERS_BICHO["grupo"]; mensagem_resultado = f"Parabéns! Você acertou o grupo!"
        elif tipo_aposta == "milhar" and aposta_numero == milhar_sorteada:
            premio = valor_aposta * MULTIPLIERS_BICHO["milhar"]; mensagem_resultado = f"Parabéns! Você acertou a milhar!"
        elif tipo_aposta == "centena" and aposta_numero == centena_sorteada:
            premio = valor_aposta * MULTIPLIERS_BICHO["centena"]; mensagem_resultado = f"Parabéns! Você acertou a centena!"
        elif tipo_aposta == "dezena" and aposta_numero == dezena_sorteada:
            premio = valor_aposta * MULTIPLIERS_BICHO["dezena"]; mensagem_resultado = f"Parabéns! Você acertou a dezena!"
            
        if premio > 0:
            user_data["credits"] += premio; session["user_credits"] = user_data["credits"]; flash(f"Você ganhou R$ {premio:.2f}!", "success")
        else: flash("Que pena, não foi desta vez.", "info")
        
        session["ultimo_jogo_bicho"] = {"tipo": tipo_aposta, "numero": aposta_valor_input, "valor_apostado": f"{valor_aposta:.2f}"}
        session["ultimo_resultado_bicho"] = {"descricao_sorteio": descricao_sorteio, "premio": f"{premio:.2f}", "mensagem": mensagem_resultado}
        return redirect(url_for("games.jogo_do_bicho"))
    except ValueError: flash("Valor da aposta inválido.", "error"); return redirect(url_for("games.jogo_do_bicho"))
    except Exception as e: flash(f"Ocorreu um erro ao processar sua aposta: {str(e)}", "error"); return redirect(url_for("games.jogo_do_bicho"))

@game_bp.route("/bet-futebol", methods=["GET"])
def bet_futebol():
    if "user_phone" not in session:
        flash("Você precisa estar logado para jogar.", "error"); return redirect(url_for("auth.login"))
    return render_template("bet_futebol.html", partidas=PARTIDAS_FUTEBOL)

@game_bp.route("/bet-futebol/apostar", methods=["POST"])
def fazer_aposta_futebol():
    if "user_phone" not in session:
        flash("Sessão expirada. Faça login novamente.", "error"); return redirect(url_for("auth.login"))
    phone_number = session["user_phone"]; user_data = users_db.get(phone_number)
    if not user_data: flash("Usuário não encontrado.", "error"); return redirect(url_for("auth.login"))
    try:
        partida_id_str = request.form.get("partida_selecionada")
        escolha_aposta = request.form.get(f"aposta_partida_{partida_id_str}")
        valor_aposta_futebol_str = request.form.get("valor_aposta_futebol")
        
        if not partida_id_str or not escolha_aposta or not valor_aposta_futebol_str:
            flash("Todos os campos da aposta de futebol são obrigatórios.", "error"); return redirect(url_for("games.bet_futebol"))
        
        partida_id = int(partida_id_str); valor_aposta = float(valor_aposta_futebol_str)
        if valor_aposta <= 0: flash("O valor da aposta deve ser positivo.", "error"); return redirect(url_for("games.bet_futebol"))
        if user_data["credits"] < valor_aposta: flash("Saldo insuficiente para esta aposta.", "error"); return redirect(url_for("games.bet_futebol"))
        
        partida_selecionada = next((p for p in PARTIDAS_FUTEBOL if p["id"] == partida_id), None)
        if not partida_selecionada: flash("Partida selecionada inválida.", "error"); return redirect(url_for("games.bet_futebol"))
        
        partida_descricao = f"{partida_selecionada['casa']} vs {partida_selecionada['fora']}"

        user_data["credits"] -= valor_aposta; session["user_credits"] = user_data["credits"]
        resultados_possiveis = ["casa", "empate", "fora"]; resultado_real_partida = random.choice(resultados_possiveis)
        odd_apostada = partida_selecionada["odds"][escolha_aposta]; premio = 0.0; mensagem_resultado_futebol = "Não premiado."
        
        if resultado_real_partida == "casa":
            resultado_partida_texto = f"Resultado: {partida_selecionada['casa']} venceu."
        elif resultado_real_partida == "fora":
            resultado_partida_texto = f"Resultado: {partida_selecionada['fora']} venceu."
        else: resultado_partida_texto = "Resultado: Empate."
        
        if escolha_aposta == resultado_real_partida:
            premio = valor_aposta * odd_apostada; mensagem_resultado_futebol = f"Parabéns! Você acertou o resultado!"
            user_data["credits"] += premio; session["user_credits"] = user_data["credits"]; flash(f"Você ganhou R$ {premio:.2f}!", "success")
        else: flash("Que pena, não foi desta vez.", "info")
        
        session["ultimo_jogo_futebol"] = {
            "partida": partida_descricao, 
            "escolha": escolha_aposta.capitalize(), 
            "odd": f"{odd_apostada:.2f}", 
            "valor_apostado": f"{valor_aposta:.2f}"
        }
        session["ultimo_resultado_futebol"] = {
            "resultado_partida": resultado_partida_texto, 
            "premio": f"{premio:.2f}", 
            "mensagem": mensagem_resultado_futebol
        }
        return redirect(url_for("games.bet_futebol"))
    except ValueError: flash("Valor da aposta inválido.", "error"); return redirect(url_for("games.bet_futebol"))
    except Exception as e: flash(f"Ocorreu um erro ao processar sua aposta de futebol: {str(e)}", "error"); return redirect(url_for("games.bet_futebol"))

@game_blueprint.route("/jogo-do-tigrinho")
def jogo_do_tigrinho():
    return render_template("jogo_tigrinho.html")
