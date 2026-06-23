# data/cars.json field reference

## Car entry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Manufacturer name shown on the card and used in search. |
| `aliases` | string[] | no | Extra search terms -- models, trims, alternative spellings. The entry matches if any alias contains the search query. |
| `methods` | Method[] | yes | List of methods. Empty array is fine alongside `unknown: true`. |
| `unknown` | boolean | no | Set to `true` when no method is documented. Shows a "Help needed" tag and a contribute link instead of instructions. |

## Method object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | One of `"temp"`, `"auto"`, `"perm"`, `"info"` -- see below. |
| `unverified` | boolean | no | Editorial flag: the steps have not been personally verified by a contributor. Signals that the entry needs checking. This is the sole signal for unconfirmed entries -- do not add `(to be confirmed)` or similar text inside step strings. |
| `models` | string | no | Which specific models or years this method applies to (e.g. `"Fiesta 2016, Focus 2017 onwards"`). Displayed in muted text next to the type tag. |
| `text` | string | no | Prose description of the method, used when there are no discrete steps or as a preamble before `steps`. |
| `steps` | string[] | no | Ordered list of steps. HTML is allowed (e.g. `<em>`). Rendered as `<ol>` for permanent methods or when there are more than two steps, otherwise `<ul>`. |
| `sub` | Sub[] | no | Named sub-sections, each with their own `label` and `steps`. Used when a method has distinct phases (e.g. Mazda's "turn on" vs "turn off"). |
| `notes` | string[] | no | Caveats or warnings, each rendered as a yellow highlighted box below the steps. |

### `type` values

| Value | Label | Meaning |
|-------|-------|---------|
| `"temp"` | Temporary | User manually disables keyless entry each time (e.g. press a button sequence when locking). |
| `"auto"` | Automatic | The fob disables itself after a period of inactivity -- nothing to remember. |
| `"perm"` | Permanent | Keyless entry is turned off until deliberately re-enabled via a settings menu or the same procedure. |
| `"info"` | -- | Not a method; contextual information only (e.g. the brand name for the feature). Rendered as a note box with no type tag. |

## Sub-section object (used in `sub`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | yes | Heading shown before the steps (e.g. `"To turn the power saving function ON"`). |
| `steps` | string[] | yes | Steps for this phase. |
