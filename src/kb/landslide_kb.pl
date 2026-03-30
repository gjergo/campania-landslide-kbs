% ================================================================
% Landslide Susceptibility Knowledge Base — Campania Region
% File: src/kb/landslide_kb.pl
%
% References:
%   - Catani et al. (2013): geotechnical class grouping
%   - Corominas et al. (2014): drainage proximity mechanism
%   - Löbmann et al. (2020): vegetation root cohesion mechanism
%   - Empirical thresholds: median slope of IFFI pixels per class
%     (Campania, this study)
% ================================================================

% ----------------------------------------------------------------
% FACTS: critical slope thresholds per lithological class
% Derived from median slope of IFFI landslide pixels per class
% (Campania region, this study). Thresholds set slightly below
% the empirical median to capture necessary (not sufficient)
% conditions for failure.
% ----------------------------------------------------------------
critical_slope(hard_rock,           18.0).
critical_slope(competent_clastic,   11.0).
critical_slope(flysch_clastic,      10.0).
critical_slope(unconsolidated_weak,  9.0).
critical_slope(volcanic_pyroclastic, 9.0).
critical_slope(unknown,             10.0).

% ----------------------------------------------------------------
% FACTS: geotechnically weak material classes
% Source: Catani et al. (2013) — cohesive/weak geotechnical groups
% These materials have low cohesion and high erodibility,
% making them susceptible to failure even at moderate slopes.
% ----------------------------------------------------------------
weak_material(unconsolidated_weak).
weak_material(volcanic_pyroclastic).
weak_material(flysch_clastic).

% ----------------------------------------------------------------
% FACTS: drainage proximity threshold (metres)
% Source: Corominas et al. (2014) — stream undercutting mechanism.
% Slopes within this distance from drainage are subject to
% lateral erosion and toe undercutting.
% ----------------------------------------------------------------
drainage_risk_threshold(200.0).

% ----------------------------------------------------------------
% FACTS: CORINE land cover stability classes
% Source: Löbmann et al. (2020) — vegetation root cohesion.
% Forest cover improves slope stability through mechanical root
% anchoring and suction; bare/sparse cover removes this effect.
%
% CORINE 2018 codes:
%   311 = broad-leaved forest
%   312 = coniferous forest
%   313 = mixed forest
%   321 = natural grassland
%   331 = bare rock / scree
%   332 = bare soil
%   333 = sparsely vegetated areas
%   334 = burnt areas
% ----------------------------------------------------------------
stabilizing_cover(311).
stabilizing_cover(312).
stabilizing_cover(313).

destabilizing_cover(331).
destabilizing_cover(332).
destabilizing_cover(333).
destabilizing_cover(334).

% ----------------------------------------------------------------
% INFERENCE RULES (4 levels of chained reasoning)
% ----------------------------------------------------------------

% Rule Level 1 — slope threshold exceeded for this lithology
slope_susceptible(Litho, Slope) :-
    critical_slope(Litho, Threshold),
    Slope > Threshold.

% Rule Level 1 — weak material on any meaningful slope (>5 deg)
material_susceptible(Litho, Slope) :-
    weak_material(Litho),
    Slope > 5.0.

% Rule Level 1 — within drainage risk distance on weak material
% (Corominas et al., 2014: toe undercutting mechanism)
drainage_susceptible(Litho, DistDrainage) :-
    weak_material(Litho),
    drainage_risk_threshold(T),
    DistDrainage < T.

% Rule Level 1 — vegetation destabilizes (bare/sparse cover)
cover_destabilized(Corine) :-
    destabilizing_cover(Corine).

% Rule Level 1 — vegetation stabilizes (forest cover)
% Negation-as-failure: no stabilization if not forest
cover_stabilized(Corine) :-
    stabilizing_cover(Corine).

% ----------------------------------------------------------------
% Rule Level 2 — combined susceptibility classification
% HIGH: slope threshold exceeded AND (weak material OR near
%       drainage OR destabilizing cover)
% MEDIUM: slope threshold exceeded (any material, any cover) OR
%         weak material on gentle slope
% LOW: fallthrough — no conditions activated
%
% Note: negation-as-failure (\+) used in medium rules to avoid
% double-firing with high classification.
% ----------------------------------------------------------------

% HIGH susceptibility cases
kb_susceptibility(Litho, Slope, _, _, high) :-
    slope_susceptible(Litho, Slope),
    weak_material(Litho).

kb_susceptibility(Litho, Slope, Dist, _, high) :-
    slope_susceptible(Litho, Slope),
    drainage_susceptible(Litho, Dist).

kb_susceptibility(Litho, Slope, _, Corine, high) :-
    slope_susceptible(Litho, Slope),
    cover_destabilized(Corine),
    \+ weak_material(Litho).   % avoid double-counting with first rule

% MEDIUM susceptibility cases
kb_susceptibility(Litho, Slope, _, Corine, medium) :-
    slope_susceptible(Litho, Slope),
    \+ weak_material(Litho),
    \+ cover_destabilized(Corine).

kb_susceptibility(Litho, Slope, _, _, medium) :-
    material_susceptible(Litho, Slope),
    \+ slope_susceptible(Litho, Slope).

% LOW susceptibility — catch-all
kb_susceptibility(_, _, _, _, low).

% ----------------------------------------------------------------
% Rule Level 3 — numeric encoding for ML feature column
% 2 = high, 1 = medium, 0 = low
% Uses first-solution semantics (cuts handled by query wrapper)
% ----------------------------------------------------------------
susceptibility_score(Litho, Slope, Dist, Corine, 2) :-
    kb_susceptibility(Litho, Slope, Dist, Corine, high).
susceptibility_score(Litho, Slope, Dist, Corine, 1) :-
    kb_susceptibility(Litho, Slope, Dist, Corine, medium).
susceptibility_score(_, _, _, _, 0).
