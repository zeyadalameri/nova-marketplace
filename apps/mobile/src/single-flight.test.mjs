import assert from 'node:assert/strict';
import test from 'node:test';

import { createSingleFlight } from './single-flight.ts';

test('concurrent callers share one refresh request', async () => {
  const runSingle = createSingleFlight();
  let calls = 0;
  let resolveRefresh;
  const refreshResult = new Promise((resolve) => {
    resolveRefresh = resolve;
  });

  const requests = Array.from({ length: 20 }, () =>
    runSingle('refresh-token', async () => {
      calls += 1;
      return refreshResult;
    }),
  );

  assert.equal(calls, 1);
  resolveRefresh('new-access-token');
  assert.deepEqual(await Promise.all(requests), Array(20).fill('new-access-token'));
});

test('a failed flight is removed so a later refresh can retry', async () => {
  const runSingle = createSingleFlight();
  let calls = 0;

  await assert.rejects(
    runSingle('refresh-token', async () => {
      calls += 1;
      throw new Error('expired refresh');
    }),
  );
  const result = await runSingle('refresh-token', async () => {
    calls += 1;
    return 'replacement-access-token';
  });

  assert.equal(result, 'replacement-access-token');
  assert.equal(calls, 2);
});
