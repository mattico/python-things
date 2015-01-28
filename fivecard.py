# Matt Ickstadt  ickst001

# Clarifications:
# Ante is required
# Always reshuffle when dealing
# no betting before discard
# ai is dealer
# announce what ai is doing
# betting always goes Human -> computer -> h -> c
# only 4 rounds of betting as above ^^^^^^
# everyone reveals cards every time
# game ends when either player can't make ante
# display the cards graphicslly (tkinter) optional

import random
from itertools import combinations
import math
from time import sleep

# constant definitions
ranks = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
suits = ('C', 'S', 'D', 'H')

starting_money = 1000
starting_cards = 5
max_draw = 4
decks = 1
ante = 50 # $50.00

# variables
deck = [x+y for x in ranks for y in suits] * decks

pot = 0
round = 0 # each time a new hand is dealt is a round
turn = 0 # each time a player gets to choose to call/fold/pass/etc. is a turn

player = {
    "money": starting_money,
    "cards": [],
    "bet": 0,
    "all-in": False,
    "action-history": ["start"],
}

# AI is Dealer
ai = {
    "money": starting_money,
    "cards": [],
    "hand-strength": 0,
    "bet": 0,
    "all-in": False,
    "action-history": ["start"],
}

# deal cards
def draw(num):
    random.shuffle(deck)
    return [deck.pop() for x in range(num)]

# not really necessary since we don't support fractional dollars
# anymore, but I don't feel like removing it
def format_money(money):
    return "${:.2f}".format(money)

# determines what type of hand it is, and gives it a unique score
def classify_hand(hand):
    if len(hand) == 0:
        return ("Fold", 0)

    global ranks, suits

    hand_type = ""
    score = 0

    # count how often each rank appears to see if 2-pair, set, etc
    counts = [0 for x in range(len(ranks))]
    for card in hand:
        counts[ranks.index(card[0])] += 1

    sorted_counts = list(reversed(sorted(counts)))
    rev_counts = list(reversed(counts))
    kickers = []

    is_straight, is_flush = False, False

    if sorted_counts[0] == 4:
        hand_type = "quads" # aka four of a kind
        score = 7 * (10**10)
        kickers = [x for x in range(len(counts)) if counts[x] == 1]
    elif sorted_counts[0] == 3 and sorted_counts[1] == 2:
        hand_type = "boat" # aka full house
        score = 6 * (10**10)
    elif sorted_counts[0] == 3 and sorted_counts[1] == 1 and sorted_counts[2] == 1:
        hand_type = "set" # aka three of a kind
        score = 3 * (10**10)
        kickers = [x for x in range(len(counts)) if counts[x] == 1]
    elif sorted_counts[0] == 2 and sorted_counts[1] == 2 and sorted_counts[2] == 1:
        hand_type = "two pair"
        score = 2 * (10**10)
        kickers = [x for x in range(len(counts)) if counts[x] == 1]
    elif sorted_counts[0] == 2:
        hand_type = "one pair"
        score = 1 * (10**10)
        kickers = [x for x in range(len(counts)) if counts[x] == 1]
    else:
        is_flush = True
        for card in hand:
            if card[1] != hand[0][1]:
                is_flush = False

        is_straight = True
        for count in counts:
            if count > 1: # can only have one of each rank
                is_straight = False
        
        if is_straight:
            # find lowest card value
            for i in range(len(counts)):
                if counts[i] > 0:
                    a = i
                    break
            # highest card value
            for i in range(len(rev_counts)):
                if rev_counts[i] > 0:
                    b = 12-i
                    break
            # if difference is 4, is straight
            if b-a != 4:
                is_straight = False

        if is_straight and is_flush:
            hand_type = "straight-flush"
            score = 8 * (10**10)
        elif is_straight:
            hand_type = "straight"
            score = 4 * (10**10)
        elif is_flush:
            hand_type = "flush"
            score = 5 * (10**10)
        else:
            for i in range(len(rev_counts)):
                if rev_counts[i] > 0:
                    hand_type = ranks[12-i] + "-high"
                    break
    
    # Add high cards to score
    if len(kickers) == 0: # no kickers
        mult = 8
        for i in range(len(rev_counts)):
            if rev_counts[i] > 0:
                for j in range(rev_counts[i]):
                    if i == 0 and is_straight: # aces count as one if in straight
                        i = 12
                    score += (13-i) * (10**mult)
                    mult -= 2
                    if mult == 0:
                        return (hand_type, score)
    else:
        mult = 8
        for i in reversed(sorted(kickers)): # kickers go first
            score += (13-i) * (10**mult)
            mult -= 2
        for i in range(len(rev_counts)): # non-kicker high cards are less important
            if rev_counts[i] > 0 and i not in kickers:
                for j in range(rev_counts[i]):
                    if i == 0 and is_straight: # aces count as one if in straight
                        i = 12
                    score += (13-i) * (10**mult)
                    mult -= 2
                    if mult == 0:
                        return (hand_type, score)

    return (hand_type, score)

