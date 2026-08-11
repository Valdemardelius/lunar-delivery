import React from 'react';

export default function EventLog({ events }) {
  return (
    <div id="log">
      {events.map((e) => (
        <div key={e.id} className={e.cls}>[д.{e.day}] {e.msg}</div>
      ))}
    </div>
  );
}