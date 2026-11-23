import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { plan, assertFeasible } from './planner.js';
import { svgReport } from './report.js';

const tech = (id = 'alex', skills = ['mechanical']) => ({ id, skills, availability: [{ start: 0, end: 480 }] });
const job = (id, extra = {}) => ({ id, title: id, duration: 60, priority: 2, due: 480, skills: ['mechanical'], dependsOn: [], ...extra });
const input = (jobs, technicians = [tech()]) => ({ dayMinutes: 480, technicians, jobs });

test('priority and due time determine which job gets capacity', () => {
  const result = plan(input([job('low', { duration: 480, priority: 3 }), job('urgent', { duration: 480, priority: 1 })]));
  assert.equal(result.scheduled[0].id, 'urgent');
  assert.equal(result.unscheduled[0].id, 'low');
});

test('one technician cannot be double booked', () => {
  const result = plan(input([job('a'), job('b')]));
  assert.deepEqual(result.scheduled.map(item => [item.start, item.end]), [[0, 60], [60, 120]]);
});

test('shared equipment cannot be double booked across technicians', () => {
  const result = plan(input([job('a', { resource: 'crane' }), job('b', { resource: 'crane' })], [tech('alex'), tech('jamie')]));
  assert.equal(result.scheduled[1].start, 60);
});

test('separate resources allow parallel jobs', () => {
  const result = plan(input([job('a', { resource: 'crane' }), job('b', { resource: 'bench' })], [tech('alex'), tech('jamie')]));
  assert.equal(result.scheduled[1].start, 0);
});

test('dependencies finish before dependent work starts', () => {
  const result = plan(input([job('a', { priority: 3 }), job('b', { priority: 1, dependsOn: ['a'] })], [tech('alex'), tech('jamie')]));
  assert.equal(result.scheduled.find(item => item.id === 'b').start, 60);
});

test('breaks cannot split an indivisible job', () => {
  const person = tech();
  person.availability = [{ start: 0, end: 50 }, { start: 80, end: 200 }];
  assert.equal(plan(input([job('a')], [person])).scheduled[0].start, 80);
});

test('all required skills must belong to the same technician', () => {
  const result = plan(input([job('a', { skills: ['mechanical', 'electrical'] })], [tech('alex'), tech('jamie', ['electrical'])]));
  assert.match(result.unscheduled[0].reason, /skills/);
});

test('failed dependency blocks descendants with an explanation', () => {
  const result = plan(input([job('a', { skills: ['welding'] }), job('b', { dependsOn: ['a'] }), job('c', { dependsOn: ['b'] })]));
  assert.equal(result.unscheduled.length, 3);
  assert.match(result.unscheduled[1].reason, /dependency: a/);
  assert.match(result.unscheduled[2].reason, /dependency: b/);
});

test('cycles and unknown dependencies are rejected', () => {
  assert.throws(() => plan(input([job('a', { dependsOn: ['b'] }), job('b', { dependsOn: ['a'] })])), /cycle/);
  assert.throws(() => plan(input([job('a', { dependsOn: ['missing'] })])), /Unknown/);
});

test('invalid data is rejected', () => {
  for (const jobs of [[job('a'), job('a')], [job('a', { duration: -1 })], [job('a', { duration: 0 })],
    [job('a', { priority: 0 })], [job('a', { due: NaN })]]) assert.throws(() => plan(input(jobs)));
  const person = tech();
  person.availability = [{ start: 0, end: 100 }, { start: 90, end: 200 }];
  assert.throws(() => plan(input([], [person])), /Overlapping/);
});

test('late jobs remain visible and are counted', () => {
  const result = plan(input([job('a', { due: 30 })]));
  assert.equal(result.scheduled[0].lateMinutes, 30);
  assert.equal(result.summary.lateJobs, 1);
});

test('empty job list gives an empty plan', () => {
  assert.equal(plan(input([])).summary.scheduledJobs, 0);
});

test('planning is deterministic, independent of input array order, and does not mutate input', () => {
  const data = input([job('c'), job('b'), job('a')], [tech('jamie'), tech('alex')]);
  const before = JSON.stringify(data);
  const result = plan(data);
  assert.equal(JSON.stringify(data), before);
  const reversed = { ...data, jobs: [...data.jobs].reverse(), technicians: [...data.technicians].reverse() };
  assert.deepEqual(plan(reversed).scheduled, result.scheduled);
});

test('SVG escapes untrusted job titles', () => {
  const data = input([job('a', { title: '<script>alert(1)</script>' })]);
  const svg = svgReport(data, plan(data));
  assert.ok(!svg.includes('<script>'));
  assert.ok(svg.includes('&lt;script&gt;'));
});

test('independent verifier catches deliberately corrupted output', () => {
  const data = input([job('a'), job('b')]);
  const result = plan(data);
  result.scheduled[1].start = 0;
  result.scheduled[1].end = 60;
  assert.throws(() => assertFeasible(data, result), /Double booking/);
});

test('demo includes assignments and three understandable failures', () => {
  const data = JSON.parse(readFileSync(new URL('./examples/workshop.json', import.meta.url), 'utf8'));
  const result = plan(data);
  assert.equal(result.summary.scheduledJobs, 7);
  assert.equal(result.summary.unscheduledJobs, 3);
});

test('100 generated workloads preserve scheduling invariants', () => {
  let seed = 42;
  const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 2 ** 32; };
  for (let run = 0; run < 100; run++) {
    const jobs = Array.from({ length: 25 }, (_, n) => job(`job-${n}`, {
      duration: 15 + Math.floor(random() * 8) * 15,
      priority: 1 + Math.floor(random() * 3), due: Math.floor(random() * 481),
      resource: random() < 0.5 ? 'crane' : null,
      dependsOn: n > 0 && random() < 0.3 ? [`job-${Math.floor(random() * n)}`] : []
    }));
    const data = input(jobs, [tech('alex'), tech('jamie'), tech('morgan')]);
    assert.equal(assertFeasible(data, plan(data)), true);
  }
});
