# Elective Navigator

Course registration prototype for **Yaşar University – Software Engineering**, focused on the hardest part of registration: **choosing electives**.

**Live demo:** https://bahar-dokur.github.io/elective-navigator/
**Demo video:** https://bahar-dokur.github.io/elective-navigator/demo.html

## The problem
- 70+ department electives and 150+ university electives, listed by code and title only
- Each elective counts only for certain slots (A pool, B pool or University pool) in a specific semester
- A wrong-pool pick is often discovered only at the graduation check

## What the prototype does
- Shows every elective slot in the curriculum, the pool it accepts and when it is due
- Ranks electives by the student's interests and grades in the courses they build on, and explains why
- Hides courses that clash with compulsory courses or are full
- Blocks wrong-pool picks (e.g. ME 4240 in an A slot), explains why, and suggests alternatives that count
- Auto-fills remaining slots, drafts next spring's plan, checks all rules and sends the plan to the advisor
- Exports the elective plan as a PNG

## Run it
Open `index.html` in any browser. No build step, no dependencies. Refresh the page to restart the demo.

## Repository
| Path | What |
|---|---|
| `index.html` | The whole app (HTML, CSS and JavaScript in one file) |
| `demo.html` | Page that plays the demo video |
| `media/elective-navigator-demo.mp4` | Demo video (English narration and subtitles) |
| `source/record.py` | Scripted demo recording with Playwright |
| `source/build.py` | Assembles frames, zooms, subtitles and narration with ffmpeg |
| `source/make_voice.ps1`, `MAKE_VOICE.bat` | Generates the narration with Windows' built-in voice |

## Data
Curriculum and elective pools come from the official 2025–26 Bologna listing of the Software Engineering program. Section times, seats and grades are **demo data**.

*Course project prototype, not the official Yaşar University system.*
