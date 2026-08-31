export function createSingleFlight<Key, Value>() {
  const flights = new Map<Key, Promise<Value>>();

  return (key: Key, task: () => Promise<Value>): Promise<Value> => {
    const existing = flights.get(key);
    if (existing) return existing;

    const flight = task().finally(() => {
      if (flights.get(key) === flight) flights.delete(key);
    });
    flights.set(key, flight);
    return flight;
  };
}
