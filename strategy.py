from enum import Enum
from typing import Optional
from collections import deque

# ---------------------------
# Enums
# ---------------------------
class Side(Enum):
    BUY = 0
    SELL = 1

class Ticker(Enum):
    TEAM_A = 0  # home team

# ---------------------------
# Mocked Order Functions
# ---------------------------
def place_market_order(side: Side, ticker: Ticker, quantity: float) -> None:
    print(f"[MARKET ORDER] {side.name} {quantity} of {ticker.name}")
    return

def place_limit_order(side: Side, ticker: Ticker, quantity: float, price: float, ioc: bool = False) -> int:
    print(f"[LIMIT ORDER] {side.name} {quantity} of {ticker.name} at {price} IOC={ioc}")
    return 1

def cancel_order(ticker: Ticker, order_id: int) -> bool:
    print(f"[CANCEL ORDER] {order_id} for {ticker.name}")
    return True

# ---------------------------
# Strategy Class
# ---------------------------
class Strategy:
    def reset_state(self):
        self.capital = 100000
        self.position = 0
        self.orders = {}
        self.last_prob = 0.5
        self.best_bid = 50
        self.best_ask = 50
        self.current_time = 0
        self.last_events = deque(maxlen=5)
        print("[RESET STATE]")

    def __init__(self):
        self.reset_state()

    # ---------------------------
    # Callbacks
    # ---------------------------
    def on_orderbook_update(self, ticker: Ticker, side: Side, quantity: float, price: float):
        if side == Side.BUY:
            self.best_bid = price
        else:
            self.best_ask = price
        print(f"[ORDERBOOK] {side.name} {quantity} @ {price}")

    def on_trade_update(self, ticker: Ticker, side: Side, quantity: float, price: float):
        print(f"[TRADE] {side.name} {quantity} @ {price}")

    def on_account_update(self, ticker: Ticker, side: Side, price: float, quantity: float, capital_remaining: float):
        self.capital = capital_remaining
        self.position += quantity if side == Side.BUY else -quantity
        print(f"[ACCOUNT] {side.name} {quantity} @ {price}, capital={self.capital}, position={self.position}")

    # ---------------------------
    # Probability Model
    # ---------------------------
    def estimate_win_prob(self, home_score, away_score, time_seconds, home_possession=None, event_type=None, shot_type=None):
        lead = home_score - away_score
        total_time = 2400
        time_factor = max(time_seconds / total_time, 0.01)

        prob = 0.5 + 0.5 * lead / 50 * time_factor

        momentum = 0
        if event_type == "SCORE" and home_possession == "home":
            self.last_events.append(1)
        elif event_type == "SCORE" and home_possession == "away":
            self.last_events.append(-1)
        else:
            self.last_events.append(0)
        momentum = sum(self.last_events) * 0.02
        prob += momentum

        if shot_type == "THREE_POINT":
            prob += 0.01
        elif shot_type == "FREE_THROW":
            prob += 0.005
        elif shot_type == "DUNK":
            prob += 0.008

        prob = min(max(prob, 0), 1)
        self.last_prob = prob
        print(f"[PROBABILITY] Lead={lead}, Momentum={momentum:.3f}, Time={time_seconds:.1f}s, Prob={prob:.3f}")
        return prob

    # ---------------------------
    # Trading Logic
    # ---------------------------
    def trade_logic(self, market_price):
        prob_price = self.last_prob * 100
        threshold = 4

        if prob_price > market_price + threshold:
            qty = min(10, self.capital / market_price)
            if self.current_time < 120:
                place_market_order(Side.BUY, Ticker.TEAM_A, qty)
            else:
                order_id = place_limit_order(Side.BUY, Ticker.TEAM_A, qty, market_price + 0.5)
                self.orders['buy'] = order_id

        elif prob_price < market_price - threshold:
            qty = min(10, self.position)
            if self.current_time < 120:
                place_market_order(Side.SELL, Ticker.TEAM_A, qty)
            else:
                order_id = place_limit_order(Side.SELL, Ticker.TEAM_A, qty, market_price - 0.5)
                self.orders['sell'] = order_id

    # ---------------------------
    # Game Event Callback
    # ---------------------------
    def on_game_event_update(
        self,
        event_type: str,
        home_away: str,
        home_score: int,
        away_score: int,
        player_name: Optional[str],
        substituted_player_name: Optional[str],
        shot_type: Optional[str],
        assist_player: Optional[str],
        rebound_type: Optional[str],
        coordinate_x: Optional[float],
        coordinate_y: Optional[float],
        time_seconds: Optional[float]
    ):
        if event_type == "END_GAME":
            self.reset_state()
            return

        self.current_time = time_seconds
        prob = self.estimate_win_prob(home_score, away_score, time_seconds)
        market_price = (self.best_bid + self.best_ask) / 2
        self.trade_logic(market_price)
        print(f"[EVENT] {event_type} {home_score}-{away_score} Time={time_seconds:.1f}s")

    