# hand strength for PEH
def hand_strength(hand, samples):
    if len(hand) == 0:
        return 0

    deck = [x+y for x in ranks for y in suits if x+y not in hand]

    ahead, tied, behind = 0, 0, 0
    ourrank = classify_hand(hand)[1]

    comb = list(combinations(deck, 5))
    if len(comb) < samples:
        samplespace = comb
    else:
        samplespace = random.sample(comb, samples)

    dot = 0

    for cards in samplespace:

        dot += 1
        if samples > 1000 and dot % (samples/10) == 0:
            print('.', end="", flush=True)

        opprank = classify_hand(cards)[1]
        if ourrank > opprank:
            ahead += 1
        elif ourrank < opprank:
            behind += 1
        else:
            tied += 1

    return (ahead+tied/2)/(ahead+tied+behind)

# (positive potential, negative potential) for hand
def hand_potential(hand, samples):
    if len(hand) == 0:
        return 0

    deck = [x+y for x in ranks for y in suits if x+y not in hand]
    
    ahead, behind, tied = 0, 1, 2

    HP = [[0 for x in range(3)] for x in range(3)]
    HPTotal = [0 for x in range(3)]
    ourrank = classify_hand(hand)[1]

    comb = list(combinations(deck, 5))
    if len(comb) < samples:
        samplespace = comb
    else:
        samplespace = random.sample(comb, samples)

    dot = 0

    for cards in samplespace:

        dot += 1
        if samples > 1000 and dot % (samples/10) == 0:
            print('.', end="", flush=True)

        opprank = classify_hand(cards)[1]

        if ourrank > opprank:
            index = ahead
        elif ourrank < opprank:
            index = behind
        else:
            index = tied
        HPTotal[index] += 1

        # modified algorithm to add discard possibilities
        for x in range(1, 5):
            lcards = list(cards)
            random.shuffle(lcards)
            lcards = lcards[x:]
            lcards.extend(random.sample(deck, x))
            opprank2 = classify_hand(lcards)[1]
            if ourrank > opprank2:
                HP[index][ahead] += 1
            elif ourrank < opprank2:
                HP[index][behind] += 1
            else:
                HP[index][tied] += 1
    try:
        Ppot = (HP[behind][ahead]+HP[behind][tied]/2+HP[tied][ahead]/2)/(HPTotal[behind]+HPTotal[tied])
    except:
        Ppot = 1.0
    try:
        Npot = (HP[ahead][behind]+HP[tied][behind]/2+HP[ahead][tied]/2)/(HPTotal[ahead]+HPTotal[tied])
    except:
        Npot = 1.0
    return(Ppot, Npot)

# http://en.wikipedia.org/wiki/Poker_Effective_Hand_Strength_(EHS)_algorithm
# use discard=False if the player has no more opportunities to discard (end of round)
def effective_hand_strength(hand, discard, samples):
    
    if len(hand) == 0:
        return 0
    HS = hand_strength(hand, samples)
    if discard:
        PPOT, NPOT = hand_potential(hand, samples)
        return HS * (1-NPOT) + (1-HS) * PPOT
    else:
        return HS

