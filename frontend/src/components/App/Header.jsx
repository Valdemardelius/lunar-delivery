import React from 'react';

export function Header({ game }) {
  return (
    <header>
      <div className="brand">
        <span className="moon">🌑</span>
        <div>
          <h1>LUNAR RUN</h1>
          <small>Диспетчер доставки — Лунная база «Скол-9»</small>
        </div>
      </div>
      <div className="stats">
        <div className="stat">
          <div className="label">День</div>
          <div className="value">{Math.min(game.day, game.days_total)} / {game.days_total}</div>
        </div>
        <div className="stat money">
          <div className="label">Кредиты</div>
          <div className="value">{game.money} ₭</div>
        </div>
        <div className={`stat rating ${game.rating <= 25 ? 'low' : ''}`}>
          <div className="label">Рейтинг базы</div>
          <div className="value">{game.rating}</div>
        </div>
      </div>
    </header>
  );
}