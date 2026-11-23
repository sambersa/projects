const validId = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,40}$/.test(value);
const requireValue = (condition, message) => { if (!condition) throw new Error(message); };
const integer = (value, min, max) => Number.isInteger(value) && value >= min && value <= max;
const overlaps = (a, b) => a.start < b.end && b.start < a.end;

export function validate(input) {
  requireValue(input && typeof input === 'object', 'Expected a workshop object');
  requireValue(integer(input.dayMinutes, 1, 1440), 'dayMinutes must be 1-1440');
  requireValue(Array.isArray(input.technicians) && input.technicians.length > 0, 'At least one technician is required');
  requireValue(Array.isArray(input.jobs), 'jobs must be an array');
  const ids = new Set();
  for (const tech of input.technicians) {
    requireValue(validId(tech.id) && !ids.has(tech.id), 'Technician IDs must be unique and valid');
    ids.add(tech.id);
    requireValue(Array.isArray(tech.skills) && tech.skills.every(validId), `Invalid skills for ${tech.id}`);
    requireValue(Array.isArray(tech.availability) && tech.availability.length > 0, `Missing availability for ${tech.id}`);
    const windows = [...tech.availability].sort((a, b) => a.start - b.start);
    for (let n = 0; n < windows.length; n++) {
      const window = windows[n];
      requireValue(integer(window.start, 0, input.dayMinutes - 1) && integer(window.end, 1, input.dayMinutes) && window.start < window.end,
        `Invalid availability for ${tech.id}`);
      requireValue(n === 0 || windows[n - 1].end <= window.start, `Overlapping availability for ${tech.id}`);
    }
  }
  ids.clear();
  for (const job of input.jobs) {
    requireValue(validId(job.id) && !ids.has(job.id), 'Job IDs must be unique and valid');
    ids.add(job.id);
    requireValue(typeof job.title === 'string' && job.title.length > 0 && job.title.length <= 120, `Invalid title for ${job.id}`);
    requireValue(integer(job.duration, 1, 1440), `Invalid duration for ${job.id}`);
    requireValue(integer(job.priority, 1, 3), `Priority must be 1-3 for ${job.id}`);
    requireValue(integer(job.due, 0, input.dayMinutes), `Invalid due time for ${job.id}`);
    requireValue(Array.isArray(job.skills) && job.skills.every(validId), `Invalid skills for ${job.id}`);
    requireValue(Array.isArray(job.dependsOn) && job.dependsOn.every(validId) && new Set(job.dependsOn).size === job.dependsOn.length,
      `Invalid dependencies for ${job.id}`);
    requireValue(job.resource === undefined || job.resource === null || validId(job.resource), `Invalid resource for ${job.id}`);
  }
  const jobs = new Map(input.jobs.map(job => [job.id, job]));
  for (const job of input.jobs) {
    for (const dep of job.dependsOn) requireValue(jobs.has(dep), `Unknown dependency ${dep}`);
  }
  const visited = new Set(), active = new Set();
  function visit(id) {
    requireValue(!active.has(id), `Dependency cycle involving ${id}`);
    if (visited.has(id)) return;
    active.add(id);
    for (const dep of jobs.get(id).dependsOn) visit(dep);
    active.delete(id);
    visited.add(id);
  }
  for (const job of input.jobs) visit(job.id);
}

function earliestSlot(tech, job, release, scheduled) {
  const blockers = scheduled.filter(item => item.technician === tech.id ||
    (job.resource && item.resource === job.resource)).sort((a, b) => a.start - b.start);
  for (const window of [...tech.availability].sort((a, b) => a.start - b.start)) {
    let start = Math.max(window.start, release);
    for (const block of blockers) {
      if (overlaps({ start, end: start + job.duration }, block)) start = block.end;
    }
    if (start + job.duration <= window.end) return { start, end: start + job.duration };
  }
  return null;
}

