# PROJECT BRIEF: Knowledge-Based System for Hydrogeological Risk Assessment - Ischia Island
EXECUTIVE SUMMARY
Project Title: Ontology-Based Landslide Risk Assessment System for Ischia Island
Domain: Geospatial Knowledge Engineering
Focus Area: Southern Italy (Meridione) - Ischia Island, Campania
Case Study: Casamicciola landslide event (November 26, 2022 - 12 fatalities)

1. PROJECT OBJECTIVES
Primary Goal
Develop a Knowledge-Based System (KBS) that integrates:

Knowledge Representation: OWL ontology modeling hydrogeological risk factors
Automated Reasoning: Inference of risk levels based on spatial and geological features
Machine Learning Integration: Comparative evaluation of symbolic vs. ML vs. hybrid approaches
Geospatial Data Integration: Fusion of heterogeneous data sources (satellite imagery, geological maps, historical events)

Key Requirement (from course guidelines)

Demonstrate "representation, reasoning, diagnosis, learning, classification" capabilities through original integration of techniques from the ICon curriculum - NOT a pure ML image recognition project.


2. WHY THIS PROJECT FITS THE COURSE REQUIREMENTS
✅ Acceptable because:

Knowledge Base is central: Ontology models domain expertise (geological factors, risk assessment rules)
Reasoning is complex: Not simple pattern matching - multi-factor spatial reasoning with uncertainty
Hybrid approach: Compares symbolic reasoning vs ML vs knowledge-enhanced ML
Original contribution: Integration of semantic web data with geospatial ML
Social relevance: Southern Italy territorial planning, insurance, civil protection

❌ Avoids rejection criteria:

NOT pure image segmentation (satellite imagery is ONE input among many)
NOT simple database queries (complex spatial reasoning required)
NOT single-run evaluation (requires cross-validation with statistical analysis)
NOT off-the-shelf tutorial replication


3. GEOGRAPHIC AND TEMPORAL SCOPE
Study Area

Location: Ischia Island, Gulf of Naples, Campania, Italy
Size: ~46 km² (manageable for 25-hour project)
Focus Zone: Monte Epomeo → Casamicciola corridor (~5-10 km²)
Coordinates: Approx 40.73°N, 13.90°E

Why Ischia?

Recent catastrophic event: November 26, 2022 landslide (well-documented)
Rich data availability: IFFI database, LiDAR DTM, geological maps
Social relevance: Emblematic case of natural risk + anthropic pressure in Southern Italy
Validation dataset: Historical events (1910, 1987, 2009, 2022) for testing

Key Event Details (for context)

Date: November 26, 2022, ~5:00 AM
Trigger: 126mm rainfall in 6 hours (20-year record)
Location: Via Celario, Casamicciola Terme
Impact: 12 deaths, 462 evacuees, 40 buildings destroyed
Flow velocity: 10-15 m/s at impact (from INGV seismic data)


4. DATA SOURCES (with download instructions)
CRITICAL: Data Acquisition Status
✅ IMMEDIATELY AVAILABLE (no registration)

Corine Land Cover 2018

URL: https://land.copernicus.eu/pan-european/corine-land-cover
Format: GeoTIFF raster
Resolution: 100m
Classes: Urban, agricultural, forest, bare soil


Copernicus DEM

URL: https://portal.opentopography.org/ OR https://land.copernicus.eu/imagery-in-situ/eu-dem
Format: GeoTIFF
Resolution: 30m (free tier)
Use for: Slope calculation, aspect, curvature


OpenStreetMap (buildings, roads, waterways)

Method A: QGIS Plugin "QuickOSM"



     Key: building, Value: *, Location: "Ischia, Italy"
     Key: highway, Value: *, Location: "Ischia, Italy"
     Key: waterway, Value: *, Location: "Ischia, Italy"

