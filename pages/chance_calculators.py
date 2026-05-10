"""Chance Calculators page - calculate costs and probabilities for sub-modules and modules."""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

# Register this page
dash.register_page(__name__, path="/chance-calculators", name="Chance Calculators", order=5)


def get_submodule_cost_table():
    """Return DataFrame for sub-module reroll cost by locks."""
    locks = list(range(8))
    costs = [10, 40, 160, 500, 1000, 1600, 2250, 3000]
    df = pd.DataFrame([costs], columns=[f"{l} Lock{'s' if l != 1 else ''}" for l in locks])
    df.insert(0, 'Locks', locks)
    df_cost = pd.DataFrame({'Locks': locks, 'Cost': costs})
    return df_cost

def get_rarity_chance_table():
    """Return DataFrame for sub-module rarity chances."""
    rarities = ['Common', 'Rare', 'Epic', 'Legendary', 'Mythic', 'Ancestral']
    chances = [46.2, 40.0, 10.0, 2.5, 1.0, 0.3]
    df = pd.DataFrame([chances], columns=rarities)
    df.insert(0, 'Rarity', 'Chance')
    return df

def get_submodule_types_count(module_type):
    """Return the number of sub-module types for the selected module type."""
    # Map module type to submodule_effects.json category
    mapping = {
        'Cannon': 'cannon_submodules_attack',
        'Armor': 'armor_submodules_defense',
        'Generator': 'generator_submodules_utility',
        'Core': 'cores_submodules_ultimate_weapons',
    }
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'submodule_effects.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for cat in data['categories']:
            if cat['category'] == mapping[module_type]:
                return len(cat['submodules'])
    except Exception:
        pass
    return 0

def pulls_needed(chance, certainty):
    """Return number of pulls needed for given chance and certainty (as decimals)."""
    import math
    if chance <= 0 or certainty >= 1:
        return float('inf')
    return math.ceil(math.log(1-certainty) / math.log(1-chance))

def format_number(value):
    """Format number as 0, 0.0k, or 0.0M."""
    if value == '∞' or value == float('inf'):
        return '∞'
    try:
        num = float(value)
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}k"
        else:
            return f"{int(num)}"
    except (ValueError, TypeError):
        return str(value)


def calculate_submodule_chances(dice_on_hand: int):
    """Calculate sub-module pull chances based on dice available."""
    # Base probabilities (placeholder - adjust based on actual game rates)
    base_rates = {
        'Common': 0.50,
        'Rare': 0.30,
        'Epic': 0.15,
        'Legendary': 0.04,
        'Mythic': 0.009,
        'Ancestral': 0.001,
    }
    
    # Calculate number of pulls possible
    pulls_1x = dice_on_hand // 10
    pulls_10x = dice_on_hand // 100
    
    data = []
    for rarity, rate in base_rates.items():
        # Probability of NOT getting the rarity in N pulls
        prob_none_1x = (1 - rate) ** pulls_1x if pulls_1x > 0 else 1.0
        prob_at_least_one_1x = 1 - prob_none_1x
        
        prob_none_10x = (1 - rate) ** (pulls_10x * 10) if pulls_10x > 0 else 1.0
        prob_at_least_one_10x = 1 - prob_none_10x
        
        data.append({
            'Rarity': rarity,
            'Base Rate': f'{rate * 100:.1f}%',
            'Chance (1x pulls)': f'{prob_at_least_one_1x * 100:.2f}%',
            'Pulls (1x)': pulls_1x,
            'Chance (10x pulls)': f'{prob_at_least_one_10x * 100:.2f}%',
            'Pulls (10x)': pulls_10x,
        })
    
    return pd.DataFrame(data)


def get_module_counts():
    """Return the number of modules for each type and rarity."""
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'module_abilities.json')
    
    counts = {
        'cannon': {'common': 2, 'rare': 4, 'epic': 0},
        'armor': {'common': 2, 'rare': 4, 'epic': 0},
        'generator': {'common': 2, 'rare': 4, 'epic': 0},
        'core': {'common': 2, 'rare': 4, 'epic': 0},
    }
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Count epic modules from JSON (all modules in JSON are epic+)
        for cat in data['categories']:
            category = cat['category']
            if category in ['cannon', 'armor', 'generators', 'cores']:
                # Map category name
                key = 'generator' if category == 'generators' else category.rstrip('s')
                counts[key]['epic'] = len(cat['modules'])
    except Exception:
        pass
    
    return counts


