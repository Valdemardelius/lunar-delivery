from app.models.domain import GameState

class GameRepository:
    def get_state(self, conn):
        row = conn.execute("SELECT * FROM game_state WHERE id=1").fetchone()
        if not row:
            return None
        return GameState(
            day=row["day"],
            money=row["money"],
            rating=row["rating"],
            game_over=bool(row["game_over"]),
            order_seq=row["order_seq"]
        )

    def update_state(self, conn, game: GameState):
        conn.execute(
            "UPDATE game_state SET day=?, money=?, rating=?, game_over=? WHERE id=1",
            (game.day, game.money, game.rating, int(game.game_over))
        )

    def increment_order_seq(self, conn, new_seq: int):
        conn.execute("UPDATE game_state SET order_seq=? WHERE id=1", (new_seq,))