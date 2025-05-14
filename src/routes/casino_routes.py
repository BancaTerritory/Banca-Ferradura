import sys
import os
import random
import time # Potencialmente para o Aviator
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

casino_bp = Blueprint("casino", __name__, url_prefix="/casino")

# --- General Casino Data ---
symbols = ["🐉", "🏮", "💰", "💎", "🐅", "🪙", "🍊", "🔔", "BAR", "🍀", "🧧"] # Generic symbols for older games

roulette_numbers = {
    0: 'green',
    1: 'red', 2: 'black', 3: 'red', 4: 'black', 5: 'red', 6: 'black', 7: 'red', 8: 'black', 9: 'red',
    10: 'black', 11: 'black', 12: 'red', 13: 'black', 14: 'red', 15: 'black', 16: 'red', 17: 'black', 18: 'red',
    19: 'red', 20: 'black', 21: 'red', 22: 'black', 23: 'red', 24: 'black', 25: 'red', 26: 'black', 27: 'red',
    28: 'black', 29: 'black', 30: 'red', 31: 'black', 32: 'red', 33: 'black', 34: 'red', 35: 'black', 36: 'red'
}

# --- Fortune Ox Data ---
fortune_ox_symbols_data = [
    {"name": "ox", "char": "🐂", "payout": 20}, # Wild
    {"name": "gold_ingot", "char": "💰", "payout": 10},
    {"name": "coins", "char": "🪙", "payout": 5},
    {"name": "red_envelope", "char": "🧧", "payout": 2},
    {"name": "oranges", "char": "🍊", "payout": 1},
    {"name": "fireworks", "char": "🎆", "payout": 0.5}
]
fortune_ox_payouts = {s["name"]: s["payout"] for s in fortune_ox_symbols_data}
def get_fortune_ox_random_symbol_name():
    return random.choice([s["name"] for s in fortune_ox_symbols_data])

# --- Sweet Bonanza Data ---
sweet_bonanza_symbols_data = [
    {"name": "red_heart_candy", "char": "💖", "payouts": {8:10, 10:25, 12:50}}, 
    {"name": "purple_candy", "char": "🟣", "payouts": {8:2.5, 10:5, 12:25}},
    {"name": "green_candy", "char": "🟢", "payouts": {8:2, 10:4, 12:15}},
    {"name": "blue_candy", "char": "🍬", "payouts": {8:1.5, 10:2, 12:12}},
    {"name": "apple", "char": "❤️", "payouts": {8:1, 10:1.5, 12:10}},
    {"name": "plum", "char": "💜", "payouts": {8:0.8, 10:1.2, 12:8}},
    {"name": "watermelon", "char": "🍉", "payouts": {8:0.5, 10:1, 12:5}},
    {"name": "grapes", "char": "🍇", "payouts": {8:0.4, 10:0.9, 12:4}},
    {"name": "banana", "char": "🍌", "payouts": {8:0.25, 10:0.75, 12:2}},
    {"name": "lollipop_scatter", "char": "🍭", "payouts": {4:3, 5:5, 6:100}, "is_scatter": True},
    {"name": "bomb_multiplier", "char": "💣", "is_multiplier": True}
]

def get_sweet_bonanza_random_symbol_name(is_free_spin=False):
    pool = [s["name"] for s in sweet_bonanza_symbols_data if not s.get("is_multiplier")]
    if not is_free_spin:
        pool = [s for s in pool if s != "lollipop_scatter" or random.random() < 0.15]
    else: 
        if random.random() < 0.2: return "bomb_multiplier"
        if random.random() < 0.25: return "lollipop_scatter"
    return random.choice(pool)

# --- Blackjack Data & Helpers ---
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

def create_deck():
    return [{'rank': rank, 'suit': suit} for suit in SUITS for rank in RANKS]

def shuffle_deck(deck):
    random.shuffle(deck)
    return deck

def deal_card(deck):
    return deck.pop()

