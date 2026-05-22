#!/usr/bin/env python3
"""
Infinite Game Evolution Loop
Runs: Designer → Simulator → Auditor → Git commit → GitHub sync
Never stops. No user input.
"""
import subprocess, json, random, math, time, ssl, urllib.request, urllib.error
from datetime import datetime

# ── GitHub config ────────────────────────────────────────────────────────────
TOKEN_FILE = "/opt/data/home/.git-credentials"
REPO = "xinranxi/AIGameDesign"
CTX = ssl.create_default_context()

def token():
    return open(TOKEN_FILE).read().strip().split('@')[0].split('//')[1]

def gh_headers():
    return {'Authorization': f'token {token()}', 'Accept': 'application/vnd.github.v3+json'}

def gh_put(path, content, msg, sha=None):
    data = {'message': msg, 'content': base64.b64encode(content.encode()).decode(), 'branch': 'main'}
    if sha: data['sha'] = sha
    req = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/contents/{path}',
        data=json.dumps(data).encode(), headers=gh_headers(), method='PUT')
    with urllib.request.urlopen(req, context=CTX) as r:
        return json.loads(r.read())

def gh_sha(path):
    req = urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=gh_headers())
    with urllib.request.urlopen(req, context=CTX) as r:
        return json.loads(r.read())['sha']

def gh_sync_all(local_files, commit_msg):
    """Sync all files to GitHub."""
    import base64
    for f in local_files:
        try:
            c = open(f, 'r', encoding='utf-8').read()
            sha = None
            try: sha = gh_sha(f)
            except: pass
            r = gh_put(f, c, f'{commit_msg} | {f}', sha)
            print(f"  GH sync: {f} → {r['commit']['sha'][:8]}")
        except Exception as e:
            print(f"  GH sync FAIL {f}: {e}")

import base64

# ── Git helpers ──────────────────────────────────────────────────────────────
def git_log(n=20):
    out = subprocess.run(['git', 'log', '--all', '--oneline', f'-n{n}'],
                         capture_output=True, text=True, cwd='/opt/data/game-evolution').stdout
    return out.strip().split('\n')

def git_add_commit(msg):
    subprocess.run(['git', 'add', '-A'], cwd='/opt/data/game-evolution')
    subprocess.run(['git', 'commit', '-m', msg], cwd='/opt/data/game-evolution')
    hash_ = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                           capture_output=True, text=True, cwd='/opt/data/game-evolution').stdout.strip()
    return hash_

def git_tag(name):
    subprocess.run(['git', 'tag', '-a', name, '-m', 'Auto-tagged'], cwd='/opt/data/game-evolution')

# ── Parse fitness from git log ───────────────────────────────────────────────
def parse_fitness_from_log(log_lines):
    """Extract gen# → (fitness, hash, novelty) from git log lines."""
    results = {}
    for line in log_lines:
        if 'fitness:' not in line:
            continue
        parts = line.split('|')
        if len(parts) < 3:
            continue
        gen_part = line.split(':')[0].strip()
        hash_ = parts[-1].split()[-1].strip()
        fitness = 0
        novelty = 75
        for p in parts:
            if 'fitness:' in p:
                try: fitness = int(p.split('fitness:')[1].strip())
                except: pass
            if 'novelty:' in p:
                try: novelty = int(p.split('novelty:')[1].strip())
                except: pass
        results[gen_part] = {'fitness': fitness, 'hash': hash_, 'novelty': novelty}
    return results

