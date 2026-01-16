import arcade
import random
import math

SCREEN_WIDTH = 1370
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Splendor: The medieval merchant"

# Splendor data model (simplified set of cards and nobles)
# Colors: orange, blue, green, red, black; gold is wildcard
COLORS = ["orange", "blue", "green", "red", "purple"]
GOLD = "gold"

# Expanded decks for Level I/II/III (cost, bonus_color, points)
# Deck I: Easy cards (0-1 points) - 20 cards
DECK_I = [
    # Single color cards (0 points)
    ({"orange": 2}, "orange", 0),
    ({"blue": 2}, "blue", 0),
    ({"green": 2}, "green", 0),
    ({"red": 2}, "red", 0),
    ({"purple": 2}, "purple", 0),
    ({"orange": 1}, "orange", 0),
    ({"blue": 1}, "blue", 0),
    ({"green": 1}, "green", 0),
    ({"red": 1}, "red", 0),
    ({"purple": 1}, "purple", 0),
    # Two color cards (0 points)
    ({"orange": 1, "blue": 1}, "green", 0),
    ({"orange": 1, "green": 1}, "red", 0),
    ({"orange": 1, "red": 1}, "purple", 0),
    ({"blue": 1, "green": 1}, "orange", 0),
    ({"blue": 1, "red": 1}, "purple", 0),
    ({"green": 1, "red": 1}, "blue", 0),
    # Three color cards (1 point)
    ({"orange": 1, "blue": 1, "green": 1}, "red", 1),
    ({"orange": 1, "blue": 1, "red": 1}, "purple", 1),
    ({"orange": 1, "green": 1, "red": 1}, "blue", 1),
    ({"blue": 1, "green": 1, "red": 1}, "orange", 1),
]

# Deck II: Medium cards (1-3 points) - 20 cards
DECK_II = [
    # Single color cards (1-2 points)
    ({"orange": 3}, "orange", 1),
    ({"blue": 3}, "blue", 1),
    ({"green": 3}, "green", 1),
    ({"red": 3}, "red", 1),
    ({"purple": 3}, "purple", 1),
    ({"orange": 4}, "orange", 2),
    ({"blue": 4}, "blue", 2),
    ({"green": 4}, "green", 2),
    ({"red": 4}, "red", 2),
    ({"purple": 4}, "purple", 2),
    # Two color cards (1-2 points)
    ({"orange": 2, "blue": 2}, "green", 1),
    ({"orange": 2, "green": 2}, "red", 1),
    ({"orange": 2, "red": 2}, "purple", 1),
    ({"blue": 2, "green": 2}, "orange", 2),
    ({"blue": 2, "red": 2}, "purple", 2),
    ({"green": 2, "red": 2}, "blue", 2),
    # Three color cards (3 points)
    ({"orange": 2, "blue": 2, "green": 2}, "red", 3),
    ({"orange": 2, "blue": 2, "red": 2}, "purple", 3),
    ({"orange": 2, "green": 2, "red": 2}, "blue", 3),
    ({"blue": 2, "green": 2, "red": 2}, "orange", 3),
]

# Deck III: Hard cards (3-5 points) - 10 cards
DECK_III = [
    # High cost single color (3-4 points)
    ({"orange": 5}, "orange", 3),
    ({"blue": 5}, "blue", 3),
    ({"green": 5}, "green", 3),
    ({"red": 5}, "red", 3),
    ({"purple": 5}, "purple", 3),
    # Multi-color high cost (4-5 points)
    ({"orange": 3, "blue": 3, "green": 3}, "red", 4),
    ({"orange": 3, "blue": 3, "red": 3}, "purple", 4),
    ({"orange": 3, "green": 3, "red": 3}, "blue", 4),
    ({"blue": 3, "green": 3, "red": 3}, "orange", 4),
    ({"orange": 4, "blue": 4, "green": 4, "red": 4}, "purple", 5),
]

# Nobles: requirement in permanent bonuses, points=3
NOBLES = [
    ({"orange": 3, "blue": 3}, 3),
    ({"green": 3, "red": 3}, 3),
    ({"purple": 3, "orange": 3}, 3),
]

