const esc = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[char]);
export const clock = minute => `${String(8 + Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`;

export function svgReport(input, result) {
  const height = 280 + input.technicians.length * 120 + result.unscheduled.length * 25;
  const left = 175, width = 850;
  const parts = [`<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="${height}" viewBox="0 0 1100 ${height}" role="img" aria-labelledby="title desc">`,
    '<title id="title">Workshop maintenance plan</title>',
    '<desc id="desc">Technician timelines showing scheduled jobs, breaks, utilization and reasons for unscheduled work.</desc>',
    `<rect width="1100" height="${height}" fill="#f4f2ec"/>`, '<g font-family="Segoe UI,Arial,sans-serif" fill="#182d35">',
    '<text x="45" y="45" font-size="13" letter-spacing="3" fill="#48766d">WORKSHOP PLANNER / DAILY PLAN</text>',
    '<text x="45" y="90" font-size="32" font-weight="700">The day, without the double bookings.</text>',
    `<text x="45" y="123" font-size="15">${result.summary.scheduledJobs} scheduled · ${result.summary.unscheduledJobs} unassigned · ${result.summary.lateJobs} late</text>`];
  input.technicians.forEach((tech, n) => {
    const y = 185 + n * 120;
    const stats = result.technicians.find(item => item.id === tech.id);
    parts.push(`<text x="45" y="${y + 25}" font-size="18" font-weight="700">${esc(tech.id)}</text>`,
      `<text x="45" y="${y + 48}" font-size="12" fill="#53706e">${stats.utilizationPercent}% booked</text>`,
      `<rect x="${left}" y="${y}" width="${width}" height="65" rx="8" fill="#e2ded4"/>`);
    for (const window of tech.availability) {
      parts.push(`<rect x="${left + window.start / input.dayMinutes * width}" y="${y}" width="${(window.end - window.start) / input.dayMinutes * width}" height="65" fill="#e4eeea"/>`);
    }
    for (const item of result.scheduled.filter(item => item.technician === tech.id)) {
      const x = left + item.start / input.dayMinutes * width;
      const w = item.duration / input.dayMinutes * width;
      const color = item.lateMinutes ? '#b65a35' : item.priority === 1 ? '#1c6258' : '#3f7774';
      parts.push(`<rect x="${x}" y="${y + 5}" width="${w}" height="55" rx="6" fill="${color}"><title>${esc(item.title)} | ${clock(item.start)}–${clock(item.end)} | ${esc(item.resource ?? 'no shared resource')}</title></rect>`,
        `<text x="${x + 8}" y="${y + 27}" font-size="12" fill="white">${esc(item.id)}</text>`);
      if (w > 100) parts.push(`<text x="${x + 8}" y="${y + 46}" font-size="10" fill="#d8efea">${clock(item.start)}–${clock(item.end)}</text>`);
    }
    for (let hour = 0; hour <= Math.floor(input.dayMinutes / 60); hour++) {
      const x = left + hour * 60 / input.dayMinutes * width;
      parts.push(`<text x="${x}" y="${y + 84}" font-size="10" fill="#53706e" text-anchor="middle">${clock(hour * 60)}</text>`);
    }
  });
  const bottom = 205 + input.technicians.length * 120;
  parts.push(`<text x="45" y="${bottom}" font-size="16" font-weight="700">Unscheduled work</text>`);
  result.unscheduled.forEach((item, n) => parts.push(`<text x="45" y="${bottom + 28 + n * 25}" font-size="12">${esc(item.id)} — ${esc(item.reason)}</text>`));
  parts.push('</g></svg>');
  return parts.join('\n') + '\n';
}

export function markdownReport(result) {
  const lines = ['# Workshop plan', '', '| Job | Technician | Start | End | Late by |', '| --- | --- | --- | --- | --- |'];
  for (const item of result.scheduled) lines.push(`| ${item.id} | ${item.technician} | ${clock(item.start)} | ${clock(item.end)} | ${item.lateMinutes} min |`);
  lines.push('', '## Unscheduled', '');
  for (const item of result.unscheduled) lines.push(`- **${item.id}:** ${item.reason}`);
  if (!result.unscheduled.length) lines.push('All jobs scheduled.');
  return lines.join('\n') + '\n';
}