def calculate_hand_value(hand):
    ace_count = sum(1 for card in hand if card['rank'] == 'A')
    value = 0
    for card in hand:
        if card['rank'].isdigit():
            value += int(card['rank'])
        elif card['rank'] in ['J', 'Q', 'K']:
            value += 10
        elif card['rank'] == 'A':
            value += 11
    while value > 21 and ace_count > 0:
        value -= 10
        ace_count -= 1
    return value

def get_random_symbols(count=9):
    return [random.choice(symbols) for _ in range(count)]

@casino_bp.route("")
def casino_lobby():
    if not session.get("user_phone"):
        flash("Você precisa estar logado para acessar o cassino.", "error")
        return redirect(url_for("auth.login_page"))
    
    games_for_lobby = [
        {"name": "Blackjack", "endpoint": "casino.blackjack_game", "img_card": "img/game_cards/blackjack_card.png"},
        {"name": "Sweet Bonanza", "endpoint": "casino.sweet_bonanza_game", "img_card": "img/game_cards/sweet_bonanza_card.png"},
        {"name": "Fortune Ox", "endpoint": "casino.fortune_ox_game", "img_card": "img/game_cards/fortune_ox_card.png"},
        {"name": "Aviator", "endpoint": "casino.aviator_game", "img_card": "img/game_cards/aviator_card.png"},
        {"name": "Fortune Tiger", "endpoint": "casino.fortune_tiger_game", "img_card": "img/game_cards/fortune_tiger_card.png"},
        {"name": "Fortune Dragon", "endpoint": "casino.fortune_dragon_game", "img_card": "img/game_cards/fortune_dragon_card.png"},
        {"name": "Roleta", "endpoint": "casino.roulette_game", "img_card": "img/game_cards/roulette_card_placeholder.png"},
    ]
    new_games_list = list(games_for_lobby) 
    popular_games_list = random.sample(games_for_lobby, k=min(len(games_for_lobby), 4))
    
    for game_list in [new_games_list, popular_games_list]:
        for game_data in game_list:
            card_path = os.path.join(os.path.dirname(__file__), "..", "static", game_data['img_card'])
            if not os.path.exists(card_path):
                print(f"Card image {card_path} not found for game {game_data['name']}. Please create one.")

    return render_template("casino/casino_lobby.html", 
                           new_games=new_games_list, 
                           popular_games=popular_games_list)

# ... (Rotas Fortune Dragon, Tiger, Roleta, Aviator, Fortune Ox, Sweet Bonanza - OMITIDAS POR BREVIDADE) ...
@casino_bp.route("/fortune-dragon")
def fortune_dragon_game():
    if not session.get("user_phone"): return redirect(url_for("auth.login_page"))
    return render_template("casino/fortune_dragon.html", game_name="Fortune Dragon")

@casino_bp.route("/fortune-dragon/spin", methods=["POST"])
def fortune_dragon_spin():
    if not session.get("user_phone"): return jsonify({"error": "Usuário não logado"}), 401
    data = request.get_json(); bet_amount = data.get("bet_amount")
    if not isinstance(bet_amount, (int, float)) or bet_amount <= 0: return jsonify({"error": "Valor da aposta inválido"}), 400
    current_credits = float(session.get("user_credits", 0.0))
    if bet_amount > current_credits: return jsonify({"error": "Saldo insuficiente"}), 400
    current_credits -= bet_amount; win_multiplier = 0
    final_symbols = get_random_symbols(9)
    if final_symbols[4] == "🐉": win_multiplier = random.choice([0,0,0.5,1,1.5,2,3,5,10])
    winnings = bet_amount * win_multiplier; current_credits += winnings
    session["user_credits"] = f"{current_credits:.2f}"
    return jsonify({"success": True, "new_balance": session["user_credits"], "winnings": f"{winnings:.2f}", "final_symbols": final_symbols})

@casino_bp.route("/fortune-tiger")
def fortune_tiger_game():
    if not session.get("user_phone"): return redirect(url_for("auth.login_page"))
    return render_template("casino/fortune_tiger.html", game_name="Fortune Tiger")

