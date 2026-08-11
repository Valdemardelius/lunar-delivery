import React from 'react';

export default function RoverList({ rovers, selectedRoverId, selectable, onSelect, onRepair, statusLabel }) {
  return (
    <div>
      {rovers.map((rover) => {
        const pct = rover.battery / rover.battery_max;
        const battClass = pct < 0.3 ? 'low' : pct < 0.6 ? 'mid' : '';
        const clickable = rover.status === 'idle';
        const classNames = [
          'rover-card',
          clickable ? 'clickable' : '',
          selectedRoverId === rover.id ? 'selected' : '',
        ].filter(Boolean).join(' ');

        return (
          <div
            key={rover.id}
            className={classNames}
            onClick={() => clickable && onSelect(rover.id)}
          >
            <div className="rover-name">
              {rover.name}
              <span className={`rover-status ${rover.status}`}>{statusLabel[rover.status] || rover.status}</span>
            </div>
            <div className="bar-track">
              <div className={`bar-fill batt ${battClass}`} style={{ width: `${pct * 100}%` }} />
            </div>
            <div className="rover-meta">
              <span>⚡ {rover.battery}/{rover.battery_max}</span>
              <span>📦 {rover.cargo_capacity}кг</span>
            </div>
            {rover.status === 'broken' && (
              <button
                className="repair-btn"
                onClick={(e) => { e.stopPropagation(); onRepair(rover.id); }}
              >
                Починить сейчас — 60₭ (или {rover.repair_days_left} дн. бесплатно)
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}