def calculate_module_pulls_needed(module_type: str, certainty: float, copies_needed: int):
    """Calculate pulls needed to get specified copies of a module with given certainty.
    
    Each pull costs 20 gems. Items are put back (with replacement), so you can get duplicates.
    Pity system: After 150 pulls without an epic, you get a guaranteed random epic module.
    
    To get K copies of a specific item with probability p per pull:
    We need to calculate pulls for K successes using negative binomial distribution approximation.
    For epic modules, account for the pity system which gives 1 random epic every 150 pulls.
    """
    counts = get_module_counts()
    module_key = module_type.lower()
    
    # Rarity rates and module counts
    common_rate = 0.685  # 68.5%
    rare_rate = 0.29     # 29%
    epic_rate = 0.025    # 2.5%
    pity_threshold = 150  # Pulls until guaranteed epic
    
    # Total modules across all types for each rarity
    total_common = sum(counts[t]['common'] for t in ['cannon', 'armor', 'generator', 'core'])  # 8 total
    total_rare = sum(counts[t]['rare'] for t in ['cannon', 'armor', 'generator', 'core'])      # 16 total
    total_epic = sum(counts[t]['epic'] for t in ['cannon', 'armor', 'generator', 'core'])      # 24 total
    
    # Chance per module (distributed equally across ALL modules of that rarity)
    common_chance = common_rate / total_common if total_common > 0 else 0  # 68.5% / 8 = 8.5625% per module
    rare_chance = rare_rate / total_rare if total_rare > 0 else 0          # 29% / 16 = 1.8125% per module
    epic_chance_base = epic_rate / total_epic if total_epic > 0 else 0     # 2.5% / 24 = 0.104% per module
    
    # For epic modules, calculate effective chance including pity system
    # Every 150 pulls guarantees 1 random epic (1/24 chance of specific epic)
    # Effective chance per pull for specific epic = base_chance + (1/24) * (1/150)
    epic_chance_pity = 1.0 / (pity_threshold * total_epic) if total_epic > 0 else 0
    epic_chance = epic_chance_base + epic_chance_pity  # Combined chance from normal drops + pity
    
    # Cost per pull
    cost_per_pull = 20
    
    data = []
    for rarity, chance in [('Common', common_chance), ('Rare', rare_chance), ('Epic (w/ pity)', epic_chance)]:
        if copies_needed == 1:
            # For 1 copy, use standard formula
            n_pulls = pulls_needed(chance, certainty)
        else:
            # For K copies, we need to find n such that P(X >= K) >= certainty
            # where X ~ Binomial(n, p)
            # Approximation: we iterate to find the right n
            import math
            from scipy import stats
            
            # Start with expected value and search
            expected = copies_needed / chance if chance > 0 else float('inf')
            n = int(expected * 1.5)  # Start with 1.5x expected
            
            if chance <= 0:
                n_pulls = float('inf')
            else:
                # Binary search for the right number of pulls
                left, right = copies_needed, int(expected * 10) if expected != float('inf') else 100000
                n_pulls = right
                
                for _ in range(100):  # Max 100 iterations
                    mid = (left + right) // 2
                    # P(X >= K) = 1 - P(X < K) = 1 - P(X <= K-1)
                    prob = 1 - stats.binom.cdf(copies_needed - 1, mid, chance)
                    
                    if prob >= certainty:
                        n_pulls = mid
                        right = mid - 1
                    else:
                        left = mid + 1
                    
                    if left > right:
                        break
        
        total_cost = n_pulls * cost_per_pull if n_pulls != float('inf') else float('inf')
        
        data.append({
            'Rarity': rarity,
            'Rate per Module': f'{chance * 100:.3f}%',
            'Pulls Needed': format_number(n_pulls),
            'Total Cost (Gems)': format_number(total_cost),
        })
    
    return pd.DataFrame(data)