@casino_bp.route("/fortune-tiger/spin", methods=["POST"])
def fortune_tiger_spin():
    if not session.get("user_phone"): return jsonify({"error": "Usuário não logado"}), 401
    data = request.get_json(); bet_amount = data.get("bet_amount")
    if not isinstance(bet_amount, (int, float)) or bet_amount <= 0: return jsonify({"error": "Valor da aposta inválido"}), 400
    current_credits = float(session.get("user_credits", 0.0))
    if bet_amount > current_credits: return jsonify({"error": "Saldo insuficiente"}), 400
    current_credits -= bet_amount; win_multiplier = 0
    final_symbols_line = [random.choice(symbols) for _ in range(3)]
    if final_symbols_line[1] == "🐅": win_multiplier = random.choice([0.5,1,2,5,10,20])
    elif final_symbols_line[0] == final_symbols_line[1] == final_symbols_line[2]:
        win_multiplier = random.choice([1,2,3,5,8,15])
        if final_symbols_line[0] == "🐅": win_multiplier = random.choice([25,50,100])
    winnings = bet_amount * win_multiplier; current_credits += winnings
    session["user_credits"] = f"{current_credits:.2f}"
    display_symbols = get_random_symbols(9); display_symbols[3:6] = final_symbols_line
    return jsonify({"success": True, "new_balance": session["user_credits"], "winnings": f"{winnings:.2f}", "final_symbols": display_symbols})

@casino_bp.route("/roulette")
def roulette_game():
    if not session.get("user_phone"): return redirect(url_for("auth.login_page"))
    return render_template("casino/roulette_game.html", game_name="Roleta")

@casino_bp.route("/roulette/spin", methods=["POST"])
def roulette_spin():
    if not session.get("user_phone"): return jsonify({"error": "Usuário não logado"}), 401
    data = request.get_json(); bet_amount = data.get("bet_amount"); bet_type = data.get("bet_type"); bet_value = data.get("bet_value")
    if not all([bet_amount, bet_type, bet_value]): return jsonify({"error": "Dados da aposta incompletos"}), 400
    if not isinstance(bet_amount, (int, float)) or bet_amount <= 0: return jsonify({"error": "Valor da aposta inválido"}), 400
    current_credits = float(session.get("user_credits", 0.0))
    if bet_amount > current_credits: return jsonify({"error": "Saldo insuficiente"}), 400
    current_credits -= bet_amount; winnings = 0
    winning_number = random.choice(list(roulette_numbers.keys())); winning_color = roulette_numbers[winning_number]
    payout_multiplier = 0
    if bet_type == "color" and bet_value == winning_color: payout_multiplier = 2
    elif bet_type == "parity" and winning_number != 0:
        if bet_value == "even" and winning_number % 2 == 0: payout_multiplier = 2
        elif bet_value == "odd" and winning_number % 2 != 0: payout_multiplier = 2
    elif bet_type == "range" and winning_number != 0:
        if bet_value == "1-18" and 1 <= winning_number <= 18: payout_multiplier = 2
        elif bet_value == "19-36" and 19 <= winning_number <= 36: payout_multiplier = 2
    winnings = bet_amount * payout_multiplier; current_credits += winnings
    session["user_credits"] = f"{current_credits:.2f}"
    return jsonify({"success": True, "new_balance": session["user_credits"], "winnings": f"{winnings:.2f}", "winning_number": winning_number, "winning_color": winning_color})

@casino_bp.route("/aviator")
def aviator_game():
    if not session.get("user_phone"): return redirect(url_for("auth.login_page"))
    return render_template("casino/aviator_game.html", game_name="Aviator")

