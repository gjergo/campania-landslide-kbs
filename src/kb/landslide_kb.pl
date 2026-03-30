% ================================================================
% Landslide Susceptibility KB — Campania Region
%
% Facts derived from:
%   - IFFI inventory median slopes per lithological class
%     (Campania, this study)
%   - Catani et al. (2013) geotechnical grouping
%   - Corominas et al. (2014) conditioning factors
% ================================================================

% --- Facts: critical slope thresholds per lithology ---
% Derived from median slope of IFFI landslide pixels per class
critical_slope(hard_rock,           18.0).
critical_slope(competent_clastic,   11.0).
critical_slope(flysch_clastic,      10.0).
critical_slope(unconsolidated_weak,  9.0).
critical_slope(volcanic_pyroclastic, 9.0).
critical_slope(unknown,             10.0).

% --- Facts: inherent material weakness (geotechnical) ---
% Catani et al. (2013): cohesive/weak material classes
weak_material(unconsolidated_weak).
weak_material(volcanic_pyroclastic).
weak_material(flysch_clastic).

% --- Facts: drainage proximity threshold (metres) ---
% Corominas et al. (2014): stream undercutting mechanism
drainage_risk_threshold(200.0).

% -------------------------------------------------------
% Rules
% -------------------------------------------------------

% Rule 1: slope exceeds lithology-specific failure threshold
slope_susceptible(Litho, Slope) :-
    critical_slope(Litho, Threshold),
    Slope > Threshold.

% Rule 2: weak material on any meaningful slope
material_susceptible(Litho, Slope) :-
    weak_material(Litho),
    Slope > 5.0.

% Rule 3: proximity to drainage on weak material
drainage_susceptible(Litho, DistDrainage) :-
    weak_material(Litho),
    drainage_risk_threshold(T),
    DistDrainage < T.

% Rule 4: combined susceptibility classification
%   high   = slope threshold exceeded AND weak material
%   high   = slope threshold exceeded AND near drainage
%   medium = slope threshold exceeded (any material)
%   medium = weak material on gentle slope
%   low    = everything else

kb_susceptibility(Litho, Slope, _, high) :-
    slope_susceptible(Litho, Slope),
    weak_material(Litho).

kb_susceptibility(Litho, Slope, Dist, high) :-
    slope_susceptible(Litho, Slope),
    drainage_susceptible(Litho, Dist).

kb_susceptibility(Litho, Slope, _, medium) :-
    slope_susceptible(Litho, Slope).

kb_susceptibility(Litho, Slope, _, medium) :-
    material_susceptible(Litho, Slope),
    \+ slope_susceptible(Litho, Slope).

kb_susceptibility(_, _, _, low).

% Rule 5: numeric encoding for ML feature column
susceptibility_score(Litho, Slope, Dist, 2) :-
    kb_susceptibility(Litho, Slope, Dist, high).
susceptibility_score(Litho, Slope, Dist, 1) :-
    kb_susceptibility(Litho, Slope, Dist, medium).
susceptibility_score(_, _, _, 0).