# actions
def player_bet():
    global pot, player, ai

    amount = int(input("enter bet amount: $"))

    if amount < 0:
        print("negative bet")
        player_bet()
        return -1

    if amount < ai["bet"] - player["bet"]:
        print("must bet more than ai's bet")
        player_bet()
        return -1

    if amount > player["money"]: # all in
        print(format_money(amount), "bet is greater than player's money (", format_money(player["money"]), "), going all-in")
        player["all-in"] = True
        player["action-history"].append("all-in")
        amount = player["money"]

    if amount > ai["money"]: # all in
        print(format_money(amount), "bet is greater than ai's money (", format_money(ai["money"]), "), going all-in")
        player["all-in"] = True
        player["action-history"].append("all-in")
        amount = ai["money"]
        
    pot += amount
    player["money"] -= amount
    player["bet"] += amount

    player["action-history"].append("bet")
    print("bet", format_money(amount), "- have", format_money(player["money"]))
    return 0

def ai_bet(amount):
    global pot, player, ai

    if amount < 0:
        return -2

    if amount < player["bet"] - ai["bet"]:
        return -1

    if amount > ai["money"]: # all in
        print("Ai goes all-in")
        ai["all-in"] = True
        ai["action-history"].append("all-in")
        ai_bet(ai["money"])
        return -1

    if amount > player["money"]: # all in
        print("Ai goes all-in")
        ai["all-in"] = True
        amount = player["money"]
        ai["action-history"].append("all-in")
        ai_bet(player["money"])
        return -1

    pot += amount
    ai["money"] -= amount
    ai["bet"] += amount

    ai["action-history"].append("bet")
    print("Ai bet", format_money(amount), "- has", format_money(ai["money"]))

def player_discard():
    global player, deck, max_draw

    discards = input("Enter cards to discard: ").upper().split()
    if len(discards) > max_draw:
        print("Can only discard up to {} cards".format(max_draw))
        player_discard()
        return

    for card in discards:
        try:
            player["cards"].remove(card)
        except:
            print(card, "is not a valid card")
            player_discard()
            return

    player["action-history"].append("draw")
    player["cards"] += draw(5-len(player["cards"]))
    print("Player Cards:", player["cards"])

def ai_discard(discards): # list of cards to discard
    global ai, deck

    print("Ai discards", len(discards))

    for card in discards:
        ai["cards"].remove(card)

    ai["action-history"].append("draw")
    ai["cards"] += draw(5-len(ai["cards"]))
    return

def player_call():
    global ai, player, pot
    if ai["all-in"]:
        player["all-in"] = True
        player["action-history"].append("all-in")
    player["action-history"].append("call")
    
    amount = ai["bet"] - player["bet"]

    pot += amount
    player["money"] -= amount
    player["bet"] += amount

def ai_call():
    global player, ai, pot
    print("Ai calls")
    if player["all-in"]:
        ai["all-in"] = True
        ai["action-history"].append("all-in")

    ai["action-history"].append("call")
    
    amount = player["bet"] - ai["bet"]

    pot += amount
    ai["money"] -= amount
    ai["bet"] += amount

def player_raise():
    global pot, player, ai

    amount = int(input("enter raise amount: $"))

    if amount < 0:
        print("negative raise")
        player_raise()
        return -1

    amount += ai["bet"] - player["bet"]

    if amount > player["money"]: # all in
        print(format_money(amount), "raise is greater than player's money (", format_money(player["money"]), "), going all-in")
        player["all-in"] = True
        player["action-history"].append("all-in")
        amount = player["money"]

    # TODO: Should we let player raise more than ai has?
    if amount > ai["money"]: # all in
        print(format_money(amount), "raise is greater than ai's money (", format_money(ai["money"]), "), going all-in")
        player["all-in"] = True
        player["action-history"].append("all-in")
        amount = ai["money"]

    pot += amount
    player["money"] -= amount
    player["bet"] += amount

    player["action-history"].append("raise")
    print("bet", format_money(amount), "- have", format_money(player["money"]))
    return 0