@casino_bp.route("/aviator/bet", methods=["POST"])
def aviator_bet():
    if not session.get("user_phone"): return jsonify({"error": "Usuário não logado"}), 401
    data = request.get_json(); bet_amount = data.get("bet_amount")
    if not isinstance(bet_amount, (int, float)) or bet_amount <= 0: return jsonify({"error": "Valor da aposta inválido"}), 400
    current_credits = float(session.get("user_credits", 0.0))
    if bet_amount > current_credits: return jsonify({"error": "Saldo insuficiente"}), 400
    current_credits -= bet_amount
    session["user_credits"] = f"{current_credits:.2f}"
    return jsonify({"success": True, "new_balance": session["user_credits"]})

@casino_bp.route("/aviator/cashout", methods=["POST"])
def aviator_cashout():
    if not session.get("user_phone"): return jsonify({"error": "Usuário não logado"}), 401
    data = request.get_json(); bet_amount = data.get("bet_amount"); multiplier = data.get("multiplier")
    if not all([isinstance(bet_amount, (int,float)), isinstance(multiplier, (int,float))]) or bet_amount <=0 or multiplier <=0: return jsonify({"error": "Dados de cash out inválidos"}),400
    current_credits = float(session.get("user_credits", 0.0))
    winnings = bet_amount * multiplier; current_credits += winnings
    session["user_credits"] = f"{current_credits:.2f}"
    return jsonify({"success": True, "new_balance": session["user_credits"], "winnings": f"{winnings:.2f}"})

@casino_bp.route("/fortune-ox")
def fortune_ox_game():
    if not session.get("user_phone"): return redirect(url_for("auth.login_page"))
    return render_template("casino/fortune_ox_game.html", game_name="Fortune Ox")

@casino_bp.route("/fortune-ox/spin", methods=["POST"])
def fortune_ox_spin():
    if not session.get("user_phone"): return jsonify({"error": "Usuário não logado"}), 401
    data = request.get_json(); bet_amount = data.get("bet_amount")
    if not isinstance(bet_amount, (int, float)) or bet_amount <= 0: return jsonify({"error": "Valor da aposta inválido"}), 400
    current_credits = float(session.get("user_credits", 0.0))
    if bet_amount > current_credits: return jsonify({"error": "Saldo insuficiente"}), 400
    current_credits -= bet_amount
    final_reels = [[get_fortune_ox_random_symbol_name() for _ in range(3)] for _ in range(3)]
    feature_triggered = False; message = "Boa sorte!"
    if random.random() < 0.20:
        feature_triggered = True; message = "Re-spin do Touro da Sorte!"
        synced_reel = [get_fortune_ox_random_symbol_name() for _ in range(3)]
        final_reels[0] = list(synced_reel); final_reels[2] = list(synced_reel)
        final_reels[1] = [get_fortune_ox_random_symbol_name() for _ in range(3)]
    total_payout_multiplier = 0
    paylines = [[(0,0),(1,0),(2,0)],[(0,1),(1,1),(2,1)],[(0,2),(1,2),(2,2)],[(0,0),(1,1),(2,2)],[(0,2),(1,1),(2,0)]]
    for line_coords in paylines:
        s = [final_reels[r][c] for r,c in line_coords]; s1,s2,s3 = s[0],s[1],s[2]; win_sym = None
        if s1==s2==s3: win_sym=s1
        elif s1==s2 and s3=="ox": win_sym=s1
        elif s1==s3 and s2=="ox": win_sym=s1
        elif s2==s3 and s1=="ox": win_sym=s2
        elif s1=="ox" and s2=="ox" and s3!="ox": win_sym=s3
        elif s1=="ox" and s3=="ox" and s2!="ox": win_sym=s2
        elif s2=="ox" and s3=="ox" and s1!="ox": win_sym=s1
        elif s1=="ox" and s2=="ox" and s3=="ox": win_sym="ox"
        if win_sym and win_sym in fortune_ox_payouts: total_payout_multiplier += fortune_ox_payouts[win_sym]
    winnings = 0
    if total_payout_multiplier > 0: 
        winnings = bet_amount * total_payout_multiplier * 10
        message = f"Você ganhou R$ {winnings:.2f}! Multiplicador x10!"
        if feature_triggered: message = f"Re-spin GIGANTE! Você ganhou R$ {winnings:.2f}!"
    elif feature_triggered: message = "Re-spin não premiou."
    else: message = "Sem prêmio."
    current_credits += winnings; session["user_credits"] = f"{current_credits:.2f}"
    return jsonify({"success":True, "new_balance":session["user_credits"], "winnings":f"{winnings:.2f}", "final_reels":final_reels, "message":message, "feature_triggered":feature_triggered})