def calculate_module_chances(gems_on_hand: int, module_type: str, copies_needed: int):
    """Calculate module pull chances based on gems available and module type.
    
    Each pull costs 20 gems. With replacement, so duplicates are possible.
    Pity system: After 150 pulls without an epic, you get a guaranteed random epic module.
    Calculate probability of getting K or more copies of a specific module.
    """
    # Get module counts
    counts = get_module_counts()
    module_key = module_type.lower()
    
    # Base rarity rates
    common_rate = 0.685  # 68.5%
    rare_rate = 0.29     # 29%
    epic_rate = 0.025    # 2.5%
    pity_threshold = 150  # Pulls until guaranteed epic
    
    # Total modules across all types for each rarity
    total_common = sum(counts[t]['common'] for t in ['cannon', 'armor', 'generator', 'core'])  # 8 total
    total_rare = sum(counts[t]['rare'] for t in ['cannon', 'armor', 'generator', 'core'])      # 16 total
    total_epic = sum(counts[t]['epic'] for t in ['cannon', 'armor', 'generator', 'core'])      # 24 total
    
    # Calculate chance per specific module (distributed equally across ALL modules of that rarity)
    common_chance = common_rate / total_common if total_common > 0 else 0  # 68.5% / 8 = 8.5625%
    rare_chance = rare_rate / total_rare if total_rare > 0 else 0          # 29% / 16 = 1.8125%
    epic_chance_base = epic_rate / total_epic if total_epic > 0 else 0     # 2.5% / 24 = 0.104%
    
    # For epic modules, include pity system in effective chance
    epic_chance_pity = 1.0 / (pity_threshold * total_epic) if total_epic > 0 else 0
    epic_chance = epic_chance_base + epic_chance_pity
    
    # Cost per pull
    cost_per_pull = 20
    
    # Calculate number of pulls possible
    n_pulls = gems_on_hand // cost_per_pull
    
    data = []
    rates = {
        'Common': common_chance,
        'Rare': rare_chance,
        'Epic (w/ pity)': epic_chance,
    }
    
    for rarity, rate in rates.items():
        if n_pulls > 0 and rate > 0:
            if copies_needed == 1:
                # Probability of at least 1 copy
                prob = 1 - (1 - rate) ** n_pulls
            else:
                # Probability of at least K copies using binomial distribution
                from scipy import stats
                # P(X >= K) = 1 - P(X < K) = 1 - P(X <= K-1)
                prob = 1 - stats.binom.cdf(copies_needed - 1, n_pulls, rate)
        else:
            prob = 0.0
        
        data.append({
            'Rarity': rarity,
            'Rate per Module': f'{rate * 100:.3f}%',
            'Pulls Possible': n_pulls,
            f'Chance (≥{copies_needed} cop{"y" if copies_needed == 1 else "ies"})': f'{prob * 100:.2f}%',
        })
    
    return pd.DataFrame(data)


def create_table(df: pd.DataFrame, table_id: str | None = None):
    """Create a styled HTML table from a DataFrame (compatible with dash_bootstrap_components)."""
    header = [html.Thead(html.Tr([html.Th(col) for col in df.columns]))]
    body = [
        html.Tbody([
            html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(len(df))
        ])
    ]
    return dbc.Table(header + body, striped=True, bordered=True, hover=True, responsive=True, className='table-dark', id=table_id)


