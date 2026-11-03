# GrainBrick V4.2 validation

V4.2 is the consolidated standalone release after V4.1.10. Version, launcher and manifest all identify V4.2. The app folder stays grainbrick-v4 to preserve user media paths. The original V4.1 standalone remains separate; the mistakenly named V4.1 Final package has been removed from the current release directory. Audio/control modules and native binaries are unchanged from the working V4.1.10 build; only version/log strings, release metadata, credits and installation documentation differ.

The complete V4.2 archive contains 226 bundled files plus RELEASE.json (227 files), about 15.9 MB compressed and 47.4 MB unpacked. It provides exactly GrainBrick V4.2.sh and grainbrick-v4 at the top level. Manifest/inventory/hash checks pass, as do executable launcher, pinned original engine, factory project/sample and required legal materials checks. Tests, Python caches, compiler tooling, logs, USB reports, old update packages, user JSON/state and personal media are excluded. The factory archive contains exactly one WAV and the AMBIENT preset.

60 host tests pass: the previous 56 runtime tests plus data importer tests for nested sample/recording/project trees, preference restoration, factory-project replacement, conflicting new personal media, running-app locks, invalid preference JSON, symlink boundaries and repeat-run protection. The actual standalone import shell launcher is exercised separately: copies succeed, backup files remain intact, Import_Report.txt is mode 0666, old runtime/log files are excluded, and a repeated run does not alter current preferences. Shell syntax validation passes.

A fresh V4.2 extract passes the original native ARM --live-controls check. The frozen-save, project and no-USB checks below passed on fresh extracts during the preceding consolidation; their audio/control runtime files are byte-identical in V4.2:

- --live-controls: physical mapped A/B/X/Y press/release routing, Y start/stop while frozen or paused, B stop then back, X direct SAMPLE return, A Freeze and SELECT pass-through. Fresh startup creates the runtime without previous installs.
- --frozen-save: physical MENU export, exact 768000-frame stereo 48 kHz / 16-bit PCM files, unique names, full buffer independent of grain/roam range, retained worker/freeze/loaded sample and rejected unfrozen saves.
- --project-playback: native output and moving read position, paused loading, restored browser selection, same-sample worker restart, moved legacy media paths, original START preview and original project handling.
- Separate fresh --input-unavailable installation: Internal output, only NO USB INPUT offered, blocked capture/recording without an interface, clear messages and working mode navigation.

All UI fixtures and logs remain under isolated work directories and are not packaged. USB/audio/process boundaries are mocked in the application UI tests. The V4.2 package therefore needs on-device installation/import confirmation; emulation does not establish USB audio timing or compatibility with the user's charging/data splitter. The AUDIO4c recorded startup click remains unresolved. No recorded-audio suppression or timing change is introduced.

The V4.2 import tool passes both the 60-test host suite and an actual shell-launcher test against a V4.2 destination. The import tool is a separate optional download, keeping the standalone package limited to its launcher and app. Existing development data is imported on the handheld from grainbrick-v4-backup; it is not embedded in the public release. The backup is never deleted by the importer.