@casino_bp.route("/sweet-bonanza")
def sweet_bonanza_game():
    if not session.get("user_phone"): return redirect(url_for("auth.login_page"))
    return render_template("casino/sweet_bonanza_game.html", game_name="Sweet Bonanza")

@casino_bp.route("/sweet-bonanza/spin", methods=["POST"])
def sweet_bonanza_spin():
    if not session.get("user_phone"): return jsonify({"error": "Usuário não logado"}), 401
    data = request.get_json(); bet_amount = data.get("bet_amount")
    if not isinstance(bet_amount, (int, float)) or bet_amount <= 0: return jsonify({"error": "Valor da aposta inválido"}), 400
    current_credits = float(session.get("user_credits", 0.0))
    if bet_amount > current_credits: return jsonify({"error": "Saldo insuficiente"}), 400
    current_credits -= bet_amount; session["user_credits"] = f"{current_credits:.2f}"
    grid_rows=5; grid_cols=6; min_cluster_size=8; total_winnings_this_spin=0; message="Gire para um mundo de doces!"; free_spins_triggered=False
    current_grid = [[get_sweet_bonanza_random_symbol_name() for _ in range(grid_cols)] for _ in range(grid_rows)]
    flat_grid_symbols = [s for row in current_grid for s in row]
    scatter_count = flat_grid_symbols.count("lollipop_scatter")
    if scatter_count >= 4:
        free_spins_triggered=True; scatter_payout_multiplier=0
        s_info = next((s for s in sweet_bonanza_symbols_data if s["name"]=="lollipop_scatter"),None)
        if s_info: scatter_payout_multiplier = s_info["payouts"].get(min(scatter_count,6),0)
        total_winnings_this_spin += bet_amount * scatter_payout_multiplier
        message = f"{scatter_count} Pirulitos! Rodadas Grátis (simulado)! Ganho Scatter: R$ {bet_amount*scatter_payout_multiplier:.2f}"
    symbol_counts = Counter(s for s in flat_grid_symbols if s not in ["lollipop_scatter","bomb_multiplier"])
    winning_clusters_details=[]
    for sym_name, count in symbol_counts.items():
        if count >= min_cluster_size:
            s_data = next((s for s in sweet_bonanza_symbols_data if s["name"]==sym_name),None)
            if s_data and "payouts" in s_data:
                pay_mult = s_data["payouts"].get(min(count,12),s_data["payouts"].get(10,s_data["payouts"].get(8,0)))
                if pay_mult > 0: total_winnings_this_spin += bet_amount*pay_mult; winning_clusters_details.append({"s":sym_name,"c":count,"w":bet_amount*pay_mult})
    has_bomb="bomb_multiplier" in flat_grid_symbols; spin_mult_val=1
    if has_bomb and total_winnings_this_spin > 0:
        spin_mult_val=random.choice([2,3,5,8,10,15,25,50,100]); total_winnings_this_spin*=spin_mult_val; message+=f" Bomba x{spin_mult_val}!"
    if not free_spins_triggered and total_winnings_this_spin > 0: message = f"Doce Vitória! Ganhou R$ {total_winnings_this_spin:.2f}!"
    elif not free_spins_triggered and total_winnings_this_spin == 0: message = "Sem combinação doce."
    current_credits = float(session.get("user_credits",0.0)); current_credits += total_winnings_this_spin; session["user_credits"]=f"{current_credits:.2f}"
    return jsonify({"success":True, "new_balance":session["user_credits"], "winnings":f"{total_winnings_this_spin:.2f}", "final_grid_symbols":flat_grid_symbols, "winning_clusters":winning_clusters_details, "message":message, "free_spins_triggered":free_spins_triggered, "applied_multiplier":spin_mult_val if has_bomb and total_winnings_this_spin > 0 else 1})

