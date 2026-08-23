# Private data inputs

No experimental or cleaned dataset is distributed in this pre-acceptance repository package.

Place the following files in `data/private/` when the data-release decision is made:

| Exact filename | Required content | SHA-256 of frozen input |
|---|---|---|
| `Arab_Light_Kinetics_Source_FWO_KAS_Starink.xlsx` | Instrument-source N2 and Air sheets used by the kinetics reconstruction | `cd23a90667cb9a78fe29e519930d4eebd87e63427f8e08b7c47ca484c199c1fb` |
| `Arab_Light_TGA_Canonical_Data.xlsx` | `Kinetic_Talpha`, `Cleaning_Audit`, and six `Raw_*` sheets | `bd79aa8575c4480aae806f45cb9c11f04f0312f1d29deb0543b3bdf2703fd60d` |
| `arab_light_TGA_cleaned_ML_ready_v2.xlsx` | `ML_Master` plus validation, feature, kinetic, cleaning, and raw-curve sheets | `943f96608fbee8232e8b541b198260d04ae42dc64bafaa1773af62941974c29f` |

The two canonical workbooks contain overlapping measurements but serve different frozen pipelines. Keep their filenames unchanged unless the code and documentation are updated together.

## Minimum ML schema

`ML_Master` must include:

```text
curve_id, atmosphere, beta, temp_K, temp_C, mass_pct, alpha
```

It must contain N2 and Air curves at 5, 10, and 20 °C/min. The final model inputs are `temp_K` and `beta`; the target is `mass_pct`.

## Verify a later upload

```bash
sha256sum data/private/*.xlsx
python run_all.py
```

Do not commit partially anonymized, downsampled, or reformatted substitutes under the frozen filenames.
