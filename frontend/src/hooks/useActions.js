import { useState, useCallback } from 'react';
import { api } from '../utils/api';

export function useActions(setState) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const withBusy = useCallback(async (fn) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }, []);

  const send = useCallback(
    async (orderId, roverId) => {
      await withBusy(async () => {
        const data = await api.send(orderId, roverId);
        setState(data);
      });
    },
    [withBusy, setState]
  );

  const repair = useCallback(
    async (roverId) => {
      await withBusy(async () => {
        const data = await api.repair(roverId);
        setState(data);
      });
    },
    [withBusy, setState]
  );

  const advanceDay = useCallback(async () => {
    await withBusy(async () => {
      const data = await api.advanceDay();
      setState(data);
    });
  }, [withBusy, setState]);

  const reset = useCallback(async () => {
    await withBusy(async () => {
      const data = await api.reset();
      setState(data);
    });
  }, [withBusy, setState]);

  return { busy, error, send, repair, advanceDay, reset };
}