def ai_raise(amount):
    global pot, player, ai

    if amount < 0:
        return -2

    amount += player["bet"] - ai["bet"]

    if amount > ai["money"]: # all in
        print("Ai goes all-in")
        ai["all-in"] = True
        ai["action-history"].append("all-in")
        amount = ai["money"]

    if amount > player["money"]: # all in
        print("Ai goes all-in")
        ai["all-in"] = True
        ai["action-history"].append("all-in")
        amount = player["money"]
        return 1

    pot += amount
    ai["money"] -= amount
    ai["bet"] += amount

    ai["action-history"].append("raise")
    print("Ai bet", format_money(amount), "- has", format_money(ai["money"]))

def player_fold():
    global player
    player["action-history"].append("fold")

def ai_fold():
    global ai
    ai["action-history"].append("fold")
    print("Ai folds")

def player_pass():
    global player
    player["action-history"].append("pass")

def ai_pass():
    global ai
    ai["action-history"].append("pass")
    print("Ai passes")

def ante_up():
    global player, ai, ante, pot
    player["money"] -= ante
    ai["money"] -= ante
    pot += ante * 2
    print("Player and Ai ante", format_money(ante))

def player_turn(actions):

    actionstring = "/".join(map(str, actions)) + ": "

    action = input(actionstring)

    if action[0] == 'b':
        player_bet()
    elif action[0] == 'p':
        player_pass()
    elif action[0] == 'f':
        player_fold()
    elif action[0] == 'r':
        player_raise()
    elif action[0] == 'c':
        player_call()
    elif action[0] == 'd':
        player_discard()
    else:
        print(action, "is not a valid action")
        player_turn(actions)
        return

# function to semi-randomly decide between fold call raise
# by sampling from a normal distribution centered around the desired ROR
def ai_normal_fcr(ror):

    # if sample is below fold_threshold, fold
    # if sample is above raise_threshold, raise
    # else call
    # need to find a stdev which gives reasonably weighted chances based on ror
    fold_threshold = 0.4
    raise_threshold = 0.9
    stdev = 0.3

    sample = random.normalvariate(ror, stdev)

    if sample < fold_threshold:
        return "fold"
    elif sample > raise_threshold:
        return "raise"
    else:
        return "call"


def ai_turn(actions):

    global ai, deck, pot, ante

    if "draw" in actions: # draw phase

        # dict of possible cards to discard : EHS of hand after discarding
        possibilities = {}
        for numdraw in range(5):
            for subset in combinations(range(4), numdraw):
                possibilities[subset] = 0

        for discards in possibilities:

            print('.', end="", flush=True)

            hand = list(ai["cards"])
            
            deck = [x+y for x in ranks for y in suits if x+y not in ai["cards"]]

            for c in sorted(discards, reverse=True):
                del hand[c]

            hand.extend([deck.pop() for x in range(5-len(hand))])

            if ai["action-history"].count("draw") == 1:
                first_move = True
            else:
                first_move = False

            possibilities[discards] = effective_hand_strength(hand, first_move, 500)
        
        print()

        # best action is the one that has highest EHS
        # discard the cards from this action
        ai_discard([ai["cards"][x] for x in max(possibilities, key=possibilities.get)])

    else: # not draw phase

        rate_of_return = ai["hand-strength"]
        action = ai_normal_fcr(rate_of_return)
        maxbet = ai["hand-strength"] * ai["money"] * 0.9

        if action == "fold":
            if "pass" in actions:
                ai_pass()
            elif "fold" in actions:
                ai_fold()
            else:
                print("what?", action, actions)
        elif action == "call":
            if "call" in actions:
                ai_call()
            elif "bet" in actions and ai["bet"] < maxbet:
                ai_bet(math.floor(ante*random.uniform(0.5, 1.5)))
            elif "pass" in actions:
                ai_pass()
            else:
                print("err1", action, actions)
        elif action == "raise":
            if "raise" in actions and ai["bet"] < maxbet:
                ai_raise(math.floor(ante*random.uniform(0.5, 1.5)))
            elif "bet" in actions and ai["bet"] < maxbet:
                ai_bet(math.floor(ante*random.uniform(1.0, 1.5)))
            elif "call" in actions:
                ai_call()
            elif "pass" in actions:
                ai_pass()
            else:
                print("err2", action, actions)
        else:
            print("err3", action, actions)

