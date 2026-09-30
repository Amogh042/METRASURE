# MetraSure — Demo Script (SIH26035)

All readings below have been checked against the OIML R-76-1 (2006) Table 6 rules that `seed.py` creates. Units are **kg** throughout.

**Before you start:** re-seed the DB (`cd backend && PYTHONPATH=. python seed.py`), start the backend and frontend, and sign in as `admin` / `admin123`.

In every module: enter the rows (use **+ Add Row** for more rows), then click **Calculate Module** (it saves automatically). The **MPE Limit** column shows which Table 6 band was applied to each row, e.g. `1e · 500e<m<=2000e`.

---

## DEMO-001: Mettler Toledo ICS689 (Class III, e = 0.01 kg, Max 30 kg). All 5 modules PASS

Table 6 bands for this instrument: **±0.005 kg** up to 5 kg (≤ 500e), **±0.01 kg** from 5 to 20 kg, **±0.015 kg** from 20 to 30 kg.

### Accuracy
| # | Test Load | Indicated Value | Error | MPE (band) | Result |
|---|---|---|---|---|---|
| 1 | 0.20 | 0.200 | 0.000 | ±0.005 (0.5e) | PASS |
| 2 | 5.00 | 5.000 | 0.000 | ±0.005 (0.5e) | PASS |
| 3 | 15.00 | 15.005 | +0.005 | ±0.010 (1e) | PASS |
| 4 | 25.00 | 25.010 | +0.010 | ±0.015 (1.5e) | PASS |
| 5 | 30.00 | 29.990 | −0.010 | ±0.015 (1.5e) | PASS |

### Repeatability (same load for every row)
| # | Test Load | Indicated Value |
|---|---|---|
| 1 | 15.00 | 15.000 |
| 2 | 15.00 | 15.005 |
| 3 | 15.00 | 15.000 |

Max − min = 0.005, within ±0.010 (1e band for 1500e): **PASS**

### Eccentricity
| # | Position | Test Load | Indicated Value |
|---|---|---|---|
| 1 | Center | 10.00 | 10.000 |
| 2 | Front-Left | 10.00 | 10.005 |
| 3 | Front-Right | 10.00 | 9.995 |
| 4 | Back-Left | 10.00 | 10.000 |
| 5 | Back-Right | 10.00 | 10.005 |

All errors are within ±0.010 (1e band): **PASS**

### Zero
| # | Indicated Value |
|---|---|
| 1 | 0.000 |

Within ±0.0025 (0.25e): **PASS**

### Tare
| # | Net Load | Indicated Value |
|---|---|---|
| 1 | 10.00 | 10.005 |

Within ±0.010 (1e band): **PASS**

**Overall: CERTIFIED: PASS**

---

## DEMO-002: CAS DB-II (Class III, e = 0.05 kg, Max 150 kg). Accuracy FAILS at 20 kg

Table 6 bands for this instrument: **±0.025 kg** up to 25 kg (≤ 500e), **±0.05 kg** from 25 to 100 kg, **±0.075 kg** from 100 to 150 kg.

### Accuracy
| # | Test Load | Indicated Value | Error | MPE (band) | Result |
|---|---|---|---|---|---|
| 1 | 1.00 | 1.00 | 0.00 | ±0.025 (0.5e) | PASS |
| 2 | **20.00** | **20.05** | **+0.05** | **±0.025 (0.5e)** | **FAIL** |
| 3 | 50.00 | 50.05 | +0.05 | ±0.050 (1e) | PASS |
| 4 | 120.00 | 120.05 | +0.05 | ±0.075 (1.5e) | PASS |
| 5 | 150.00 | 150.00 | 0.00 | ±0.075 (1.5e) | PASS |

> **Talking point:** rows 2, 3 and 4 all have the **same +0.05 kg error**. It fails at 20 kg (400e falls in the 0.5e band) and passes at 50 kg and 120 kg. A flat "1e everywhere" limit would have passed this scale, so the stepped Table 6 limits catch a fault the old approach missed.

