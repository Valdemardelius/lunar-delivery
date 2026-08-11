import React from 'react';
import EventLog from '../EventLog/EventLog';

export function BottomRow({ game, events, busy, gameOver, onAdvanceDay }) {
  return (
    <div className="bottom-row">
      <div className="panel">
        <h2>Журнал событий</h2>
        <EventLog events={events} />
      </div>
      <div className="panel day-panel">
        <div>
          <h2>Цель миссии</h2>
          <div className="goal-box">
            Продержаться <b style={{ color: 'var(--text)' }}>{game.days_total} дней</b>, заработать
            максимум кредитов и не дать рейтингу базы упасть до нуля.
            <br /><br />
            Рейтинг падает за просроченные и провалившиеся заказы — если он обнулится, миссия провалена.
          </div>
        </div>
        <button
          className="next-day-btn"
          disabled={busy || gameOver}
          onClick={onAdvanceDay}
        >
          Завершить день ▸
        </button>
      </div>
    </div>
  );
}