def bet_round():
    global ante, player, ai, pot

    turn = 0 # player always starts per clarifications

    while True:
        turn += 1

        actions = ["fold"]

        if turn % 2 == 1:
            print("\nPlayer's Turn - Pot:{} Player Bet:{} Ai Bet:{}".format(format_money(pot), format_money(player["bet"]), format_money(ai["bet"])))

            if player["bet"] == ai["bet"]:
                actions.append("pass")
            
            if player["bet"] < ai["bet"]:
                actions.extend(["call", "raise"])
            else:
                actions.append("bet")

            if ai["all-in"]:
                actions = ["fold", "call"]

            player_turn(actions)
        
        else:
            if player["bet"] == ai["bet"]:
                actions.append("pass")

            if pot > 2 * ante:
                actions.append("fold")

            if ai["bet"] < player["bet"]:
                actions.extend(["call", "raise"])
            else:
                actions.append("bet")

            if player["all-in"]:
                actions = ["fold", "call"]  

            ai_turn(actions)

        # check if end round
        if player["action-history"][-1] == "pass" and ai["action-history"][-1] == "pass" or \
           "fold" in player["action-history"] or "fold" in ai["action-history"] or \
           (player["all-in"] and ai["all-in"]):
            return

def main():

    global player, ai, ante, pot, round

    while player["money"] > ante and ai["money"] > ante:
    # reset round variables
        round += 1
        deck = [x+y for x in ranks for y in suits] * decks
        turn = 0
        pot = 0
        player = {
            "money": player["money"],
            "cards": draw(starting_cards),
            "hand-strength": 0,
            "bet": 0,
            "all-in": False,
            "action-history": ["start"],
        }
        ai = {
            "money": ai["money"],
            "cards": draw(starting_cards),
            "hand-strength": 0,
            "bet": 0,
            "all-in": False,
            "action-history": ["start"],
        }

        # round info
        print("\nRound {} - Player: {} Ai: {}".format(round, format_money(player["money"]), format_money(ai["money"])))
        print("Player Cards:", player["cards"])

        # ante
        ante_up()

        print("\nDraw Phase")
        player_turn(["draw", "pass"])
        ai_turn(["draw", "pass"])

        # betting round 1
        print("\nBetting Round 1")

        # hand strength after draw phase
        ai["hand-strength"] = effective_hand_strength(ai["cards"], True, 100000)
        bet_round()

        if not ("fold" in player["action-history"] or "fold" in ai["action-history"] or (player["all-in"] and ai["all-in"])):

            print("\nDraw Phase")
            print("Player Cards:", player["cards"])
            player_turn(["draw", "pass"])
            ai_turn(["draw", "pass"])

            # betting round 2
            print("\nBetting Round 2")

            # hand strength after draw phase
            ai["hand-strength"] = effective_hand_strength(ai["cards"], False, 100000)
            bet_round()

        # showdowm
        sleep(1)
        player_hand, player_score = classify_hand(player["cards"])
        ai_hand, ai_score = classify_hand(ai["cards"])
        print("\nPlayer Cards:", player["cards"], "=", player_hand)
        print("Ai Cards:    ", ai["cards"], "=", ai_hand)
        
        if player_score > ai_score or "fold" in ai["action-history"]:
            print("Player won the pot:", format_money(pot))
            player["money"] += pot
        elif player_score < ai_score or "fold" in player["action-history"]:
            print("Ai won the pot:", format_money(pot))
            ai["money"] += pot
        else: # hands have identical scores
            print("Player and Ai hands have equal score, pot is split between the two")
            ai["money"] += pot//2
            pot -= pot//2
            player["money"] += pot

        sleep(1)

import pdb, traceback, sys
if __name__ == '__main__':
    try:
        main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

# game result
print("\n\n")
if player["money"] < ante:
    print("AI wins!")
elif ai["money"] < ante:
    print("Player wins!")
else:
    print("Game result error")