# Page layout
layout = html.Div([
    html.H1('Chance Calculators', className="page-title"),

    # Section 1: Sub-Modules
    html.H2('1. Sub-Module Effects', className="section-title mt-4"),


    # Module Type, Certainty, and Ban Dropdowns
    dbc.Row([
        dbc.Col([
            html.Label('Module Type:', className='mb-2'),
            dcc.Dropdown(
                id='module-type',
                options=[
                    {'label': 'Cannon', 'value': 'Cannon'},
                    {'label': 'Armor', 'value': 'Armor'},
                    {'label': 'Generator', 'value': 'Generator'},
                    {'label': 'Core', 'value': 'Core'},
                ],
                value='Cannon',
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
        dbc.Col([
            html.Label('Certainty:', className='mb-2'),
            dcc.Dropdown(
                id='certainty',
                options=[
                    {'label': '99%', 'value': 0.99},
                    {'label': '95%', 'value': 0.95},
                    {'label': '90%', 'value': 0.90},
                    {'label': '80%', 'value': 0.80},
                ],
                value=0.95,
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
        dbc.Col([
            html.Label('# Ban Sub-Module Effects:', className='mb-2'),
            dcc.Dropdown(
                id='ban-count',
                options=[{'label': str(i), 'value': i} for i in range(0, 5)],
                value=0,
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Available Sub-Module Slots:', className='mb-2'),
            dcc.Dropdown(
                id='available-slots',
                options=[{'label': str(i), 'value': i} for i in range(1, 8)],
                value=7,
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
        dbc.Col([
            html.Label('Currently Locked Slots:', className='mb-2'),
            dcc.Dropdown(
                id='locked-slots',
                options=[{'label': str(i), 'value': i} for i in range(0, 8)],
                value=0,
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
    ]),
    html.Div(id='submodule-types-count', className='mb-2'),
    html.Div(id='submodule-lock-constraints', className='mb-2'),

    # Pulls Needed & Cost Table
    html.H3('1.1 Rerolls & Cost Needed for Specific Sub-Module', className="subsection-title mt-3"),
    html.P("This table shows the estimated number of pulls and the associated costs needed to obtain a specific sub-module with a given certainty."),
    html.Div(id='submodule-pulls-needed-table', className='mb-4'),

    # Chances of Getting Sub-Modules Based on Dice on Hand
    html.H3('1.2 Chances of Getting Sub-Modules Based on Dice on Hand', className="subsection-title mt-3"),
    html.Label('Dice on Hand:', className='mb-2'),
    dbc.Input(
        id='dice-on-hand',
        type='number',
        placeholder='Enter number of dice',
        value=0,
        min=0,
        className='mb-3'
    ),
    html.P("This table shows the estimated chances of obtaining specific sub-modules based on the number of dice you have on hand."),

    html.Div(id='submodule-chances-dice-table', className='mb-4'),

    html.Hr(),

    # Section 2: Modules
    html.H2('2. Module Chance', className="section-title mt-4"),
    dbc.Row([
        dbc.Col([
            html.Label('Module Type:', className='mb-2'),
            dcc.Dropdown(
                id='module-type-section2',
                options=[
                    {'label': 'Cannon', 'value': 'Cannon'},
                    {'label': 'Armor', 'value': 'Armor'},
                    {'label': 'Generator', 'value': 'Generator'},
                    {'label': 'Core', 'value': 'Core'},
                ],
                value='Cannon',
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
        dbc.Col([
            html.Label('Banner Type:', className='mb-2'),
            dcc.Dropdown(
                id='banner-type',
                options=[
                    {'label': 'Standard Banner', 'value': 'standard'},
                    {'label': 'Special Banner', 'value': 'special'},
                ],
                value='standard',
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
        dbc.Col([
            html.Label('Certainty:', className='mb-2'),
            dcc.Dropdown(
                id='certainty-section2',
                options=[
                    {'label': '99%', 'value': 0.99},
                    {'label': '95%', 'value': 0.95},
                    {'label': '90%', 'value': 0.90},
                    {'label': '80%', 'value': 0.80},
                ],
                value=0.95,
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
        dbc.Col([
            html.Label('# Copies Needed:', className='mb-2'),
            dcc.Dropdown(
                id='copies-needed',
                options=[{'label': str(i), 'value': i} for i in range(1, 9)],
                value=1,
                clearable=False,
                className='mb-3'
            ),
        ], width=3),
    ]),
    html.Div(id='module-counts-display', className='mb-3'),
    html.H4('2.1 Pulls & Cost Needed for Specific Module', className="subsection-title mt-3"),
    html.P("This table shows the estimated number of pulls (at 20 gems each) and total cost needed to obtain the specified number of copies of a specific module with the given certainty."),
    html.Div(id='module-cost-table', className='mb-4'),
    html.H4('2.2 Module Chance Based on Gems on Hand', className="subsection-title mt-3"),
    html.P("This table shows the estimated chances of obtaining the specified number of copies of a specific module based on the number of gems you have on hand (each pull costs 20 gems)."),
    dbc.Row([
        dbc.Col([
            html.Label('Gems on Hand:', className='mb-2'),
            dbc.Input(
                id='gems-on-hand',
                type='number',
                placeholder='Enter gems amount',
                value=10000,
                min=0,
                className='mb-3'
            ),
        ], width=4),
    ]),
    html.Div(id='module-chance-table', className='mb-4'),
    
    html.H4('2.3 Expected Module Accumulation', className="subsection-title mt-3"),
    html.P("This table shows the expected number of modules you will accumulate across all pulls. Common modules convert to 10 dice each, rare modules are shown per module type (total rare / 4), and epic modules exclude the specific module you're targeting."),
    html.Div(id='module-accumulation-table', className='mb-4'),
])


# Callbacks

# --- Sub-Module Section Callbacks ---
@callback(
    Output('submodule-lock-cost-table', 'children'),
    Input('module-type', 'value')
)
def update_submodule_lock_cost_table(_):
    df = get_submodule_cost_table()
    return create_table(df, 'submodule-lock-cost-data')

@callback(
    Output('submodule-rarity-chance-table', 'children'),
    Input('module-type', 'value')
)
def update_submodule_rarity_chance_table(_):
    df = get_rarity_chance_table()
    return create_table(df, 'submodule-rarity-chance-data')

@callback(
    Output('submodule-types-count', 'children'),
    Input('module-type', 'value')
)
def update_submodule_types_count(module_type):
    n_types = get_submodule_types_count(module_type)
    return html.Div(f"Number of sub-module types for {module_type}: {n_types}", className='fw-bold')

@callback(
    Output('submodule-lock-constraints', 'children'),
    [Input('available-slots', 'value'), Input('locked-slots', 'value')]
)
def update_submodule_lock_constraints(available_slots, locked_slots):
    if available_slots is None:
        available_slots = 7
    if locked_slots is None:
        locked_slots = 0
    
    max_locks = available_slots - 1
    min_locks = locked_slots
    available_to_reroll = available_slots - locked_slots
    
    return html.Div([
        html.Span(f"Lock constraints: Min {min_locks} locks, Max {max_locks} locks | ", className='fw-bold'),
        html.Span(f"Available slots to reroll: {available_to_reroll}", className='fw-bold text-success')
    ])

@callback(
    Output('submodule-pulls-needed-table', 'children'),
    [Input('module-type', 'value'), Input('certainty', 'value'), Input('ban-count', 'value'),
     Input('available-slots', 'value'), Input('locked-slots', 'value')]
)
def update_submodule_pulls_needed_table(module_type, certainty, ban_count, available_slots, locked_slots):
    if available_slots is None:
        available_slots = 7
    if locked_slots is None:
        locked_slots = 0
    
    rarities = ['Common', 'Rare', 'Epic', 'Legendary', 'Mythic', 'Ancestral']
    base_chances = [46.2, 40.0, 10.0, 2.5, 1.0, 0.3]
    locks = list(range(8))
    costs = [10, 40, 160, 500, 1000, 1600, 2250, 3000]
    n_types = max(1, get_submodule_types_count(module_type) - (ban_count or 0))
    
    # Calculate available slots to reroll
    available_to_reroll = max(1, available_slots - locked_slots)
    
    # Lock constraints
    min_locks = locked_slots
    max_locks = available_slots - 1
    
    pulls = []
    for rarity, base in zip(rarities, base_chances):
        # Base chance per pull for one specific sub-module
        chance_per_type = (base / 100.0) / n_types if n_types > 0 else 0
        
        row = {
            'Rarity': rarity,
            'Chance per type': f"{chance_per_type*100:.3f}%",
        }
        
        # Calculate pulls needed for EACH lock level
        # Each lock level means different number of available slots to reroll
        for l, cost in zip(locks, costs):
            if l < min_locks or l > max_locks:
                row[f'{l} Lock{"s" if l != 1 else ""}'] = 'N/A'
            else:
                # Available slots for this lock level
                slots_available_for_lock = available_slots - l
                
                if slots_available_for_lock <= 0:
                    row[f'{l} Lock{"s" if l != 1 else ""}'] = 'N/A'
                else:
                    # Use hypergeometric distribution (sampling without replacement)
                    # Each effect can only appear once per reroll across all slots
                    # P(at least one success) = 1 - P(no success)
                    # P(no success) = C(N-K, n) / C(N, n)
                    # Where: N = total types, K = desired types (1), n = slots being filled
                    import math
                    N = n_types  # Total number of sub-module types available
                    K = 1  # We want 1 specific type
                    n = min(slots_available_for_lock, N)  # Can't draw more than available types
                    
                    if n >= N:
                        # If we're drawing all or more types than available, we're guaranteed to get it
                        prob_get_specific_type = 1.0
                    elif n > 0 and N > 0:
                        # Hypergeometric: P(at least one success in n draws from N types)
                        # P(no success) = C(N-K, n) / C(N, n)
                        prob_no_success = math.comb(N - K, n) / math.comb(N, n) if N >= K and N >= n else 1.0
                        prob_get_specific_type = 1 - prob_no_success
                    else:
                        prob_get_specific_type = 0
                    
                    # Effective chance per pull = P(rarity) × P(specific type | rarity)
                    effective_chance = (base / 100.0) * prob_get_specific_type
                    n_pulls = pulls_needed(effective_chance, certainty)
                    
                    # Calculate and display formatted cost in dice only
                    if n_pulls != float('inf'):
                        total_dice = n_pulls * cost
                        row[f'{l} Lock{"s" if l != 1 else ""}\n({cost} Dice/Reroll)'] = format_number(total_dice)
                    else:
                        row[f'{l} Lock{"s" if l != 1 else ""}\n({cost} Dice/Reroll)'] = '∞'
        
        pulls.append(row)
    df = pd.DataFrame(pulls)
    return create_table(df, 'submodule-pulls-needed-data')


@callback(
    Output('submodule-chances-dice-table', 'children'),
    [Input('dice-on-hand', 'value'), Input('module-type', 'value'), Input('ban-count', 'value'),
     Input('available-slots', 'value'), Input('locked-slots', 'value')]
)
def update_submodule_chances_dice_table(dice_on_hand, module_type, ban_count, available_slots, locked_slots):
    """Calculate chances of getting sub-modules based on dice on hand.
    
    For each rarity and lock level:
    - Calculate number of rerolls possible: dice_on_hand / cost_per_reroll
    - Calculate chance per pull accounting for multiple available slots
    - Calculate overall chance: P = 1 - (1-p_effective)^n, where n is number of rerolls
    """
    if dice_on_hand is None or dice_on_hand < 0:
        dice_on_hand = 0
    if available_slots is None:
        available_slots = 7
    if locked_slots is None:
        locked_slots = 0
    
    rarities = ['Common', 'Rare', 'Epic', 'Legendary', 'Mythic', 'Ancestral']
    base_chances = [46.2, 40.0, 10.0, 2.5, 1.0, 0.3]
    locks = list(range(8))
    costs = [10, 40, 160, 500, 1000, 1600, 2250, 3000]
    n_types = max(1, get_submodule_types_count(module_type) - (ban_count or 0))
    
    # Calculate available slots to reroll
    available_to_reroll = max(1, available_slots - locked_slots)
    
    # Lock constraints
    min_locks = locked_slots
    max_locks = available_slots - 1
    
    rows = []
    for rarity, base in zip(rarities, base_chances):
        # Calculate single slot chance for display
        p_single = (base / 100.0) / n_types if n_types > 0 else 0
        
        row = {
            'Rarity': rarity,
            'Chance per type': f"{p_single*100:.3f}%",
        }
        
        # Calculate chance for each lock level
        for l, cost in zip(locks, costs):
            if l < min_locks or l > max_locks:
                row[f'{l} Lock{"s" if l != 1 else ""}'] = 'N/A'
            elif cost > 0:
                # Calculate slots available for this lock level
                slots_available_for_lock = available_slots - l
                
                if slots_available_for_lock <= 0:
                    row[f'{l} Lock{"s" if l != 1 else ""}'] = 'N/A'
                else:
                    # Use hypergeometric distribution for this specific lock level
                    import math
                    N = n_types  # Total number of sub-module types available
                    K = 1  # We want 1 specific type
                    n = min(slots_available_for_lock, N)  # Can't draw more than available types
                    
                    if n >= N:
                        # If we're drawing all or more types than available, we're guaranteed to get it
                        prob_get_specific_type = 1.0
                    elif n > 0 and N > 0:
                        # Hypergeometric: P(at least one success in n draws from N types)
                        prob_no_success = math.comb(N - K, n) / math.comb(N, n) if N >= K and N >= n else 1.0
                        prob_get_specific_type = 1 - prob_no_success
                    else:
                        prob_get_specific_type = 0
                    
                    # Effective chance per pull = P(rarity) × P(specific type | rarity)
                    effective_chance = (base / 100.0) * prob_get_specific_type
                    
                    # Calculate number of rerolls possible and overall chance
                    n_rerolls = dice_on_hand // cost
                    if effective_chance > 0 and n_rerolls > 0:
                        # P(at least one success in n_rerolls) = 1 - (1 - effective_chance)^n_rerolls
                        chance = 1 - (1 - effective_chance) ** n_rerolls
                        row[f'{l} Lock{"s" if l != 1 else ""}'] = f"{chance*100:.2f}%"
                    else:
                        row[f'{l} Lock{"s" if l != 1 else ""}'] = "0.00%"
            else:
                row[f'{l} Lock{"s" if l != 1 else ""}'] = "N/A"
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return create_table(df, 'submodule-chances-dice-data')


@callback(
    Output('module-counts-display', 'children'),
    Input('module-type-section2', 'value')
)
def update_module_counts_display(module_type):
    """Display module counts for selected type."""
    counts = get_module_counts()
    module_key = module_type.lower()
    common_count = counts[module_key]['common']
    rare_count = counts[module_key]['rare']
    epic_count = counts[module_key]['epic']
    total_epic = sum(counts[t]['epic'] for t in ['cannon', 'armor', 'generator', 'core'])
    
    return html.Div([
        html.Span(f"{module_type} modules: ", className='fw-bold'),
        html.Span(f"Common: {common_count} | Rare: {rare_count} | Epic: {epic_count} (out of {total_epic} total epic)", className='text-info')
    ])


@callback(
    Output('module-cost-table', 'children'),
    [Input('module-type-section2', 'value'),
     Input('certainty-section2', 'value'),
     Input('copies-needed', 'value')]
)
def update_module_cost_table(module_type, certainty, copies_needed):
    """Update module cost table based on module type, certainty, and copies needed."""
    df = calculate_module_pulls_needed(module_type, certainty, copies_needed)
    return create_table(df, 'module-cost-data')


@callback(
    Output('module-chance-table', 'children'),
    [Input('gems-on-hand', 'value'),
     Input('module-type-section2', 'value'),
     Input('copies-needed', 'value')]
)
def update_module_chance_table(gems_on_hand, module_type, copies_needed):
    """Update module chance table based on gems available, module type, and copies needed."""
    if gems_on_hand is None or gems_on_hand < 0:
        gems_on_hand = 0
    df = calculate_module_chances(gems_on_hand, module_type, copies_needed)
    return create_table(df, 'module-chance-data')


@callback(
    Output('module-accumulation-table', 'children'),
    [Input('gems-on-hand', 'value'),
     Input('module-type-section2', 'value')]
)
def update_module_accumulation_table(gems_on_hand, module_type):
    """Calculate expected module accumulation across all pulls."""
    if gems_on_hand is None or gems_on_hand < 0:
        gems_on_hand = 0
    
    # Get module counts
    counts = get_module_counts()
    
    # Rarity rates
    common_rate = 0.685  # 68.5%
    rare_rate = 0.29     # 29%
    epic_rate = 0.025    # 2.5%
    pity_threshold = 150
    
    # Total modules
    total_common = sum(counts[t]['common'] for t in ['cannon', 'armor', 'generator', 'core'])
    total_rare = sum(counts[t]['rare'] for t in ['cannon', 'armor', 'generator', 'core'])
    total_epic = sum(counts[t]['epic'] for t in ['cannon', 'armor', 'generator', 'core'])
    
    # Cost per pull
    cost_per_pull = 20
    n_pulls = gems_on_hand // cost_per_pull
    
    # Expected number of each rarity from n pulls
    expected_common_total = n_pulls * common_rate
    expected_rare_total = n_pulls * rare_rate
    expected_epic_base = n_pulls * epic_rate
    
    # Add pity epics: every 150 pulls guarantees 1 epic
    expected_epic_from_pity = n_pulls // pity_threshold
    expected_epic_total = expected_epic_base + expected_epic_from_pity
    
    # Calculate per-type breakdown
    # Common: total common modules worth 10 dice each
    total_dice_from_common = expected_common_total * 10
    
    # Rare: divide by 4 types to get rare modules per type
    expected_rare_per_type = expected_rare_total / 4
    
    # Epic: other epic modules (excluding the one you're targeting)
    # Since there are total_epic modules and we're targeting 1, there are (total_epic - 1) "other" epics
    # But we get a random distribution, so on average we get (expected_epic_total / total_epic) of our target
    # and the rest are "other" epics
    expected_target_epic = expected_epic_total / total_epic if total_epic > 0 else 0
    expected_other_epics = expected_epic_total - expected_target_epic
    
    data = [{
        'Pulls': n_pulls,
        'Total Common Modules': f'{expected_common_total:.2f}',
        'Total Dice from Common': f'{total_dice_from_common:.0f}',
        'Rare Modules per Type': f'{expected_rare_per_type:.2f}',
        'Target Epic Modules': f'{expected_target_epic:.2f}',
        'Other Epic Modules': f'{expected_other_epics:.2f}',
    }]
    
    df = pd.DataFrame(data)
    return create_table(df, 'module-accumulation-data')
