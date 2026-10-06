# ZTE Kids Watch — Home Assistant integration

Unofficial Home Assistant integration for **ZTE / nubia "Care" kids smartwatches**
(*ZTE Kids* / *ChildrenWatchAbroad*, backend `care-api.nubia.com`). Log in with your
own account and get each watch as an HA device: location on the map, battery, steps,
and an on-demand location refresh.

> Not affiliated with ZTE/nubia. Uses an undocumented app API that may change or break
> at any time. Intended only for your **own** account and your own children's watches.

## Installation

### HACS (custom repository)

1. HACS → **⋮** → **Custom repositories**.
2. Repository: `https://github.com/tormjens/zte_kids`, category **Integration**.
3. Install **ZTE Kids Watch**, then **restart Home Assistant**.
4. **Settings → Devices & Services → + Add Integration → "ZTE Kids Watch"** and sign in.

### Manual

Copy `custom_components/zte_kids/` into your HA `config/custom_components/`, restart,
then add the integration from the UI.

## Entities

One device per watch: `device_tracker` (GPS), `sensor` battery / steps / last-fix, and
a **Refresh location** `button`.

See [`custom_components/zte_kids/README.md`](custom_components/zte_kids/README.md) for
full details, how it works, and troubleshooting.

## License

MIT — see [LICENSE](LICENSE).