# --- Blackjack Routes ---
@casino_bp.route("/blackjack")
def blackjack_game():
    if not session.get("user_phone"):
        flash("Você precisa estar logado para jogar Blackjack.", "error")
        return redirect(url_for("auth.login_page"))
    # Clear previous game state if any
    session.pop('blackjack_deck', None)
    session.pop('blackjack_player_hand', None)
    session.pop('blackjack_dealer_hand', None)
    session.pop('blackjack_bet', None)
    return render_template("casino/blackjack_game.html", game_name="Blackjack")

@casino_bp.route("/blackjack/action", methods=["POST"])
def blackjack_action():
    if not session.get("user_phone"):
        return jsonify({"error": "Usuário não logado"}), 401

    data = request.get_json()
    action = data.get("action")
    bet_amount = data.get("bet_amount")
    current_credits = float(session.get("user_credits", 0.0))
    response_data = {
        "player_hand": [], "dealer_hand": [], "message": "",
        "new_balance": f"{current_credits:.2f}", "game_over": False
    }

    if action == "deal":
        if not isinstance(bet_amount, (int, float)) or bet_amount <= 0:
            return jsonify({"error": "Valor da aposta inválido"}), 400
        if bet_amount > current_credits:
            return jsonify({"error": "Saldo insuficiente"}), 400
        
        current_credits -= bet_amount
        session["user_credits"] = f"{current_credits:.2f}"
        session["blackjack_bet"] = bet_amount

        deck = shuffle_deck(create_deck() * 6) # Use 6 decks for more casino-like feel
        player_hand = [deal_card(deck), deal_card(deck)]
        dealer_hand = [deal_card(deck), deal_card(deck)]
        session['blackjack_deck'] = deck
        session['blackjack_player_hand'] = player_hand
        session['blackjack_dealer_hand'] = dealer_hand

        response_data["player_hand"] = player_hand
        response_data["dealer_hand"] = dealer_hand # Dealer's second card will be hidden by frontend initially
        response_data["new_balance"] = f"{current_credits:.2f}"
        player_value = calculate_hand_value(player_hand)
        dealer_value_shown = calculate_hand_value([dealer_hand[0]]) # Only first card shown

        if player_value == 21 and dealer_value_shown != 10 and dealer_value_shown != 11: # Player Blackjack, dealer no BJ check yet
            # Blackjack Payout 3:2
            winnings = bet_amount * 1.5
            current_credits += bet_amount + winnings # Return original bet + winnings
            session["user_credits"] = f"{current_credits:.2f}"
            response_data["message"] = f"Blackjack! Você ganhou R$ {winnings:.2f}!"
            response_data["new_balance"] = f"{current_credits:.2f}"
            response_data["game_over"] = True
        elif player_value == 21 and (dealer_hand[0]['rank'] == 'A' or dealer_hand[0]['rank'] in ['10','J','Q','K']) and calculate_hand_value(dealer_hand) == 21:
            # Player and Dealer Blackjack - Push
            current_credits += bet_amount # Return original bet
            session["user_credits"] = f"{current_credits:.2f}"
            response_data["message"] = "Push! Ambos têm Blackjack."
            response_data["new_balance"] = f"{current_credits:.2f}"
            response_data["game_over"] = True
        else:
            response_data["message"] = "Sua vez. Hit ou Stand?"
        return jsonify(response_data)

    # --- Actions for an ongoing game (Hit, Stand) ---
    player_hand = session.get('blackjack_player_hand', [])
    dealer_hand = session.get('blackjack_dealer_hand', [])
    deck = session.get('blackjack_deck', [])
    current_bet = session.get('blackjack_bet', 0)

    if not all([player_hand, dealer_hand, deck, current_bet]):
        return jsonify({"error": "Jogo não iniciado ou estado inválido. Por favor, comece um novo jogo."}), 400

    if action == "hit":
        player_hand.append(deal_card(deck))
        session['blackjack_player_hand'] = player_hand
        player_value = calculate_hand_value(player_hand)
        response_data["player_hand"] = player_hand
        response_data["dealer_hand"] = dealer_hand
        response_data["new_balance"] = f"{current_credits:.2f}"

        if player_value > 21:
            response_data["message"] = f"Você estourou com {player_value}! Dealer vence."
            response_data["game_over"] = True
            # Bet already deducted, no winnings
        elif player_value == 21:
             # Player has 21, automatically stands. Proceed to dealer's turn.
            response_data["message"] = "Você tem 21! Vez do Dealer."
            # Fall through to dealer's play logic (similar to stand)
            pass # Let it proceed to dealer play logic below if action was stand or player got 21
        else:
            response_data["message"] = "Hit ou Stand?"
        
        if response_data["game_over"] or player_value == 21: # if game over or player has 21, proceed to dealer logic if player didn't bust
             if not (player_value > 21): # if player didn't bust
                # Dealer's turn
                dealer_value = calculate_hand_value(dealer_hand)
                while dealer_value < 17:
                    dealer_hand.append(deal_card(deck))
                    dealer_value = calculate_hand_value(dealer_hand)
                session['blackjack_dealer_hand'] = dealer_hand
                response_data["dealer_hand"] = dealer_hand # Update dealer hand for frontend

                if dealer_value > 21:
                    response_data["message"] = f"Dealer estourou com {dealer_value}! Você venceu R$ {current_bet:.2f}!"
                    current_credits += current_bet * 2 # Original bet + winnings
                elif player_value > dealer_value:
                    response_data["message"] = f"Você venceu com {player_value} contra {dealer_value} do Dealer! Ganhou R$ {current_bet:.2f}!"
                    current_credits += current_bet * 2
                elif player_value < dealer_value:
                    response_data["message"] = f"Dealer venceu com {dealer_value} contra {player_value}."
                    # Bet already deducted
                else: # Push
                    response_data["message"] = f"Push! Empate com {player_value}."
                    current_credits += current_bet # Return original bet
                
                session["user_credits"] = f"{current_credits:.2f}"
                response_data["new_balance"] = f"{current_credits:.2f}"
                response_data["game_over"] = True
        return jsonify(response_data)

    if action == "stand":
        player_value = calculate_hand_value(player_hand)
        dealer_value = calculate_hand_value(dealer_hand)

        # Dealer plays (hits until 17 or more)
        while dealer_value < 17:
            dealer_hand.append(deal_card(deck))
            dealer_value = calculate_hand_value(dealer_hand)
        
        session['blackjack_dealer_hand'] = dealer_hand
        response_data["player_hand"] = player_hand
        response_data["dealer_hand"] = dealer_hand # Now reveal dealer's full hand
        response_data["game_over"] = True

        if dealer_value > 21:
            response_data["message"] = f"Dealer estourou com {dealer_value}! Você venceu R$ {current_bet:.2f}!"
            current_credits += current_bet * 2 # Original bet + winnings
        elif player_value > dealer_value:
            response_data["message"] = f"Você venceu com {player_value} contra {dealer_value} do Dealer! Ganhou R$ {current_bet:.2f}!"
            current_credits += current_bet * 2
        elif player_value < dealer_value:
            response_data["message"] = f"Dealer venceu com {dealer_value} contra {player_value}."
            # Bet already deducted
        else: # Push
            response_data["message"] = f"Push! Empate com {player_value}."
            current_credits += current_bet # Return original bet
        
        session["user_credits"] = f"{current_credits:.2f}"
        response_data["new_balance"] = f"{current_credits:.2f}"
        return jsonify(response_data)

    return jsonify({"error": "Ação inválida"}), 400


