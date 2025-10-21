# Research Database

This directory contains the evidence-based research foundation for the Hybrid Athlete Platform. All training protocols are backed by peer-reviewed scientific studies.

## Structure

```
research_database/
├── methodologies/          # Training methodologies
│   ├── polarized_training/
│   ├── norwegian_method/
│   ├── maf_method/
│   ├── block_periodization/
│   ├── concurrent_training/
│   └── hiit_protocols/
├── goals/                  # Goal-specific research
│   ├── endurance/
│   │   ├── 5k/
│   │   ├── 10k/
│   │   ├── half_marathon/
│   │   ├── marathon/
│   │   └── ultra/
│   ├── strength/
│   │   ├── powerlifting/
│   │   ├── olympic_lifting/
│   │   └── hypertrophy/
│   └── hybrid/
│       ├── concurrent_protocols/
│       └── interference_mitigation/
├── populations/            # Population-specific research
│   ├── age_groups/
│   ├── gender_specific/
│   ├── detraining_periods/
│   └── injury_recovery/
├── constraints/            # Constraint-based research
│   ├── time_efficient/
│   ├── equipment_minimal/
│   └── schedule_flexible/
└── physiology/            # Physiological systems
    ├── vo2max_development/
    ├── lactate_threshold/
    ├── running_economy/
    ├── muscle_hypertrophy/
    └── body_composition/
```

## Research Quality Standards

Each research module includes:

- **Primary sources**: Peer-reviewed studies with citations
- **Meta-analyses**: Where available for stronger evidence
- **Effect sizes**: Quantified improvements expected
- **Population specificity**: Which populations studied
- **Time horizons**: How long adaptations take
- **Limitations**: What the research doesn't tell us
- **Practical application**: How to implement findings
- **Conflicts**: Where research contradicts or shows individual variation

## Citation Format

All research is cited using the following format:

```yaml
citation:
  authors: ["Last Name, First Initial.", "Last Name, First Initial."]
  year: 2023
  title: "Study Title"
  journal: "Journal Name"
  volume: 123
  issue: 4
  pages: "123-456"
  doi: "10.1234/journal.2023.123456"
  url: "https://doi.org/10.1234/journal.2023.123456"
```

## Research Entry Template

See `templates/research_article_template.yaml` for the standard format.