The other modules pass, so the failure is clearly isolated to Accuracy. They're optional for the video, because a single failing module already makes the overall verdict FAIL.

| Module | Rows (Load → Indicated) |
|---|---|
| Repeatability | 75.00 → 75.00 · 75.00 → 75.02 · 75.00 → 75.00 |
| Eccentricity (load 50.00) | Center 50.00 · Front-Left 50.02 · Front-Right 49.98 · Back-Left 50.00 · Back-Right 50.02 |
| Zero | 0.00 |
| Tare | Net 30.00 → 30.02 |

**Overall: REJECTED: FAIL**

---

## DEMO-003: Demo Precision Instruments DPB-6K (Class II, e = 0.001 kg, Max 6 kg). Optional, shows multi-class support

Class II bands: ±0.0005 kg up to 5 kg (≤ 5000e), ±0.001 kg above that.

| # | Test Load | Indicated Value | MPE (band) |
|---|---|---|---|
| 1 | 0.05 | 0.0500 | ±0.0005 (0.5e, `0<=m<=5000e`) |
| 2 | 5.00 | 5.0005 | ±0.0005 (0.5e, `0<=m<=5000e`) |
| 3 | 6.00 | 6.0010 | ±0.0010 (1e, `5000e<m<=20000e`) |

---

## 2.5-minute video click-through (10 steps)

**Prep (before you start recording):**
- Complete all 5 DEMO-001 modules with the readings above.
- Open its summary, click **Generate Official PDF Report** once, and keep that tab open.
- Sign out, or start the recording from the login page.

| # | Time | Action | Say / show |
|---|---|---|---|
| 1 | 0:00–0:10 | On the login page, enter `admin` / `admin123` and click **Sign In**. You land on the Dashboard. | "MetraSure digitises OIML R-76 verification of weighing instruments." Point at the stat cards. |
| 2 | 0:10–0:30 | Navbar → **Rule Engine**. Filter **Class III** + **Accuracy**. | Three rules: `0<=m<=500e` = 0.5e, `500e<m<=2000e` = 1e, `2000e<m<=10000e` = 1.5e. "Table 6 lives in the database: versioned and audited, not hard-coded." Switch the filter to **Class II** to show multi-class support. |
| 3 | 0:30–0:40 | Navbar → **Instruments** → DEMO-002 **View / Test →** → **Start Calibration Session →**. | "A Class III platform scale, e = 50 g." |
| 4 | 0:40–1:05 | On the **Accuracy Test** tab, enter the 5 DEMO-002 rows and click **Calculate Module**. | Type quickly; the rows are in the table above. |
| 5 | 1:05–1:25 | Point at the **MPE Limit** column, then click **Why?** on row 2. | "The engine computes m = load / e for each row and picks the band. Same +50 g error: it fails at 20 kg (0.5e) and passes at 50 kg and 120 kg." |
| 6 | 1:25–1:35 | Click **View Full Summary**. | The verdict reads **✗ REJECTED: FAIL**. |
| 7 | 1:35–1:55 | Click **Generate Official PDF Report**. | Point at the Load / Indication / Error / MPE / Result / **Rule ID** columns: "every row is traceable to the exact rule." |
| 8 | 1:55–2:10 | Switch to the prepared DEMO-001 PDF tab. | "A compliant scale: all 5 modules pass and it is certified." |
| 9 | 2:10–2:22 | Scan the PDF's QR code with a phone, or open its link. A phone scan only works against the deployed app, because the QR points at `FRONTEND_URL`. Locally, open `http://localhost:3000/verify/<token>` instead. | The public verification page confirms the report is genuine. |
| 10 | 2:22–2:30 | Navbar → **Rule Engine** → click the history icon on any rule. | "Every rule change is logged with who, when and why. Deterministic, auditable compliance." |
