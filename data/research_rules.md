# Rules transcribed from the Team 27 research page

This reference keeps the measurements and cues from the research page in one place. The active deep-squat values are read by `src/config.py` from `research_rules.json`; `.env` can override them for experiments. Other exercise notes are recorded here but are not active in the prototype because their movement phases, angle conventions, or thresholds are incomplete.

| Exercise | Research-page data | Prototype status |
| --- | --- | --- |
| Deep squat | Relative depth reference 32.1%; team adds a 3 percentage-point margin, giving 29.1%. Waist/hip recovery 0.48% with 0.02% error gives a 0.50% maximum drift. Head recovery 0.163% with 0.006% error gives a 0.169% maximum drift. | Implemented. The Python app reads 0.291, 0.005, and 0.00169 from `research_rules.json`. It uses nose-to-ankle image height as a scale approximation. |
| Plank | Angle from shoulder, hip, and foot: below 178° = too low; strictly between 178° and 192° = good; above 192° = too high. The notes do not classify exactly 178° or 192°. | Recorded, not implemented. Confirm the side of the angle and add a hold-duration rule. |
| Bicep curl | Angle from shoulder, elbow, and wrist: above 160° prompts “go up”; below 30° prompts “go down.” | Recorded, not implemented. These endpoint cues do not specify the complete rep transition. |
| Arm rainbow | Track upright position and arm angle; determine whether the camera is in front or behind. | Recorded, not implemented. No numeric threshold is supplied. |
| Farmer's carry | Use neck and waist; torso-to-vertical angle should be below 8°. | Recorded, not implemented. A duration or event rule is still needed. |
| Good morning | Chest/spine/waist angle below 84.5° is marked not good; upper-leg/lower-leg/foot angle below 12° is marked good. | Recorded, not implemented. Confirm the angle convention and how these two conditions combine. |

## How the squat values are used

The app counts a valid repetition only after the detected hip point moves down by at least 29.1% of its calibrated image height, returns near the standing position, and passes the two return-drift checks. These values were copied from the team notes; the program does not recalculate them from raw UI-PRMD files. The UI-PRMD archives are optional reference data for later comparison. Their Vicon/Kinect coordinate systems differ from MediaPipe's camera-image landmarks, so values should not be transferred without checking the calculations and camera setup.

The underlying transcription is in [`research_rules.json`](research_rules.json), which the prototype reads for its default squat thresholds.

## References listed in the team research page

- [SunFounder ESP32-CAM setup and streaming guide](https://www.sunfounder.com/blogs/news/esp32-cam-tutorial-step-by-step-guide-to-setup-streaming-and-troubleshooting)
- [UI-PRMD paper table cited for the deep-squat notes](https://pmc.ncbi.nlm.nih.gov/articles/PMC5773117/table/T2/) and the [UI-PRMD Zenodo dataset](https://zenodo.org/records/23104965)
- [GitHub angle calculation reference for plank](https://github.com/Vollkorn01/Deep-Learning-Fitness-Exercise-Correction-Keras/blob/master/calculateAngle.py)
- [GitHub bicep-curl counter reference](https://github.com/raxor555/Bicep-Curl-Counter/blob/main/bicepcurl.py)
- [Farmer's-carry paper PDF](https://link.springer.com/content/pdf/10.1186/s40798-019-0222-z.pdf)
- [Schellenberg et al., “Kinetic and kinematic differences between deadlifts and goodmornings”](https://doi.org/10.1186/2052-1847-5-27)

These are the links transcribed from the team page. The app currently reads the deep-squat numbers from the team's notes; it does not scrape these websites or train on the datasets.