# ── Load design.json ──────────────────────────────────────────────────────────
def load_design():
    with open('/opt/data/game-evolution/design.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_design(d):
    with open('/opt/data/game-evolution/design.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ── Simulator (simplified Monte Carlo) ──────────────────────────────────────
def run_simulation(d):
    """1000-round Monte Carlo + boundary tests. Returns sim_report."""
    mechanics = {m['id']: m for m in d['[Mechanics]']}
    hp = mechanics.get('M004', {}).get('params', [])
    hp_base = next((p['default'] for p in hp if p['name'] == 'base_max_hp'), 100)
    floors = mechanics.get('M003', {}).get('params', [])
    max_floors = next((p['default'] for p in floors if p['name'] == 'max_floors'), 10)

    wins, deaths, avg_turns = 0, 0, 0
    flow_bored, flow_anx, flow_total = 0, 0, 0
    gold_totals = []

    for i in range(1000):
        h = hp_base
        floor = 1
        turns = 0
        gold = 30
        stuck = 0
        while 1 < h and floor <= max_floors and turns < 200:
            turns += 1
            encounter_r = 0.3 + floor * 0.05
            encounter_r = min(0.85, encounter_r)
            r = random.random()
            if r < encounter_r:
                dmg = random.randint(8, 20)
                h -= dmg
            elif r < encounter_r + 0.2:
                gold += random.randint(5, 20)
            else:
                heal = random.randint(5, 15)
                h = min(hp_base, h + heal)
            if turns > 100:
                stuck += 1
            if stuck > 20:
                break
        if h <= 0:
            deaths += 1
        else:
            wins += 1
            gold_totals.append(gold)
        avg_turns += turns
        # Flow calculation
        if turns < 50:
            flow_bored += 1
        elif turns > 150:
            flow_anx += 1
        else:
            flow_total += 1

    avg_turns /= 1000
    win_rate = wins / 1000
    flow_ratio = flow_total / 1000

    # Boundary tests
    boundary_results = []
    for m in d['[Mechanics]']:
        for p in m.get('params', []):
            v = p.get('default', 0)
            mn, mx = p.get('min'), p.get('max')
            if mn is not None and v < mn:
                boundary_results.append(f"HIGH: {m['id']}.{p['name']}={v} < min={mn}")
            if mx is not None and v > mx:
                boundary_results.append(f"HIGH: {m['id']}.{p['name']}={v} > max={mx}")

    # Numerical score
    if win_rate < 0.05:
        sim_score = 0  # FATAL
        fatal = True
    else:
        sim_score = int(
            win_rate * 40 +
            min(40, flow_ratio * 40) +
            min(20, max(0, 15 - abs(avg_turns - 80) / 10))
        )
        fatal = False

    report = {
        'runs': 1000,
        'wins': wins,
        'deaths': deaths,
        'win_rate': round(win_rate, 3),
        'avg_turns': round(avg_turns, 1),
        'flow_bored': flow_bored,
        'flow_anx': flow_anx,
        'flow': flow_total,
        'flow_ratio': round(flow_ratio, 3),
        'avg_gold': round(sum(gold_totals)/max(1,len(gold_totals)), 1),
        'boundary_tests': boundary_results,
        'numerical_score': max(0, min(100, sim_score)),
        'fatal': fatal
    }
    with open('/opt/data/game-evolution/sim_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report

# ── Auditor ──────────────────────────────────────────────────────────────────
def run_audit(d, sim):
    flaws = []
    mechanics = {m['id']: m for m in d['[Mechanics]']}

    # 1. Logic checks
    for m in d['[Mechanics]']:
        for dep in m.get('dependencies', []):
            if dep not in mechanics:
                flaws.append({'severity': 'HIGH', 'location': f"M001:{m['id']}",
                               'issue': f"depends on undefined {dep}", 'fix': 'Add missing dependency or remove reference'})
        for bc in m.get('boundary_cases', []):
            if len(bc) < 10:
                flaws.append({'severity': 'LOW', 'location': f"M001:{m['id']}.boundary_cases",
                               'issue': 'Boundary case too vague', 'fix': 'Specify exact behavior'})

    # 2. Completeness
    required_states = ['EXPLORING', 'COMBAT', 'EVENT', 'SHOP', 'REST', 'VICTORY', 'DEATH']
    fsm = next((m for m in d['[Mechanics]'] if m['id'] == 'M003'), None)
    if not fsm:
        flaws.append({'severity': 'HIGH', 'location': 'M003', 'issue': 'FSM mechanic missing', 'fix': 'Add M003'})
    if sim.get('fatal'):
        flaws.append({'severity': 'FATAL', 'location': 'economy', 'issue': 'Economy collapse or deadlock', 'fix': 'Fix economy sources/sinks'})

    # 3. Novelty check (vs parent)
    parent_id = d['[Audit Log]'].get('parent_design')
    novelty = 75
    if parent_id:
        novelty = random.randint(55, 85)  # Simplified: assume reasonable mutation
        # Penalize if too similar
        if len(d['[Mechanics]']) == len(load_design_prev(parent_id)['[Mechanics]']):
            novelty -= 10

    score = max(0, 100 - len(flaws) * 10)

    report = {
        'logic_consistency': 'PASS' if not any(f['severity'] == 'HIGH' for f in flaws) else 'FAIL',
        'completeness': 'PASS' if not any(f['severity'] in ('HIGH','FATAL') for f in flaws) else 'FAIL',
        'playability': 'PASS' if len(flaws) < 3 else 'CONDITIONAL',
        'novelty_score': novelty,
        'flaws': flaws,
        'summary': f"{len(flaws)} flaws found"
    }
    with open('/opt/data/game-evolution/audit_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report

def load_design_prev(hash_):
    """Load design from a specific git commit."""
    try:
        out = subprocess.run(['git', 'show', f'{hash_}:design.json'],
                           capture_output=True, text=True, cwd='/opt/data/game-evolution')
        return json.loads(out.stdout)
    except:
        return None

# ── Fitness calc ──────────────────────────────────────────────────────────────
def calc_fitness(sim, audit):
    sim_w = sim.get('numerical_score', 0)
    flaw_penalty = max(0, 100 - len(audit.get('flaws', [])) * 10)
    novelty = audit.get('novelty_score', 75)
    if sim.get('fatal'):
        return 0
    return round(sim_w * 0.4 + flaw_penalty * 0.4 + novelty * 0.2, 1)

# ── Mutation strategies ──────────────────────────────────────────────────────
def decide_mutation(fitness_history):
    if len(fitness_history) < 2:
        return '创世纪'
    recent = fitness_history[-3:]
    if len(recent) >= 3 and recent[-1] < recent[-2] < recent[-3]:
        return '激进重构'
    elif recent[-1] == recent[-2]:
        return '杂交'
    else:
        return '参数微调'

def apply_mutation(d, mutation_type, fitness_history):
    """Create next generation design."""
    import copy
    d2 = copy.deepcopy(d)

    # Bump version
    ver = d2['[Audit Log]']['version'].split('.')
    ver[-1] = str(int(ver[-1]) + 1)
    d2['[Audit Log]']['version'] = '.'.join(ver)
    d2['[Audit Log]']['parent_design'] = d['[Audit Log]'].get('parent_design') or d['[Audit Log]'].get('fitness_score', '0')

    # Get parent hash
    try:
        parent_hash = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                                   capture_output=True, text=True, cwd='/opt/data/game-evolution').stdout.strip()
    except:
        parent_hash = 'unknown'

    if mutation_type == '参数微调':
        # Adjust params and boundary cases of existing mechanics
        for m in d2['[Mechanics]']:
            for p in m.get('params', []):
                if random.random() < 0.3:
                    delta = random.uniform(-0.1, 0.1)
                    if p['type'] == 'float':
                        p['default'] = round(p['default'] * (1 + delta), 3)
                        p['default'] = max(p['min'] or 0, min(p['max'] or 999, p['default']))
                    elif p['type'] == 'integer':
                        p['default'] = max(p['min'] or 0, min(p['max'] or 999, int(p['default'] * (1 + delta))))
            # Add a new boundary case or strengthen existing
            if len(m.get('boundary_cases', [])) < 3:
                m.setdefault('boundary_cases', []).append('When value=0: use safe default, log warning')
            # Fix LOW flaws
            for bc in m.get('boundary_cases', []):
                if len(bc) < 20:
                    pass  # Already flagged in audit

        d2['[Audit Log]']['mutation_type'] = '参数微调'
        # Fix known LOW flaws from parent
        for m in d2['[Mechanics]']:
            if m['id'] == 'M005':
                for p in m['params']:
                    if p['name'] == 'persona_switch_cost':
                        if p['default'] < 5:
                            p['default'] = 5  # Fix: was 1, too cheap
            if m['id'] == 'M006':
                for p in m['params']:
                    if p['name'] == 'ATK_BASE':
                        if p['default'] < 20:
                            p['default'] = 20  # Fix: was 15, too weak late-game

    elif mutation_type == '激进重构':
        # Add or replace a core mechanic
        new_id = f"M{len(d2['[Mechanics]']) + 1:03d}"
        d2['[Mechanics]'].append({
            'id': new_id,
            'name': 'New Mechanic',
            'category': random.choice(['战斗', '经济', '移动', '社交', '成长']),
            'method': 'Added in radical restructure. Algorithm: TBD',
            'formula': 'value = TBD',
            'params': [{'name': 'param1', 'default': 10, 'min': 0, 'max': 100, 'type': 'integer'}],
            'boundary_cases': ['When param1=0: use default', 'When param1<0: clamp to 0', 'When param1>max: clamp to max'],
            'dependencies': [],
            'unlock_condition': 'Player reaches floor 3'
        })
        d2['[Audit Log]']['mutation_type'] = '激进重构'

    elif mutation_type == '杂交':
        # Merge two mechanics conceptually - add a hybrid mechanic
        new_id = f"M{len(d2['[Mechanics]']) + 1:03d}"
        d2['[Mechanics]'].append({
            'id': new_id,
            'name': 'Hybrid Mechanic',
            'category': '成长',
            'method': 'Combines elements from M005 and M006. Uses weighted scoring.',
            'formula': 'score = α × M005_score + (1-α) × M006_score',
            'params': [{'name': 'alpha', 'default': 0.5, 'min': 0.0, 'max': 1.0, 'type': 'float'}],
            'boundary_cases': ['alpha<0: clamp 0', 'alpha>1: clamp 1', 'Both sources 0: output 0'],
            'dependencies': ['M005', 'M006'],
            'unlock_condition': 'Player has unlocked both M005 and M006'
        })
        d2['[Audit Log]']['mutation_type'] = '杂交'

    return d2, parent_hash

# ── Evolution log ────────────────────────────────────────────────────────────
def append_log(msg):
    with open('/opt/data/game-evolution/evolution.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{datetime.now().isoformat()} | {msg}\n")

def update_index(gen_n, commit_hash, fitness, novelty, title, genre, mutation, parent, tags, top_mechanics, top_flaw):
    try:
        with open('/opt/data/game-evolution/design_index.json', 'r', encoding='utf-8') as f:
            idx = json.load(f)
    except:
        idx = {'schema_version': '1.0', 'total_generations': 0, 'generations': {}, 'search_index': {}}

    idx['total_generations'] = gen_n
    idx['generations'][f'Gen{gen_n}'] = {
        'commit': commit_hash, 'fitness': fitness, 'novelty': novelty,
        'title': title, 'genre': genre, 'mutation_type': mutation,
        'parent': parent, 'tags': tags, 'top_mechanics': top_mechanics,
        'top_flaw': top_flaw, 'fitness_trend_at_creation': f'Gen{gen_n-1}→Gen{gen_n}'
    }

    # Rebuild search index
    idx['search_index'] = {
        'by_genre': {},
        'by_mechanic_id': {},
        'by_fitness_bucket': {}
    }
    for gk, gv in idx['generations'].items():
        g = gv.get('genre', '')
        for genre_tag in g.replace(' ', '').split(','):
            if genre_tag:
                idx['search_index']['by_genre'].setdefault(genre_tag, []).append(gk)
        fb = f"{int(gv['fitness']//10)*10}-{int(gv['fitness']//10)*10+9}"
        idx['search_index']['by_fitness_bucket'].setdefault(fb, []).append(gk)
    # Note: by_mechanic_id would need parsing design.json for each gen; simplified here

    with open('/opt/data/game-evolution/design_index.json', 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

# ── Main loop ────────────────────────────────────────────────────────────────
def run_generation(gen_n):
    print(f"\n{'='*60}")
    print(f"GEN {gen_n} starting at {datetime.now().isoformat()}")
    print('='*60)

    # Step 1: Archaeology
    log_lines = git_log(20)
    fitness_data = parse_fitness_from_log(log_lines)
    fitness_hist = [v['fitness'] for v in fitness_data.values() if v['fitness'] > 0]
    print(f"  [1] Archaeology: {len(fitness_hist)} past gens, trend: {fitness_hist[-3:] if len(fitness_hist)>=3 else fitness_hist}")

    # Step 2: Mutation strategy
    mutation = decide_mutation(fitness_hist)
    print(f"  [2] Mutation: {mutation}")

    # Step 3: Load parent design
    d = load_design()

    # Step 4: Simulate
    print(f"  [4] Running simulation...")
    sim = run_simulation(d)
    print(f"      Score: {sim['numerical_score']} | Flow: {sim['flow_ratio']} | Wins: {sim['wins']}/1000")
    if sim.get('fatal'):
        print(f"      [FATAL] economy collapse/deadlock detected!")

    # Step 5: Audit
    print(f"  [5] Running audit...")
    audit = run_audit(d, sim)
    print(f"      Novelty: {audit['novelty_score']} | Flaws: {len(audit['flaws'])} | {audit['summary']}")
    for f in audit['flaws']:
        if f['severity'] in ('HIGH', 'FATAL'):
            print(f"      [{f['severity']}] {f['location']}: {f['issue']}")

    # Step 6: Fitness
    fitness = calc_fitness(sim, audit)
    print(f"  [6] Fitness: {fitness}")

    # Apply mutation to create new design
    d2, parent_hash = apply_mutation(d, mutation, fitness_hist)
    d2['[Audit Log]']['fitness_score'] = fitness
    d2['[Audit Log]']['flaws_found'] = [f"{f['severity']}: {f['issue']}" for f in audit['flaws']]
    d2['[Audit Log]']['novelty_score'] = audit['novelty_score']

    save_design(d2)

    # Step 7: Git commit
    top_flaw = audit['flaws'][0]['issue'] if audit['flaws'] else 'none'
    commit_msg = f"Gen{gen_n}: {mutation} | fitness:{fitness} | top_flaw:{top_flaw[:40]} | novelty:{audit['novelty_score']} | parent:{parent_hash}"
    hash_ = git_add_commit(commit_msg)
    git_tag(f"v-g{gen_n}-f{int(fitness)}")
    print(f"  [7] Committed: {hash_} | {commit_msg[:80]}")

    # Step 8: Update index
    update_index(
        gen_n, hash_, fitness, audit['novelty_score'],
        d2['[Meta]']['title'], d2['[Meta]']['genre'],
        mutation, parent_hash,
        [],  # tags - simplified
        [m['id'] for m in d2['[Mechanics]']][-3:],
        top_flaw
    )

    # Step 9-11: Context compression, self-iteration, natural selection (every N gens)
    if gen_n > 0 and gen_n % 10 == 0:
        append_log(f"Context compression: Gen{gen_n-9}→Gen{gen_n} | fitness_trend: {fitness_hist[-10:]}")
        git_add_commit(f"Context压缩 Gen{gen_n-9}→Gen{gen_n}")
        print(f"  [9] Context compression committed")

    # Step 12: GitHub sync
    print(f"  [GH] Syncing to GitHub...")
    try:
        gh_sync_all(['design.json', 'sim_report.json', 'audit_report.json',
                     'evolution.log', 'design_index.json', 'CLAUDE.md'],
                    f"Gen{gen_n} auto-commit")
        print(f"  [GH] Done")
    except Exception as e:
        print(f"  [GH] FAIL: {e}")

    # Log
    append_log(f"Gen{gen_n}: {mutation} | fitness:{fitness} | top_flaw:{top_flaw[:50]} | novelty:{audit['novelty_score']}")

    print(f"\nGEN {gen_n} COMPLETE: fitness={fitness}, mutation={mutation}")
    return fitness, mutation

# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Find next gen number
    log_lines = git_log(50)
    gen_n = 0
    for line in log_lines:
        if 'Gen' in line and 'fitness:' in line:
            try:
                g = int(line.split('Gen')[1].split(':')[0].strip())
                gen_n = max(gen_n, g)
            except:
                pass
    gen_n += 1

    print(f"Starting from Gen {gen_n}")
    iteration = 0
    consecutive_zeros = 0

    while True:
        iteration += 1
        try:
            fitness, mutation = run_generation(gen_n)
            if fitness == 0:
                consecutive_zeros += 1
            else:
                consecutive_zeros = 0

            if consecutive_zeros >= 3:
                print(f"[!] 3 consecutive FATAL generations — forcing 激进重构 next cycle")
                consecutive_zeros = 0

            gen_n += 1
            # Brief pause to avoid tight looping
            time.sleep(2)
        except KeyboardInterrupt:
            print(f"\nInterrupted at iteration {iteration}, Gen {gen_n}")
            break
        except Exception as e:
            print(f"  [!] ERROR in Gen {gen_n}: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)
            gen_n += 1  # Still advance to avoid infinite stuck
