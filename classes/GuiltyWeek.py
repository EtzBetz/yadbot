from classes import Bot, DBConnect, Player


class GuiltyWeek:
    year = None
    week = None
    reasons = []
    confirmed_reason = None
    players = []
    confirmed_players = []


    def __init__(self, year, week, reasons=None, confirmed_reason=None, players=None, confirmed_players=None) -> None:
        super().__init__()
        self.year = year
        self.week = week
        if reasons is not None:
            this.reasons = reasons
        self.confirmed_reason = confirmed_reason
        if players is not None:
            this.players = players
        if confirmed_players is not None:
            this.confirmed_players = confirmed_players