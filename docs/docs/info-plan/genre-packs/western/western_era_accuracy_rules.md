# Western Era Accuracy Rules

## Rule

If a detail affects realism, plot, culture, movement, survival, law, conflict, or technology, BookForge must not guess.

## Required Research Categories

- Setting and geography.
- Weapons and ammunition.
- Clothing and material culture.
- Transportation, horses, tack, wagons, and rail.
- Travel distance, terrain, route, daylight, and weather.
- Food, water, medicine, shelter, money, trade, and supplies.
- Law enforcement, courts, jails, posses, sheriffs, marshals, and local power.
- Town, ranch, camp, mine, homestead, saloon, church, and school structure.
- Occupations and daily work.
- Speech, idiom, and blocked modernisms.
- Indigenous, settler, immigrant, and frontier dynamics.
- Gender roles, class pressure, religion, and community norms.
- Flora, fauna, seasons, storms, drought, heat, cold, mud, and dust.

## Research Needed Behavior

When the system wants to use an unsupported detail, it should emit a research-needed request instead of inventing:

```json
{
  "status": "research_needed",
  "category": "transportation",
  "question": "Could this route be crossed by wagon in this season and terrain?",
  "affected_text": "They reached the mining camp before sundown.",
  "risk": "Possible travel-distance or terrain mismatch"
}
```

## Validation Rules

- A historical detail is valid only for its recorded time, place, culture, and use case.
- A generally true Western detail may still be wrong for the active year or region.
- Historical validity does not automatically make a word or object appropriate for the active character voice.
- Cultural sensitivity review is required for portrayals of Native communities, immigrant groups, women, and marginalized groups.
- Intentional anachronism must be explicitly approved and scoped.
