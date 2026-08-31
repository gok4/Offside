/* ============================================
   OFFSIDE — main.js
   Simple hash-based router + renderers.
   Routes:
     #/                -> home (badge wall)
     #/team/<slug>      -> team squad page
     #/icons            -> icons/legends gallery
     #/match/<matchId>  -> match center (score, stats, lineups, points)
     #/standings        -> league table
   ============================================ */

const app = document.getElementById('app');

const POSITION_GROUPS = [
  { label: 'Goalkeepers', positions: ['GK'] },
  { label: 'Defenders', positions: ['RB', 'CB', 'LB'] },
  { label: 'Midfielders', positions: ['CDM', 'CM', 'CAM', 'RM', 'LM'] },
  { label: 'Forwards', positions: ['RW', 'LW', 'ST'] },
];

let teamsData = null;
let iconsData = null;

function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

async function loadTeams() {
  if (teamsData) return teamsData;
  const res = await fetch('data/teams.json');
  const json = await res.json();
  teamsData = json.teams || [];
  return teamsData;
}

async function loadIcons() {
  if (iconsData) return iconsData;
  try {
    const res = await fetch('data/icons.json');
    const json = await res.json();
    iconsData = json.icons || [];
  } catch (e) {
    iconsData = [];
  }
  return iconsData;
}

