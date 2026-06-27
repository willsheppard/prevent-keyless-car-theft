# data/cars.json field reference

## Car entry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Manufacturer name shown on the card and used in search. |
| `aliases` | string[] | no | Extra search terms -- models, trims, alternative spellings. The entry matches if any alias contains the search query. |
| `techniques` | Technique[] | yes | List of techniques. Empty array is fine alongside `unknown: true`. |
| `info` | string[] | no | Contextual notes about the car's keyless system (e.g. the manufacturer's brand name for the feature). Each is rendered as a yellow highlighted box after the techniques. |
| `unknown` | boolean | no | Set to `true` when no technique is documented. Shows a "Help needed" tag and a contribute link instead of instructions. |

## Technique object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | One of `"temp"`, `"auto"`, `"perm"` -- see below. |
| `unverified` | boolean | no | Editorial flag: the steps have not been personally verified by a contributor. Not currently rendered differently by the UI, but signals that the entry needs checking. Often paired with `(to be confirmed)` text inside the step string itself. |
| `models` | string | no | Which specific models or years this technique applies to (e.g. `"Fiesta 2016, Focus 2017 onwards"`). Displayed in muted text next to the type tag. |
| `text` | string | no | Prose description of the technique, used when there are no discrete steps or as a preamble before `steps`. |
| `steps` | string[] | no | Ordered list of steps. HTML is allowed (e.g. `<em>`). Rendered as `<ol>` for permanent techniques or when there are more than two steps, otherwise `<ul>`. |
| `sub` | Sub[] | no | Named sub-sections, each with their own `label` and `steps`. Used when a technique has distinct phases (e.g. Mazda's "turn on" vs "turn off"). |
| `notes` | string[] | no | Caveats or warnings, each rendered as a yellow highlighted box below the steps. |

### `type` values

| Value | Label | Meaning |
|-------|-------|---------|
| `"temp"` | Temporary | User manually disables keyless entry each time (e.g. press a button sequence when locking). |
| `"auto"` | Automatic | The fob disables itself after a period of inactivity -- nothing to remember. |
| `"perm"` | Permanent | Keyless entry is turned off until deliberately re-enabled via a settings menu or the same procedure. |

## Sub-section object (used in `sub`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | yes | Heading shown before the steps (e.g. `"To turn the power saving function ON"`). |
| `steps` | string[] | yes | Steps for this phase. |
