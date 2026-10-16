# Elective Navigator - narration generator for Windows (built-in voices)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $here "narration"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo } | Where-Object { $_.Culture.Name -like "en-*" }
if (-not $voices) { Write-Host "No English voice found. Add one: Settings > Time & language > Speech > Add voices (English US)."; Read-Host "Press Enter"; exit 1 }
$pick = $voices | Where-Object { $_.Name -like "*Zira*" } | Select-Object -First 1
if (-not $pick) { $pick = $voices | Select-Object -First 1 }
$s.SelectVoice($pick.Name)
$s.Rate = 1
Write-Host ("Voice: " + $pick.Name)
$lines = @(
  'This is Elective Navigator, our course registration prototype for Yaşar University Software Engineering.'
  'When we asked classmates about registration, electives came up first.'
  'There are dozens of them, each one only counts for certain slots, and a wrong pick is often discovered at the graduation check.'
  'We sign in as a demo student in the fourth year.'
  'The home page now shows elective progress at a glance: two slots completed, three due this term, and three more in spring.'
  'The Elective Planner lays out every elective slot in the curriculum, which pool it accepts, and when it''s due.'
  'We pick our interests: AI and data, and robotics.'
  'Electives are ranked by interest, and by how well this student did in the courses they build on. Every card explains why.'
  'Two switches hide everything that clashes with a compulsory course, or is already full.'
  'Details show the schedule, what the course builds on, and exactly which slots it counts toward.'
  'We add Machine Learning to slot A2.'
  'Now, a classic mistake: Robot Mechanics sounds perfect for a robotics fan.'
  'But it belongs to the B pool and is only offered in spring, so it wouldn''t count this term. The planner explains why, and offers robotics courses that do count.'
  'The last open slot is filled automatically, with the best clash-free match.'
  'One more click drafts next spring too, including Robot Mechanics, in the slot where it actually counts.'
  'The summary checks every rule: the right pools, no clashes, open seats, and thirty-seven of forty ECTS.'
  'We send it to the advisor, and download the plan.'
  'From scattered course codes to a complete, valid elective plan in under two minutes.'
  'That''s Elective Navigator. Thanks for watching.'
)
for ($i = 0; $i -lt $lines.Count; $i++) {
  $f = Join-Path $out ("{0:D2}.wav" -f ($i + 1))
  $s.SetOutputToWaveFile($f); $s.Speak($lines[$i]); $s.SetOutputToNull()
  Write-Host ("Saved " + $f)
}
$s.Dispose()
Write-Host "Done. Tell Claude the narration is ready."
Read-Host "Press Enter to close"