# Token supply: start with 7 of each color and 5 gold
INITIAL_BANK = {c: 7 for c in COLORS}
INITIAL_BANK[GOLD] = 5

# Rules
MAX_POINTS = 15
HAND_LIMIT = 10


class Player:
    def __init__(self, name):
        self.name = name
        self.tokens = {c: 0 for c in COLORS + [GOLD]}
        self.points = 0
        self.bonuses = {c: 0 for c in COLORS}
        self.reserved = []  # list of (cost, bonus_color, points)

    def total_tokens(self):
        return sum(self.tokens.values())

    def can_buy(self, card):
        cost, bonus_color, pts = card
        gold_needed = 0
        for c, required in cost.items():
            effective = max(0, required - self.bonuses.get(c, 0))
            pay_with_color = min(effective, self.tokens.get(c, 0))
            gold_needed += effective - pay_with_color
        return gold_needed <= self.tokens.get(GOLD, 0)

    def pay_for_card(self, card):
        cost, bonus_color, pts = card
        gold_to_spend = 0
        spent = {c: 0 for c in COLORS + [GOLD]}
        # First spend colored tokens
        for c, required in cost.items():
            effective = max(0, required - self.bonuses.get(c, 0))
            spend = min(effective, self.tokens[c])
            self.tokens[c] -= spend
            spent[c] += spend
            gold_to_spend += effective - spend
        # Spend gold for remaining
        self.tokens[GOLD] -= gold_to_spend
        spent[GOLD] += gold_to_spend
        return spent

    def buy(self, card):
        spent = self.pay_for_card(card)
        cost, bonus_color, pts = card
        self.points += pts
        self.bonuses[bonus_color] += 1
        return pts, spent

    def get_tokens_display(self):
        """Return tokens in a nice readable format"""
        token_list = []
        for color in COLORS + [GOLD]:
            if self.tokens[color] > 0:
                token_list.append(f"{self.tokens[color]} {color}")
        if token_list:
            return ", ".join(token_list)
        return "No tokens"

    def get_discounts_display(self):
        """Return permanent discounts in a nice readable format"""
        discount_list = []
        for color in COLORS:
            if self.bonuses[color] > 0:
                discount_list.append(f"{self.bonuses[color]} {color}")
        if discount_list:
            return ", ".join(discount_list)
        return "No discounts"


class SplendorGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color((35, 35, 60))

        self.players = [Player("You"), Player("Bot")]
        self.current_turn = 0
        self.message = "Welcome to Splendor! Click cards to select. Press T(3-diff) / D(2-same) / R(reserve) / B(buy)."
        self.message2 = "SPLENDOR"
        self.game_over = False
        self.final_message = ""
        self.finish_round = False  # when someone reaches >=15 this flag ends after equal turns

        # Layout constants
        self.top_bar_height = 110
        self.bottom_panel_height = 110

        # Bank tokens
        self.bank = INITIAL_BANK.copy()

        # Token layout
        left = 160
        gap = 90
        self.token_positions = {
            "orange": (left + 0 * gap, SCREEN_HEIGHT - 60),
            "blue": (left + 1 * gap, SCREEN_HEIGHT - 60),
            "green": (left + 2 * gap, SCREEN_HEIGHT - 60),
            "red": (left + 3 * gap, SCREEN_HEIGHT - 60),
            "purple": (left + 4 * gap, SCREEN_HEIGHT - 60),
            GOLD: (left + 5 * gap + 30, SCREEN_HEIGHT - 60),
        }

        # Decks and display
        self.deck_I = DECK_I[:]
        self.deck_II = DECK_II[:]
        self.deck_III = DECK_III[:]
        random.shuffle(self.deck_I)
        random.shuffle(self.deck_II)
        random.shuffle(self.deck_III)
        self.display_I = []
        self.display_II = []
        self.display_III = []
        self._refill_display()

        # Nobles setup (for 2 players -> 2 nobles)
        nobles = NOBLES[:]
        random.shuffle(nobles)
        self.nobles = nobles[:2]

        # Selection and action state
        self.selected_card = None  # (zone, index) where zone in {"I","II","III","RES"}
        self.action_mode = None  # None | 'take3' | 'take2' | 'reserve' | 'buy'
        self.token_picks = []  # list of chosen colors when in take3 mode

    def draw_medieval_token(self, x, y, color):
        base_colors = {
            "orange": (204, 85, 0),
            "blue": (60, 90, 180),
            "green": (50, 140, 90),
            "red": (170, 60, 60),
            "purple": (120, 60, 150),
            GOLD: (210, 170, 30),
        }
        arcade.draw_circle_filled(x, y, 24, base_colors[color])
        arcade.draw_circle_outline(x, y, 24, (240, 220, 60), 2)
        arcade.draw_text(
            f"{self.bank[color]}", x, y - 10, (0, 0, 0) if color != "purple" else (250, 250, 250), 12, anchor_x="center"
        )

    def draw_card(self, x, y, card, level=None):
        cost, bonus_color, pts = card
        
        # Color mapping for your specific gem types
        color_map = {
            "orange": (204, 85, 0),  # MAGNOLIA
            "blue": (50, 70, 140),     # Deep blue  
            "green": (50, 100, 70),    # Forest green
            "red": (140, 50, 50),      # Rich burgundy
            "purple": (100, 50, 120),  # Royal purple
        }
        
        # Always use gem color for background - no level-based backgrounds
        bg = color_map.get(bonus_color, (70, 60, 50))  # Simple fallback
        
        card_rect = arcade.rect.XYWH(x, y, 120, 160)
        arcade.draw_rect_filled(card_rect, bg)
        arcade.draw_rect_outline(card_rect, (228, 208, 10), 2)
        
        # Points and bonus color
        arcade.draw_text(str(pts), x - 52, y + 60, (228, 208, 10), 16)
        if bonus_color:
            arcade.draw_text(f"+{bonus_color[:1].upper()}", x + 30, y + 60, (228, 208, 10), 16)
        
        # Cost rows
        oy = 30
        for c in COLORS:
            amt = cost.get(c, 0)
            if amt > 0:
                arcade.draw_text(f"{c[:1].upper()}: {amt}", x - 50, y + oy, (228, 208, 10), 14)
                oy -= 20
        
        # Level indicator - orange dots at bottom center
        if level:
            dot_count = {"I": 1, "II": 2, "III": 3}[level]
            dot_y = y - 70  # Bottom of the card
            
            for i in range(dot_count):
                dot_x = x - 12 + (i * 12)  # Center the dots horizontally
                arcade.draw_circle_filled(dot_x, dot_y, 3, (228, 208, 10))  # Yellow dots
    def draw_top_bar(self):
        top_bar_rect = arcade.rect.XYWH(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - self.top_bar_height // 2, SCREEN_WIDTH, self.top_bar_height
        )
        arcade.draw_rect_filled(top_bar_rect, (35, 35, 60))
        arcade.draw_rect_outline(top_bar_rect, (240, 220, 60), 1)
        for c, (x, y) in self.token_positions.items():
            self.draw_medieval_token(x, y, c)
        turn_text = f"Turn: {self.players[self.current_turn].name}"
        if self.game_over:
            turn_text = "Game over"
        arcade.draw_text(turn_text, 20, SCREEN_HEIGHT - 80, (240, 220, 60), 16)
        arcade.draw_text(self.message, 20, SCREEN_HEIGHT - 100, (240, 220, 60), 12)
        arcade.draw_text(self.message2, 770, SCREEN_HEIGHT - 80, (240, 220, 60), 40, bold=True, font_name="Times New Roman")
        # Controls at top-right
        inst_x = SCREEN_WIDTH - 200
        inst_y = SCREEN_HEIGHT - 30
        arcade.draw_text("Controls:", inst_x, inst_y, (240, 220, 60), 12)
        lines = [
            "T: take 3, then click 3 coins",
            "D: take 2, then click a color",
            "R: reserve, then click face-up",
            "B: buy, then click face-up/res",
        ]
        for i, line in enumerate(lines):
            arcade.draw_text(line, inst_x, inst_y - 16 * (i + 1), (240, 220, 60), 11)

    def draw_status_message(self):
        pass

    def draw_game_over_message(self):
        """Black screen with winner announcement"""
        if self.game_over:
            # Full black screen
            overlay_rect = arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 
                                         SCREEN_WIDTH, SCREEN_HEIGHT)
            arcade.draw_rect_filled(overlay_rect, (0, 0, 0))
            
            # Winner announcement
            '''arcade.draw_text(f"{self.final_message} WINS!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, 
                           (240, 220, 60), 48, bold=True, anchor_x="center")
'''
            arcade.draw_text(
                f"{self.final_message} WON THE GAME!",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 + 50,
                (240, 220, 60),  
                48,
                bold=True,
                anchor_x="center",
                font_name="Times New Roman"  
            )
            
            # Both players' scores
            p1 = self.players[0]
            p2 = self.players[1]
            arcade.draw_text(f"You: {p1.points} pts", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, 
                           (255, 255, 255), 24, anchor_x="center")
            arcade.draw_text(f"Bot: {p2.points} pts", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, 
                           (255, 255, 255), 24, anchor_x="center")

    def draw_bottom_panel(self):
        # Removed all highlighting boxes - no background rectangles or outlines

        # Sidebar stats on the right
        sidebar_x = SCREEN_WIDTH - 370
        p1 = self.players[0]
        arcade.draw_text(f"You: {p1.points} pts", sidebar_x, 190, (228, 208, 10), 14)
        arcade.draw_text(f"Tokens: {p1.get_tokens_display()}", sidebar_x, 165, (228, 208, 10), 12, width=250)
        arcade.draw_text(f"Bonuses: {p1.get_discounts_display()}", sidebar_x, 140, (228, 208, 10), 12, width=250)
        arcade.draw_text(f"Reserved: {len(p1.reserved)}/3", sidebar_x, 115, (228, 208, 10), 12)
        # Player 2
        p2 = self.players[1]
        arcade.draw_text(f"Bot: {p2.points} pts", sidebar_x, 80, (228, 208, 10), 14)
        arcade.draw_text(f"Tokens: {p2.get_tokens_display()}", sidebar_x, 55, (228, 208, 10), 12, width=250)
        arcade.draw_text(f"Bonuses: {p2.get_discounts_display()}", sidebar_x, 30, (228, 208, 10), 12, width=250)

        # Render displays
        self._draw_displays()
        self._draw_nobles()
        
        # Score text at bottom-left (no box)
        score_text = f"Score — You: {self.players[0].points} | Bot: {self.players[1].points}"
        arcade.draw_text(score_text, 20, 10, (228, 208, 10), 12)

    def on_draw(self):
        self.clear()
        
        if self.game_over:
            # Only show black screen with winner when game is over
            self.draw_game_over_message()
        else:
            # Show normal game elements
            self.draw_top_bar()
            self.draw_status_message()
            self.draw_bottom_panel()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_over:
            return
        if self.current_turn != 0:
            return
        # If an action mode is active, interpret click accordingly
        if self.action_mode == 'take3':
            for c, (tx, ty) in self.token_positions.items():
                if c == GOLD:
                    continue
                if (x - tx) ** 2 + (y - ty) ** 2 <= 24 * 24:
                    if self.bank[c] <= 0:
                        self.message = f"{c} unavailable"
                        return
                    if c in self.token_picks:
                        self.message = "Pick different colors"
                        return
                    self.token_picks.append(c)
                    if len(self.token_picks) == 3:
                        # apply take
                        p = self.players[0]
                        if p.total_tokens() + 3 > HAND_LIMIT:
                            self.message = "Max coin limit 10"
                            self.token_picks = []
                            self.action_mode = None
                            return
                        for cc in self.token_picks:
                            self.bank[cc] -= 1
                            p.tokens[cc] += 1
                        self._enforce_hand_limit(p)
                        self.message = f"Took: {', '.join(self.token_picks)}"
                        self.action_mode = None
                        self.token_picks = []
                        self._end_player_action()
                    else:
                        self.message = f"Picked {c}. Choose {3 - len(self.token_picks)} more."
                    return
        elif self.action_mode == 'take2':
            # Click a color to take 2 if bank >= 4
            for c, (tx, ty) in self.token_positions.items():
                if c == GOLD:
                    continue
                if (x - tx) ** 2 + (y - ty) ** 2 <= 24 * 24:
                    if self.bank[c] < 4:
                        self.message = f"Need 4 {c} in bank"
                        return
                    p = self.players[0]
                    if p.total_tokens() + 2 > HAND_LIMIT:
                        self.message = "Max coin limit 10"
                        return
                    self.bank[c] -= 2
                    p.tokens[c] += 2
                    self._enforce_hand_limit(p)
                    self.message = f"Took 2 {c}"
                    self.action_mode = None
                    self._end_player_action()
                    return
        elif self.action_mode in ('reserve', 'buy'):
            sel = self._card_hit_test(x, y)
            if sel:
                self.selected_card = sel
                if self.action_mode == 'reserve':
                    z, _ = sel
                    if z == 'RES':
                        self.message = "Click a face-up card to reserve"
                        return
                    if self._reserve_selected(self.players[0]):
                        self.action_mode = None
                        self._end_player_action()
                else:  # buy
                    if self._buy_selected(self.players[0]):
                        self.action_mode = None
                        self._end_player_action()
                return

        # No (or unmatched) action mode: normal select preview
        sel = self._card_hit_test(x, y)
        if sel:
            self.selected_card = sel
            self.message = f"Selected card from {sel[0]} slot {sel[1]}"
            return

    def check_game_end(self):
        current = self.players[self.current_turn]
        if current.points >= MAX_POINTS and not self.finish_round:
            # mark to finish the round so both have equal turns
            self.finish_round = True
        if self.finish_round and self.current_turn == 1:
            self.end_game()

    def card_score(self, player, card):
        cost, bonus, pts = card
        missing = 0
        for c, req in cost.items():
            req = max(0, req - player.bonuses.get(c, 0))
            have = player.tokens.get(c, 0)
            missing += max(0, req - have)
        return pts * 10 + player.bonuses.get(bonus, 0) * 2 - missing

    def ai_move(self):
        if self.game_over:
            return
            
        bot = self.players[1]
        # Try to buy any affordable from displays first
        all_visible = (
            [("I", i, c) for i, c in enumerate(self.display_I)]
            + [("II", i, c) for i, c in enumerate(self.display_II)]
            + [("III", i, c) for i, c in enumerate(self.display_III)]
        )
        affordable = [(z, i, c) for (z, i, c) in all_visible if bot.can_buy(c)]
        if affordable:
            z, i, card = max(affordable, key=lambda t: t[2][2])
            pts, spent = bot.buy(card)
            # Return spent coins to bank (same as player)
            for c in COLORS + [GOLD]:
                if spent.get(c, 0) > 0:
                    self.bank[c] += spent[c]
            self._remove_card_from_display(z, i)
            self.message = f"Rival bought a {card[1]} card for {card[2]} pts"
            self._refill_display()
            self._check_and_award_nobles(bot)
            self.check_game_end()
            return
        # Otherwise take 3 different if possible biased to needs
        if bot.total_tokens() >= HAND_LIMIT:
            self.message = "Rival at max coin limit 10"
            return
        needed = self._needed_colors_for_best(bot)
        taken = []
        for c in needed:
            if len(taken) == 3:
                break
            if c in taken:
                continue
            if self.bank.get(c, 0) > 0:
                self.bank[c] -= 1
                bot.tokens[c] += 1
                taken.append(c)
        if not taken:
            # try take 2 of same if >=4
            for c in COLORS:
                if self.bank[c] >= 4 and bot.total_tokens() + 2 <= HAND_LIMIT:
                    self.bank[c] -= 2
                    bot.tokens[c] += 2
                    taken = [c, c]
                    break
        self._enforce_hand_limit(bot)
        self.message = f"Rival took {', '.join(taken) if taken else 'nothing'}"

    def end_turn(self):
        if self.game_over:
            return
        self.current_turn = 1 - self.current_turn
        if self.current_turn == 1:
            self.ai_move()
            self.check_game_end()
            if not self.game_over:
                self.current_turn = 0
    
    def end_game(self):
        self.game_over = True
        max_points = max(p.points for p in self.players)
        winners = [p for p in self.players if p.points == max_points]
        if len(winners) == 1:
            self.final_message = winners[0].name
        else:
            winner = min(winners, key=lambda p: sum(p.tokens.values()))
            self.final_message = winner.name
        arcade.schedule(lambda _: arcade.close_window(), 5)

    # ---------- Helpers and rules ----------
    def _refill_display(self):
        while len(self.display_I) < 4 and self.deck_I:
            self.display_I.append(self.deck_I.pop())
        while len(self.display_II) < 4 and self.deck_II:
            self.display_II.append(self.deck_II.pop())
        while len(self.display_III) < 4 and self.deck_III:
            self.display_III.append(self.deck_III.pop())

    def _draw_displays(self):
        # Non-overlapping rows with colored backgrounds + reserved area
        xs = [380, 560, 740, 920]
        # Card row positions
        yI, yII, yIII = 120, 290, 460
        
        # Calculate reserved area to match card rows height
        top_card_y = yIII + 80    # Top of highest row (Level III cards)
        bottom_card_y = yI - 80   # Bottom of lowest row (Level I cards)
        reserved_height = (top_card_y - bottom_card_y) + 10
        reserved_center_y = (top_card_y + bottom_card_y) / 2
        
        # Reserved column background - matches card rows height exactly
        arcade.draw_rect_filled(arcade.rect.XYWH(140, reserved_center_y, 160, reserved_height), (60, 60, 70))
        arcade.draw_rect_outline(arcade.rect.XYWH(140, reserved_center_y, 160, reserved_height), (228, 208, 10), 2)
        arcade.draw_text("Reserved", 110, top_card_y +10, (228, 208, 10), 14)  # Text at top of reserved area
        self._draw_reserved()
        
        # Cards
        for i, card in enumerate(self.display_I):
            self.draw_card(xs[i], yI, card, "I")
        for i, card in enumerate(self.display_II):
            self.draw_card(xs[i], yII, card, "II")
        for i, card in enumerate(self.display_III):
            self.draw_card(xs[i], yIII, card, "III")
        
        # selection highlight
        if self.selected_card:
            zone, idx = self.selected_card
            y = {"I": yI, "II": yII, "III": yIII}.get(zone, yI)
            x = xs[idx]
            arcade.draw_rect_outline(arcade.rect.XYWH(x, y, 124, 164), (255, 255, 255), 3)

    def _draw_nobles(self):
        # Draw nobles stacked vertically on the right side between controls and score
        # Red backdrop behind the nobles column
        panel_center_x = SCREEN_WIDTH - 120
        panel_center_y = SCREEN_HEIGHT - self.top_bar_height -125
        panel = arcade.rect.XYWH(panel_center_x, panel_center_y, 160, 200)
        arcade.draw_rect_filled(panel,(35, 35, 60) )
        arcade.draw_rect_outline(panel, (240, 220, 60), 2)
        col_x = SCREEN_WIDTH - 120
        start_y = SCREEN_HEIGHT - self.top_bar_height - 80  # just below top bar/controls
        spacing = 90
        for i, noble in enumerate(self.nobles[:2]):
            req, pts = noble
            y = start_y - i * spacing
            r = arcade.rect.XYWH(col_x, y, 120, 70)
            arcade.draw_rect_filled(r,(127, 23, 52))  # Lighter red
            arcade.draw_rect_outline(r, (240, 220, 60), 2)
            arcade.draw_text(f"{pts}p", col_x - 50, y + 20, (240, 220, 60), 12)
            oy = 0
            for c, a in req.items():
                arcade.draw_text(f"{c[:1].upper()}:{a}", col_x - 10, y + 20 - oy, (240, 220, 60), 10)
                oy += 14

    def _draw_reserved(self):
        # Draw player's reserved (left column), max 3 slots
        p = self.players[0]
        
        # Calculate slot positions to match the new reserved area
        # Using the same card row positions as in _draw_displays
        yI, yII, yIII = 120, 290, 460  # Match the card row Y positions
        
        # Position reserved slots to align with card rows
        slots_y = [yIII, yII, yI]  # Top to bottom: Level III, II, I positions
        x = 140
        
        for i in range(3):
            r = arcade.rect.XYWH(x, slots_y[i], 120, 160)
            arcade.draw_rect_outline(r, (180, 180, 180), 1)
            if i < len(p.reserved):
                self.draw_card(x, slots_y[i], p.reserved[i])
        
        # highlight if selected reserved
        if self.selected_card and self.selected_card[0] == 'RES':
            idx = self.selected_card[1]
            if 0 <= idx < 3:
                arcade.draw_rect_outline(arcade.rect.XYWH(x, slots_y[idx], 124, 164), (255, 255, 255), 3)

    def _card_hit_test(self, x, y):
        # Use the same coordinates as _draw_displays method
        yI, yII, yIII = 175, 335, 495
        xs = [380, 560, 740, 920]
        # Reserved hit-test first - use same coordinates as _draw_reserved
        slots_y = [495, 335, 175]
        rx = 140
        for i in range(3):
            if rx - 60 < x < rx + 60 and slots_y[i] - 80 < y < slots_y[i] + 80:
                p = self.players[0]
                if i < len(p.reserved):
                    return ('RES', i)
        for i in range(4):
            if i < len(self.display_I) and xs[i] - 60 < x < xs[i] + 60 and yI - 80 < y < yI + 80:
                return ("I", i)
            if i < len(self.display_II) and xs[i] - 60 < x < xs[i] + 60 and yII - 80 < y < yII + 80:
                return ("II", i)
            if i < len(self.display_III) and xs[i] - 60 < x < xs[i] + 60 and yIII - 80 < y < yIII + 80:
                return ("III", i)
        return None

    def _remove_card_from_display(self, zone, index):
        if zone == "I":
            self.display_I.pop(index)
        elif zone == "II":
            self.display_II.pop(index)
        elif zone == "III":
            self.display_III.pop(index)

    def _take_three_diff(self, player):
        # This function assumes chosen colors are stored temporarily; here we do simple heuristic: take the first three available
        available = [c for c in COLORS if self.bank[c] > 0]
        if len(available) < 3:
            self.message = "Need 3 different colors available"
            return False
        chosen = available[:3]
        for c in chosen:
            self.bank[c] -= 1
            player.tokens[c] += 1
        self.message = f"Took 3 tokens: {', '.join(chosen)}"
        self._enforce_hand_limit(player)
        return True

    def _take_two_same(self, player):
        for c in COLORS:
            if self.bank[c] >= 4:
                self.bank[c] -= 2
                player.tokens[c] += 2
                self.message = f"Took 2 {c} tokens"
                self._enforce_hand_limit(player)
                return True
        self.message = "No color has 4 in bank"
        return False

    def _reserve_selected(self, player):
        if len(player.reserved) >= 3:
            self.message = "Reserve limit reached"
            return False
        if not self.selected_card:
            self.message = "Select a face-up card to reserve"
            return False
        zone, idx = self.selected_card
        card = None
        if zone in ("I", "II", "III"):
            card = (self.display_I if zone == "I" else self.display_II if zone == "II" else self.display_III)[idx]
            self._remove_card_from_display(zone, idx)
            self._refill_display()
        if card is None:
            self.message = "Invalid selection"
            return False
        player.reserved.append(card)
        if self.bank[GOLD] > 0:
            self.bank[GOLD] -= 1
            player.tokens[GOLD] += 1
        self.message = "Reserved a card and took 1 gold"
        self._enforce_hand_limit(player)
        return True

    def _buy_selected(self, player):
        if not self.selected_card:
            self.message = "Select a card"
            return False
        zone, idx = self.selected_card
        card = None
        from_reserved = False
        if zone == "RES":
            if idx < len(player.reserved):
                card = player.reserved[idx]
                from_reserved = True
        else:
            display = self.display_I if zone == "I" else self.display_II if zone == "II" else self.display_III
            if idx < len(display):
                card = display[idx]
        if card is None:
            self.message = "Invalid selection"
            return False
        if not player.can_buy(card):
            self.message = "Cannot afford"
            return False
        pts, spent = player.buy(card)
        # Return only COINS used to bank (colors + gold), bonuses are discounts and not returned
        for c in COLORS + [GOLD]:
            if spent.get(c, 0) > 0:
                self.bank[c] += spent[c]
        if from_reserved:
            player.reserved.pop(idx)
        else:
            self._remove_card_from_display(zone, idx)
            self._refill_display()
        self.message = f"Bought {card[1]} for {card[2]} pts"
        self._check_and_award_nobles(player)
        return True

    def _check_and_award_nobles(self, player):
        gained = []
        i = 0
        while i < len(self.nobles):
            req, pts = self.nobles[i]
            if all(player.bonuses.get(c, 0) >= v for c, v in req.items()):
                player.points += pts
                gained.append(i)
            i += 1
        # Remove in reverse order to keep indices
        for idx in reversed(gained):
            self.nobles.pop(idx)
        if gained:
            self.message += f"; claimed {len(gained)} noble(s)"

    def _enforce_hand_limit(self, player):
        if player.total_tokens() <= HAND_LIMIT:
            return
        # Simple policy: return extras starting from colors with most tokens (excluding gold last)
        excess = player.total_tokens() - HAND_LIMIT
        order = sorted(COLORS, key=lambda c: player.tokens[c], reverse=True) + [GOLD]
        for c in order:
            while excess > 0 and player.tokens[c] > 0:
                player.tokens[c] -= 1
                self.bank[c] += 1
                excess -= 1

    def _needed_colors_for_best(self, player):
        visible = self.display_I + self.display_II + self.display_III
        if not visible:
            return COLORS
        target = max(visible, key=lambda c: self.card_score(player, c))
        cost = target[0]
        # return colors sorted by deficit desc
        deficits = []
        for c in COLORS:
            needed = max(0, cost.get(c, 0) - player.bonuses.get(c, 0) - player.tokens.get(c, 0))
            deficits.append((c, needed))
        deficits.sort(key=lambda t: t[1], reverse=True)
        return [c for c, d in deficits if d > 0] + [c for c, d in deficits if d == 0]

    # ---------- Input handling for actions ----------
    def on_key_press(self, symbol, modifiers):
        if self.game_over or self.current_turn != 0:
            return
        p = self.players[0]
        # T = take 3 different (enter pick mode)
        if symbol in (arcade.key.T,):
            if p.total_tokens() >= HAND_LIMIT:
                self.message = "Max coin limit 10"
                return
            self.action_mode = 'take3'
            self.token_picks = []
            self.message = "Pick 3 different coins by clicking on them"
        # D = take 2 same
        elif symbol in (arcade.key.D,):
            if p.total_tokens() >= HAND_LIMIT:
                self.message = "Max coin limit 10"
                return
            self.action_mode = 'take2'
            self.message = "Click a coin color to take 2 (need 4 in bank)"
        # R = reserve selected face-up
        elif symbol in (arcade.key.R,):
            self.action_mode = 'reserve'
            self.message = "Click a face-up card to reserve"
        # B = buy selected (from display or reserved)
        elif symbol in (arcade.key.B,):
            self.action_mode = 'buy'
            self.message = "Click a face-up or reserved card to buy"

    def _end_player_action(self):
        self._check_and_award_nobles(self.players[0])
        self.check_game_end()
        self.end_turn()

    # For viewing reserved selection via mouse (left side slots)
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        # Selecting reserved via scroll: cycle selection if any reserved
        if self.current_turn != 0 or self.game_over:
            return
        p = self.players[0]
        if not p.reserved:
            return
        # set selection to reserved index 0 (for simplicity)
        self.selected_card = ("RES", 0)
        self.message = "Selected reserved card 1"


if __name__ == "__main__":
    game = SplendorGame()
    arcade.run()