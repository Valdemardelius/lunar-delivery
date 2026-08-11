import React from 'react';

export default function GameOverModal({ success, score, money, rating, onRestart }) {
  return (
    <div className="modal-bg">
      <div className="modal">
        <h2>{success ? '🌕 Миссия завершена' : '☄️ База потеряла доверие'}</h2>
        <p>
          {success
            ? 'Пройдено 15 дней на лунной базе «Скол-9».'
            : 'Рейтинг базы упал до нуля — контракт на снабжение расторгнут.'}
        </p>
        <div className="score">{score} очков</div>
        <p>Кредиты: {money}₭ · Рейтинг: {rating}</p>
        <button onClick={onRestart}>Начать заново</button>
      </div>
    </div>
  );
}