async function loadSponsors() {
  const row = document.getElementById('sponsor-row');
  try {
    const res = await fetch('data/sponsors.json');
    const json = await res.json();
    const sponsors = json.sponsors || [];
    if (sponsors.length === 0) return;
    row.innerHTML = sponsors
      .map(s => `<img src="assets/sponsors/${encodeURIComponent(s.image)}" alt="${escapeHtml(s.name)}">`)
      .join('');
  } catch (e) {
    // no sponsors.json yet — footer just stays empty, that's fine
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

/* ---------- Renderers ---------- */

async function renderHome() {
  const teams = await loadTeams();

  app.innerHTML = `
    <section class="hero">
      <span class="hero-eyebrow">Global Football League</span>
      <h1 class="hero-title">24 clubs. One league.</h1>
      <p class="hero-sub">Pick a club to view its squad, or step into the Icons gallery to see the legends of the game.</p>
    </section>
    <p class="section-label">Clubs</p>
    <div class="badge-wall">
      ${teams.map(t => `
        <a class="badge-tile" href="#/team/${slugify(t.name)}">
          <img src="assets/team_logos/${encodeURIComponent(t.logo)}" alt="${escapeHtml(t.name)} badge" loading="lazy">
          <span>${escapeHtml(t.name)}</span>
        </a>
      `).join('')}
    </div>
  `;
}

async function renderTeam(slug) {
  const teams = await loadTeams();
  const team = teams.find(t => slugify(t.name) === slug);

  if (!team) {
    app.innerHTML = `<div class="empty-state">No club found for this link. <a href="#/">Back to clubs</a>.</div>`;
    return;
  }

  const groupsHtml = POSITION_GROUPS.map(group => {
    const players = team.players.filter(p => group.positions.includes(p.position));
    if (players.length === 0) return '';
    return `
      <div class="position-group">
        <p class="section-label">${group.label}</p>
        <div class="player-grid">
          ${players.map(p => renderPlayerCard(team.name, p)).join('')}
        </div>
      </div>
    `;
  }).join('');

  app.innerHTML = `
    <div class="team-header">
      <img src="assets/team_logos/${encodeURIComponent(team.logo)}" alt="${escapeHtml(team.name)} badge">
      <div>
        <h1>${escapeHtml(team.name)}</h1>
        ${team.manager ? `<p class="manager">Manager: ${escapeHtml(team.manager)}</p>` : ''}
      </div>
    </div>
    ${groupsHtml}
    <a class="back-link" href="#/">&larr; All clubs</a>
  `;
}

function renderPlayerCard(teamName, player) {
  if (!player.image) {
    return `
      <button class="player-card" data-team="${escapeHtml(teamName)}" data-player="${escapeHtml(player.name)}">
        <div class="player-img-wrap"><span class="empty-state" style="border:none;padding:0;font-size:0.7rem;">No image yet</span></div>
        <div class="player-meta">
          <p class="player-name">${escapeHtml(player.name)}</p>
          <span class="player-position">${escapeHtml(player.position)}</span>
        </div>
      </button>
    `;
  }
  const src = `assets/player_cards/${encodeURIComponent(teamName)}/${encodeURIComponent(player.image)}`;
  return `
    <button class="player-card" data-team="${escapeHtml(teamName)}" data-player="${escapeHtml(player.name)}">
      <div class="player-img-wrap">
        <img src="${src}" alt="${escapeHtml(player.name)}" loading="lazy">
      </div>
      <div class="player-meta">
        <p class="player-name">${escapeHtml(player.name)}</p>
        <span class="player-position">${escapeHtml(player.position)}</span>
      </div>
    </button>
  `;
}

async function renderIcons() {
  const icons = await loadIcons();

  if (icons.length === 0) {
    app.innerHTML = `
      <section class="hero">
        <span class="hero-eyebrow">Legends</span>
        <h1 class="hero-title">Icons</h1>
      </section>
      <div class="empty-state">
        No icons added yet. Once icon images are in <code>assets/icons/</code> and listed in <code>data/icons.json</code>, they'll appear here.
      </div>
    `;
    return;
  }

  app.innerHTML = `
    <section class="hero">
      <span class="hero-eyebrow">Legends</span>
      <h1 class="hero-title">Icons</h1>
    </section>
    <div class="icons-grid">
      ${icons.map(i => `
        <div class="player-card">
          <div class="player-img-wrap">
            <img src="assets/icons/${encodeURIComponent(i.image)}" alt="${escapeHtml(i.name)}" loading="lazy">
          </div>
          <div class="player-meta">
            <p class="player-name">${escapeHtml(i.name)}</p>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

/* ---------- Match Center & Standings ---------- */

async function loadMatch(matchId) {
  const res = await fetch(`data/matches/${matchId}.json`);
  if (!res.ok) throw new Error('Match not found');
  return res.json();
}

async function loadStandings() {
  const res = await fetch('data/standings.json');
  const json = await res.json();
  return json.standings || [];
}

function teamLogoSrc(teams, teamName) {
  const team = teams.find(t => t.name === teamName);
  return team ? `assets/team_logos/${encodeURIComponent(team.logo)}` : '';
}

function playerPosition(teams, teamName, playerName) {
  const team = teams.find(t => t.name === teamName);
  const player = team?.players.find(p => p.name === playerName);
  return player ? player.position : '';
}

const TEAM_STAT_LABELS = {
  totalShots: 'Total Shots',
  shotsOnTarget: 'Shots On Target',
  touchesInOppositionBox: 'Touches In Box',
  accuratePasses: 'Accurate Passes',
  yellowCards: 'Yellow Cards',
};

function renderStatBars(homeStats, awayStats) {
  return Object.entries(TEAM_STAT_LABELS).map(([key, label]) => {
    const h = homeStats[key] || 0;
    const a = awayStats[key] || 0;
    const total = h + a || 1;
    const homePct = (h / total) * 100;
    return `
      <div class="compare-row">
        <div class="compare-labels"><span class="compare-home-val">${h}</span><span class="compare-away-val">${a}</span></div>
        <p class="compare-stat-name">${label}</p>
        <div class="compare-track">
          <div class="compare-home-bar" style="width:${homePct}%"></div>
          <div class="compare-away-bar" style="width:${100 - homePct}%"></div>
        </div>
      </div>`;
  }).join('');
}

function renderLineupList(teamName, names, playerStats, teams) {
  if (!names || names.length === 0) {
    return `<li class="empty-line">&mdash;</li>`;
  }
  return names.map(name => {
    const stats = playerStats[name] || {};
    const pos = playerPosition(teams, teamName, name);
    return `
      <li>
        <button class="lineup-player" data-team="${escapeHtml(teamName)}" data-player="${escapeHtml(name)}">
          <span class="lineup-pos">${escapeHtml(pos)}</span>
          <span class="lineup-name">${escapeHtml(name)}</span>
          <span class="lineup-pts">${stats.points ?? ''}</span>
        </button>
      </li>`;
  }).join('');
}

function renderPointsTable(team, teams) {
  const rows = Object.entries(team.playerStats)
    .sort((a, b) => (b[1].points || 0) - (a[1].points || 0))
    .map(([name, stats]) => {
      const pos = playerPosition(teams, team.name, name);
      return `
        <tr>
          <td>${escapeHtml(name)}</td>
          <td>${escapeHtml(pos)}</td>
          <td class="pts-val">${stats.points ?? 0}</td>
        </tr>`;
    }).join('');
  return `
    <p class="section-label">${escapeHtml(team.name)}</p>
    <table class="points-table">
      <thead><tr><th>Player</th><th>Pos</th><th>Pts</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

async function renderMatch(matchId) {
  const teams = await loadTeams();
  let match;
  try {
    match = await loadMatch(matchId);
  } catch (e) {
    app.innerHTML = `<div class="empty-state">No match found for this link. <a href="#/standings">Back to standings</a>.</div>`;
    return;
  }

  const home = match.homeTeam;
  const away = match.awayTeam;

  app.innerHTML = `
    <div class="scoreboard">
      <div class="scoreboard-meta">
        ${match.matchweek ? `<span>Matchweek ${escapeHtml(String(match.matchweek))}</span>` : ''}
        ${match.date ? `<span>${escapeHtml(match.date)}</span>` : ''}
        ${match.venue ? `<span>${escapeHtml(match.venue)}</span>` : ''}
      </div>
      <div class="scoreboard-row">
        <div class="scoreboard-team home">
          <img class="scoreboard-badge" src="${teamLogoSrc(teams, home.name)}" alt="${escapeHtml(home.name)} badge">
          <span class="scoreboard-team-name">${escapeHtml(home.name)}</span>
        </div>
        <div class="scoreboard-center">
          <div class="scoreboard-score">${home.score} &mdash; ${away.score}</div>
          <div class="scoreboard-status">${match.status === 'completed' ? 'Full Time' : escapeHtml((match.status || '').toUpperCase())}</div>
        </div>
        <div class="scoreboard-team away">
          <img class="scoreboard-badge" src="${teamLogoSrc(teams, away.name)}" alt="${escapeHtml(away.name)} badge">
          <span class="scoreboard-team-name">${escapeHtml(away.name)}</span>
        </div>
      </div>
    </div>

    <p class="section-label">Match Stats</p>
    <div class="compare-bars">
      ${renderStatBars(home.teamStats, away.teamStats)}
    </div>

    <p class="section-label">Lineups</p>
    <div class="lineups-grid">
      <div class="lineup-col">
        <h4>${escapeHtml(home.name)}</h4>
        <ul class="lineup-list">${renderLineupList(home.name, home.startingXI, home.playerStats, teams)}</ul>
        <p class="lineup-subheading">Substitutes</p>
        <ul class="lineup-list">${renderLineupList(home.name, [...(home.substitutes || []), ...(home.unusedSubstitutes || [])], home.playerStats, teams)}</ul>
      </div>
      <div class="lineup-col">
        <h4>${escapeHtml(away.name)}</h4>
        <ul class="lineup-list">${renderLineupList(away.name, away.startingXI, away.playerStats, teams)}</ul>
        <p class="lineup-subheading">Substitutes</p>
        <ul class="lineup-list">${renderLineupList(away.name, [...(away.substitutes || []), ...(away.unusedSubstitutes || [])], away.playerStats, teams)}</ul>
      </div>
    </div>

    <p class="section-label">Fantasy Points</p>
    ${renderPointsTable(home, teams)}
    ${renderPointsTable(away, teams)}

    <a class="back-link" href="#/standings">&larr; Standings</a>
  `;
}

async function renderStandingsPage() {
  const standings = await loadStandings();

  if (standings.length === 0) {
    app.innerHTML = `
      <section class="hero">
        <span class="hero-eyebrow">Offside — Global Super League</span>
        <h1 class="hero-title">Standings</h1>
      </section>
      <div class="empty-state">No completed matches yet. Check back after matchweek 1.</div>
    `;
    return;
  }

  app.innerHTML = `
    <section class="hero">
      <span class="hero-eyebrow">Offside — Global Super League</span>
      <h1 class="hero-title">Standings</h1>
    </section>
    <table class="standings-table">
      <thead>
        <tr><th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr>
      </thead>
      <tbody>
        ${standings.map(r => `
          <tr>
            <td class="rank-cell">${r.rank}</td>
            <td><a href="#/team/${slugify(r.team)}">${escapeHtml(r.team)}</a></td>
            <td>${r.played}</td><td>${r.won}</td><td>${r.drawn}</td><td>${r.lost}</td>
            <td>${r.goalsFor}</td><td>${r.goalsAgainst}</td>
            <td class="${r.goalDifference > 0 ? 'gd-pos' : (r.goalDifference < 0 ? 'gd-neg' : '')}">${r.goalDifference > 0 ? '+' + r.goalDifference : r.goalDifference}</td>
            <td class="pts-cell">${r.points}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

async function loadVersion() {
  const tag = document.getElementById('version-tag');
  try {
    const res = await fetch('data/version.json');
    const json = await res.json();
    if (json.version) tag.textContent = `· v${json.version}`;
  } catch (e) {
    // no version.json yet — footer just omits the version, that's fine
  }
}

/* ---------- Player quick-view modal ---------- */

const STAT_LABELS = { pac: 'PAC', sho: 'SHO', pas: 'PAS', dri: 'DRI', def: 'DEF', phy: 'PHY' };

const modalOverlay = document.getElementById('player-modal');
const modalBody = document.getElementById('modal-body');
const modalClose = document.getElementById('modal-close');

function statBar(label, value) {
  const pct = Math.max(0, Math.min(100, value));
  return `
    <div class="stat-row">
      <span class="stat-label">${label}</span>
      <div class="stat-bar"><div class="stat-fill" style="width:${pct}%"></div></div>
      <span class="stat-value">${value}</span>
    </div>
  `;
}

async function openPlayerModal(teamName, playerName) {
  const teams = await loadTeams();
  const team = teams.find(t => t.name === teamName);
  const player = team?.players.find(p => p.name === playerName);
  if (!player) return;

  const imgSrc = player.image
    ? `assets/player_cards/${encodeURIComponent(teamName)}/${encodeURIComponent(player.image)}`
    : null;

  if (!player.stats) {
    modalBody.innerHTML = `
      ${imgSrc ? `<img class="modal-player-img" src="${imgSrc}" alt="${escapeHtml(playerName)}">` : ''}
      <h2 class="modal-name">${escapeHtml(playerName)}</h2>
      <p class="modal-sub">${escapeHtml(player.position)} · ${escapeHtml(teamName)}</p>
      <p class="empty-state" style="margin-top:16px;">Stats not available for this player yet.</p>
    `;
  } else {
    const s = player.stats;
    modalBody.innerHTML = `
      ${imgSrc ? `<img class="modal-player-img" src="${imgSrc}" alt="${escapeHtml(playerName)}">` : ''}
      <h2 class="modal-name">${escapeHtml(playerName)}</h2>
      <p class="modal-sub">${escapeHtml(player.position)} · ${escapeHtml(teamName)}${s.nation ? ` · ${escapeHtml(s.nation)}` : ''}</p>
      <div class="modal-ovr">${s.ovr} <span>OVR</span></div>
      <div class="stat-list">
        ${Object.entries(STAT_LABELS).map(([key, label]) => statBar(label, s[key])).join('')}
      </div>
    `;
  }

  modalOverlay.hidden = false;
  document.body.style.overflow = 'hidden';
}

function closePlayerModal() {
  modalOverlay.hidden = true;
  document.body.style.overflow = '';
}

modalClose.addEventListener('click', closePlayerModal);
modalOverlay.addEventListener('click', (e) => {
  if (e.target === modalOverlay) closePlayerModal();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !modalOverlay.hidden) closePlayerModal();
});

// Event delegation: catches clicks on player cards in home/team/icons views,
// and lineup-player rows in the match center, since content is re-rendered
// dynamically by the router.
app.addEventListener('click', (e) => {
  const trigger = e.target.closest('.player-card, .lineup-player');
  if (trigger && trigger.dataset.team && trigger.dataset.player) {
    openPlayerModal(trigger.dataset.team, trigger.dataset.player);
  }
});

/* ---------- Router ---------- */

function setActiveNav(route) {
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    const isIcons = href === '#/icons';
    const isStandings = href === '#/standings';
    let active;
    if (isIcons) {
      active = route.startsWith('#/icons');
    } else if (isStandings) {
      active = route.startsWith('#/standings') || route.startsWith('#/match/');
    } else {
      active = (route === '#/' || route.startsWith('#/team'));
    }
    link.classList.toggle('active', active);
  });
}

async function router() {
  const route = window.location.hash || '#/';
  setActiveNav(route);
  window.scrollTo(0, 0);

  if (route === '#/' || route === '') {
    await renderHome();
  } else if (route.startsWith('#/team/')) {
    const slug = route.replace('#/team/', '');
    await renderTeam(slug);
  } else if (route.startsWith('#/icons')) {
    await renderIcons();
  } else if (route.startsWith('#/match/')) {
    const matchId = route.replace('#/match/', '');
    await renderMatch(matchId);
  } else if (route.startsWith('#/standings')) {
    await renderStandingsPage();
  } else {
    app.innerHTML = `<div class="empty-state">Page not found. <a href="#/">Back to clubs</a>.</div>`;
  }
}

window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', () => {
  router();
  loadSponsors();
  loadVersion();
});
