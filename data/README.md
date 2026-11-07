# UI-PRMD reference data

The live app does not load UI-PRMD at runtime. The dataset is for offline inspection and for discussing whether the hand-entered squat rules are sensible. It contains Vicon and Kinect positions/angles for 10 rehabilitation movements, including deep squats (`m01`), and examples labelled as intentionally incorrect.

Download the [dataset record on Zenodo](https://zenodo.org/records/23104965). For a small first pass, extract only the segmented deep-squat files and corresponding incorrect segmented examples, if those archives are provided in the downloaded record. The text files use comma-separated values. Keep the extracted archive under `data/ui_prmd/`; this directory is ignored by Git.

The team's research notes propose a 2D squat depth threshold of 32.1%, then subtract a 3 percentage-point tolerance to get 29.1%. They also propose maximum return drift values of 0.5% for the hip/waist point and 0.169% for the head point. Those are currently entered in `.env.example`. This version uses detected nose-to-ankle image height as its scale instead of asking for a height in centimetres. That is a prototype choice, and the result is not directly interchangeable with Vicon/Kinect measurements. Validate any comparison carefully and ask the instructor or a qualified movement professional before describing these as clinical criteria.

If your team cites UI-PRMD in a report, cite A. Vakanski, H-p. Jun, D. Paul, and R. Baker, “A Data Set of Human Body Movements for Physical Rehabilitation Exercises,” *Data*, 3(1), 2 (2018), DOI: 10.3390/data3010002.