/** Deterministic greedy list scheduling, with no promise of a globally optimal plan. */
export function plan(input) {
  validate(input);
  const scheduled = [], unscheduled = [];
  const pending = new Map(input.jobs.map(job => [job.id, job]));
  const finished = new Map(), rejected = new Set();
  while (pending.size) {
    const ready = [...pending.values()].filter(job => job.dependsOn.every(id => !pending.has(id)));
    ready.sort((a, b) => a.priority - b.priority || a.due - b.due || a.id.localeCompare(b.id, 'en'));
    const job = ready[0];
    requireValue(job, 'Cannot resolve dependencies');
    pending.delete(job.id);
    const failed = job.dependsOn.filter(id => rejected.has(id));
    let reason;
    if (failed.length) reason = `Blocked by unscheduled dependency: ${failed.join(', ')}`;
    const qualified = input.technicians.filter(tech => job.skills.every(skill => tech.skills.includes(skill)));
    if (!reason && qualified.length === 0) reason = 'No technician has all required skills';
    const release = Math.max(0, ...job.dependsOn.map(id => finished.get(id)?.end ?? 0));
    const candidates = reason ? [] : qualified.map(tech => {
      const slot = earliestSlot(tech, job, release, scheduled);
      const load = scheduled.filter(item => item.technician === tech.id).reduce((sum, item) => sum + item.duration, 0);
      return slot && { ...slot, technician: tech.id, load };
    }).filter(Boolean);
    candidates.sort((a, b) => a.end - b.end || a.load - b.load || a.technician.localeCompare(b.technician, 'en'));
    if (!reason && candidates.length === 0) reason = 'No continuous slot within technician availability and resource capacity';
    if (reason) {
      rejected.add(job.id);
      unscheduled.push({ id: job.id, title: job.title, reason });
      continue;
    }
    const best = candidates[0];
    const item = { ...job, technician: best.technician, start: best.start, end: best.end,
      lateMinutes: Math.max(0, best.end - job.due) };
    scheduled.push(item);
    finished.set(job.id, item);
  }
  scheduled.sort((a, b) => a.start - b.start || a.technician.localeCompare(b.technician, 'en'));
  const technicians = input.technicians.map(tech => {
    const available = tech.availability.reduce((sum, w) => sum + w.end - w.start, 0);
    const booked = scheduled.filter(item => item.technician === tech.id).reduce((sum, item) => sum + item.duration, 0);
    return { id: tech.id, availableMinutes: available, bookedMinutes: booked, utilizationPercent: Math.round(booked / available * 100) };
  });
  const result = { scheduled, unscheduled, technicians, summary: {
    totalJobs: input.jobs.length, scheduledJobs: scheduled.length, unscheduledJobs: unscheduled.length,
    lateJobs: scheduled.filter(item => item.lateMinutes > 0).length,
    totalLateMinutes: scheduled.reduce((sum, item) => sum + item.lateMinutes, 0)
  } };
  assertFeasible(input, result);
  return result;
}

/** Independent invariant checks protect output against future algorithm regressions. */
export function assertFeasible(input, result) {
  const scheduled = new Map(result.scheduled.map(item => [item.id, item]));
  requireValue(scheduled.size === result.scheduled.length, 'Duplicate scheduled job');
  const assigned = [...result.scheduled, ...result.unscheduled].map(item => item.id);
  requireValue(assigned.length === input.jobs.length && new Set(assigned).size === input.jobs.length &&
    input.jobs.every(job => assigned.includes(job.id)), 'Plan must account for each job exactly once');
  for (const item of result.scheduled) {
    const source = input.jobs.find(job => job.id === item.id);
    const tech = input.technicians.find(tech => tech.id === item.technician);
    requireValue(source && tech && item.duration === source.duration && item.end - item.start === source.duration, 'Invalid assignment');
    requireValue(source.skills.every(skill => tech.skills.includes(skill)), 'Skill mismatch');
    requireValue(tech.availability.some(w => item.start >= w.start && item.end <= w.end), 'Outside availability');
    for (const id of source.dependsOn) requireValue(scheduled.has(id) && scheduled.get(id).end <= item.start, 'Dependency violated');
    for (const other of result.scheduled) {
      if (other.id === item.id) continue;
      requireValue(!(overlaps(item, other) && (item.technician === other.technician ||
        (source.resource && source.resource === input.jobs.find(job => job.id === other.id).resource))), 'Double booking');
    }
  }
  return true;
}