Method B: Overpass Turbo (https://overpass-turbo.eu)

overpass     [out:json][timeout:25];
     area["name"="Ischia"]["admin_level"="8"]->.searchArea;
     (way["building"](area.searchArea););
     out geom;
```
   - Export as: GeoJSON or Shapefile

#### ⏳ REQUIRES REQUEST (2-5 day turnaround)

4. **IFFI - Italian Landslide Inventory**
   - **Primary source**: Email request to idrogeo@isprambiente.it or datipst@mase.gov.it
   - **Fallback**: Regione Campania portal http://www.difesa.suolo.regione.campania.it
   - **Content**: Historical landslide polygons/points with attributes (type, date, activity status)
   - **Email template**:
```
     Subject: IFFI Data Request - Ischia Island (Academic Research)
     
     Dear ISPRA Team,
     
     I am a graduate student at [University] conducting research on 
     hydrogeological risk assessment for my Knowledge Engineering course.
     
     Could you please provide IFFI inventory data for:
     - Casamicciola Terme
     - Ischia
     - Forio
     - Lacco Ameno
     - Barano d'Ischia
     - Serrara Fontana
     
     Preferred format: Shapefile or GeoPackage
     Purpose: Academic project (non-commercial)
     
     Thank you,
     [Name, University, Email]
```

5. **LiDAR DTM (1m resolution)** - Optional but valuable
   - URL: https://gn.mase.gov.it/portale/pst-data-distribution
   - Status: New web platform (Sept 2024) - try direct download first
   - Fallback: Email to datipst@mase.gov.it with Ischia tile IDs

6. **Geological Map**
   - Source: Geoportale Campania https://sit2.regione.campania.it
   - Note: Ischia has specialized volcanic geology maps
   - Alternative: ISPRA WMS service (view-only if download fails)

#### 📚 SCIENTIFIC LITERATURE (Essential reading)

**Primary reference** (MUST READ):
- **Title**: "Tracking the November 26, 2022, Casamicciola debris flow through seismic signals (Ischia, southern Italy)"
- **Authors**: Danesi, Carlino et al. (INGV + Univ. Camerino)
- **Journal**: Landslides (2025)
- **Find on**: Google Scholar
- **Contains**: Precise event timeline, flow dynamics, rainfall data

**Additional context**:
- CNR-IRPI Report: https://polaris.irpi.cnr.it (2022 event analysis)
- Papers you found: Check titles on "ontology-based landslide knowledge", "LHAKG knowledge graph"

---

## 5. SYSTEM ARCHITECTURE

### Component Breakdown
```
┌─────────────────────────────────────────────────┐
│          DATA ACQUISITION LAYER                 │
│  - Geospatial rasters (DEM, land cover)        │
│  - Vector data (IFFI, OSM, geology)            │
│  - Precipitation records                        │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│       FEATURE EXTRACTION ENGINE                 │
│  - Slope/aspect from DEM                        │
│  - Distance to waterways                        │
│  - Land cover classification                    │
│  - Lithology extraction                         │
│  - Precipitation intensity                      │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         ONTOLOGY POPULATION                     │
│  - GeographicCell individuals (100m grid)       │
│  - Property assertions (hasSlopeValue, etc.)    │
│  - Spatial relationships                        │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐  ┌────────▼──────────┐
│   REASONER     │  │   ML CLASSIFIER   │
│  (Symbolic)    │  │  (Random Forest/  │
│  - SWRL rules  │  │   XGBoost)        │
│  - OWL2        │  │                   │
└───────┬────────┘  └────────┬──────────┘
        │                    │
        └─────────┬──────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         HYBRID INTEGRATION                      │
│  - Reasoner output as ML features              │
│  - Ensemble voting                              │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│    VALIDATION & EVALUATION                      │
│  - Cross-validation against IFFI events         │
│  - Precision/Recall/F1 metrics                  │
│  - Spatial accuracy assessment                  │
└─────────────────────────────────────────────────┘

6. ONTOLOGY DESIGN SPECIFICATION
Core Classes (OWL)
turtle# Top-level classes
:GeographicArea rdfs:subClassOf owl:Thing .
:RiskFactor rdfs:subClassOf owl:Thing .
:RiskLevel rdfs:subClassOf owl:Thing .
:HistoricalEvent rdfs:subClassOf owl:Thing .

# Geographic area subclasses
:Slope rdfs:subClassOf :GeographicArea .
  :VeryLowSlope rdfs:subClassOf :Slope .   # < 5°
  :LowSlope rdfs:subClassOf :Slope .       # 5-15°
  :MediumSlope rdfs:subClassOf :Slope .    # 15-25°
  :HighSlope rdfs:subClassOf :Slope .      # 25-35°
  :VeryHighSlope rdfs:subClassOf :Slope .  # > 35°

:LithologyType rdfs:subClassOf :GeographicArea .
  :VolcanicRock rdfs:subClassOf :LithologyType .
  :PyroclasticDeposit rdfs:subClassOf :LithologyType .
  :WeatheredTuff rdfs:subClassOf :LithologyType .

:LandCover rdfs:subClassOf :GeographicArea .
  :Urban rdfs:subClassOf :LandCover .
  :Forest rdfs:subClassOf :LandCover .
  :Agricultural rdfs:subClassOf :LandCover .
  :BareSoil rdfs:subClassOf :LandCover .
  :Deforested rdfs:subClassOf :LandCover .

# Risk factor taxonomy
:TopographicFactor rdfs:subClassOf :RiskFactor .
:GeologicalFactor rdfs:subClassOf :RiskFactor .
:HydrologicalFactor rdfs:subClassOf :RiskFactor .
:AnthropicFactor rdfs:subClassOf :RiskFactor .

# Risk levels (ordered)
:VeryLowRisk rdfs:subClassOf :RiskLevel .
:LowRisk rdfs:subClassOf :RiskLevel .
:MediumRisk rdfs:subClassOf :RiskLevel .
:HighRisk rdfs:subClassOf :RiskLevel .
:VeryHighRisk rdfs:subClassOf :RiskLevel .
Object Properties
turtle:hasLithology rdf:type owl:ObjectProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range :LithologyType .

:hasLandCover rdf:type owl:ObjectProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range :LandCover .

:hasSlopeClass rdf:type owl:ObjectProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range :Slope .

:hasRiskLevel rdf:type owl:ObjectProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range :RiskLevel .

:contributesToRisk rdf:type owl:ObjectProperty ;
  rdfs:domain :RiskFactor ;
  rdfs:range :RiskLevel .
Data Properties
turtle:hasSlopeValue rdf:type owl:DatatypeProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range xsd:float .  # degrees

:distanceToWaterBody rdf:type owl:DatatypeProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range xsd:float .  # meters

:precipitationIntensity rdf:type owl:DatatypeProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range xsd:float .  # mm/hour

:elevationMeters rdf:type owl:DatatypeProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range xsd:float .

:buildingDensity rdf:type owl:DatatypeProperty ;
  rdfs:domain :GeographicArea ;
  rdfs:range xsd:float .  # buildings per km²
Example SWRL Rules
swrl# Rule 1: High slope + pyroclastic soil + high precipitation → Very High Risk
GeographicArea(?x) ∧ hasSlopeValue(?x, ?s) ∧ swrlb:greaterThan(?s, 35) ∧
hasLithology(?x, PyroclasticDeposit) ∧ 
precipitationIntensity(?x, ?p) ∧ swrlb:greaterThan(?p, 50)
→ hasRiskLevel(?x, VeryHighRisk)

# Rule 2: Deforestation increases risk factor
GeographicArea(?x) ∧ hasLandCover(?x, Deforested) ∧
hasSlopeValue(?x, ?s) ∧ swrlb:greaterThan(?s, 25)
→ contributesToRisk(AnthropicFactor, HighRisk)

# Rule 3: Urban area on unstable ground → Increase risk
GeographicArea(?x) ∧ hasLandCover(?x, Urban) ∧
hasSlopeValue(?x, ?s) ∧ swrlb:greaterThan(?s, 20) ∧
distanceToWaterBody(?x, ?d) ∧ swrlb:lessThan(?d, 100)
→ hasRiskLevel(?x, HighRisk)

7. IMPLEMENTATION ROADMAP
Phase 1: Data Preparation (5 hours)
Tasks:

Download all available datasets (see Section 4)
Reproject to common CRS (EPSG:32633 - WGS84/UTM Zone 33N)
Create 100m x 100m grid over Ischia
Extract features for each grid cell:

python   # Pseudocode
   for cell in grid:
       features[cell.id] = {
           'slope': extract_slope(dem, cell),
           'aspect': extract_aspect(dem, cell),
           'elevation': extract_mean_elevation(dem, cell),
           'lithology': extract_dominant_class(geology, cell),
           'landcover': extract_dominant_class(corine, cell),
           'dist_water': distance_to_nearest(rivers, cell.centroid),
           'building_count': count_intersecting(buildings, cell)
       }
Tools: Python (geopandas, rasterio, numpy), QGIS for validation
Deliverable: ischia_grid_features.csv or .gpkg with ~4600 grid cells

Phase 2: Ontology Development (4 hours)
Tasks:

Create OWL ontology in Protégé (see Section 6 for structure)
Define all classes, properties, and restrictions
Write SWRL rules for risk assessment (minimum 5 rules)
Test reasoning with HermiT or Pellet reasoner
Export as .owl file

Tools: Protégé 5.x, Owlready2 (Python) for programmatic access
Deliverable: ischia_landslide_risk.owl

Phase 3: Knowledge Base Population (3 hours)
Tasks:

Convert grid features to ontology individuals

python   from owlready2 import *
   
   onto = get_ontology("ischia_landslide_risk.owl").load()
   
   for idx, row in grid_features.iterrows():
       cell = onto.GeographicArea(f"cell_{idx}")
       cell.hasSlopeValue = [row['slope']]
       cell.distanceToWaterBody = [row['dist_water']]
       
       # Assign lithology class
       if row['lithology'] == 'pyroclastic':
           cell.hasLithology = [onto.PyroclasticDeposit]
       
       # ... continue for all properties
   
   onto.save("ischia_populated.owl")

Run reasoner to infer risk levels
Extract inferred classifications

Tools: Owlready2, RDFLib
Deliverable: Populated ontology + extracted risk classifications

Phase 4: Machine Learning Baseline (4 hours)
Tasks:

Prepare ML dataset from grid features
Train multiple classifiers:

Random Forest
XGBoost
SVM with RBF kernel


Use IFFI historical events as ground truth labels

Positive class: Cells with historical landslides
Negative class: Random sample of stable cells


5-fold cross-validation
Record: Precision, Recall, F1, AUC for each fold

Critical: Report MEAN ± STD for all metrics (not single run!)
Tools: scikit-learn, imbalanced-learn (for class imbalance)
Deliverable: ml_evaluation_results.csv with metrics per fold

Phase 5: Hybrid Approach (3 hours)
Tasks:

Method A: Use reasoner outputs as ML features

python   # Add reasoner-inferred risk level as categorical feature
   features['inferred_risk_symbolic'] = reasoner_output
   
   # Train ML with augmented features

Method B: Ensemble voting

python   final_prediction = weighted_vote(
       symbolic_reasoner_output,
       ml_classifier_output,
       weights=[0.4, 0.6]  # Tune via validation
   )
```

3. Compare hybrid vs pure approaches

**Deliverable**: Comparative evaluation table

---

### Phase 6: Validation & Evaluation (4 hours)

**Tasks**:
1. Validate against 2022 Casamicciola event
   - Did high-risk zones overlap with actual landslide path?
   - Calculate spatial accuracy (IoU, buffer analysis)

2. Statistical comparison:
```
   Approach          | Precision | Recall | F1    | Inference Time
   ------------------|-----------|--------|-------|---------------
   Symbolic Only     | X.XX±0.XX | ...    | ...   | ...
   ML Only (RF)      | X.XX±0.XX | ...    | ...   | ...
   ML Only (XGB)     | X.XX±0.XX | ...    | ...   | ...
   Hybrid (Method A) | X.XX±0.XX | ...    | ...   | ...
   Hybrid (Method B) | X.XX±0.XX | ...    | ...   | ...

Sensitivity analysis: How do rule thresholds affect results?
Create risk map visualization in QGIS

Deliverable:

Evaluation report
Risk map (PNG/PDF)
Statistical analysis notebook


Phase 7: Documentation (2 hours)
Structure (following course requirements):

Introduction (1 page)

Problem statement
Motivation (Southern Italy context)
Objectives


Background (1-2 pages)

Brief literature review (5-10 key papers)
NOT long explanations of well-known algorithms
Focus on ontology-based approaches to geospatial risk


Knowledge Base Design (3-4 pages) ⭐ MOST IMPORTANT

Ontology structure (class diagram)
SWRL rules with justification
Why these classes/properties/rules?
Complexity analysis (number of classes, axioms, reasoning depth)


System Implementation (2-3 pages)

Pipeline architecture
Tools used (with versions)
Data preprocessing steps
Feature engineering rationale


Evaluation (3-4 pages) ⭐ CRITICAL

Experimental protocol (cross-validation setup)
Tables with Mean ± Std for all metrics
Comparison of approaches (symbolic/ML/hybrid)
Validation against real events
Error analysis: Where does each approach fail?


Conclusions (1 page)

Key findings
Limitations (e.g., data gaps, simplifications)
Future work



What to AVOID:

❌ Long explanations of Random Forest, SWRL syntax, etc.
❌ Code screenshots (put code in appendix or GitHub)
❌ Single-run confusion matrices
❌ Padding with generic content

What to INCLUDE:

✅ Design choices: "We chose slope threshold of 35° because..."
✅ Statistical rigor: Multiple runs, confidence intervals
✅ KB complexity metrics: Number of axioms, reasoning time
✅ Real-world validation: 2022 event overlay


8. SUCCESS CRITERIA CHECKLIST
Must Have (to pass):

 OWL ontology with ≥20 classes, ≥10 object properties, ≥5 SWRL rules
 Automated reasoning produces risk classifications
 ML baseline trained and evaluated (≥3 algorithms)
 Comparison table: Symbolic vs ML vs Hybrid
 Validation against ≥1 real historical event
 Cross-validation results (≥5 folds) with Mean±Std reported
 Documentation 10-15 pages (focused, no padding)
