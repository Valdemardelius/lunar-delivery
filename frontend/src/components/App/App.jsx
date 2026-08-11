import React from 'react';
import { useGame } from '../../hooks/useGame';
import { useActions } from '../../hooks/useActions';
import { useSelection } from '../../hooks/useSelection';
import { Header } from './Header';
import { BottomRow } from './BottomRow';
import MoonMap from '../MoonMap/MoonMap';
import RoverList from '../RoverList/RoverList';
import OrderDetail from '../OrderDetail/OrderDetail';
import GameOverModal from '../GameOverModal/GameOverModal';
import { statusLabel } from '../../utils/constants';

export default function App() {
  // Все хуки вызываются на каждом рендере, до любого return
  const { state, setState } = useGame();
  const { busy, error, send, repair, advanceDay, reset } = useActions(setState);
  const { selectedOrderId, selectedRoverId, setSelectedRoverId, selectOrder, clearSelection } = useSelection();

  // useMemo тоже должен быть вызван до раннего возврата
  const zonesById = React.useMemo(() => {
    if (!state) return {};
    return Object.fromEntries(state.zones.map((z) => [z.id, z]));
  }, [state]);

  // Теперь ранний возврат (после всех хуков)
  if (!state) {
    return <div className="loading-screen">Связь с базой «Скол-9»…</div>;
  }

  // После этого можно безопасно использовать state и zonesById
  const { game, rovers, orders, events, zones, base } = state;
  const gameOver = !!game.game_over;
  const score = game.money + game.rating * 5;
  const selectedOrder = orders.find((o) => o.id === selectedOrderId) || null;

  const handleSend = () => {
    if (!selectedOrderId || !selectedRoverId) return;
    send(selectedOrderId, selectedRoverId);
    clearSelection();
  };

  const handleAdvanceDay = () => {
    advanceDay();
    clearSelection();
  };

  return (
    <div id="app">
      <Header game={game} />

      <div className="layout">
        <div className="panel">
          <h2>Роверы</h2>
          <RoverList
            rovers={rovers}
            selectedRoverId={selectedRoverId}
            selectable={!!selectedOrderId}
            onSelect={setSelectedRoverId}
            onRepair={repair}
            statusLabel={statusLabel}
          />
        </div>

        <div className="panel map-wrap">
          <h2>Карта поверхности</h2>
          <MoonMap
            zones={zones}
            base={base}
            orders={orders}
            rovers={rovers}
            selectedOrderId={selectedOrderId}
            onSelectOrder={selectOrder}
          />
          <div className="legend">
            {zones.map((z) => (
              <span key={z.id}>
                <i style={{ background: z.color }} />
                {z.name} · риск {Math.round(z.risk * 100)}%
              </span>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Заказ</h2>
          <OrderDetail
            order={selectedOrder}
            zone={selectedOrder ? zonesById[selectedOrder.zone_id] : null}
            rovers={rovers}
            currentDay={game.day}
            selectedRoverId={selectedRoverId}
            onSelectRover={setSelectedRoverId}
            onSend={handleSend}
            busy={busy}
          />
          {error && <div className="err-msg">{error}</div>}
        </div>
      </div>

      <BottomRow
        game={game}
        events={events}
        busy={busy}
        gameOver={gameOver}
        onAdvanceDay={handleAdvanceDay}
      />

      {gameOver && (
        <GameOverModal
          success={game.rating > 0}
          score={score}
          money={game.money}
          rating={game.rating}
          onRestart={reset}
        />
      )}
    </div>
  );
}