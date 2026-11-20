# Rules transcribed from the Team 27 research page

This reference keeps the measurements and cues from the research page in one place. The deep-squat values are read by `src/config.py` from `research_rules.json`; `.env` can override them for experiments. The software now offers prototype modes for all six listed exercises. Some modes include clearly labeled timing or movement-cycle assumptions because the research notes do not fully define those parts.

| Exercise | Research-page data | Prototype status |
| --- | --- | --- |
| Deep squat | Relative depth reference 32.1%; team adds a 3 percentage-point margin, giving 29.1%. Waist/hip recovery 0.48% with 0.02% error gives a 0.50% maximum drift. Head recovery 0.163% with 0.006% error gives a 0.169% maximum drift. | Implemented. The Python app reads 0.291, 0.005, and 0.00169 from `research_rules.json`. It uses nose-to-ankle image height as a scale approximation. |
| Plank | Angle from shoulder, hip, and foot: below 178° = too low; strictly between 178° and 192° = good; above 192° = too high. The notes do not classify exactly 178° or 192°. | Prototype mode implemented. It accepts the inclusive 178°–192° range and counts a 10-second hold. The endpoints are assigned to good and 10 seconds is a demo duration; neither choice is specified by the notes. |
| Bicep curl | Angle from shoulder, elbow, and wrist: above 160° prompts “go up”; below 30° prompts “go down.” | Prototype mode implemented. It counts an extended (>160°) to flexed (<30°) to extended (>160°) cycle. The research gives the endpoints but not this rep sequence. |
| Arm rainbow | Track upright position and arm angle; determine whether the camera is in front or behind. | Prototype mode implemented for a front-facing camera. It counts one wrist rising above the shoulder and returning below it. The lean and wrist-height thresholds are provisional because the notes supply no numbers. |
| Farmer's carry | Use neck and waist; torso-to-vertical angle should be below 8°. | Prototype mode implemented. It uses shoulder-to-hip torso angle as an image landmark approximation and requires a 10-second hold. The notes do not define the hold duration or this landmark substitution. |
| Good morning | Chest/spine/waist angle below 84.5° is marked not good; upper-leg/lower-leg/foot angle below 12° is marked good. | Prototype mode implemented using hip and knee landmark angles. It applies the noted 84.5° and 12° checks, plus provisional 140° hinge and 160° standing endpoints to define a full repetition. The angle convention needs team confirmation. |

## How the squat values are used

The app counts a valid repetition only after the detected hip point moves down by at least 29.1% of its calibrated image height, returns near the standing position, and passes the two return-drift checks. These values were copied from the team notes; the program does not recalculate them from raw UI-PRMD files. The UI-PRMD archives are optional reference data for later comparison. Their Vicon/Kinect coordinate systems differ from MediaPipe's camera-image landmarks, so values should not be transferred without checking the calculations and camera setup.

The underlying transcription is in [`research_rules.json`](research_rules.json), which the app reads for all exercise modes. The tracking logic is in `src/exercise_modes.py`. Values under `prototype_rule`, `prototype_thresholds`, and `prototype_rep_thresholds` are added to make a runnable demo; they are not measurements from the research document.

## References listed in the team research page

- [SunFounder ESP32-CAM setup and streaming guide](https://www.sunfounder.com/blogs/news/esp32-cam-tutorial-step-by-step-guide-to-setup-streaming-and-troubleshooting)
- [UI-PRMD paper table cited for the deep-squat notes](https://pmc.ncbi.nlm.nih.gov/articles/PMC5773117/table/T2/) and the [UI-PRMD Zenodo dataset](https://zenodo.org/records/23104965)
- [GitHub angle calculation reference for plank](https://github.com/Vollkorn01/Deep-Learning-Fitness-Exercise-Correction-Keras/blob/master/calculateAngle.py)
- [GitHub bicep-curl counter reference](https://github.com/raxor555/Bicep-Curl-Counter/blob/main/bicepcurl.py)
- [Farmer's-carry paper PDF](https://link.springer.com/content/pdf/10.1186/s40798-019-0222-z.pdf)
- [Schellenberg et al., “Kinetic and kinematic differences between deadlifts and goodmornings”](https://doi.org/10.1186/2052-1847-5-27)

These are the links transcribed from the team page. The app currently reads the deep-squat numbers from the team's notes; it does not scrape these websites or train on the datasets.
